# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64
import hashlib

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountStatementImport(models.TransientModel):
    """
    Adds the mutasi-ai async import path to the OCA import wizard.

    When a Mutasi AI Backend is selected, ``import_file_button`` queues
    an ``account.statement.import.mutasi.ai.job`` instead of parsing
    the file synchronously, after rejecting the upload when a file
    with the same SHA-256 checksum was already handled by another job
    (see ``_check_mutasi_ai_duplicate``).
    """

    _inherit = "account.statement.import"

    mutasi_ai_backend_id = fields.Many2one(
        string="Mutasi AI Backend",
        comodel_name="account.statement.import.mutasi.ai.backend",
        help=(
            "Select a mutasi-ai backend to extract this bank statement file "
            "with AI instead of a regular file parser. The file is queued "
            "and processed in the background; leave empty to use other "
            "installed format parsers."
        ),
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if "mutasi_ai_backend_id" in fields_list and not res.get(
            "mutasi_ai_backend_id"
        ):
            journal_id = self.env.context.get("journal_id") or self.env.context.get(
                "default_journal_id"
            )
            if journal_id:
                journal = self.env["account.journal"].browse(journal_id)
                if journal.exists() and journal.default_mutasi_ai_backend_id:
                    res[
                        "mutasi_ai_backend_id"
                    ] = journal.default_mutasi_ai_backend_id.id
        return res

    def import_file_button(self):
        self.ensure_one()
        if self.mutasi_ai_backend_id:
            return self._enqueue_mutasi_ai_import()
        return super().import_file_button()

    def _enqueue_mutasi_ai_import(self):
        """Queue an asynchronous mutasi-ai import job for this wizard.

        Rejects the upload via ``_check_mutasi_ai_duplicate`` before
        any ``ir.attachment`` or job record is created, so a file that
        was already queued, processed, or imported is never sent to
        the (billed) mutasi-ai service again.

        :return: a ``display_notification`` client action that closes
            the wizard
        :rtype: dict
        """
        self.ensure_one()
        file_checksum = self._compute_mutasi_ai_file_checksum()
        self._check_mutasi_ai_duplicate(file_checksum)
        attachment = (
            self.env["ir.attachment"]
            .sudo()
            .create(self._prepare_mutasi_ai_attachment())
        )
        job = (
            self.env["account.statement.import.mutasi.ai.job"]
            .sudo()
            .create(self._prepare_mutasi_ai_job(attachment))
        )
        attachment.sudo().write(
            {
                "res_model": "account.statement.import.mutasi.ai.job",
                "res_id": job.id,
            }
        )
        job.action_enqueue()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Mutasi AI"),
                "message": _(
                    "Bank statement '%s' queued for AI extraction. It is "
                    "processed in the background; you can follow its progress "
                    "from the related bank statement."
                )
                % (self.statement_filename or ""),
                "type": "success",
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }

    def _compute_mutasi_ai_file_checksum(self):
        """Compute the SHA-256 hex digest of the decoded uploaded file.

        Matches exactly the ``Idempotency-Key`` value
        ``AccountStatementImportMutasiAiBackend._call_service`` sends
        to the mutasi-ai service for the same file content. Computed
        independently here so a duplicate upload can be rejected
        before any HTTP call is made.

        :return: SHA-256 hex digest of ``self.statement_file`` decoded
            from base64
        :rtype: str
        """
        self.ensure_one()
        data_file = base64.b64decode(self.statement_file or b"")
        return hashlib.sha256(data_file).hexdigest()

    def _check_mutasi_ai_duplicate(self, file_checksum):
        """Reject re-uploading a file already handled by another job.

        Searches for another
        ``account.statement.import.mutasi.ai.job`` with the same
        ``file_checksum`` whose ``state`` means the file was already
        queued, processed, or successfully imported (``queued``,
        ``processing``, ``done``, ``already_imported``). Jobs in
        ``draft``, ``need_review``, or ``failed`` do not block, so a
        re-upload after a failure remains possible. An empty
        ``file_checksum`` never matches, so old jobs created before
        this field existed are ignored.

        :param file_checksum: SHA-256 hex digest of the uploaded file,
            as returned by ``_compute_mutasi_ai_file_checksum``
        :type file_checksum: str
        :raises UserError: if a blocking duplicate job is found
        """
        self.ensure_one()
        if not file_checksum:
            return
        duplicate_job = (
            self.env["account.statement.import.mutasi.ai.job"]
            .sudo()
            .search(
                [
                    ("file_checksum", "=", file_checksum),
                    (
                        "state",
                        "in",
                        ("queued", "processing", "done", "already_imported"),
                    ),
                ],
                limit=1,
            )
        )
        if not duplicate_job:
            return
        error_message = (
            _(
                """
Context: Enqueue mutasi-ai statement import
Database ID: %s
Problem: A file with the same content was already imported by job '%s'
Solution: Check job '%s' instead of uploading the same file again
"""
            )
            % (self.id, duplicate_job.name, duplicate_job.name)
        )
        raise UserError(error_message)

    def _prepare_mutasi_ai_attachment(self):
        self.ensure_one()
        return {
            "name": self.statement_filename or "statement",
            "datas": self.statement_file,
            "type": "binary",
        }

    def _prepare_mutasi_ai_job(self, attachment):
        """Build the ``account.statement.import.mutasi.ai.job`` values.

        Extension point: override to add fields to the job without
        touching ``_enqueue_mutasi_ai_import``.

        :param attachment: the ``ir.attachment`` already created for
            the uploaded file
        :type attachment: recordset of ``ir.attachment``
        :return: dict of job values, including ``file_checksum``
        :rtype: dict
        """
        self.ensure_one()
        journal_id = self.env.context.get("journal_id")
        statement_id = False
        if self.env.context.get("active_model") == "account.bank.statement":
            active_ids = self.env.context.get("active_ids") or []
            if active_ids:
                statement_id = active_ids[0]
        return {
            "attachment_id": attachment.id,
            "statement_filename": self.statement_filename,
            "journal_id": journal_id,
            "statement_id": statement_id,
            "backend_id": self.mutasi_ai_backend_id.id,
            "file_checksum": self._compute_mutasi_ai_file_checksum(),
        }
