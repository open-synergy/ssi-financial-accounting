// Copyright 2026 OpenSynergy Indonesia
// Copyright 2026 PT. Simetri Sinergi Indonesia
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

odoo.define(
    "ssi_financial_accounting.account_bank_statement__bank_statement_tour",
    function (require) {
        "use strict";

        var tour = require("web_tour.tour");

        // Shared navigation: Financial Accounting > Bank & Cash > Bank
        // Statements. "Bank & Cash" (level 2) has children so it renders as
        // a dropdown-toggle; "Bank Statements" (level 3) is a leaf. The
        // landing menu of the app is "Invoices" (Account Receivable), so no
        // substring collision guard is needed here (patterns.md §A).
        function openBankStatementsMenu() {
            return [
                tour.stepUtils.showAppsMenuItem(),
                {
                    content: "Open the Financial Accounting app",
                    trigger:
                        '.o_app[data-menu-xmlid="ssi_financial_accounting.menu_root_financial_accounting"]',
                },
                {
                    content: "Open the Bank & Cash menu",
                    trigger:
                        '.o_menu_sections [data-menu-xmlid="ssi_financial_accounting.menu_bank_cash"]',
                },
                {
                    content: "Open the Bank Statements menu",
                    trigger:
                        '.o_menu_sections [data-menu-xmlid="ssi_financial_accounting.account_bank_statement_menu"]',
                },
                {
                    content: "Bank Statements list is displayed",
                    trigger:
                        ".o_control_panel .breadcrumb-item.active:contains(Bank Statements)",
                    extra_trigger: ".o_list_view",
                    run: function () {
                        // Assertion only.
                    },
                },
            ];
        }

        // Open the fixture record identified by its Journal column value
        // (the Journal column is shown in the tree, unlike the record's
        // own "name", which is still "/" before the statement is posted).
        function openRecordByJournal(journalName) {
            return [
                {
                    content: "Open the record",
                    trigger:
                        ".o_data_row:contains(" + journalName + ") .o_data_cell:first",
                    extra_trigger: ".o_list_view",
                },
                {
                    trigger: ".o_form_view",
                    run: function () {
                        // Assertion only.
                    },
                },
            ];
        }

        // IK: docs/account_bank_statement__bank_statement/01-create.md
        tour.register(
            "ssi_financial_accounting_account_bank_statement_bank_statement_create",
            {test: true, url: "/web"},
            [].concat(openBankStatementsMenu(), [
                // Flow 2 -- Click New.
                {
                    content: "Click New",
                    trigger: ".o_list_button_add",
                    extra_trigger: ".o_list_view",
                },
                {
                    content: "Form is open in edit mode",
                    trigger: ".o_form_view.o_form_editable",
                    run: function () {
                        // Assertion only.
                    },
                },

                // Flow 3 -- Journal (many2one rendered with
                // widget="selection" -> <select>, gabungan tag+class,
                // NOT a descendant "input"; field-writing-rules.md
                // "Field selection" table).
                {
                    content: "Select the Journal",
                    trigger: "select.o_field_widget[name='journal_id']",
                    extra_trigger: ".o_form_view.o_form_editable",
                    run: "text Tour Bank Statement Create",
                },
                // Flow 3 -- Ending Balance (Monetary widget wraps the
                // input, so " input" is required here).
                {
                    content: "Fill in the Ending Balance",
                    trigger: ".o_field_widget[name='balance_end_real'] input",
                    run: "text 100.0",
                },

                // Flow 4 (Inline Action, System group only) -- on the
                // Policies tab, click Reload Template Policy. Optional
                // per the IK text, but exercised here to prove the
                // button actually works, following the precedent in
                // ssi_customer_invoice_export's create tour.
                {
                    content: "Open the Policies tab",
                    trigger: ".o_notebook .nav-link:contains(Policies)",
                },
                {
                    content: "Click Reload Template Policy",
                    trigger: "button[name='action_reload_policy_template']",
                },
                {
                    content: "Reload Template Policy call has completed",
                    trigger: "button[name='action_reload_policy_template']:enabled",
                    run: function () {
                        // Assertion only.
                    },
                },

                // Flow 5 -- Save.
                {
                    content: "Save the record",
                    trigger: ".o_form_button_save",
                },
                {
                    content: "Record is saved",
                    trigger: ".o_form_view.o_form_readonly",
                    run: function () {
                        // Assertion only.
                    },
                },

                // Post-Condition -- status is New.
                {
                    content: "Status is New",
                    trigger:
                        ".o_statusbar_status .o_arrow_button[data-value='open'].btn-primary",
                    run: function () {
                        // Assertion only.
                    },
                },
            ])
        );

        // IK: docs/account_bank_statement__bank_statement/04-post.md
        tour.register(
            "ssi_financial_accounting_account_bank_statement_bank_statement_post",
            {test: true, url: "/web"},
            [].concat(
                openBankStatementsMenu(),
                openRecordByJournal("Tour Bank Statement Post"),
                [
                    // Flow 3 -- Click Post.
                    {
                        content: "Click the Post button",
                        trigger: ".o_statusbar_buttons button[name='button_post']",
                        extra_trigger: ".o_form_view",
                    },
                    // Post-Condition -- status is Processing.
                    {
                        content: "Status is Processing",
                        trigger:
                            ".o_statusbar_status .o_arrow_button[data-value='posted'].btn-primary",
                        run: function () {
                            // Assertion only.
                        },
                    },
                ]
            )
        );

        // IK: docs/account_bank_statement__bank_statement/05-validate.md
        tour.register(
            "ssi_financial_accounting_account_bank_statement_bank_statement_validate",
            {test: true, url: "/web"},
            [].concat(
                openBankStatementsMenu(),
                openRecordByJournal("Tour Bank Statement Validate"),
                [
                    // Flow 3 -- Click Validate.
                    {
                        content: "Click the Validate button",
                        trigger:
                            ".o_statusbar_buttons button[name='button_validate_or_action']",
                        extra_trigger: ".o_form_view",
                    },
                    // Post-Condition -- status is Validated.
                    {
                        content: "Status is Validated",
                        trigger:
                            ".o_statusbar_status .o_arrow_button[data-value='confirm'].btn-primary",
                        run: function () {
                            // Assertion only.
                        },
                    },
                ]
            )
        );

        // IK: docs/account_bank_statement__bank_statement/06-reset-to-new.md
        tour.register(
            "ssi_financial_accounting_account_bank_statement_bank_statement" +
                "_reset_to_new",
            {test: true, url: "/web"},
            [].concat(
                openBankStatementsMenu(),
                openRecordByJournal("Tour Bank Statement Reset New"),
                [
                    // Flow 3 -- Click Reset to New.
                    {
                        content: "Click the Reset to New button",
                        trigger: ".o_statusbar_buttons button[name='button_reopen']",
                        extra_trigger: ".o_form_view",
                    },
                    // Post-Condition -- status is New.
                    {
                        content: "Status is New",
                        trigger:
                            ".o_statusbar_status .o_arrow_button[data-value='open'].btn-primary",
                        run: function () {
                            // Assertion only.
                        },
                    },
                ]
            )
        );

        // IK: docs/account_bank_statement__bank_statement/07-reset-to-processing.md
        tour.register(
            "ssi_financial_accounting_account_bank_statement_bank_statement" +
                "_reset_to_processing",
            {test: true, url: "/web"},
            [].concat(
                openBankStatementsMenu(),
                openRecordByJournal("Tour Bank Statement Reset Processing"),
                [
                    // Flow 3 -- Click Reset to Processing.
                    {
                        content: "Click the Reset to Processing button",
                        trigger: ".o_statusbar_buttons button[name='button_reprocess']",
                        extra_trigger: ".o_form_view",
                    },
                    // Post-Condition -- status is Processing.
                    {
                        content: "Status is Processing",
                        trigger:
                            ".o_statusbar_status .o_arrow_button[data-value='posted'].btn-primary",
                        run: function () {
                            // Assertion only.
                        },
                    },
                ]
            )
        );

        // IK: docs/account_bank_statement__bank_statement/08-print.md
        //
        // Bounded per odoo-development-ui-test skill, patterns.md §Q: the
        // Print wizard's own Print button returns a report action with no
        // DOM "finished" signal (it triggers a PDF download) and is never
        // clicked here -- the tour only proves the wizard opens with a
        // report available, then discards it.
        tour.register(
            "ssi_financial_accounting_account_bank_statement_bank_statement_print",
            {test: true, url: "/web"},
            [].concat(
                openBankStatementsMenu(),
                openRecordByJournal("Tour Bank Statement Print"),
                [
                    // Flow 3 -- Click Print. The button name is a
                    // numeric action id in the DOM (id="%(...)d"
                    // template), never a stable [name=...] -- see
                    // odoo-development-ui-test skill, patterns-dialogs-
                    // and-wizards.md §H point 1.
                    {
                        content: "Click the Print button",
                        trigger: ".o_statusbar_buttons button:contains(Print)",
                        extra_trigger: ".o_form_view",
                    },
                    // Flow 4-5 stop here (see module comment above): the
                    // wizard is shown to be usable, but the Print button
                    // inside it is not clicked.
                    {
                        content: "The Select Report To Print wizard is displayed",
                        trigger: ".o_form_view",
                        run: function () {
                            // Assertion only.
                        },
                    },
                    {
                        content: "A report is available and Print is enabled",
                        trigger: ".modal-footer button[name='action_print']:enabled",
                        run: function () {
                            // Assertion only.
                        },
                    },
                    {
                        content: "Cancel the wizard",
                        trigger: ".modal-footer button:contains(Cancel)",
                    },
                    {
                        content: "Wizard is closed",
                        trigger: "body:not(:has(.modal))",
                        run: function () {
                            // Assertion only.
                        },
                    },
                ]
            )
        );
    }
);
