odoo.define('osp_customization.osp_popup', function (require) {
    "use strict";

    var config = require('web.config');
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var utils = require('web.utils');
    var publicWidget = require('web.public.widget');
    const {ReCaptcha} = require('google_recaptcha.ReCaptchaV3');

    var _t = core._t;

    publicWidget.registry.OspPopup = publicWidget.Widget.extend({
        selector: ".s_website_form_osp_popup",
        disabledInEditableMode: false,
        read_events: {
            'click .s_website_form_send_osp_popup': '_onSubmitClick',
        },

        /**
         * @constructor
         */
        init: function () {
            this._super(...arguments);
            this._recaptcha = new ReCaptcha();
        },

        /**
         * @override
         */
        willStart: function () {
            this._recaptcha.loadLibs();
            return this._super(...arguments);
        },

        /**
         * @override
         */
        start: function () {
            var defs = [this._super.apply(this, arguments)];
            this.$popup = this.$target.closest('.osp_popup_modal');
            // Initialize IntlTelInput
            var phone_input = document.querySelector(".intlTelInput");
            this.itiPhone = window.intlTelInput(phone_input, {
                separateDialCode: true,
                preferredCountries: ['my', 'in', 'us'],
                utilsScript: "/intl_phone_field/static/src/lib/utils.js",
            });
            return Promise.all(defs);
        },

        /**
         * @private
         */
        _onSubmitClick: async function () {
            var self = this;
            var $medium = this.$("input.osp_popup_medium");
            var $name = this.$("input.osp_popup_name");
            var $email = this.$("input.osp_popup_email");
            var invalid_name, invalid_email, invalid_phone;

            var mailformat = new RegExp("^(([^<>()[\\]\\\\.,;:\\s@\"]+(\\.[^<>()[\\]\\\\.,;:\\s@\"]+)*)|(\".+\"))@((\\[[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\])|(([a-zA-Z\\-0-9]+\\.)+[a-zA-Z]{2,}))$");

            if (!$name.val()) {
                this.$target.addClass('o_has_error').find('.form-control.osp_popup_name').addClass('is-invalid');
                invalid_name = true;
            } else {
                this.$target.find('.form-control.osp_popup_name').removeClass('is-invalid');
                invalid_name = false;
            }
            if (!mailformat.test($email.val())) {
                this.$target.addClass('o_has_error').find('.form-control.osp_popup_email').addClass('is-invalid');
                invalid_email = true;
            } else {
                this.$target.find('.form-control.osp_popup_email').removeClass('is-invalid');
                invalid_email = false;
            }

            var isValid = this.itiPhone.isValidNumber();
            if (!isValid) {
                this.$target.addClass('o_has_error').find('.form-control.osp_popup_phone').addClass('is-invalid');
                invalid_phone = true;
            } else {
                this.$target.find('.form-control.osp_popup_phone').removeClass('is-invalid');
                invalid_phone = false;
            }

            if (invalid_name) {
                this.$target.find('span.osp_popup_error').html("Please fill the form correctly.");
                return false;
            }
            if (invalid_email) {
                this.$target.find('span.osp_popup_error').html("Please enter a valid email address.");
                return false;
            }
            if (invalid_phone) {
                this.$target.find('span.osp_popup_error').html("Please enter a valid phone number.");
                return false;
            }

            this.$target.removeClass('o_has_error');
            this.$target.find('span.osp_popup_error').html();
            const tokenObj = await this._recaptcha.getToken('osp_popup_form');
            if (tokenObj.error) {
                self.displayNotification({
                    type: 'danger',
                    title: _t("Error"),
                    message: tokenObj.error,
                    sticky: true,
                });
                return false;
            }

            var fullNumber = this.itiPhone.getNumber();
            this._rpc({
                route: '/osp_customization/osp_popup/submit',
                params: {
                    'name': $name.val(),
                    'email': $email.val(),
                    'phone': fullNumber,
                    'medium': $medium.val(),
                    recaptcha_token_response: tokenObj.token,
                },
            }).then(function (result) {
                if (result) {
                    self.$popup.find('div.s_website_form_osp_popup').addClass('o_hidden');
                    self.$popup.find('div.s_website_form_osp_popup_thanks').removeClass('o_hidden');
                }
            });
        },

    });
});
