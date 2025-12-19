========================
VoIP FreePBX Integration
========================

.. |badge1| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: Beta
.. |badge2| image:: https://img.shields.io/badge/license-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-OCA%2Fconnector--telephony-lightgray.png?logo=github
    :target: https://github.com/OCA/connector-telephony/tree/19.0/voip_freepbx
    :alt: OCA/connector-telephony

|badge1| |badge2| |badge3|

This module allows the use of VoIP directly from Odoo with FreePBX/Asterisk.

It relies on SIP.js to connect to the PBX using a WebSocket directly
from the browser. Odoo server will not connect directly to the PBX server,
but will have users and passwords stored.

**Features:**

- WebRTC Softphone in browser
- Click-to-Call from Contacts/CRM
- Call History Logging
- Partner linking
- Call accept/reject
- Mute/Hold
- Call Transfer

**Table of contents**

.. contents::
   :local:

Configuration
=============

Create the PBX Connection
-------------------------

1. Access in Debug mode
2. Go to ``Settings > Technical > Discuss > FreePBX Servers``
3. Create a PBX server and define:
   - Domain name or IP address
   - WebSocket URL (e.g., ``wss://pbx.example.com:8089/ws``)

You can set it as ``Test`` or ``Production``. Test environment will
never contact the PBX server.

Configure FreePBX
-----------------

Your FreePBX/Asterisk server needs WebRTC support:

1. Enable WSS transport in FreePBX (Settings > Asterisk SIP Settings > chan_pjsip)
2. Create a WebRTC-enabled extension with:
   - AVPF: Yes
   - ICE Support: Yes
   - RTCP Mux: Yes
   - Media Encryption: DTLS

Configure Users
---------------

For each user, define their PBX credentials:

1. Admin: Go to ``Settings > Users & Companies > Users`` > VOIP tab
2. User: Go to ``Preferences`` > VOIP tab

Set the PBX server, username, and password.

Usage
=====

Once configured, the system will automatically login to the PBX server.
Use the softphone button in the top bar to open the VoIP widget.

**Making calls:**

1. Click a partner's phone number (shown in green)
2. Use the numpad in the widget

**During a call:**

- Transfer the call
- Mute/unmute
- Hold/unhold
- End the call

**Widget sections:**

1. Recent calls - history with status and duration
2. Call Activities - pending phone call activities
3. Contacts - quick access to partners with phone numbers

Known Issues / Roadmap
======================

- Allow to enable or disable VoIP per user (Login/Logout)
- Create automated call system based on activities

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/connector-telephony/issues>`_.

Credits
=======

Authors
-------

* Dixmit
* Florian Klaner

Contributors
------------

- `Dixmit <https://www.dixmit.com>`__:
  - Enric Alomar
  - Luis Rodriguez

- `Tecnativa <https://www.tecnativa.com>`__:
  - Carlos Roca

- `digiflo <https://www.digiflo.at>`__:
  - Florian Klaner (FreePBX integration)

Maintainers
-----------

This module is maintained by the OCA.

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

This module is part of the `OCA/connector-telephony <https://github.com/OCA/connector-telephony/tree/19.0/voip_freepbx>`_ project on GitHub.
