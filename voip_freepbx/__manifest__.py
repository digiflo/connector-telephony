# Copyright 2025 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "VoIP FreePBX Integration",
    "summary": "Integrate Odoo with FreePBX/Asterisk via WebRTC",
    "version": "19.0.1.0.0",
    "author": "Dixmit, Florian Klaner, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/connector-telephony",
    "license": "AGPL-3",
    "category": "Productivity/VOIP",
    "excludes": ["voip"],
    "depends": ["mail", "contacts", "crm"],
    "data": [
        "security/ir.model.access.csv",
        "data/voip_pbx_data.xml",
        "views/res_users.xml",
        "views/voip_call.xml",
        "views/voip_pbx.xml",
        "views/menus.xml",
    ],
    "demo": ["demo/demo_data.xml"],
    "assets": {
        "web.assets_backend": [
            "voip_freepbx/static/src/**/*",
        ],
        "voip_freepbx.agent_assets": [
            "voip_freepbx/static/lib/*.js",
        ],
        "web.assets_unit_tests": [
            "voip_freepbx/static/tests/**/*",
        ],
    },
    "installable": True,
    "application": True,
}
