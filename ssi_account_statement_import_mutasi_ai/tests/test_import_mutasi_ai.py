# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64
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


def _sample_response(status="ok", unique_suffix="a", currency_code="IDR"):
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
                    "balance_start": 1000000.0,
                    "balance_end_real": 1300000.0,
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

    def test_run_dedup_second_run_need_review(self):
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
        # All transactions already imported -> no new statement, need_review.
        self.assertEqual(job2.state, "need_review")
        self.assertFalse(job2.statement_ids)
        lines = self.env["account.bank.statement.line"].search(
            [("payment_ref", "=", "TRANSFER MASUK"), ("amount", "=", 500000.0)]
        )
        self.assertEqual(len(lines), 1, "deduplication failed: expected exactly 1 line")

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

    def test_run_error_path_sets_failed(self):
        job = self._make_job(unique_suffix="error")
        with patch(_CALL_SERVICE_PATH, side_effect=UserError("boom")):
            job._run()
        self.assertEqual(job.state, "failed")
        self.assertIn("boom", job.error_message)
        self.assertFalse(job.statement_ids)

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
