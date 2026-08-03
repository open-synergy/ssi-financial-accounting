# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64
import hashlib
from unittest.mock import Mock, patch

from odoo.exceptions import AccessError, UserError
from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase

_BACKEND_MODEL = "account.statement.import.mutasi.ai.backend"
_JOB_MODEL = "account.statement.import.mutasi.ai.job"
_CALL_SERVICE_PATH = (
    "odoo.addons.ssi_account_statement_import_mutasi_ai.models."
    "account_statement_import_mutasi_ai_backend."
    "AccountStatementImportMutasiAiBackend._call_service"
)
_REQUESTS_GET_PATH = (
    "odoo.addons.ssi_account_statement_import_mutasi_ai.models."
    "account_statement_import_mutasi_ai_backend.requests.get"
)


def _sample_response(
    status="ok",
    unique_suffix="a",
    currency_code="IDR",
    balance_start=1000000.0,
    balance_end_real=1300000.0,
):
    """Build a fake mutasi-ai ``StatementExtractionRead`` JSON response.

    :param status: top-level ``status`` field (``ok``/``need_review``/
        ``failed``)
    :param unique_suffix: appended to ``id`` and every transaction's
        ``unique_import_id`` so distinct calls do not collide
    :param currency_code: ``result.currency_code``
    :param balance_start: ``result.statements[0].balance_start``; pass
        ``None`` to simulate the service omitting the opening balance
    :param balance_end_real: ``result.statements[0].balance_end_real``;
        pass ``None`` to simulate the service omitting the closing
        balance
    :return: a JSON-serializable dict shaped like the real service
        response
    :rtype: dict
    """
    return {
        "id": "stmt_test_%s" % unique_suffix,
        "status": status,
        "source_filename": "statement.pdf",
        "content_type": "application/pdf",
        "model": None,
        "error": None,
        "result": {
            "currency_code": currency_code,
            "account_number": None,
            "warnings": [],
            "statements": [
                {
                    "name": "STMT-1",
                    "date": "2026-01-31",
                    "balance_start": balance_start,
                    "balance_end_real": balance_end_real,
                    "transactions": [
                        {
                            "date": "2026-01-05",
                            "amount": 500000.0,
                            "payment_ref": "TRANSFER MASUK",
                            "unique_import_id": "mutasi-ai-tx-%s-1" % unique_suffix,
                            "account_number": None,
                            "partner_name": "Budi",
                            "ref": None,
                        },
                        {
                            "date": "2026-01-10",
                            "amount": -200000.0,
                            "payment_ref": "PEMBAYARAN",
                            "unique_import_id": "mutasi-ai-tx-%s-2" % unique_suffix,
                            "account_number": None,
                            "partner_name": None,
                            "ref": None,
                        },
                    ],
                }
            ],
        },
    }


