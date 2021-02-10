odoo.define('pivotino_website.user_management', function (require) {
    "use strict";

    var Class = require('web.Class');
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var time = require('web.time');
    var weWidgets = require('wysiwyg.widgets');
    var websiteNavbarData = require('website.navbar');
    var websiteRootData = require('website.root');
    var Widget = require('web.Widget');
    var session = require('web.session');

    var _t = core._t;
    var qweb = core.qweb;

    var AddUserManagement = weWidgets.Dialog.extend({
        template: 'add_user_page',
        xmlDependencies: weWidgets.Dialog.prototype.xmlDependencies.concat(
            ['/pivotino_website/static/src/xml/add_user_management.xml']
        ),

        /**
         * @constructor
         * @override
         */
        init: function (parent, userid, options) {
            var self = this;

            var buttons = [
                {text: _t("Save"), classes: 'btn-primary', click: this.save_user},
                {text: _t("Discard"), classes: 'mr-auto', close: true},
            ];

            this._super(parent, _.extend({}, {
                title: _t("Add User"),
                size: 'medium',
                buttons: buttons,
            }, options || {}));
        },
        
        /**
         * @override
         */
        start: function () {
            var r = this._super.apply(this, arguments);
            return r;
        },

        /**
         * @override
         */
        destroy: function () {
            $('.popover').popover('hide');
            return this._super.apply(this, arguments);
        },

        /**
         * @override
         */
        save_user: function (data) {
            var self = this;
            
            var params = {
                email: this.$('#user_email').val(),
                access_rights: this.$('#user_rights').val(),
            };

            this._rpc({
                model: 'res.users',
                method: 'user_management_add',
                args: [session.user_id, params],
            }).then(function (result) {
                if (result == true) {
                    window.location.reload(true);
                } else {
                    self.destroy()
                    Dialog.alert(self, _t("The email has already exist in the system!"), {
                        title: _t('Email validation'),
                    });
                }
            });

        },
    });

    var EditUserManagement = weWidgets.Dialog.extend({
        template: 'edit_user_page',
        xmlDependencies: weWidgets.Dialog.prototype.xmlDependencies.concat(
            ['/pivotino_website/static/src/xml/add_user_management.xml']
        ),

        init: function (parent, userid, options) {
            var self = this;
            this.userid = userid

            var buttons = [
                {text: _t("Save"), classes: 'btn-primary', click: this.save_user},
                {text: _t("Discard"), classes: 'mr-auto', close: true},
            ];

            this._super(parent, _.extend({}, {
                title: _t("Edit User"),
                size: 'medium',
                buttons: buttons,
            }, options || {}));
        },

        start: function () {
            var r = this._super.apply(this, arguments);
            return r;
        },

        destroy: function () {
            $('.popover').popover('hide');
            return this._super.apply(this, arguments);
        },

        save_user: function (data) {
            var self = this;

            var params = {
                partner: this.userid,
                name: this.$('#name').val(),
                access_rights: this.$('#user_rights').val(),
            };

            return this._rpc({
                model: 'res.users',
                method: 'user_management_edit',
                args: [session.user_id, params],
            }).then(function () {
                window.location.reload(true);
            });
        },
    });

    var DeleteUserManagement = weWidgets.Dialog.extend({
        template: 'delete_user_page',
        xmlDependencies: weWidgets.Dialog.prototype.xmlDependencies.concat(
            ['/pivotino_website/static/src/xml/add_user_management.xml']
        ),

        init: function (parent, userid, options) {
            var self = this;
            this.userid = userid

            var buttons = [
                {text: _t("Okay"), classes: 'btn-primary', click: this.save_user},
                {text: _t("Discard"), classes: 'mr-auto', close: true},
            ];

            this._super(parent, _.extend({}, {
                title: _t("Delete User"),
                size: 'medium',
                buttons: buttons,
            }, options || {}));
        },

        start: function () {
            var r = this._super.apply(this, arguments);
            return r;
        },

        destroy: function () {
            $('.popover').popover('hide');
            return this._super.apply(this, arguments);
        },

        save_user: function (data) {
            var self = this;
            var params = {
                partner: this.userid,
            };

            return this._rpc({
                model: 'res.users',
                method: 'user_management_delete',
                args: [session.user_id, params],
            }).then(function () {
                window.location.reload(true);
            });
        },
    });

    var UserManagement = Widget.extend({
        template: 'pivotino_website.portal_my_user_management',
        events: {
            'click .user_management_add': '_onAddUserButtonClick',
            'click .user_management_edit': '_onEditUserButtonClick',
            'click .user_management_delete': '_onDeleteUserButtonClick',
            'click .user_management_send': '_onSendUserButtonClick',
        },

        _onAddUserButtonClick: function (ev) {
            var moID = $(ev.currentTarget).data('id');
            var dialog = new AddUserManagement(this,moID, {'fromCreateUser': true}).open();
            return dialog;
        },

        _onEditUserButtonClick: function (ev) {
            var moID = $(ev.currentTarget).data('id');
            var dialog = new EditUserManagement(this,moID, {'fromEditUser': true}).open();
            return dialog;
        },

        _onDeleteUserButtonClick: function (ev) {
            var moID = $(ev.currentTarget).data('id');
            var dialog = new DeleteUserManagement(this,moID, {'fromDeleteUser': true}).open();
            return dialog;
        },

        _onSendUserButtonClick: function (ev) {
            var moID = $(ev.currentTarget).data('id');
            return this._rpc({
                model: 'res.users',
                method: 'user_management_send',
                args: [moID],
            }).then(function () {
                window.location.reload(true);
            });
        }
    });

websiteRootData.websiteRootRegistry.add(UserManagement, '#portal_my_user_management');

return {
    AddUserManagement: AddUserManagement,
    EditUserManagement: EditUserManagement,
    DeleteUserManagement: DeleteUserManagement,
};
});
