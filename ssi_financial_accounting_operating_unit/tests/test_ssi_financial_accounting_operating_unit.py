# Copyright 2024 OpenSynergy Indonesia
# Copyright 2024 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo_yaml_test import YamlTransactionCase

from odoo.exceptions import UserError
from odoo.tests import Form, tagged

# Most scenarios below are plain Python (not YAML) because the odoo-yaml-test
# DSL has no primitive for the two things most of them need: asserting that a
# step raises an exception (ir.rule/constraint checks), and running an action
# as a dynamically-created user (`as_user` only accepts a fixed XML ID via
# env.ref, not a record created at runtime). Only the two scenarios that are
# pure CRUD/state assertions live in the YAML file.


@tagged("post_install", "-at_install")
class TestSsiFinancialAccountingOperatingUnit(YamlTransactionCase):
    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.operating_unit = self._create_operating_unit(
            "Test Main Operating Unit", "TESTMAINOU"
        )

    def _create_operating_unit(self, name, code):
        partner = self.env["res.partner"].create({"name": "%s Partner" % name})
        return self.env["operating.unit"].create(
            {
                "name": name,
                "code": code,
                "partner_id": partner.id,
                "company_id": self.company.id,
            }
        )

    def _create_ou_scoped_user(self, login, group_xmlids, operating_units):
        group_ids = [self.env.ref("base.group_user").id]
        for xmlid in group_xmlids:
            group_ids.append(self.env.ref(xmlid).id)
        return self.env["res.users"].create(
            {
                "name": login,
                "login": login,
                "email": "%s@example.com" % login,
                "company_id": self.company.id,
                "company_ids": [(6, 0, [self.company.id])],
                "groups_id": [(6, 0, group_ids)],
                "assigned_operating_unit_ids": [(6, 0, operating_units.ids)],
            }
        )

    def test_ssi_financial_accounting_operating_unit(self):
        self.run_yaml_scenario("test_data_ssi_financial_accounting_operating_unit.yaml")

    # ------------------------------------------------------------------
    # Delegation regressions (_inherits to account.move) — introspection,
    # not expressible as a YAML create/assert scenario.
    # ------------------------------------------------------------------

    def test_bank_statement_line_ou_via_delegation_not_mixin(self):
        """Regression: account.bank.statement.line gets operating_unit_id via
        _inherits delegation from account.move — NOT from mixin.single_operating_unit.
        Adding the mixin would break the delegation field. This test verifies the field
        exists via delegation.
        """
        model = self.env["account.bank.statement.line"]

        fields_info = model.fields_get(["operating_unit_id"])
        self.assertIn("operating_unit_id", fields_info)

        local_fields = model._fields
        local_field = local_fields.get("operating_unit_id")
        self.assertEqual(
            local_field.related_field.model_name if local_field else None,
            "account.move",
            "operating_unit_id on account.bank.statement.line must be a "
            "delegation field originating from account.move, not a mixin field.",
        )

    def test_account_payment_ou_via_delegation(self):
        """Regression: account.payment exposes operating_unit_id via
        _inherits delegation to account.move (same pattern as
        bank.statement.line, BL-0003) — NOT via mixin.single_operating_unit
        added directly to account.payment.
        """
        model = self.env["account.payment"]

        fields_info = model.fields_get(["operating_unit_id"])
        self.assertIn("operating_unit_id", fields_info)

        local_field = model._fields.get("operating_unit_id")
        self.assertEqual(
            local_field.related_field.model_name if local_field else None,
            "account.move",
            "operating_unit_id on account.payment must be a delegation "
            "field originating from account.move, not a mixin field.",
        )

        journal = self.env["account.journal"].create(
            {
                "name": "Test Payment Delegation Journal",
                "code": "TSTPAYDJ",
                "type": "bank",
            }
        )
        partner = self.env["res.partner"].create(
            {"name": "Test Payment Delegation Partner"}
        )

        payment = self.env["account.payment"].create(
            {
                "journal_id": journal.id,
                "partner_id": partner.id,
                "amount": 100.0,
                "operating_unit_id": self.operating_unit.id,
            }
        )
        self.assertEqual(
            payment.operating_unit_id,
            self.operating_unit,
            "Setting operating_unit_id on account.payment must persist via "
            "delegation to the underlying account.move (move_id).",
        )
        self.assertEqual(
            payment.move_id.operating_unit_id,
            self.operating_unit,
            "account.payment.operating_unit_id must delegate to move_id.",
        )

    # ------------------------------------------------------------------
    # BL-0043 — readonly after post + onchange IndexError guard.
    # ------------------------------------------------------------------

    def test_move_operating_unit_id_readonly_after_post(self):
        """operating_unit_id must stay editable while draft, and become
        readonly once the move is posted."""
        ou_a = self._create_operating_unit("Test Readonly OU A", "TESTROA")
        ou_b = self._create_operating_unit("Test Readonly OU B", "TESTROB")
        journal = self.env["account.journal"].create(
            {"name": "Test Readonly Journal", "code": "TSTROJ", "type": "general"}
        )
        account_1 = self.env["account.account"].search([], limit=1)
        account_2 = self.env["account.account"].search(
            [("id", "!=", account_1.id)], limit=1
        )
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": journal.id,
                "operating_unit_id": ou_a.id,
                "line_ids": [
                    (0, 0, {"account_id": account_1.id, "debit": 100.0, "credit": 0.0}),
                    (0, 0, {"account_id": account_2.id, "debit": 0.0, "credit": 100.0}),
                ],
            }
        )

        draft_form = Form(move)
        draft_form.operating_unit_id = ou_b  # draft: must not raise

        move.action_post()
        posted_form = Form(move)
        with self.assertRaises(AssertionError):
            posted_form.operating_unit_id = ou_a

    def test_onchange_operating_unit_without_journal_no_indexerror(self):
        """BL-0043 regression: previously `journal[0]` on an empty search
        result raised IndexError when operating_unit_id was set on a move
        without a journal_id yet. Invoked directly (not via Form) because
        Form's own default-journal computation would mask the empty
        journal_id condition this regression targets."""
        ou_a = self._create_operating_unit("Test Guard OU A", "TESTGUARDA")
        move = self.env["account.move"].new({"move_type": "entry"})
        move.journal_id = False
        move.operating_unit_id = ou_a
        move._onchange_operating_unit()  # must not raise IndexError
        self.assertFalse(move.journal_id)

    def test_onchange_operating_unit_selects_matching_journal(self):
        """Existing behavior preserved by the BL-0043 guard: setting
        operating_unit_id auto-selects a journal restricted to that OU."""
        ou_a = self._create_operating_unit("Test Onchange OU A", "TESTONCA")
        ou_b = self._create_operating_unit("Test Onchange OU B", "TESTONCB")
        journal_b = self.env["account.journal"].create(
            {
                "name": "Test Onchange Journal B",
                "code": "TSTONCJB",
                "type": "general",
                "operating_unit_ids": [(6, 0, [ou_b.id])],
            }
        )
        form = Form(self.env["account.move"].with_context(default_move_type="entry"))
        form.operating_unit_id = ou_b
        self.assertEqual(form.journal_id.id, journal_b.id)
        self.assertNotEqual(ou_a.id, ou_b.id)

    # ------------------------------------------------------------------
    # Constraints — require assertRaises(UserError), not expressible in YAML.
    # ------------------------------------------------------------------

    def test_check_company_operating_unit_mismatch_raises(self):
        """OU belonging to a different company than the move must be rejected."""
        other_company = self.env["res.company"].create(
            {"name": "Test Other Company OU"}
        )
        partner = self.env["res.partner"].create({"name": "Other Company OU Partner"})
        other_ou = self.env["operating.unit"].create(
            {
                "name": "Other Company OU",
                "code": "OTHERCOU",
                "partner_id": partner.id,
                "company_id": other_company.id,
            }
        )
        journal = self.env["account.journal"].create(
            {"name": "Test Company Check Journal", "code": "TSTCCJ", "type": "general"}
        )
        with self.assertRaises(UserError):
            self.env["account.move"].create(
                {
                    "move_type": "entry",
                    "journal_id": journal.id,
                    "company_id": self.company.id,
                    "operating_unit_id": other_ou.id,
                }
            )

    def test_check_journal_operating_unit_mismatch_raises_for_account_move_active_model(
        self,
    ):
        """Mismatched OU/journal must raise when active_model is account.move
        itself (no self-heal branch)."""
        ou_a = self._create_operating_unit("Test Journal Check OU A", "TESTJCKA")
        ou_b = self._create_operating_unit("Test Journal Check OU B", "TESTJCKB")
        journal_a = self.env["account.journal"].create(
            {
                "name": "Test Journal Check A",
                "code": "TSTJCKJA",
                "type": "general",
                "operating_unit_ids": [(6, 0, [ou_a.id])],
            }
        )
        with self.assertRaises(UserError):
            self.env["account.move"].with_context(active_model="account.move").create(
                {
                    "move_type": "entry",
                    "journal_id": journal_a.id,
                    "operating_unit_id": ou_b.id,
                }
            )

    def test_check_journal_operating_unit_self_heals_for_other_active_model(self):
        """When created from another model (e.g. sale.order), a mismatched
        journal is healed by re-selecting a journal that matches the OU,
        instead of raising."""
        ou_a = self._create_operating_unit("Test Heal OU A", "TESTHEALA")
        ou_b = self._create_operating_unit("Test Heal OU B", "TESTHEALB")
        journal_a = self.env["account.journal"].create(
            {
                "name": "Test Heal Journal A",
                "code": "TSTHEALJA",
                "type": "general",
                "operating_unit_ids": [(6, 0, [ou_a.id])],
            }
        )
        journal_b = self.env["account.journal"].create(
            {
                "name": "Test Heal Journal B",
                "code": "TSTHEALJB",
                "type": "general",
                "operating_unit_ids": [(6, 0, [ou_b.id])],
            }
        )
        move = (
            self.env["account.move"]
            .with_context(active_model="sale.order")
            .create(
                {
                    "move_type": "entry",
                    "journal_id": journal_a.id,
                    "operating_unit_id": ou_b.id,
                }
            )
        )
        self.assertEqual(move.journal_id, journal_b)

    # ------------------------------------------------------------------
    # BL-0041 / BL-0042 — record rule configuration + functional isolation.
    # ------------------------------------------------------------------

    def test_rule_account_move_domain_force_has_ou_empty_fallback(self):
        rule = self.env.ref(
            "ssi_financial_accounting_operating_unit.account_move_rule_ou"
        )
        domain = rule.domain_force.replace(" ", "").replace("\n", "")
        self.assertIn("'operating_unit_id','=',False", domain)

    def test_rule_account_move_line_domain_force_has_ou_empty_fallback(self):
        rule = self.env.ref(
            "ssi_financial_accounting_operating_unit.account_move_line_rule_ou"
        )
        domain = rule.domain_force.replace(" ", "").replace("\n", "")
        self.assertIn("'operating_unit_id','=',False", domain)

    def test_rule_account_bank_statement_domain_force_has_ou_empty_fallback(self):
        rule = self.env.ref(
            "ssi_financial_accounting_operating_unit.account_bank_statement_rule_ou"
        )
        domain = rule.domain_force.replace(" ", "").replace("\n", "")
        self.assertIn("'operating_unit_id','=',False", domain)

    def test_rule_account_payment_domain_force_has_ou_empty_fallback(self):
        rule = self.env.ref(
            "ssi_financial_accounting_operating_unit.account_payment_rule_ou"
        )
        domain = rule.domain_force.replace(" ", "").replace("\n", "")
        self.assertIn("'operating_unit_id','=',False", domain)

    def test_rule_account_payment_groups_include_customer_and_vendor_ou_groups(self):
        """BL-0042: the payment rule must apply to the payment-specific OU
        groups, not to journal_entry_ou_group."""
        rule = self.env.ref(
            "ssi_financial_accounting_operating_unit.account_payment_rule_ou"
        )
        customer_group = self.env.ref(
            "ssi_financial_accounting_operating_unit.customer_payment_ou_group"
        )
        vendor_group = self.env.ref(
            "ssi_financial_accounting_operating_unit.vendor_payment_ou_group"
        )
        self.assertEqual(set(rule.groups.ids), {customer_group.id, vendor_group.id})

    def test_rule_account_move_visibility_fallback_and_isolation(self):
        """BL-0041: a user scoped to OU A sees OU A moves and no-OU moves,
        but not OU B moves."""
        ou_a = self._create_operating_unit("Test Rule Move OU A", "TESTRULEMA")
        ou_b = self._create_operating_unit("Test Rule Move OU B", "TESTRULEMB")
        journal = self.env["account.journal"].create(
            {"name": "Test Rule Move Journal", "code": "TSTRULEMJ", "type": "general"}
        )
        move_a = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": journal.id,
                "operating_unit_id": ou_a.id,
            }
        )
        move_none = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": journal.id,
                "operating_unit_id": False,
            }
        )
        move_b = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": journal.id,
                "operating_unit_id": ou_b.id,
            }
        )
        user = self._create_ou_scoped_user(
            "test_rule_move_user",
            ["ssi_financial_accounting_operating_unit.journal_entry_ou_group"],
            ou_a,
        )
        visible = (
            self.env["account.move"]
            .with_user(user)
            .search([("id", "in", (move_a + move_none + move_b).ids)])
        )
        self.assertEqual(set(visible.ids), {move_a.id, move_none.id})

    def test_rule_account_bank_statement_visibility_fallback_and_isolation(self):
        """BL-0041: same fallback+isolation guarantee for account.bank.statement."""
        ou_a = self._create_operating_unit("Test Rule Stmt OU A", "TESTRULESA")
        ou_b = self._create_operating_unit("Test Rule Stmt OU B", "TESTRULESB")
        journal = self.env["account.journal"].create(
            {"name": "Test Rule Stmt Journal", "code": "TSTRULESJ", "type": "bank"}
        )
        statement_a = self.env["account.bank.statement"].create(
            {"name": "Stmt A", "journal_id": journal.id, "operating_unit_id": ou_a.id}
        )
        statement_none = self.env["account.bank.statement"].create(
            {
                "name": "Stmt None",
                "journal_id": journal.id,
                "operating_unit_id": False,
            }
        )
        statement_b = self.env["account.bank.statement"].create(
            {"name": "Stmt B", "journal_id": journal.id, "operating_unit_id": ou_b.id}
        )
        user = self._create_ou_scoped_user(
            "test_rule_statement_user",
            ["ssi_financial_accounting_operating_unit.bank_statement_ou_group"],
            ou_a,
        )
        visible = (
            self.env["account.bank.statement"]
            .with_user(user)
            .search([("id", "in", (statement_a + statement_none + statement_b).ids)])
        )
        self.assertEqual(set(visible.ids), {statement_a.id, statement_none.id})

    # ------------------------------------------------------------------
    # account.statement.import._complete_stmts_vals — OU assignment on import.
    # ------------------------------------------------------------------

    def test_complete_stmts_vals_single_operating_unit(self):
        ou_a = self._create_operating_unit("Test Import OU A", "TESTIMPA")
        journal = self.env["account.journal"].create(
            {
                "name": "Test Import Journal Single OU",
                "code": "TSTIMPJ1",
                "type": "bank",
                "operating_unit_ids": [(6, 0, [ou_a.id])],
            }
        )
        wizard = self.env["account.statement.import"].new({})
        stmts_vals = [{"transactions": [{"payment_ref": "Test Import Line"}]}]
        result = wizard._complete_stmts_vals(stmts_vals, journal, "1234567890")
        self.assertEqual(result[0]["operating_unit_id"], ou_a.id)

    def test_complete_stmts_vals_multiple_operating_units_default_match(self):
        ou_a = self._create_operating_unit("Test Import Multi OU A", "TESTIMPMA")
        ou_b = self._create_operating_unit("Test Import Multi OU B", "TESTIMPMB")
        journal = self.env["account.journal"].create(
            {
                "name": "Test Import Journal Multi OU",
                "code": "TSTIMPJ2",
                "type": "bank",
                "operating_unit_ids": [(6, 0, [ou_a.id, ou_b.id])],
            }
        )
        user = self._create_ou_scoped_user(
            "test_import_default_user",
            ["ssi_financial_accounting_operating_unit.bank_statement_ou_group"],
            ou_a + ou_b,
        )
        user.default_operating_unit_id = ou_b
        wizard = self.env["account.statement.import"].with_user(user).new({})
        stmts_vals = [{"transactions": [{"payment_ref": "Test Import Line"}]}]
        result = wizard._complete_stmts_vals(stmts_vals, journal, "1234567890")
        self.assertEqual(result[0]["operating_unit_id"], ou_b.id)

    def test_complete_stmts_vals_multiple_operating_units_no_default_match(self):
        ou_a = self._create_operating_unit("Test Import NoMatch OU A", "TESTIMPNA")
        ou_b = self._create_operating_unit("Test Import NoMatch OU B", "TESTIMPNB")
        ou_other = self._create_operating_unit(
            "Test Import NoMatch OU Other", "TESTIMPNO"
        )
        journal = self.env["account.journal"].create(
            {
                "name": "Test Import Journal NoMatch",
                "code": "TSTIMPJ3",
                "type": "bank",
                "operating_unit_ids": [(6, 0, [ou_a.id, ou_b.id])],
            }
        )
        user = self._create_ou_scoped_user(
            "test_import_nomatch_user",
            ["ssi_financial_accounting_operating_unit.bank_statement_ou_group"],
            ou_a + ou_b + ou_other,
        )
        user.default_operating_unit_id = ou_other
        wizard = self.env["account.statement.import"].with_user(user).new({})
        stmts_vals = [{"transactions": [{"payment_ref": "Test Import Line"}]}]
        result = wizard._complete_stmts_vals(stmts_vals, journal, "1234567890")
        self.assertEqual(result[0]["operating_unit_id"], ou_a.id)
