# Copyright 2025 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re
from odoo import api, models
from odoo.fields import Domain


class VoipOcaCall(models.Model):
    _inherit = "res.partner"

    def format_partner(self):
        # Use phone field, mobile may not exist in Odoo 19 CE
        mobile = getattr(self, 'mobile', False) or False
        return {
            "id": self.id,
            "type": "partner",
            "displayName": self.display_name,
            "email": self.email,
            "landlineNumber": self.phone,
            "mobileNumber": mobile,
            "name": self.name,
        }

    @api.model
    def voip_get_contacts(self, _search, offset, limit):
        # Only use phone field, mobile may not exist in Odoo 19 CE
        domain = [("phone", "!=", False)]
        if _search:
            search_fields = ["name", "phone", "email"]
            search_domain = Domain.OR(
                *[[(field, "ilike", _search)] for field in search_fields]
            )
            domain = Domain.AND(domain, search_domain)
        contacts = self.search(domain, offset=offset, limit=limit)
        return [contact.format_partner() for contact in contacts]

    @api.model
    def get_contacts(self, offset, limit, search_terms, t9_search=False):
        """Compatible with Odoo Enterprise voip module."""
        domain = [("phone", "!=", False)]
        if search_terms:
            search_fields = ["name", "phone", "email"]
            search_domain = Domain.OR(
                *[[(field, "ilike", search_terms)] for field in search_fields]
            )
            domain = Domain.AND(domain, search_domain)
        contacts = self.search(domain, offset=offset, limit=limit)
        # Return in format expected by enterprise voip
        return {
            "res.partner": [
                {
                    "id": c.id,
                    "name": c.name,
                    "display_name": c.display_name,
                    "email": c.email,
                    "phone": c.phone,
                    "mobile": getattr(c, 'mobile', False) or False,
                }
                for c in contacts
            ]
        }

    def get_activity_main_partner_id(self):
        """Override to return the partner itself."""
        return self

    def _link_voip_calls_to_partner(self):
        """Link existing voip.call records to this partner based on phone number."""
        VoipCall = self.env["voip.call"]
        for partner in self:
            phone_numbers = []
            if partner.phone:
                # Normalize phone number (remove non-digits)
                normalized = re.sub(r'\D', '', partner.phone)
                if normalized:
                    phone_numbers.append(normalized)
                    # Also try with country code variations
                    if normalized.startswith('43'):
                        phone_numbers.append('0' + normalized[2:])
                    elif normalized.startswith('0'):
                        phone_numbers.append('43' + normalized[1:])

            if phone_numbers:
                # Find calls without partner that match any of the phone numbers
                for phone in phone_numbers:
                    calls = VoipCall.search([
                        ("partner_id", "=", False),
                        ("phone_number", "ilike", phone),
                    ])
                    if calls:
                        calls.write({"partner_id": partner.id})

    @api.model_create_multi
    def create(self, vals_list):
        partners = super().create(vals_list)
        # Link any existing calls to the new partners
        partners._link_voip_calls_to_partner()
        return partners

    def write(self, vals):
        res = super().write(vals)
        # If phone was updated, try to link calls
        if "phone" in vals:
            self._link_voip_calls_to_partner()
        return res
