# Copyright 2025 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import ssl
import socket
from urllib.parse import urlparse

from odoo import api, fields, models


class VoipFreePbx(models.Model):
    _name = "voip.pbx"
    _description = "VoIP PBX Server Configuration"

    name = fields.Char(required=True, default="FreePBX")
    domain = fields.Char(
        string="PBX Domain/IP",
        required=True,
        help="FreePBX server IP or domain (e.g., pbx.example.com)"
    )
    ws_server = fields.Char(
        string="WebSocket URL",
        required=True,
        help="WebSocket URL for WebRTC connection (e.g., wss://pbx.example.com:8089/ws)"
    )
    external_ip = fields.Char(
        string="External IP",
        help="External IP address for NAT traversal"
    )
    stun_server = fields.Char(
        string="STUN Server",
        default="stun:stun.l.google.com:19302",
        help="STUN server for WebRTC NAT traversal"
    )
    mode = fields.Selection(
        [("test", "Test"), ("prod", "Production")],
        string="Environment",
        default="prod",
        required=True,
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
    )

    # Connection status
    connection_status = fields.Selection(
        [
            ("disconnected", "Disconnected"),
            ("connecting", "Connecting"),
            ("connected", "Connected"),
            ("error", "Error"),
        ],
        string="Status",
        default="disconnected",
        readonly=True,
    )

    @api.model
    def get_default_pbx(self):
        """Get the default PBX configuration for the current company."""
        return self.search([
            ("company_id", "=", self.env.company.id),
            ("active", "=", True),
            ("mode", "=", "prod"),
        ], limit=1) or self.search([("active", "=", True)], limit=1)

    def test_connection(self):
        """Test the connection to FreePBX by checking if the port is reachable."""
        self.ensure_one()

        try:
            # Parse WebSocket URL
            parsed = urlparse(self.ws_server)
            host = parsed.hostname or self.domain
            port = parsed.port or (8089 if parsed.scheme == 'wss' else 8088)

            # Test TCP connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)

            if parsed.scheme == 'wss':
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                sock = context.wrap_socket(sock, server_hostname=host)

            sock.connect((host, port))
            sock.close()

            self.connection_status = "connected"
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Connection Successful",
                    "message": f"Successfully connected to {host}:{port}",
                    "type": "success",
                },
            }
        except socket.timeout:
            self.connection_status = "error"
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Connection Timeout",
                    "message": f"Could not reach {self.ws_server} (timeout)",
                    "type": "danger",
                },
            }
        except Exception as e:
            self.connection_status = "error"
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Connection Failed",
                    "message": str(e),
                    "type": "danger",
                },
            }
