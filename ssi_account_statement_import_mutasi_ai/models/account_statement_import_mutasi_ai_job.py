# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64
import json
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountStatementImportMutasiAiJob(models.Model):
    """
    Tracks one asynchronous bank statement extraction request sent to a
    mutasi-ai backend.

    A job is created by the ``account.statement.import`` wizard when a
    Mutasi AI Backend is selected, then processed in the background via
    ``queue_job`` (``_run``) since a single extraction can take up to the
    backend's configured timeout. Progress and failures are tracked on
    ``state`` / ``error_message`` so users can monitor and retry imports
    without blocking the web request.
    """

    _name = "account.statement.import.mutasi.ai.job"
    _description = "Mutasi AI Statement Import Job"
    _order = "create_date desc"

    name = fields.Char(
        string="Reference",
        required=True,
        readonly=True,
        copy=False,
        default="New",
        help="Sequential reference of this import job.",
    )
    attachment_id = fields.Many2one(
        string="Statement File",
        comodel_name="ir.attachment",
        required=True,
        readonly=True,
        help="Original bank statement file uploaded by the user and sent "
        "to the mutasi-ai service.",
    )
    statement_filename = fields.Char(
        string="Filename",
        readonly=True,
        help="Original filename of the uploaded bank statement file.",
    )
    journal_id = fields.Many2one(
        string="Journal",
        comodel_name="account.journal",
        readonly=True,
        domain=[("type", "=", "bank")],
        help="Bank journal the import was launched from, if any. When set, "
        "it constrains which journal the resulting bank statement is "
        "attached to; when empty, the journal is resolved from the "
        "account number returned by mutasi-ai.",
    )
    statement_id = fields.Many2one(
        string="Target Statement",
        comodel_name="account.bank.statement",
        readonly=True,
        help="Existing bank statement the import was launched from (e.g. "
        "via its 'Import Statement' button), if any. When set, the "
        "extracted transactions are added to this statement instead of "
        "creating a new one.",
    )
    backend_id = fields.Many2one(
        string="Mutasi AI Backend",
        comodel_name="account.statement.import.mutasi.ai.backend",
        required=True,
        readonly=True,
        help="Backend configuration used to call the mutasi-ai service.",
    )
    state = fields.Selection(
        string="Status",
        selection=[
            ("draft", "Draft"),
            ("queued", "Queued"),
            ("processing", "Processing"),
            ("done", "Done"),
            ("need_review", "Need Review"),
            ("failed", "Failed"),
        ],
        default="draft",
        required=True,
        readonly=True,
        copy=False,
        help=(
            "Job status: "
            "Draft = not yet queued, "
            "Queued = waiting for a queue_job worker, "
            "Processing = currently calling the mutasi-ai service, "
            "Done = statement imported successfully, "
            "Need Review = imported but mutasi-ai flagged low confidence, "
            "Failed = the service call or import raised an error."
        ),
    )
    external_id = fields.Char(
        string="Mutasi AI Extraction ID",
        readonly=True,
        copy=False,
        help="ID of the extraction record on the mutasi-ai service "
        "(StatementExtractionRead.id).",
    )
    external_status = fields.Char(
        string="Mutasi AI Status",
        readonly=True,
        copy=False,
        help="Raw status returned by the mutasi-ai service "
        "(ok / need_review / failed).",
    )
    error_message = fields.Text(
        string="Error Message",
        readonly=True,
        copy=False,
        help="Error raised while calling the mutasi-ai service or "
        "importing the extracted transactions.",
    )
    response_json = fields.Text(
        string="Raw Response",
        readonly=True,
        copy=False,
        help="Raw JSON response from the mutasi-ai service, kept for "
        "troubleshooting.",
    )
    statement_ids = fields.Many2many(
        string="Bank Statements",
        comodel_name="account.bank.statement",
        relation="account_statement_import_mutasi_ai_job_statement_rel",
        column1="job_id",
        column2="statement_id",
        readonly=True,
        copy=False,
        help="Bank statement(s) created from this job's extracted " "transactions.",
    )

    @api.model
    def create(self, vals):
        if vals.get("name", "New") in (False, "New"):
            vals["name"] = (
                self.env["ir.sequence"].next_by_code(
                    "account.statement.import.mutasi.ai.job"
                )
                or "New"
            )
        return super().create(vals)

    def action_enqueue(self):
        for record in self.sudo():
            record._enqueue()

    def _enqueue(self):
        self.ensure_one()
        self.write({"state": "queued", "error_message": False})
        self.with_delay(
            description=_("Import bank statement via mutasi-ai: %s")
            % (self.statement_filename or self.name)
        )._run()

    def action_retry(self):
        for record in self.sudo():
            record._retry()

    def _retry(self):
        self.ensure_one()
        if self.state not in ("failed", "need_review"):
            error_message = (
                _(
                    """
Context: Retry mutasi-ai statement import job
Database ID: %s
Problem: Job is in state '%s', only 'Failed' or 'Need Review' jobs can be retried
Solution: Wait for the current job to finish, or check its result
"""
                )
                % (self.id, self.state)
            )
            raise UserError(error_message)
        self._enqueue()

    def action_open_statements(self):
        for record in self.sudo():
            result = record._open_statements()
        return result

    def _open_statements(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "account.action_bank_statement_tree"
        )
        action["domain"] = [("id", "in", self.statement_ids.ids)]
        return action

    def _run(self):
        """Call the mutasi-ai service and import the resulting transactions.

        Meant to be invoked via ``with_delay()``. Never re-raises: any
        failure is caught and recorded on ``state`` / ``error_message`` so
        the job can be inspected and retried from the UI, instead of
        relying on queue_job's own retry/failure handling.
        """
        self.ensure_one()
        self.write({"state": "processing"})
        try:
            data_file = base64.b64decode(self.attachment_id.datas or b"")
            filename = self.statement_filename or self.attachment_id.name or "statement"

            response_json = self.backend_id._call_service(data_file, filename)
            external_status = response_json.get("status")
            triplet = self.backend_id._transform_result(response_json, filename)

            import_context = {}
            if self.journal_id:
                import_context["journal_id"] = self.journal_id.id
            if self.statement_id:
                # Mirrors the context the base wizard normally receives when
                # opened from an existing statement's "Import Statement"
                # button, so `import_single_statement` updates it instead
                # of creating a new one.
                import_context["active_model"] = "account.bank.statement"
                import_context["active_ids"] = [self.statement_id.id]
            wizard = (
                self.env["account.statement.import"]
                .sudo()
                .with_context(**import_context)
                .create(
                    {
                        "statement_file": self.attachment_id.datas,
                        "statement_filename": filename,
                    }
                )
            )
            result = {"statement_ids": [], "notifications": []}
            wizard.import_single_statement(triplet, result)

            state = "need_review" if external_status == "need_review" else "done"
            if not result["statement_ids"]:
                state = "need_review"

            self.write(
                {
                    "state": state,
                    "external_id": response_json.get("id"),
                    "external_status": external_status,
                    "response_json": json.dumps(response_json),
                    "statement_ids": [(6, 0, result["statement_ids"])],
                    "error_message": False,
                }
            )
        except Exception as exc:  # noqa: BLE001 - job must never propagate
            _logger.exception(
                "mutasi-ai import job %s failed",
                self.id,
            )
            self.write(
                {
                    "state": "failed",
                    "error_message": str(exc),
                }
            )
