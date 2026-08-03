# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64
import json
import logging
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Extra grace period, on top of the backend's own `timeout_seconds`, before
# a `queued` job whose `queue_job_id` is still `started` is considered
# orphaned by a dead worker (see `_compute_retry_ok`).
_STUCK_JOB_MARGIN = timedelta(seconds=300)


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
    file_checksum = fields.Char(
        string="File Checksum",
        readonly=True,
        copy=False,
        index=True,
        help="SHA-256 hex digest of the decoded content of the uploaded "
        "file. Used by the import wizard to reject re-uploading a file "
        "that was already queued, processed, or successfully imported "
        "by another job.",
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
            ("done", "Done"),
            ("need_review", "Need Review"),
            ("already_imported", "Already Imported"),
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
            "Done = statement imported successfully, "
            "Need Review = imported but mutasi-ai flagged low confidence, "
            "Already Imported = every transaction in the file had "
            "already been imported previously, so no new statement was "
            "created, "
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
    notification_message = fields.Text(
        string="Import Notification",
        readonly=True,
        copy=False,
        help="Feedback returned by the import wizard about the outcome "
        "of this job, e.g. how many transactions were ignored because "
        "they had already been imported. Empty when the wizard reported "
        "nothing noteworthy.",
    )
    queue_job_id = fields.Many2one(
        string="Queue Job",
        comodel_name="queue.job",
        readonly=True,
        copy=False,
        ondelete="set null",
        help="Background queue_job record running this job's ``_run()``. "
        "Set when the job is enqueued via ``_enqueue()``. Used to tell "
        "whether a 'Queued' job whose worker died is safe to retry.",
    )
    retry_ok = fields.Boolean(
        string="Retry Allowed",
        compute="_compute_retry_ok",
        compute_sudo=True,
        help="Technical field telling whether the Retry button/action "
        "may run right now. True for 'Failed' and 'Need Review' jobs, "
        "and for 'Queued' jobs whose background queue_job is missing, "
        "already finished, or has been running past the backend's "
        "configured timeout — all signs that the worker that was "
        "supposed to process it has died, leaving the job stuck.",
    )

    @api.depends(
        "state",
        "queue_job_id.state",
        "queue_job_id.date_started",
        "queue_job_id.date_enqueued",
        "queue_job_id.date_created",
        "backend_id.timeout_seconds",
    )
    def _compute_retry_ok(self):
        """Decide whether the Retry action is currently allowed.

        See the module's backlog issue #114 for the four rules this
        implements: a job can be retried when it is ``failed`` or
        ``need_review``, or when it is ``queued`` but its paired
        ``queue_job_id`` shows the background worker is no longer (or
        never was) actually running it.
        """
        now = fields.Datetime.now()
        for record in self:
            result = False
            if record.state in ("failed", "need_review"):
                result = True
            elif record.state == "queued":
                result = record._queued_retry_ok(now)
            record.retry_ok = result

    def _queued_retry_ok(self, now):
        """Return whether a ``queued`` job's background job looks dead.

        :param now: current datetime, injected so the whole record set
            computed together compares against the same instant
        :type now: datetime.datetime
        :return: ``True`` when ``queue_job_id`` is empty, already
            finished (``done``/``failed``/``cancelled``), or still
            "running" (``wait_dependencies``/``pending``/``enqueued``/
            ``started``) well past ``backend_id.timeout_seconds``
        :rtype: bool
        """
        self.ensure_one()
        queue_job = self.queue_job_id
        if not queue_job:
            return True
        if queue_job.state in ("done", "failed", "cancelled"):
            return True
        if queue_job.state in (
            "wait_dependencies",
            "pending",
            "enqueued",
            "started",
        ):
            started_at = (
                queue_job.date_started
                or queue_job.date_enqueued
                or queue_job.date_created
            )
            if not started_at:
                return False
            timeout = timedelta(seconds=self.backend_id.timeout_seconds)
            return now - started_at > timeout + _STUCK_JOB_MARGIN
        return False

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
        """Move this job to ``queued`` and delay its ``_run()``.

        Stores the resulting ``queue.job`` record on ``queue_job_id``
        (via ``Job.db_record()``) so ``_compute_retry_ok`` can later
        tell whether the background worker is still alive.
        """
        self.ensure_one()
        self.write({"state": "queued", "error_message": False})
        delayable_job = self.with_delay(
            description=_("Import bank statement via mutasi-ai: %s")
            % (self.statement_filename or self.name)
        )._run()
        self.write({"queue_job_id": delayable_job.db_record().id})

    def action_retry(self):
        for record in self.sudo():
            record._retry()

    def _retry(self):
        """Re-enqueue this job, raising when ``retry_ok`` is false.

        :raises UserError: when ``retry_ok`` is false, i.e. the job is
            neither ``failed``/``need_review`` nor a ``queued`` job
            whose background ``queue_job_id`` looks dead
        """
        self.ensure_one()
        if not self.retry_ok:
            error_message = (
                _(
                    """
Context: Retry mutasi-ai statement import job
Database ID: %s
Problem: Job is in state '%s' and cannot be retried right now
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

    def _prepare_notification_message(self, result):
        """Build the user-facing summary of an ``import_single_statement``
        call.

        Extension point: override in a glue module to change how the
        wizard's ``result`` dict is rendered on the job.

        Normally joins the ``message`` of every dict in
        ``result["notifications"]`` (one per line), e.g. how many
        transactions were ignored as duplicates. ``result["details"]``
        (the ignored line ids) is intentionally not stored.

        ``_create_bank_statements``/``_update_bank_statements`` (in
        ``ssi_account_statement_import``/upstream OCA
        ``account_statement_import``) return early, before building
        ``notifications``, whenever *every* transaction in the file was
        already imported (``result["statement_ids"]`` stays empty).
        Without a fallback that specific case would leave this field
        empty even though it is the one situation users most need an
        explanation for, so a generic duplicate-file message is
        synthesized when both ``notifications`` and ``statement_ids``
        are empty.

        :param result: the ``result`` dict built by
            ``account.statement.import.import_single_statement``
            (keys ``statement_ids`` and ``notifications``)
        :return: the notification text, or ``False`` when there is
            nothing to report
        """
        notifications = result.get("notifications") or []
        if notifications:
            messages = [
                notification["message"]
                for notification in notifications
                if notification.get("message")
            ]
            return "\n".join(messages) if messages else False
        if not result.get("statement_ids"):
            return _(
                "All transactions in this file had already been "
                "imported previously (duplicates), so no new bank "
                "statement was created."
            )
        return False

    def _run(self):
        """Call the mutasi-ai service and import the resulting transactions.

        Meant to be invoked via ``with_delay()``. Never re-raises: any
        failure is caught and recorded on ``state`` / ``error_message`` so
        the job can be inspected and retried from the UI, instead of
        relying on queue_job's own retry/failure handling.
        """
        self.ensure_one()
        try:
            data_file = base64.b64decode(self.attachment_id.datas or b"")
            filename = self.statement_filename or self.attachment_id.name or "statement"

            response_json = self.backend_id._call_service(data_file, filename)
            external_status = response_json.get("status")
            triplet = self.backend_id._transform_result(
                response_json, filename, file_checksum=self.file_checksum
            )

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

            if not result["statement_ids"]:
                # Every transaction in the file was already imported, so
                # there is nothing left to review; this overrides
                # ``external_status`` even when the service itself
                # flagged the file as "need_review".
                state = "already_imported"
            else:
                state = "need_review" if external_status == "need_review" else "done"

            self.write(
                {
                    "state": state,
                    "external_id": response_json.get("id"),
                    "external_status": external_status,
                    "response_json": json.dumps(response_json),
                    "statement_ids": [(6, 0, result["statement_ids"])],
                    "error_message": False,
                    "notification_message": self._prepare_notification_message(result),
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