@tagged("post_install", "-at_install")
class TestImportMutasiAi(TransactionCase):
    def setUp(self):
        super().setUp()
        self.backend = self.env[_BACKEND_MODEL].create(
            {
                "name": "Test Backend",
                "code": "TEST-BACKEND",
                "base_url": "https://carik.example.com",
                "bearer_token": "test-token",
            }
        )
        self.bank_journal = self.env["account.journal"].search(
            [("type", "=", "bank")], limit=1
        )
        # Use the company's default currency so _match_journal/_match_currency
        # can resolve the journal regardless of which currencies are active
        # in the test database (mirrors ssi_account_statement_import_pdf).
        self.company_currency = self.env.company.currency_id.name

    def _make_attachment(self, filename="statement.pdf"):
        return self.env["ir.attachment"].create(
            {
                "name": filename,
                "datas": base64.b64encode(b"dummy pdf content"),
                "type": "binary",
            }
        )

    def _make_job(self, unique_suffix="a", filename="statement.pdf"):
        attachment = self._make_attachment(filename)
        return self.env[_JOB_MODEL].create(
            {
                "attachment_id": attachment.id,
                "statement_filename": filename,
                "journal_id": self.bank_journal.id if self.bank_journal else False,
                "backend_id": self.backend.id,
            }
        )

    # ------------------------------------------------------------------
    # _transform_result — pure seam, no HTTP
    # ------------------------------------------------------------------

    def test_transform_result_returns_triplet(self):
        response = _sample_response()
        currency_code, account_number, statements = self.backend._transform_result(
            response, "statement.pdf"
        )
        self.assertEqual(currency_code, "IDR")
        self.assertIsNone(account_number)
        self.assertEqual(len(statements), 1)

        transactions = statements[0]["transactions"]
        self.assertEqual(len(transactions), 2)
        self.assertEqual(transactions[0]["amount"], 500000.0)
        self.assertEqual(transactions[1]["amount"], -200000.0)
        self.assertEqual(transactions[0]["payment_ref"], "TRANSFER MASUK")
        self.assertNotIn("ref", transactions[0])

    def test_transform_result_fallback_unique_import_id(self):
        response = _sample_response()
        response["result"]["statements"][0]["transactions"][0][
            "unique_import_id"
        ] = None
        _currency, _account, statements = self.backend._transform_result(
            response, "statement.pdf"
        )
        self.assertTrue(statements[0]["transactions"][0]["unique_import_id"])

    def test_transform_result_fallback_uses_checksum_not_filename(self):
        """A checksum-based fallback id contains the checksum, not the name.

        Positive scenario — trigger P1 (L-01/L-02: what is asserted is
        the bare tuple returned by ``_transform_result``, not a record
        field YAML's ``assert`` could ``getattr``).
        """
        response = _sample_response()
        response["result"]["statements"][0]["transactions"][0][
            "unique_import_id"
        ] = None
        _currency, _account, statements = self.backend._transform_result(
            response, "statement.pdf", file_checksum="abc123checksum"
        )
        fallback_id = statements[0]["transactions"][0]["unique_import_id"]
        self.assertIn("abc123checksum", fallback_id)
        self.assertNotIn("statement.pdf", fallback_id)

    def test_transform_result_fallback_same_checksum_different_filenames(self):
        """Different filenames with the same checksum collide on purpose.

        Positive scenario — trigger P1 (L-01/L-02: same reasoning as
        above, the return value is a bare tuple).
        """
        response_a = _sample_response()
        response_a["result"]["statements"][0]["transactions"][0][
            "unique_import_id"
        ] = None
        response_b = _sample_response()
        response_b["result"]["statements"][0]["transactions"][0][
            "unique_import_id"
        ] = None
        _c1, _a1, statements_a = self.backend._transform_result(
            response_a, "january.pdf", file_checksum="same-checksum"
        )
        _c2, _a2, statements_b = self.backend._transform_result(
            response_b, "february.pdf", file_checksum="same-checksum"
        )
        self.assertEqual(
            statements_a[0]["transactions"][0]["unique_import_id"],
            statements_b[0]["transactions"][0]["unique_import_id"],
        )

    def test_transform_result_fallback_same_filename_different_checksums(self):
        """The same filename with different checksums does not collide.

        Positive scenario — trigger P1 (L-01/L-02: same reasoning as
        above, the return value is a bare tuple).
        """
        response_a = _sample_response()
        response_a["result"]["statements"][0]["transactions"][0][
            "unique_import_id"
        ] = None
        response_b = _sample_response()
        response_b["result"]["statements"][0]["transactions"][0][
            "unique_import_id"
        ] = None
        _c1, _a1, statements_a = self.backend._transform_result(
            response_a, "statement.pdf", file_checksum="checksum-one"
        )
        _c2, _a2, statements_b = self.backend._transform_result(
            response_b, "statement.pdf", file_checksum="checksum-two"
        )
        self.assertNotEqual(
            statements_a[0]["transactions"][0]["unique_import_id"],
            statements_b[0]["transactions"][0]["unique_import_id"],
        )

    def test_transform_result_fallback_without_checksum_uses_filename(self):
        """Omitting ``file_checksum`` keeps the old filename-based id.

        Positive scenario — trigger P1 (L-01/L-02: same reasoning as
        above, the return value is a bare tuple).
        """
        response = _sample_response()
        response["result"]["statements"][0]["transactions"][0][
            "unique_import_id"
        ] = None
        _currency, _account, statements = self.backend._transform_result(
            response, "statement.pdf"
        )
        fallback_id = statements[0]["transactions"][0]["unique_import_id"]
        self.assertIn("statement.pdf", fallback_id)

    def test_transform_result_keeps_service_provided_unique_import_id(self):
        """A service-provided ``unique_import_id`` wins over the checksum.

        Positive scenario — trigger P1 (L-01/L-02: same reasoning as
        above, the return value is a bare tuple).
        """
        response = _sample_response()
        provided_id = response["result"]["statements"][0]["transactions"][0][
            "unique_import_id"
        ]
        _currency, _account, statements = self.backend._transform_result(
            response, "statement.pdf", file_checksum="should-be-ignored"
        )
        actual_id = statements[0]["transactions"][0]["unique_import_id"]
        self.assertEqual(actual_id, provided_id)
        self.assertNotIn("should-be-ignored", actual_id)

    def test_transform_result_failed_status_raises(self):
        response = _sample_response(status="failed")
        response["error"] = "Could not read the file"
        with self.assertRaises(UserError):
            self.backend._transform_result(response, "statement.pdf")

    def test_transform_result_no_statements_raises(self):
        response = _sample_response()
        response["result"]["statements"] = []
        with self.assertRaises(UserError):
            self.backend._transform_result(response, "statement.pdf")

    def test_transform_result_omits_null_balance_keys(self):
        """Omit ``balance_start``/``balance_end_real`` when null.

        Positive scenario — trigger P1 (L-01/L-02: what is asserted is
        the bare tuple returned by ``_transform_result``, not a record
        field YAML's ``assert`` could ``getattr``).
        """
        response = _sample_response(balance_start=None, balance_end_real=None)
        _currency, _account, statements = self.backend._transform_result(
            response, "statement.pdf"
        )
        self.assertNotIn("balance_start", statements[0])
        self.assertNotIn("balance_end_real", statements[0])

    def test_transform_result_keeps_numeric_balance_keys(self):
        """Keep numeric ``balance_start``/``balance_end_real`` as float.

        Positive scenario — trigger P1 (L-01/L-02: same reasoning as
        above, the return value is a bare tuple).
        """
        response = _sample_response(balance_start=1000000.0, balance_end_real=1300000.0)
        _currency, _account, statements = self.backend._transform_result(
            response, "statement.pdf"
        )
        self.assertIsInstance(statements[0]["balance_start"], float)
        self.assertEqual(statements[0]["balance_start"], 1000000.0)
        self.assertIsInstance(statements[0]["balance_end_real"], float)
        self.assertEqual(statements[0]["balance_end_real"], 1300000.0)

    def test_transform_result_transaction_without_amount_raises(self):
        """Reject a transaction whose ``amount`` is null.

        Negative scenario — trigger P1 (L-01/L-02: this exercises the
        return-value/exception contract of a pure method, which YAML's
        record-bound ``assert`` cannot observe).
        """
        response = _sample_response()
        response["result"]["statements"][0]["transactions"][0]["amount"] = None
        with self.assertRaises(UserError) as cm:
            self.backend._transform_result(response, "statement.pdf")
        self.assertIn(
            "mutasi-ai response has a transaction without amount",
            str(cm.exception),
        )

    # ------------------------------------------------------------------
    # Job _run — mocked HTTP call
    # ------------------------------------------------------------------

    def test_run_success_creates_statement(self):
        if not self.bank_journal:
            self.skipTest("No bank journal found in test environment")
        job = self._make_job(unique_suffix="success")
        with patch(
            _CALL_SERVICE_PATH,
            return_value=_sample_response(
                unique_suffix="success", currency_code=self.company_currency
            ),
        ):
            job._run()
        self.assertEqual(job.state, "done")
        self.assertEqual(job.external_id, "stmt_test_success")
        self.assertTrue(job.statement_ids)
        lines = self.env["account.bank.statement.line"].search(
            [("statement_id", "in", job.statement_ids.ids)]
        )
        self.assertEqual(len(lines), 2)

    def test_run_with_statement_id_updates_existing_statement(self):
        if not self.bank_journal:
            self.skipTest("No bank journal found in test environment")
        existing_statement = self.env["account.bank.statement"].create(
            {
                "journal_id": self.bank_journal.id,
                "date": "2026-01-31",
            }
        )
        statement_count_before = self.env["account.bank.statement"].search_count([])
        job = self._make_job(unique_suffix="update")
        job.write({"statement_id": existing_statement.id})
        with patch(
            _CALL_SERVICE_PATH,
            return_value=_sample_response(
                unique_suffix="update", currency_code=self.company_currency
            ),
        ):
            job._run()
        self.assertEqual(job.state, "done")
        self.assertEqual(
            job.statement_ids,
            existing_statement,
            "job must report the existing statement it updated, not a new one",
        )
        statement_count_after = self.env["account.bank.statement"].search_count([])
        self.assertEqual(
            statement_count_before,
            statement_count_after,
            "importing into an existing statement must not create a new statement",
        )
        lines = self.env["account.bank.statement.line"].search(
            [("statement_id", "=", existing_statement.id)]
        )
        self.assertEqual(len(lines), 2)
        self.assertIn(
            job,
            existing_statement.mutasi_ai_job_ids,
            "the updated bank statement must expose the import job "
            "via mutasi_ai_job_ids",
        )

    def test_run_links_job_to_created_statement(self):
        if not self.bank_journal:
            self.skipTest("No bank journal found in test environment")
        job = self._make_job(unique_suffix="link")
        with patch(
            _CALL_SERVICE_PATH,
            return_value=_sample_response(
                unique_suffix="link", currency_code=self.company_currency
            ),
        ):
            job._run()
        self.assertTrue(job.statement_ids)
        self.assertIn(
            job,
            job.statement_ids.mutasi_ai_job_ids,
            "the created bank statement must expose its import job "
            "via mutasi_ai_job_ids",
        )

    def test_run_dedup_second_run_already_imported(self):
        """Re-importing an all-duplicate file is ``already_imported``.

        Positive scenario — trigger P6 (L-15: an end-to-end job run
        requires patching ``_call_service``; ``odoo-yaml-test`` has no
        mock/patch support). Feeding the exact same response twice
        means every transaction on the second run is a duplicate, so
        ``statement_ids`` stays empty and the job must land on
        ``already_imported`` (not ``need_review``, which is reserved
        for a low-confidence extraction that still produced new
        transactions), with ``notification_message`` explaining why.
        """
        if not self.bank_journal:
            self.skipTest("No bank journal found in test environment")
        response = _sample_response(
            unique_suffix="dedup", currency_code=self.company_currency
        )
        job1 = self._make_job(unique_suffix="dedup")
        with patch(_CALL_SERVICE_PATH, return_value=response):
            job1._run()
        self.assertEqual(job1.state, "done")

        job2 = self._make_job(unique_suffix="dedup")
        with patch(_CALL_SERVICE_PATH, return_value=response):
            job2._run()
        # All transactions already imported -> no new statement,
        # already_imported.
        self.assertEqual(job2.state, "already_imported")
        self.assertFalse(job2.statement_ids)
        self.assertTrue(job2.notification_message)
        lines = self.env["account.bank.statement.line"].search(
            [("payment_ref", "=", "TRANSFER MASUK"), ("amount", "=", 500000.0)]
        )
        self.assertEqual(len(lines), 1, "deduplication failed: expected exactly 1 line")

    def test_run_dedup_second_run_already_imported_null_balance(self):
        """Re-importing an all-duplicate null-balance file is already_imported.

        Positive scenario — trigger P6 (L-15: an end-to-end job run
        requires patching ``_call_service``; no mock support in YAML).
        Null-balance variant of
        ``test_run_dedup_second_run_already_imported`` reproducing the
        reported bug: before the fix, the second run raised
        ``TypeError`` (``NoneType`` ``+=`` ``float``) instead of
        finishing as ``already_imported``.
        """
        if not self.bank_journal:
            self.skipTest("No bank journal found in test environment")
        response = _sample_response(
            unique_suffix="nullbal-dedup",
            currency_code=self.company_currency,
            balance_start=None,
            balance_end_real=None,
        )
        job1 = self._make_job(unique_suffix="nullbal-dedup")
        with patch(_CALL_SERVICE_PATH, return_value=response):
            job1._run()
        self.assertEqual(job1.state, "done")

        job2 = self._make_job(unique_suffix="nullbal-dedup")
        with patch(_CALL_SERVICE_PATH, return_value=response):
            job2._run()
        # All transactions already imported -> no new statement,
        # already_imported, and no TypeError even though balances are
        # null.
        self.assertEqual(job2.state, "already_imported")
        self.assertFalse(job2.statement_ids)
        lines = self.env["account.bank.statement.line"].search(
            [("payment_ref", "=", "TRANSFER MASUK"), ("amount", "=", 500000.0)]
        )
        self.assertEqual(len(lines), 1, "deduplication failed: expected exactly 1 line")

    def test_run_dedup_full_duplicate_need_review_status_wins(self):
        """A fully-duplicate need_review response is still already_imported.

        Positive scenario — trigger P6 (L-15: an end-to-end job run
        requires patching ``_call_service``; no mock support in YAML).
        The duplicate-file rule (``statement_ids`` empty ->
        ``already_imported``) must win over ``external_status`` even
        when the mutasi-ai service itself flags the (fully duplicate)
        file as ``need_review``.
        """
        if not self.bank_journal:
            self.skipTest("No bank journal found in test environment")
        response = _sample_response(
            unique_suffix="dedup-needreview", currency_code=self.company_currency
        )
        job1 = self._make_job(unique_suffix="dedup-needreview")
        with patch(_CALL_SERVICE_PATH, return_value=response):
            job1._run()
        self.assertEqual(job1.state, "done")

        response2 = _sample_response(
            status="need_review",
            unique_suffix="dedup-needreview",
            currency_code=self.company_currency,
        )
        job2 = self._make_job(unique_suffix="dedup-needreview")
        with patch(_CALL_SERVICE_PATH, return_value=response2):
            job2._run()
        self.assertEqual(job2.state, "already_imported")
        self.assertEqual(job2.external_status, "need_review")
        self.assertFalse(job2.statement_ids)

    def test_run_second_run_null_balance_adds_new_transaction(self):
        """A second null-balance run with one new line still succeeds.

        Positive scenario — trigger P6 (L-15: end-to-end job run
        requires patching ``_call_service``). With balance keys
        omitted (null in the source response), re-importing a file
        that has one additional transaction must create a statement
        containing only that new line, without duplicating or
        raising on the already-imported one.
        """
        if not self.bank_journal:
            self.skipTest("No bank journal found in test environment")
        response = _sample_response(
            unique_suffix="nullbal-add",
            currency_code=self.company_currency,
            balance_start=None,
            balance_end_real=None,
        )
        job1 = self._make_job(unique_suffix="nullbal-add")
        with patch(_CALL_SERVICE_PATH, return_value=response):
            job1._run()
        self.assertEqual(job1.state, "done")

        response2 = _sample_response(
            unique_suffix="nullbal-add",
            currency_code=self.company_currency,
            balance_start=None,
            balance_end_real=None,
        )
        response2["result"]["statements"][0]["transactions"].append(
            {
                "date": "2026-01-15",
                "amount": 750000.0,
                "payment_ref": "TRANSFER BARU",
                "unique_import_id": "mutasi-ai-tx-nullbal-add-new",
                "account_number": None,
                "partner_name": "Citra",
                "ref": None,
            }
        )
        job2 = self._make_job(unique_suffix="nullbal-add")
        with patch(_CALL_SERVICE_PATH, return_value=response2):
            job2._run()

        self.assertEqual(job2.state, "done")
        self.assertTrue(job2.statement_ids)
        new_lines = self.env["account.bank.statement.line"].search(
            [("statement_id", "in", job2.statement_ids.ids)]
        )
        self.assertEqual(len(new_lines), 1)
        self.assertEqual(new_lines.payment_ref, "TRANSFER BARU")
        existing_lines = self.env["account.bank.statement.line"].search(
            [("payment_ref", "=", "TRANSFER MASUK"), ("amount", "=", 500000.0)]
        )
        self.assertEqual(
            len(existing_lines),
            1,
            "already-imported transaction must not be duplicated",
        )

    def test_run_need_review_status(self):
        if not self.bank_journal:
            self.skipTest("No bank journal found in test environment")
        job = self._make_job(unique_suffix="review")
        with patch(
            _CALL_SERVICE_PATH,
            return_value=_sample_response(
                status="need_review",
                unique_suffix="review",
                currency_code=self.company_currency,
            ),
        ):
            job._run()
        self.assertEqual(job.state, "need_review")
        self.assertEqual(job.external_status, "need_review")
        self.assertTrue(job.statement_ids)

    def test_run_uses_checksum_based_unique_import_id(self):
        """A full job run stores a checksum-based ``unique_import_id``.

        Positive scenario — trigger P6 (L-15: an end-to-end job run
        requires patching ``_call_service``; ``odoo-yaml-test`` has no
        mock/patch support). ``_run`` must pass the job's own
        ``file_checksum`` through to ``_transform_result``, so the
        resulting statement line's ``unique_import_id`` is built from
        the checksum rather than the filename.
        """
        if not self.bank_journal:
            self.skipTest("No bank journal found in test environment")
        response = _sample_response(
            unique_suffix="checksum-run", currency_code=self.company_currency
        )
        response["result"]["statements"][0]["transactions"][0][
            "unique_import_id"
        ] = None
        job = self._make_job(unique_suffix="checksum-run")
        job.write({"file_checksum": "run-checksum-value"})
        with patch(_CALL_SERVICE_PATH, return_value=response):
            job._run()
        self.assertEqual(job.state, "done")
        line = self.env["account.bank.statement.line"].search(
            [("payment_ref", "=", "TRANSFER MASUK"), ("amount", "=", 500000.0)]
        )
        self.assertEqual(len(line), 1)
        self.assertIn("run-checksum-value", line.unique_import_id)
        self.assertNotIn("statement.pdf", line.unique_import_id)

    def test_run_error_path_sets_failed(self):
        job = self._make_job(unique_suffix="error")
        with patch(_CALL_SERVICE_PATH, side_effect=UserError("boom")):
            job._run()
        self.assertEqual(job.state, "failed")
        self.assertIn("boom", job.error_message)
        self.assertFalse(job.statement_ids)

    # ------------------------------------------------------------------
    # notification_message — mocked HTTP call
    # ------------------------------------------------------------------

    def test_notification_message_false_when_all_new(self):
        """No notification when the whole file is newly imported.

        Positive scenario — trigger P6 (L-15: an end-to-end job run
        requires patching ``_call_service``; ``odoo-yaml-test`` has no
        mock/patch support).
        """
        if not self.bank_journal:
            self.skipTest("No bank journal found in test environment")
        job = self._make_job(unique_suffix="notif-new")
        with patch(
            _CALL_SERVICE_PATH,
            return_value=_sample_response(
                unique_suffix="notif-new", currency_code=self.company_currency
            ),
        ):
            job._run()
        self.assertEqual(job.state, "done")
        self.assertFalse(job.notification_message)

    def test_notification_message_all_duplicate_second_run(self):
        """Re-importing an all-duplicate file reports it on the job.

        Positive scenario — trigger P6 (L-15: an end-to-end job run
        requires patching ``_call_service``; ``odoo-yaml-test`` has no
        mock/patch support). Mirrors
        ``test_run_dedup_second_run_already_imported`` but also asserts
        the new ``notification_message`` field, populated here by the
        fallback message ``_prepare_notification_message`` synthesizes
        when the wizard's own ``result["notifications"]`` stays empty
        (``_create_bank_statements``/``_update_bank_statements`` return
        before building it when every transaction was a duplicate).
        """
        if not self.bank_journal:
            self.skipTest("No bank journal found in test environment")
        response = _sample_response(
            unique_suffix="notif-dup", currency_code=self.company_currency
        )
        job1 = self._make_job(unique_suffix="notif-dup")
        with patch(_CALL_SERVICE_PATH, return_value=response):
            job1._run()
        self.assertEqual(job1.state, "done")

        job2 = self._make_job(unique_suffix="notif-dup")
        with patch(_CALL_SERVICE_PATH, return_value=response):
            job2._run()
        self.assertEqual(job2.state, "already_imported")
        self.assertTrue(job2.notification_message)
        self.assertIn("already been imported", job2.notification_message)

    def test_notification_message_partial_duplicate_second_run(self):
        """A partially-duplicate re-import reports the ignored lines.

        Positive scenario — trigger P6 (L-15: an end-to-end job run
        requires patching ``_call_service``; ``odoo-yaml-test`` has no
        mock/patch support). With one new transaction added on top of
        an already-imported file, the job finishes ``done`` and
        ``notification_message`` carries the wizard's own "already
        been imported" message instead of the all-duplicate fallback.
        """
        if not self.bank_journal:
            self.skipTest("No bank journal found in test environment")
        response = _sample_response(
            unique_suffix="notif-partial", currency_code=self.company_currency
        )
        job1 = self._make_job(unique_suffix="notif-partial")
        with patch(_CALL_SERVICE_PATH, return_value=response):
            job1._run()
        self.assertEqual(job1.state, "done")

        response2 = _sample_response(
            unique_suffix="notif-partial", currency_code=self.company_currency
        )
        response2["result"]["statements"][0]["transactions"].append(
            {
                "date": "2026-01-15",
                "amount": 750000.0,
                "payment_ref": "TRANSFER BARU",
                "unique_import_id": "mutasi-ai-tx-notif-partial-new",
                "account_number": None,
                "partner_name": "Citra",
                "ref": None,
            }
        )
        job2 = self._make_job(unique_suffix="notif-partial")
        with patch(_CALL_SERVICE_PATH, return_value=response2):
            job2._run()
        self.assertEqual(job2.state, "done")
        self.assertTrue(job2.notification_message)
        self.assertIn("already been imported", job2.notification_message)

    def test_notification_message_false_on_failure(self):
        """A failed job leaves ``notification_message`` untouched.

        Negative scenario — trigger P6 (L-15: an end-to-end job run
        requires patching ``_call_service``; ``odoo-yaml-test`` has no
        mock/patch support). ``_run``'s ``except`` branch must not set
        ``notification_message``, so it stays at its default (empty)
        value.
        """
        job = self._make_job(unique_suffix="notif-error")
        with patch(_CALL_SERVICE_PATH, side_effect=UserError("boom")):
            job._run()
        self.assertEqual(job.state, "failed")
        self.assertFalse(job.notification_message)

    def test_retry_only_allowed_from_failed_or_need_review(self):
        job = self._make_job(unique_suffix="retryguard")
        with self.assertRaises(UserError):
            job.action_retry()

    # ------------------------------------------------------------------
    # Wizard enqueue path — does NOT parse/import synchronously
    # ------------------------------------------------------------------

    def test_import_file_button_enqueues_job_not_statement(self):
        statement_count_before = self.env["account.bank.statement"].search_count([])
        wizard = self.env["account.statement.import"].create(
            {
                "statement_file": base64.b64encode(b"dummy pdf content"),
                "statement_filename": "enqueue_test.pdf",
                "mutasi_ai_backend_id": self.backend.id,
            }
        )
        wizard.import_file_button()

        jobs = self.env[_JOB_MODEL].search(
            [("statement_filename", "=", "enqueue_test.pdf")]
        )
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs.state, "queued")
        self.assertEqual(jobs.backend_id, self.backend)
        statement_count_after = self.env["account.bank.statement"].search_count([])
        self.assertEqual(
            statement_count_before,
            statement_count_after,
            "enqueue path must not create a statement synchronously",
        )

    def test_enqueue_returns_close_action(self):
        wizard = self.env["account.statement.import"].create(
            {
                "statement_file": base64.b64encode(b"dummy pdf content"),
                "statement_filename": "close_action_test.pdf",
                "mutasi_ai_backend_id": self.backend.id,
            }
        )
        action = wizard.import_file_button()
        self.assertEqual(action["tag"], "display_notification")
        self.assertEqual(action["params"]["type"], "success")
        self.assertEqual(
            action["params"]["next"]["type"],
            "ir.actions.act_window_close",
            "the import wizard must close after a successful enqueue",
        )

    def test_enqueue_from_existing_statement_captures_statement_id(self):
        if not self.bank_journal:
            self.skipTest("No bank journal found in test environment")
        existing_statement = self.env["account.bank.statement"].create(
            {
                "journal_id": self.bank_journal.id,
                "date": "2026-01-31",
            }
        )
        wizard = (
            self.env["account.statement.import"]
            .with_context(
                active_model="account.bank.statement",
                active_ids=[existing_statement.id],
            )
            .create(
                {
                    "statement_file": base64.b64encode(b"dummy pdf content"),
                    "statement_filename": "enqueue_from_statement_test.pdf",
                    "mutasi_ai_backend_id": self.backend.id,
                }
            )
        )
        wizard.import_file_button()

        job = self.env[_JOB_MODEL].search(
            [("statement_filename", "=", "enqueue_from_statement_test.pdf")]
        )
        self.assertEqual(len(job), 1)
        self.assertEqual(job.statement_id, existing_statement)

    def test_enqueue_without_active_statement_leaves_statement_id_empty(self):
        wizard = self.env["account.statement.import"].create(
            {
                "statement_file": base64.b64encode(b"dummy pdf content"),
                "statement_filename": "enqueue_no_statement_test.pdf",
                "mutasi_ai_backend_id": self.backend.id,
            }
        )
        wizard.import_file_button()

        job = self.env[_JOB_MODEL].search(
            [("statement_filename", "=", "enqueue_no_statement_test.pdf")]
        )
        self.assertEqual(len(job), 1)
        self.assertFalse(job.statement_id)

    def test_enqueue_links_queue_job_id(self):
        """``_enqueue()`` stores the ``queue.job`` it just created.

        Positive scenario — trigger P1 (L-01: the interesting value is
        the intermediate ``Job`` returned by ``with_delay()._run()``,
        exposed on the record only via ``queue_job_id`` after
        ``_enqueue()`` writes it; YAML's ``call`` action discards
        method return values, so only calling ``_enqueue()`` directly
        in Python can pin the model/method it links to).
        """
        job = self._make_job(unique_suffix="link-queue-job")
        job._enqueue()
        self.assertTrue(job.queue_job_id)
        self.assertEqual(job.queue_job_id.model_name, _JOB_MODEL)
        self.assertEqual(job.queue_job_id.method_name, "_run")

    def test_preselect_backend_from_journal_default(self):
        if not self.bank_journal:
            self.skipTest("No bank journal found in test environment")
        self.bank_journal.write({"default_mutasi_ai_backend_id": self.backend.id})
        form = Form(
            self.env["account.statement.import"].with_context(
                journal_id=self.bank_journal.id,
                default_journal_id=self.bank_journal.id,
            )
        )
        self.assertEqual(form.mutasi_ai_backend_id, self.backend)

    # ------------------------------------------------------------------
    # file_checksum duplicate guard — pure Python (base64 fixtures)
    # ------------------------------------------------------------------

    def _make_job_with_checksum(self, file_checksum, state, filename="dup.pdf"):
        """Create a job directly with a fixed ``file_checksum``/``state``.

        Bypasses the wizard so the duplicate-guard tests can set up a
        prior job in an arbitrary state without going through
        ``_run()``.

        :param file_checksum: value to store on ``file_checksum``
        :type file_checksum: str
        :param state: value to store on ``state``
        :type state: str
        :param filename: filename recorded on the job/attachment
        :type filename: str
        :return: the created job record
        :rtype: recordset of ``account.statement.import.mutasi.ai.job``
        """
        attachment = self._make_attachment(filename)
        return self.env[_JOB_MODEL].create(
            {
                "attachment_id": attachment.id,
                "statement_filename": filename,
                "backend_id": self.backend.id,
                "file_checksum": file_checksum,
                "state": state,
            }
        )

    def test_enqueue_sets_file_checksum(self):
        """Enqueueing a new file stores its SHA-256 hex digest.

        Positive scenario — trigger P10 (L-09/L-10/L-11: the wizard's
        ``statement_file`` is a binary field, so the fixture needs
        ``base64``, which the YAML ``EVAL:`` whitelist does not allow).
        """
        content = b"file checksum positive test content"
        wizard = self.env["account.statement.import"].create(
            {
                "statement_file": base64.b64encode(content),
                "statement_filename": "checksum_new.pdf",
                "mutasi_ai_backend_id": self.backend.id,
            }
        )
        wizard.import_file_button()
        job = self.env[_JOB_MODEL].search(
            [("statement_filename", "=", "checksum_new.pdf")]
        )
        self.assertEqual(len(job), 1)
        self.assertEqual(len(job.file_checksum), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in job.file_checksum))

    def test_enqueue_file_checksum_matches_sha256_of_content(self):
        """The stored checksum equals SHA-256 of the decoded file.

        Positive scenario — trigger P10 (L-09/L-10/L-11: same reasoning
        as above; this also computes the expected digest with
        ``hashlib``, unavailable to YAML ``EVAL:``). Confirms the value
        is exactly the ``Idempotency-Key`` ``_call_service`` would send
        for the same content.
        """
        content = b"file checksum equality test content"
        expected = hashlib.sha256(content).hexdigest()
        wizard = self.env["account.statement.import"].create(
            {
                "statement_file": base64.b64encode(content),
                "statement_filename": "checksum_equal.pdf",
                "mutasi_ai_backend_id": self.backend.id,
            }
        )
        wizard.import_file_button()
        job = self.env[_JOB_MODEL].search(
            [("statement_filename", "=", "checksum_equal.pdf")]
        )
        self.assertEqual(job.file_checksum, expected)

    def test_enqueue_duplicate_of_done_job_raises_and_creates_nothing(self):
        """Re-uploading a file already ``done`` is rejected.

        Negative scenario — trigger P10 (L-09/L-10/L-11: fixture needs
        ``base64``). No new ``ir.attachment`` nor job record may be
        created when the guard rejects the upload.
        """
        content = b"file checksum duplicate done test content"
        checksum = hashlib.sha256(content).hexdigest()
        previous_job = self._make_job_with_checksum(
            checksum, "done", filename="dup_done_prev.pdf"
        )
        job_count_before = self.env[_JOB_MODEL].search_count([])
        attachment_count_before = self.env["ir.attachment"].search_count([])
        wizard = self.env["account.statement.import"].create(
            {
                "statement_file": base64.b64encode(content),
                "statement_filename": "dup_done_new.pdf",
                "mutasi_ai_backend_id": self.backend.id,
            }
        )
        with self.assertRaises(UserError) as cm:
            wizard.import_file_button()
        self.assertIn(previous_job.name, str(cm.exception))
        self.assertEqual(self.env[_JOB_MODEL].search_count([]), job_count_before)
        self.assertEqual(
            self.env["ir.attachment"].search_count([]), attachment_count_before
        )

    def test_enqueue_duplicate_of_failed_job_is_allowed(self):
        """Re-uploading a file whose prior job ``failed`` is allowed.

        Positive scenario — trigger P10 (L-09/L-10/L-11: fixture needs
        ``base64``). A ``failed`` job must not block a retry-by-upload,
        so a new job is created instead of raising.
        """
        content = b"file checksum duplicate failed test content"
        checksum = hashlib.sha256(content).hexdigest()
        self._make_job_with_checksum(checksum, "failed", filename="dup_failed_prev.pdf")
        wizard = self.env["account.statement.import"].create(
            {
                "statement_file": base64.b64encode(content),
                "statement_filename": "dup_failed_new.pdf",
                "mutasi_ai_backend_id": self.backend.id,
            }
        )
        wizard.import_file_button()
        new_job = self.env[_JOB_MODEL].search(
            [("statement_filename", "=", "dup_failed_new.pdf")]
        )
        self.assertEqual(len(new_job), 1)
        self.assertEqual(new_job.file_checksum, checksum)

    def test_enqueue_different_content_gets_different_checksums(self):
        """Two files with different content get different checksums.

        Positive scenario — trigger P10 (L-09/L-10/L-11: fixture needs
        ``base64``). Neither upload raises, and the two jobs end up
        with distinct ``file_checksum`` values.
        """
        wizard_a = self.env["account.statement.import"].create(
            {
                "statement_file": base64.b64encode(b"content variant A"),
                "statement_filename": "distinct_a.pdf",
                "mutasi_ai_backend_id": self.backend.id,
            }
        )
        wizard_a.import_file_button()
        wizard_b = self.env["account.statement.import"].create(
            {
                "statement_file": base64.b64encode(b"content variant B"),
                "statement_filename": "distinct_b.pdf",
                "mutasi_ai_backend_id": self.backend.id,
            }
        )
        wizard_b.import_file_button()
        job_a = self.env[_JOB_MODEL].search(
            [("statement_filename", "=", "distinct_a.pdf")]
        )
        job_b = self.env[_JOB_MODEL].search(
            [("statement_filename", "=", "distinct_b.pdf")]
        )
        self.assertEqual(len(job_a), 1)
        self.assertEqual(len(job_b), 1)
        self.assertNotEqual(job_a.file_checksum, job_b.file_checksum)

    # ------------------------------------------------------------------
    # Test Connection — mocked HTTP
    # ------------------------------------------------------------------

    def test_test_connection_success(self):
        health_response = Mock(status_code=200)
        health_response.json.return_value = {"status": "ok", "version": "1.2.3"}
        me_response = Mock(status_code=200)
        me_response.json.return_value = {"sub": "svc-account"}
        with patch(_REQUESTS_GET_PATH, side_effect=[health_response, me_response]):
            result = self.backend.action_test_connection()
        self.assertEqual(result["params"]["type"], "success")

    def test_test_connection_unauthorized_raises(self):
        health_response = Mock(status_code=200)
        health_response.json.return_value = {"status": "ok", "version": "1.2.3"}
        me_response = Mock(status_code=401)
        with patch(_REQUESTS_GET_PATH, side_effect=[health_response, me_response]):
            with self.assertRaises(UserError):
                self.backend.action_test_connection()

    # ------------------------------------------------------------------
    # Security
    # ------------------------------------------------------------------

    def test_non_configurator_cannot_create_backend(self):
        demo_user = self.env.ref("base.user_demo")
        with self.assertRaises(AccessError):
            self.env[_BACKEND_MODEL].with_user(demo_user).create(
                {
                    "name": "Unauthorized Backend",
                    "code": "UNAUTH-TEST",
                    "base_url": "https://carik.example.com",
                    "bearer_token": "test-token",
                }
            )
