# Copyright 2025 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import api, fields, models
from odoo.fields import Domain


class VoipOcaCall(models.Model):
    _name = "voip.call"
    _description = "Voip OCA Call"

    phone_number = fields.Char(required=True)
    type_call = fields.Selection(
        [
            ("incoming", "Incoming"),
            ("outgoing", "Outgoing"),
        ],
        default="outgoing",
    )
    state = fields.Selection(
        [
            ("aborted", "Aborted"),
            ("calling", "Calling"),
            ("missed", "Missed"),
            ("ongoing", "Ongoing"),
            ("rejected", "Rejected"),
            ("terminated", "Terminated"),
        ],
        default="calling",
        index=True,
    )
    pbx_id = fields.Many2one("voip.pbx", "PBX")
    end_date = fields.Datetime()
    start_date = fields.Datetime()
    activity_name = fields.Char(
        help="The name of the activity related to this phone call, if any."
    )
    partner_id = fields.Many2one("res.partner", "Contact", index=True)
    user_id = fields.Many2one(
        "res.users", "Responsible", default=lambda self: self.env.uid, index=True
    )

    @api.depends("state", "partner_id.name")
    def _compute_display_name(self):
        state_labels = {
            "aborted": "Aborted",
            "calling": "Calling",
            "missed": "Missed",
            "ongoing": "Ongoing",
            "rejected": "Rejected",
            "terminated": "Terminated",
        }
        for rec in self:
            name = rec.partner_id.display_name or rec.phone_number
            state_label = state_labels.get(rec.state, rec.state)
            rec.display_name = f"{state_label} - {name}"

    def _find_partner_by_phone(self):
        """Try to find a partner matching this call's phone number."""
        if self.partner_id:
            return self.partner_id
        if not self.phone_number:
            return self.env["res.partner"]

        # Normalize phone number
        import re
        normalized = re.sub(r'\D', '', self.phone_number)
        if not normalized:
            return self.env["res.partner"]

        # Try different variations
        phone_variants = [normalized]
        if normalized.startswith('43'):
            phone_variants.append('0' + normalized[2:])
            phone_variants.append('+43' + normalized[2:])
        elif normalized.startswith('0'):
            phone_variants.append('43' + normalized[1:])
            phone_variants.append('+43' + normalized[1:])

        for phone in phone_variants:
            partner = self.env["res.partner"].search([
                "|", "|",
                ("phone", "ilike", phone),
                ("phone_sanitized", "ilike", phone),
                ("phone", "ilike", "%" + phone[-8:]),  # Last 8 digits
            ], limit=1)
            if partner:
                # Link the partner permanently
                self.sudo().write({"partner_id": partner.id})
                return partner

        return self.env["res.partner"]

    def format_call(self):
        # Calculate duration if we have start and end dates
        duration = 0
        duration_str = ""
        if self.start_date and self.end_date:
            delta = self.end_date - self.start_date
            duration = int(delta.total_seconds())
            minutes, seconds = divmod(duration, 60)
            hours, minutes = divmod(minutes, 60)
            if hours:
                duration_str = f"{hours}h {minutes}m {seconds}s"
            elif minutes:
                duration_str = f"{minutes}m {seconds}s"
            else:
                duration_str = f"{seconds}s"

        # Format date string
        date_str = ""
        if self.create_date:
            # Convert to user timezone and format
            user_tz = self.env.user.tz or "UTC"
            create_date_local = fields.Datetime.context_timestamp(
                self.with_context(tz=user_tz), self.create_date
            )
            date_str = create_date_local.strftime("%d.%m.%Y %H:%M")

        # Try to find partner if not already linked
        partner = self._find_partner_by_phone()

        return {
            "id": self.id,
            "creationDate": self.create_date,
            "typeCall": self.type_call,
            "displayName": self.display_name,
            "endDate": self.end_date,
            "partner": partner and partner.format_partner(),
            "phoneNumber": self.phone_number,
            "startDate": self.start_date,
            "createDate": self.create_date,
            "state": self.state,
            "dateStr": date_str,
            "duration": duration,
            "durationStr": duration_str,
        }

    @api.model
    def _get_number_of_missed_calls(self):
        """Get count of missed calls - compatible with enterprise voip."""
        domain = [("user_id", "=", self.env.uid), ("state", "=", "missed")]
        # Check if user has last_seen_phone_call field (enterprise)
        if hasattr(self.env.user, 'last_seen_phone_call') and self.env.user.last_seen_phone_call:
            domain += [("id", ">", self.env.user.last_seen_phone_call.id)]
        return self.search_count(domain)

    @api.model
    def get_recent_calls(self, _search, offset, limit):
        domain = [("user_id", "=", self.env.uid)]
        if _search:
            search_fields = [
                "phone_number",
                "partner_id.name",
                "activity_name",
            ]
            search_domain = Domain.OR(
                *[[(field, "ilike", _search)] for field in search_fields]
            )
            domain = Domain.AND(domain, search_domain)
        return [
            call.format_call()
            for call in self.search(
                domain, offset=offset, limit=limit, order="create_date DESC"
            )
        ]

    @api.model
    def create_call(self, values):
        if not values.get("partner_id"):
            phone_number = values.get("phone_number", "")
            # Search by phone_sanitized (normalized) or phone field
            partner = self.env["res.partner"].search(
                [("phone_sanitized", "=", phone_number)],
                limit=1,
            )
            if not partner:
                # Fallback: search by phone field
                partner = self.env["res.partner"].search(
                    [("phone", "=", phone_number)],
                    limit=1,
                )
            values["partner_id"] = partner.id if partner else False
        return self.create(values).format_call()

    def _to_store_data(self):
        """Convert call to store_data format expected by enterprise voip JS."""
        result = {
            "voip.call": [],
            "res.partner": [],
        }
        for call in self:
            call_data = {
                "id": call.id,
                "create_date": call.create_date.isoformat() if call.create_date else False,
                "direction": call.type_call,  # Enterprise uses 'direction', we use 'type_call'
                "display_name": call.display_name,
                "end_date": call.end_date.isoformat() if call.end_date else False,
                "partner_id": call.partner_id.id if call.partner_id else False,
                "phone_number": call.phone_number,
                "start_date": call.start_date.isoformat() if call.start_date else False,
                "state": call.state,
            }
            result["voip.call"].append(call_data)

            if call.partner_id:
                partner_data = {
                    "id": call.partner_id.id,
                    "name": call.partner_id.name,
                    "display_name": call.partner_id.display_name,
                    "email": call.partner_id.email,
                    "phone": call.partner_id.phone,
                    "mobile": getattr(call.partner_id, 'mobile', False) or False,
                }
                # Avoid duplicates
                if not any(p["id"] == partner_data["id"] for p in result["res.partner"]):
                    result["res.partner"].append(partner_data)

        return result

    @api.model
    def create_and_format(
        self,
        phone_number=None,
        partner_id=None,
        direction="outgoing",
        res_id=None,
        res_model=None,
    ):
        """Creates a call - compatible with Odoo Enterprise voip module."""
        # Map direction to type_call
        type_call = "outgoing" if direction == "outgoing" else "incoming"

        # Try to find partner from res_id/res_model if not provided
        if not partner_id and res_id and res_model:
            try:
                related_record = self.env[res_model].browse(res_id)
                if hasattr(related_record, 'partner_id') and related_record.partner_id:
                    partner_id = related_record.partner_id.id
            except Exception:
                pass

        values = {
            "phone_number": phone_number or "",
            "partner_id": partner_id,
            "type_call": type_call,
            "state": "calling",
            "user_id": self.env.uid,
        }

        call = self.create(values)

        # Return format expected by enterprise voip JS: {ids: [...], store_data: {...}}
        return {
            "ids": [call.id],
            "store_data": call._to_store_data(),
        }

    def get_contact_info(self):
        """Find and link partner by phone number - compatible with enterprise voip."""
        self.ensure_one()
        if self.partner_id:
            return self._to_store_data()

        number = self.phone_number
        if not number:
            return False

        # Try to find partner by phone number
        import re
        normalized = re.sub(r'\D', '', number)

        # Search strategies
        partner = None
        search_variants = [number, normalized]

        # Add Austrian variants
        if normalized.startswith('43'):
            search_variants.append('0' + normalized[2:])
            search_variants.append('+43' + normalized[2:])
        elif normalized.startswith('0'):
            search_variants.append('43' + normalized[1:])
            search_variants.append('+43' + normalized[1:])

        for variant in search_variants:
            partner = self.env["res.partner"].search([
                "|",
                ("phone", "ilike", variant),
                ("phone_sanitized", "ilike", variant),
            ], limit=1)
            if partner:
                break

        if not partner:
            return False

        self.sudo().partner_id = partner
        return self._to_store_data()

    # Enterprise-compatible call state methods
    def abort_call(self):
        """Abort the call - compatible with enterprise voip."""
        self.sudo().state = "aborted"
        return self._to_store_data()

    def start_call(self):
        """Start the call (set ongoing) - compatible with enterprise voip."""
        calls_sudo = self.sudo()
        calls_sudo.start_date = fields.Datetime.now()
        calls_sudo.state = "ongoing"
        return self._to_store_data()

    def end_call(self, activity_name=None):
        """End the call - compatible with enterprise voip."""
        calls_sudo = self.sudo()
        calls_sudo.end_date = fields.Datetime.now()
        calls_sudo.state = "terminated"
        if activity_name:
            calls_sudo.activity_name = activity_name
        return self._to_store_data()

    def reject_call(self):
        """Reject the call - compatible with enterprise voip."""
        self.sudo().state = "rejected"
        return self._to_store_data()

    def miss_call(self):
        """Mark call as missed - compatible with enterprise voip."""
        self.sudo().state = "missed"
        return self._to_store_data()

    # Legacy methods for voip_freepbx JS
    def terminate_call(self):
        self.end_date = fields.Datetime.now()
        self.state = "terminated"
        return self.format_call()

    def accept_call(self):
        self.start_date = fields.Datetime.now()
        self.state = "ongoing"
        return self.format_call()
