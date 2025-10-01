# satu file satu class/fungsi (sesuai kebiasaan Anda), fungsi tunggal
def install_generic_coa_if_demo(cr, registry):
    """
    Pasang l10n_generic_coa HANYA jika DB dibuat dengan demo data.
    Aman untuk dipanggil berulang (cek dulu status modul).
    """
    import odoo
    from odoo.api import Environment

    # Demo mode: tanpa-demo == False → berarti demo diaktifkan saat init DB
    without_demo = bool(odoo.tools.config.get("without_demo"))
    if without_demo:
        return  # DB dibuat tanpa demo → tidak melakukan apa pun

    env = Environment(cr, odoo.SUPERUSER_ID, {})

    # Jika sudah terpasang, keluar
    mod = env["ir.module.module"].search([("name", "=", "l10n_generic_coa")], limit=1)
    if mod and mod.state in ("installed", "to install", "to upgrade"):
        return

    # Tandai untuk dipasang, lalu pasang
    if mod:
        mod.button_immediate_install()
    else:
        # fallback aman jika record modul belum tersinkron
        env["ir.module.module"].update_list()
        mod = env["ir.module.module"].search(
            [("name", "=", "l10n_generic_coa")], limit=1
        )
        if mod:
            mod.button_immediate_install()
