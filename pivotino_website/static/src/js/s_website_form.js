odoo.define('pivotino_website.s_website_form', function (require) {
    'use strict';

    var core = require('web.core');
    var publicWidget = require('web.public.widget');

    var _t = core._t;
    var qweb = core.qweb;

    publicWidget.registry.s_website_form.include({
        check_error_fields: function (error_fields) {
            var res = this._super.apply(this, arguments);
            if (res && $("input[type=email]").length) {
                var emailField = $("input[type=email]");
                var mailformat = new RegExp("^(([^<>()[\\]\\\\.,;:\\s@\"]+(\\.[^<>()[\\]\\\\.,;:\\s@\"]+)*)|(\".+\"))@((\\[[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\])|(([a-zA-Z\\-0-9]+\\.)+[a-zA-Z]{2,}))$");
                if (!mailformat.test(emailField.val())) {
                    this.update_status('error', _t("Please enter a valid email address."));
                    emailField.addClass('is-invalid');
                    return false;
                } else {
                    emailField.removeClass('is-invalid');
                }
            }
            return res
        },

        update_status: function (status, message) {
            if (status !== 'success') { // Restore send button behavior if result is an error
                this.$target.find('.s_website_form_send, .o_website_form_send')
                    .removeAttr('disabled')
                    .removeClass('disabled'); // !compatibility
            }
            var $result = this.$('#s_website_form_result, #o_website_form_result'); // !compatibility

            if (status === 'error' && !message) {
                message = _t("An error has occured, please try again later.");
            }

            // Note: we still need to wait that the widget is properly started
            // before any qweb rendering which depends on xmlDependencies
            // because the event handlers are binded before the call to
            // willStart for public widgets...
            this.__started.then(() => $result.replaceWith(qweb.render(`website_form.status_${status}`, {
                message: message,
            })));
        },
    });

});
