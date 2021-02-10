odoo.define('pivotino_website.pivotino_website', function (require) {
    'use strict';

    var ajax = require('web.ajax');

    // Global call when document is ready
    $(function () {
        $(".domain_instruction").hover(function () {
            $(this).popover({
                title: "Name Convention",
                content: "Max size is <strong>15</strong> <br /> " +
                  "Should be start &amp; end with alphanumeric <br /> " +
                  "Only lowercase is allowed <br /> " +
                  "Hyphen(-) can be used in-between",
                html: true
            }).popover('show');
        }, function () {
            $(this).popover('hide');
        });

        $(".pivotino_subscription_form input#company").focusout(function (ev) {
            if ($(ev.target).val() && !$(".pivotino_subscription_form input#domain").val()) {
                var company = $(ev.target).val();
                if (company) {
                    $(".pivotino_subscription_form .auto_suggest_loader").removeClass('d-none');
                    $(".pivotino_subscription_form input#domain").attr('readonly', 'readonly');
                    $(".pivotino_subscription_form button.pivotino-subscribe").attr('disabled', 'disabled');
                    ajax.jsonRpc('/pivotino/auto-suggest-domain', 'call', {'company': company})
                      .then(function (result) {
                          $(".pivotino_subscription_form input#domain").val(result);
                          $(".pivotino_subscription_form .auto_suggest_loader").addClass('d-none');
                          $(".pivotino_subscription_form input#domain").removeAttr('readonly', 'readonly');
                          $(".pivotino_subscription_form button.pivotino-subscribe").removeAttr('disabled', 'disabled');
                      });
                }
            }
        });
    });
});
