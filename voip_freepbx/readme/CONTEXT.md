This module is intended to integrate directly with a VoIP Provider via WebRTC.

The provider needs to supply a WebRTC system where we will plug in.

Currently, it has been tested with:

- [FreePBX](https://www.freepbx.org/) / Asterisk
- [Zerovoz](https://zerovoz.com/)
- [Ringover](https://www.ringover.es/)

Theoretically, it should work with any PBX that supports WebSocket connections (RFC 7118):

- Axivox
- OnSIP
- Twilio
- Any Asterisk-based system with WebRTC enabled
