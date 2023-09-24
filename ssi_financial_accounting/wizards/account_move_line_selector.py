from odoo import api, fields, models


class AccountMoveLineSelector(models.TransientModel):
    _name = "account_move_line_selector"
    _description = "Journal Item Selector"

    active_model = fields.Char(
        string="Active Model",
    )
    active_id = fields.Integer(
        string="Active ID",
    )
    filter_account_ok = fields.Boolean(
        string="Filter by Account",
        default=False,
    )
    account_ids = fields.Many2many(
        string="Allowed Accounts",
        comodel_name="account.account",
    )
    filter_partner_ok = fields.Boolean(
        string="Filter by Partner",
        default=False,
    )
    partner_ids = fields.Many2many(
        string="Allowed Partners",
        comodel_name="res.partner",
    )
    filter_journal_ok = fields.Boolean(
        string="Filter by Journal",
        default=False,
    )
    journal_ids = fields.Many2many(
        string="Allowed Journals",
        comodel_name="account.journal",
    )
    filter_analytic_ok = fields.Boolean(
        string="Filter by Analytic Account",
        default=False,
    )
    analytic_account_ids = fields.Many2many(
        string="Allowed Analytic Accounts",
        comodel_name="account.analytic.account",
    )
    direction = fields.Selection(
        string="Direction",
        selection=[
            ("dr", "Debit"),
            ("cr", "Credit"),
            ("both", "Both"),
        ],
        default="dr",
    )
    reconcile = fields.Boolean(
        string="Reconcile",
        default=True,
    )
    allowed_move_line_ids = fields.Many2many(
        string="Allowed Move Lines",
        comodel_name="account.move.line",
        compute="_compute_allowed_move_line_ids",
        store=False,
    )
    move_line_ids = fields.Many2many(
        string="Selected Move Lines",
        comodel_name="account.move.line",
    )
    field_mapping = fields.Text(
        string="Field Mapping",
    )

    @api.depends(
        "filter_account_ok",
        "account_ids",
        "filter_journal_ok",
        "journal_ids",
        "filter_partner_ok",
        "partner_ids",
        "filter_analytic_ok",
        "analytic_account_ids",
        "direction",
        "reconcile",
    )
    def _compute_allowed_move_line_ids(self):
        for record in self:
            criteria = [
                ("reconciled", "=", record.reconcile),
                ("account_id.reconcile", "=", True),
            ]

            if record.direction == "dr":
                criteria.append(("debit", ">", 0.0))
            elif record.direction == "cr":
                criteria.append(("credit", ">", 0.0))

            if record.filter_account_ok:
                criteria.append(("account_id", "in", record.account_ids.ids))

            if record.filter_journal_ok:
                criteria.append(("journal_id", "in", record.journal_ids.ids))

            if record.filter_partner_ok:
                criteria.append(("partner_id", "in", record.partner_ids.ids))

            if record.filter_analytic_ok:
                criteria.append(
                    ("analytic_account_id", "in", record.analytic_account_ids.ids)
                )

            record.allowed_move_line_ids = self.env["account.move.line"].search(
                criteria
            )

    def action_confirm(self):
        for record in self.sudo():
            record._confirm()

    def _confirm(self):
        self.ensure_one()
        for aml in self.move_line_ids:
            aml._transform_to_other_data(self)
