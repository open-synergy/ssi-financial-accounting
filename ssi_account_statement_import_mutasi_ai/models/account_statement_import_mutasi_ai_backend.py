# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import hashlib
import mimetypes

import requests

from odoo import _, fields, models
from odoo.exceptions import UserError

# mutasi-ai default MAX_UPLOAD_BYTES (~15 MiB). The service itself enforces
# this limit; checking it client-side avoids uploading a file that the
# service will reject anyway.
_MAX_UPLOAD_BYTES = 15 * 1024 * 1024


class AccountStatementImportMutasiAiBackend(models.Model):
    """
    Represents a connection profile to a mutasi-ai bank statement
    extraction service (FastAPI, OAuth2/Bearer resource server).

    Holds the base URL and static bearer token used to call the
    ``POST /api/v1/statements`` endpoint, and provides the seams used by
    the async import job: ``_call_service`` (HTTP) and
    ``_transform_result`` (pure, no HTTP) to convert the service response
    into the triplet expected by OCA ``account.statement.import``.
    """

    _name = "account.statement.import.mutasi.ai.backend"
    _inherit = ["mixin.master_data"]
    _description = "Mutasi AI Statement Import Backend"

    base_url = fields.Char(
        string="Base URL",
        required=True,
        help="Base URL of the mutasi-ai service, without trailing slash "
        "(e.g. https://carik.cantum.co.id). The wizard calls "
        "POST {base_url}/api/v1/statements to upload the bank statement file.",
    )
    bearer_token = fields.Char(
        string="Bearer Token",
        required=True,
        help="Static bearer token sent as 'Authorization: Bearer <token>' on "
        "every call to the mutasi-ai service (e.g. an Authentik long-lived "
        "token or the service's DEV_BEARER_TOKEN).",
    )
    model = fields.Char(
        string="Extraction Model",
        help="Optional Claude model override sent as the 'model' form field. "
        "Leave empty to use the service's default model.",
    )
    timeout_seconds = fields.Integer(
        string="Timeout (seconds)",
        default=600,
        required=True,
        help="Maximum time to wait for the mutasi-ai extraction response. "
        "The service itself may take up to CLAUDE_EXTRACTION_TIMEOUT_SECONDS "
        "(default 600s) to analyze a single file.",
    )
    verify_ssl = fields.Boolean(
        string="Verify SSL",
        default=True,
        help="Verify the service's TLS certificate. Disable only for "
        "self-signed certificates in a development environment.",
    )
    currency_id = fields.Many2one(
        string="Fallback Currency",
        comodel_name="res.currency",
        help="Currency used when the mutasi-ai response does not include a "
        "currency_code. If both this field and the response omit the "
        "currency, the import will fail with a missing currency error.",
    )

    def _get_headers(self, idempotency_key=None):
        """Build the HTTP headers used to call the mutasi-ai service."""
        self.ensure_one()
        headers = {"Authorization": "Bearer %s" % self.bearer_token}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return headers

    def _call_service(self, data_file, filename):
        """Upload a bank statement file and return the raw JSON response.

        :param data_file: raw file bytes (already base64-decoded)
        :param filename: original filename, used for content-type guessing
            and the multipart filename
        :return: parsed JSON body of the ``StatementExtractionRead`` response
        :rtype: dict
        """
        self.ensure_one()
        if len(data_file) > _MAX_UPLOAD_BYTES:
            error_message = (
                _(
                    """
Context: Upload bank statement file to mutasi-ai service
Database ID: %s
Problem: File '%s' is %d bytes, larger than the service limit of %d bytes
Solution: Split the file or use a smaller export of the bank statement
"""
                )
                % (self.id, filename, len(data_file), _MAX_UPLOAD_BYTES)
            )
            raise UserError(error_message)

        content_type = mimetypes.guess_type(filename or "")[0] or (
            "application/octet-stream"
        )
        idempotency_key = hashlib.sha256(data_file).hexdigest()

        try:
            response = requests.post(
                "%s/api/v1/statements" % self.base_url.rstrip("/"),
                files={"file": (filename or "statement", data_file, content_type)},
                data={"model": self.model} if self.model else None,
                headers=self._get_headers(idempotency_key=idempotency_key),
                timeout=self.timeout_seconds,
                verify=self.verify_ssl,
            )
        except requests.exceptions.RequestException as exc:
            error_message = (
                _(
                    """
Context: Upload bank statement file to mutasi-ai service
Database ID: %s
Problem: Could not reach mutasi-ai backend '%s': %s
Solution: Check the Base URL, network connectivity, and that the service \
is running, then retry
"""
                )
                % (self.id, self.base_url, str(exc))
            )
            raise UserError(error_message) from exc

        if response.status_code not in (200, 201):
            error_message = (
                _(
                    """
Context: Upload bank statement file to mutasi-ai service
Database ID: %s
Problem: mutasi-ai backend '%s' returned HTTP %d: %s
Solution: Verify the Bearer Token and Base URL configuration, or check the \
mutasi-ai service logs
"""
                )
                % (self.id, self.base_url, response.status_code, response.text[:500])
            )
            raise UserError(error_message)

        try:
            return response.json()
        except ValueError as exc:
            error_message = (
                _(
                    """
Context: Upload bank statement file to mutasi-ai service
Database ID: %s
Problem: mutasi-ai backend '%s' returned a non-JSON response
Solution: Check the mutasi-ai service logs for the actual error
"""
                )
                % (self.id, self.base_url)
            )
            raise UserError(error_message) from exc

    def _transform_result(self, result_json, filename):
        """Convert a mutasi-ai ``StatementExtractionRead`` JSON body into
        the OCA ``account.statement.import`` triplet.

        This is the pure seam for testing: no HTTP call, just a dict-in
        dict-out transformation.

        :param result_json: parsed JSON body returned by ``_call_service``
        :param filename: original filename, used to build a fallback
            ``unique_import_id`` when the service omits one
        :return: ``(currency_code, account_number, statements)`` triplet
        :rtype: tuple
        """
        self.ensure_one()
        if result_json.get("status") == "failed":
            error_message = (
                _(
                    """
Context: Extract bank statement via mutasi-ai service
Database ID: %s
Problem: mutasi-ai extraction failed: %s
Solution: Check the source file quality (scan/photo legibility) and retry, \
or use the Reprocess action on the mutasi-ai service if the issue is transient
"""
                )
                % (self.id, result_json.get("error") or _("unknown error"))
            )
            raise UserError(error_message)

        extraction_result = result_json.get("result") or {}
        currency_code = extraction_result.get("currency_code") or (
            self.currency_id.name if self.currency_id else False
        )
        if not currency_code:
            error_message = (
                _(
                    """
Context: Extract bank statement via mutasi-ai service
Database ID: %s
Problem: mutasi-ai response has no currency_code and no Fallback Currency \
is configured on this backend
Solution: Set a Fallback Currency on the mutasi-ai backend configuration
"""
                )
                % (self.id,)
            )
            raise UserError(error_message)

        account_number = extraction_result.get("account_number")

        statements = []
        for st_idx, source_statement in enumerate(
            extraction_result.get("statements") or []
        ):
            transactions = []
            for tx_idx, source_tx in enumerate(
                source_statement.get("transactions") or []
            ):
                unique_import_id = source_tx.get(
                    "unique_import_id"
                ) or "mutasi-ai-%s-%s-%s" % (filename, st_idx, tx_idx)
                transactions.append(
                    {
                        "payment_ref": source_tx.get("payment_ref") or "/",
                        "date": source_tx.get("date"),
                        "amount": source_tx.get("amount"),
                        "unique_import_id": unique_import_id,
                        "account_number": source_tx.get("account_number"),
                        "partner_name": source_tx.get("partner_name"),
                    }
                )
            statement_date = source_statement.get("date") or (
                transactions[0]["date"] if transactions else False
            )
            statements.append(
                {
                    "name": source_statement.get("name"),
                    "date": statement_date,
                    "balance_start": source_statement.get("balance_start"),
                    "balance_end_real": source_statement.get("balance_end_real"),
                    "transactions": transactions,
                }
            )

        if not statements:
            error_message = (
                _(
                    """
Context: Extract bank statement via mutasi-ai service
Database ID: %s
Problem: mutasi-ai response contains no statements
Solution: Check the source file quality (scan/photo legibility) and retry
"""
                )
                % (self.id,)
            )
            raise UserError(error_message)

        return (currency_code, account_number, statements)

    def action_test_connection(self):
        for record in self.sudo():
            result = record._test_connection()
        return result

    def _test_connection(self):
        """Call GET /api/v1/health then GET /api/v1/me to verify the Base
        URL and Bearer Token, and report the outcome to the user."""
        self.ensure_one()
        base_url = self.base_url.rstrip("/")

        try:
            health_response = requests.get(
                "%s/api/v1/health" % base_url,
                timeout=10,
                verify=self.verify_ssl,
            )
        except requests.exceptions.RequestException as exc:
            error_message = (
                _(
                    """
Context: Test connection to mutasi-ai service
Database ID: %s
Problem: Could not reach '%s/api/v1/health': %s
Solution: Check the Base URL and network connectivity
"""
                )
                % (self.id, base_url, str(exc))
            )
            raise UserError(error_message) from exc

        if health_response.status_code != 200:
            error_message = (
                _(
                    """
Context: Test connection to mutasi-ai service
Database ID: %s
Problem: '%s/api/v1/health' returned HTTP %d
Solution: Check that the mutasi-ai service is running and the Base URL is correct
"""
                )
                % (self.id, base_url, health_response.status_code)
            )
            raise UserError(error_message)

        try:
            me_response = requests.get(
                "%s/api/v1/me" % base_url,
                headers=self._get_headers(),
                timeout=10,
                verify=self.verify_ssl,
            )
        except requests.exceptions.RequestException as exc:
            error_message = (
                _(
                    """
Context: Test connection to mutasi-ai service
Database ID: %s
Problem: Could not reach '%s/api/v1/me': %s
Solution: Check the Base URL and network connectivity
"""
                )
                % (self.id, base_url, str(exc))
            )
            raise UserError(error_message) from exc

        if me_response.status_code != 200:
            error_message = (
                _(
                    """
Context: Test connection to mutasi-ai service
Database ID: %s
Problem: '%s/api/v1/me' returned HTTP %d — the Bearer Token was rejected
Solution: Verify the Bearer Token configured on this backend
"""
                )
                % (self.id, base_url, me_response.status_code)
            )
            raise UserError(error_message)

        health_data = health_response.json()
        me_data = me_response.json()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Connection Successful"),
                "message": _("mutasi-ai %s — authenticated as %s")
                % (
                    health_data.get("version") or "?",
                    me_data.get("sub") or me_data.get("name") or "?",
                ),
                "type": "success",
                "sticky": False,
            },
        }
