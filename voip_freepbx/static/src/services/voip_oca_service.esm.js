/*
    Copyright 2025 Dixmit
    License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
    This service will contain all the items necessary for the views
    of the voip widgets.
*/
import {matchString} from "../utils/utils.esm";
import {reactive} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {session} from "@web/session";
import {url} from "@web/core/utils/urls";
import {user} from "@web/core/user";

export class VoipOCA {
    constructor(env, services) {
        /* Store voip data in the service, not the session */
        Object.assign(this, session.voip);
        delete session.voip;
        this.status = "disconnected";
        this.selectedTab = "activity_list";
        this.uid = user.userId;
        this.store = services["mail.store"];
        this.numpadTab = false;
        this.orm = services.orm;
        this.isOpened = false;
        this.isFolded = false;
        this.partner = {};
        this.activity = {};
        this.call = {};
        this.inCall = false;
        this.searchValue = "";
        this.numpad = {
            isOpen: false,
            value: "",
            selection: {
                start: 0,
                end: 0,
                direction: "none",
            },
        };
        this.user = env.services.user;
        // We will make this service reactive,
        // this way we will hanble the changes on the component
        return reactive(this);
    }
    /* Widget Buttons */
    handleVoip() {
        if (!this.isOpened) {
            this.isFolded = false;
        }
        this.isOpened = !this.isOpened;
    }
    handleFold() {
        this.isFolded = !this.isFolded;
    }
    async open({partner = null, activity = null, call = null}) {
        let partner_id = partner && partner.id;
        if (activity) {
            partner_id = activity.main_partner_id && activity.main_partner_id[0];
        } else if (call) {
            partner_id = call.partner && call.partner.id;
        }
        this.activity = activity || {};
        this.call = call || {};
        if (partner_id) {
            const result = await this.orm.call("res.partner", "format_partner", [
                [partner_id],
            ]);
            this.partner = result || {};
        } else {
            this.partner = {};
        }
    }
    async acceptCall() {
        if (this.call && this.call.id) {
            this.call = await this.orm.call("voip.call", "accept_call", [[this.call.id]]);
        }
    }
    async rejectCall() {
        if (this.call && this.call.id) {
            await this.orm.call("voip.call", "reject_call", [[this.call.id]]);
        }
        this.inCall = false;
        this.call = {};
        this.partner = {};
        this.activity = {};
    }
    /* Elements */

    get partners() {
        const partners = Array.isArray(this._partners) ? this._partners : [];
        return partners.filter(
            (partner) =>
                !this.searchValue ||
                [
                    partner.name,
                    partner.displayName,
                    partner.mobileNumber,
                    partner.landlineNumber,
                ].some((x) => matchString(x, this.searchValue))
        );
    }
    get activities() {
        const activities = Array.isArray(this._activities) ? this._activities : [];
        return activities.filter(
            (activity) =>
                !this.searchValue ||
                [activity.summary, activity.resName, activity.main_partner].some(
                    (x) => matchString(x, this.searchValue)
                )
        );
    }

    get calls() {
        const calls = Array.isArray(this._calls) ? this._calls : [];
        return calls
            .filter(
                (call) =>
                    !this.searchValue ||
                    [call.phoneNumber, call.displayName].some((x) =>
                        matchString(x, this.searchValue)
                    )
            )
            .sort((a, b) => new Date(b.createDate) - new Date(a.createDate));
    }
    get partnerProps() {
        return {
            partner: this.partner || {},
            activity: this.activity || {},
            call: this.call || {},
        };
    }

    /* Search functions */
    async searchPartners(_search = "", offset = 0, limit = 13) {
        const partners = await this.orm.call("res.partner", "voip_get_contacts", [], {
            offset,
            limit,
            _search,
        });
        // Store partners locally - ensure it's an array
        this._partners = Array.isArray(partners) ? partners : [];
    }
    async searchActivities(_search = "", offset = 0, limit = 13) {
        const result = await this.orm.call(
            "mail.activity",
            "get_call_activities",
            [],
            {
                offset,
                limit,
                _search,
            }
        );
        // Store activities locally - handle various response formats
        let activities = [];
        if (Array.isArray(result)) {
            activities = result;
        } else if (result && typeof result === "object") {
            // activity_format() returns {"mail.activity": [...]}
            activities = result["mail.activity"] || Object.values(result)[0] || [];
            if (!Array.isArray(activities)) {
                activities = [];
            }
        }
        this._activities = activities;
    }
    async searchCalls(_search = "", offset = 0, limit = 13) {
        const calls = await this.orm.call("voip.call", "get_recent_calls", [], {
            offset,
            limit,
            _search,
        });
        // Store calls locally - ensure it's an array
        this._calls = Array.isArray(calls) ? calls : [];
    }
    /* Image functions */
    imagePartner(partner_id) {
        return url("/web/image", {
            model: "res.partner",
            id: partner_id,
            field: "avatar_128",
        });
    }
}

export const voipOCAService = {
    dependencies: ["mail.store", "orm"],
    async start() {
        return new VoipOCA(...arguments);
    },
};

registry.category("services").add("voip_freepbx", voipOCAService);
