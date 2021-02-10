odoo.define('pivotino_website.resend_email', function (require) {
'use strict';

var publicWidget = require('web.public.widget');

publicWidget.registry.ResendEmail = publicWidget.Widget.extend({
    selector: '#wrapwrap:has(.resend-email)',
    events: {
        'click .resend-email': 'resend_email',
    },

    start: function () {
        var self = this;
        this._super.apply(this, arguments);
       },

    init: function () {
        var self = this;
        this._super.apply(this, arguments);
        this.seconds = 30;
        this.minutes = 0;
       },

    counter: function() {
        var self = this;
        self.seconds--;
        if(self.seconds == 0) {
             self.minutes = self.minutes-1;
             self.seconds = 30;
        }
        self.$('#timer').html('<span>Please wait for  ' + '<strong style="font-size: 30px;">' + self.seconds + '</strong>'+ '  seconds before you try again...</span>');
            if(self.minutes == -1) {
                clearInterval(self.timer);
                self.minutes = 0;
                self.$('#resend').removeClass('d-none');
                self.$('#timer').addClass('d-none');
            }
    },

    resend_email: function () {
        var self = this;
        var email = $('#email').val();
        var token = $('#token').val();
        self.$('#resend').addClass('d-none');
        self.$('#timer').removeClass('d-none');
        self.timer = setInterval(function(){self.counter()},1000);
        return this._rpc({
            route: '/pivotino/subscription/resend',
            params: {
                subscription_token: token,
                email: email,
            },
        }).then(function (result) {
            if (result === true){
                alert('Email resend succesfully!');
            } else {
                alert('Email resend failed!');
            }
        });
    },

});
});
