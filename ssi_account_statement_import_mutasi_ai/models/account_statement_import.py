# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models


class AccountStatementImport(models.TransientModel):
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
        self.ensure_one()
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

    def _prepare_mutasi_ai_attachment(self):
        self.ensure_one()
        return {
            "name": self.statement_filename or "statement",
            "datas": self.statement_file,
            "type": "binary",
        }

    def _prepare_mutasi_ai_job(self, attachment):
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
        }
