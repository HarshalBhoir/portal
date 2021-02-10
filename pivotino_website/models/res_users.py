import uuid
import urllib3
import logging
import passlib.context
import ssl
import xmlrpc.client
from odoo.addons.auth_signup.models.res_partner import now
from odoo.exceptions import UserError
from odoo import api, fields, models, _
from simplecrypt import encrypt, decrypt
import base64

DEFAULT_CRYPT_CONTEXT = passlib.context.CryptContext(
    # kdf which can be verified by the context. The default encryption kdf is
    # the first of the list
    ['pbkdf2_sha512', 'plaintext'],
    # deprecated algorithms are still verified as usual, but ``needs_update``
    # will indicate that the stored hash should be replaced by a more recent
    # algorithm. Passlib 1.6 supports an `auto` value which deprecates any
    # algorithm but the default, but Ubuntu LTS only provides 1.5 so far.
    deprecated=['plaintext'],
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_logger = logging.getLogger(__name__)


class SubscriptionError(Exception):
    pass


# class ChangePasswordUser(models.TransientModel):
#     """ A model to configure users in the change password wizard. """
#     _inherit = 'change.password.user'
#     _description = 'User, Change Password Wizard'
#
#     def change_password_button(self):
#         for line in self:
#             if not line.new_passwd:
#                 raise UserError(_("Before clicking on 'Change Password', you have to write a new password."))
#             line.user_id.write({'internal_password': line.new_passwd})
#         return super(ChangePasswordUser, self).change_password_button()


class ResUsers(models.Model):
    _inherit = 'res.users'

    dummy_user_id = fields.Many2one('res.users.dummy', string='Dummy User ID',
                                    readonly=True)
    first_logged_in = fields.Boolean(string="First Login", readonly=True,
                                     default=False)
    customer_client_id = fields.Integer(string="Customer ID", default=0,
                                        readonly=True)
    user_role = fields.Selection([
        ('user', 'User'),
        ('owner', 'Business Owner'),
    ], string='User Role', default=False)
    internal_password = fields.Char(string="Internal Password",
                                    invisible=True, copy=False)

    def _set_password(self):
        ctx = self._crypt_context()
        hash_password = ctx.hash if hasattr(ctx, 'hash') else ctx.encrypt
        for user in self:
            cipher = encrypt('AIM', user.password)
            new_cip = base64.b64encode(cipher)
            str_cipher = new_cip.decode('utf-8')
            self.env.cr.execute(
                'UPDATE res_users SET internal_password=%s WHERE id=%s',
                (str_cipher, user.id)
            )
            self._set_encrypted_password(user.id, hash_password(user.password))

    @api.model
    def create(self, values):
        res = super(ResUsers, self).create(values)
        if res.partner_id:
            res.partner_id.with_context(from_user=True).write({
                'email': res.login,
                'user_role': res.user_role
            })
            if res.state == 'new':
                res.partner_id.with_context(from_user=True).write({
                    'res_user_state': 'Pending'
                })
            elif res.state == 'active':
                res.partner_id.with_context(from_user=True).write({
                    'res_user_state': 'Active'
                })
            parent_company = res.partner_id.parent_id
            if parent_company.subscription_company:
                url = parent_company.instance_url
                db = parent_company.databse_id.name
                self.env.cr.execute(
                    'select password, internal_password from res_users where id=%s', (res.id,))
                result = self.env.cr.fetchone()
                username = res.login
                password = res.password
                params = {
                    'name': res.name,
                    'active': res.active,
                    'login': res.login,
                    'email': res.login,
                    'tz': res.tz,
                    'cust_email_creation': True,
                }
                try:
                    common = xmlrpc.client.ServerProxy(
                        '{}/xmlrpc/2/common'.format(url), verbose=False,
                        context=ssl._create_unverified_context())
                    uid = common.authenticate(db, username, password, {})
                    models = xmlrpc.client.ServerProxy(
                        '{}/xmlrpc/2/object'.format(url), verbose=False,
                        context=ssl._create_unverified_context())

                    new_instance_user = models.execute_kw(db, uid, password, 'res.users', 'create',
                                                          [uid, params])
                    models.execute_kw(db, uid, password, 'res.users', 'api_set_password',
                                      [result, new_instance_user])
                except Exception:
                    pass
        return res

    def write(self, vals):
        res = super(ResUsers, self).write(vals)
        if not self.env.context.get('from_partner'):
            for user in self:
                if user.partner_id:
                    if user.user_role:
                        user.partner_id.with_context(from_user=True).write({
                            'user_role': user.user_role
                        })

                    if user.active is False:
                        user.partner_id.with_context(from_user=True).write({
                            'active': False
                        })
                    else:
                        user.partner_id.with_context(from_user=True).write({
                            'active': True
                        })
                        if user.state == 'new':
                            user.partner_id.with_context(from_user=True).write({
                                'res_user_state': 'Pending'
                            })
                        elif user.state == 'active':
                            user.partner_id.with_context(from_user=True).write({
                                'res_user_state': 'Active'
                            })

                if 'active' in vals or 'name' in vals:
                    parent_company = user.partner_id.parent_id
                    if parent_company.subscription_company:
                        url = parent_company.instance_url
                        db = parent_company.database_id.name
                        username = user.login
                        password = user.password
                        params = {
                            'name': user.name,
                            'active': user.active,
                        }
                        try:
                            common = xmlrpc.client.ServerProxy(
                                '{}/xmlrpc/2/common'.format(url), verbose=False,
                                context=ssl._create_unverified_context())
                            uid = common.authenticate(db, username, password, {})
                            models = xmlrpc.client.ServerProxy(
                                '{}/xmlrpc/2/object'.format(url), verbose=False,
                                context=ssl._create_unverified_context())
                            models.execute_kw(db, uid, password, 'res.users', 'write',
                                              [uid, params])
                        except Exception:
                            pass

                if 'password' in vals:
                    parent_company = user.partner_id.parent_id
                    if parent_company.subscription_company:
                        url = parent_company.instance_url
                        db = parent_company.database_id.name
                        username = user.login
                        password = user.password
                        try:
                            common = xmlrpc.client.ServerProxy(
                                '{}/xmlrpc/2/common'.format(url),
                                verbose=False,
                                context=ssl._create_unverified_context())
                            uid = common.authenticate(db, username, password,
                                                      {})
                            models = xmlrpc.client.ServerProxy(
                                '{}/xmlrpc/2/object'.format(url),
                                verbose=False,
                                context=ssl._create_unverified_context())
                            self.env.cr.execute(
                                'select password, internal_password from res_users where id=%s',
                                (user.id,))
                            result = self.env.cr.fetchone()
                            models.execute_kw(db, uid, password,
                                              'res.users',
                                              'api_set_password',
                                              [result, uid])
                        except Exception:
                            pass

        return res

    def unlink(self):
        if not self.env.context.get('from_partner'):
            for user in self:
                if user.partner_id:
                    user.partner_id.with_context(from_user=True).unlink()
        return super().unlink()

    def user_management_add(self, params):
        existing_email = self.env['res.users'].search(
            [('login', '=', params.get('email'))])
        parent_company = self.partner_id.parent_id
        if existing_email:
            return False
        else:
            vals = {
                'name': parent_company.name + '- New User',
                'login': params.get('email'),
                'user_role': params.get('access_rights'),
            }
            new_user = self.create(vals)
            new_user.partner_id.sudo().write({
                'parent_id': parent_company,
            })
            return True

    def user_management_edit(self, params):
        edit_user = self.env['res.users'].search([('partner_id', '=', params.get('partner'))])
        edit_user.sudo().write({
            'name': params.get('name'),
            'user_role': params.get('access_rights'),
        })
        edit_user.partner_id.sudo().write({
            'name': params.get('name'),
            'user_role': params.get('access_rights'),
        })
        return True

    def user_management_send(self):
        send_user = self.env['res.users'].search(
            [('partner_id', '=', self.id)])
        if send_user.login:
            send_user.action_reset_password()
        return True

    def user_management_delete(self, params):
        delete_user = self.env['res.users'].search([('partner_id', '=', params.get('partner'))])
        delete_user.sudo().write({
            'active': False,
        })
        return True

    # override function to disable odoo base welcome email when create user
    def action_reset_password(self):
        """ create signup token for each user, and send their signup url by email """
        # prepare reset password signup
        create_mode = bool(self.env.context.get('create_user'))

        # no time limit for initial invitation, only for reset password
        expiration = False if create_mode else now(days=+1)

        self.mapped('partner_id').signup_prepare(signup_type="reset",
                                                 expiration=expiration)

        # send email to users with their signup url
        template = False
        if create_mode:
            try:
                template = self.env.ref('auth_signup.set_password_email',
                                        raise_if_not_found=False)
            except ValueError:
                pass
        if not template:
            template = self.env.ref('auth_signup.reset_password_email')
        assert template._name == 'mail.template'

        template_values = {
            'email_to': '${object.email|safe}',
            'email_cc': False,
            'auto_delete': True,
            'partner_to': False,
            'scheduled_date': False,
        }
        template.write(template_values)

        for user in self:
            if not user.email:
                raise UserError(_(
                    "Cannot send email: user %s has no email address.") % user.name)
            if not user.share:
                with self.env.cr.savepoint():
                    force_send = not (
                        self.env.context.get('import_file', False))
                    template.with_context(lang=user.lang).send_mail(user.id,
                                                                    force_send=force_send,
                                                                    raise_exception=True)
                _logger.info("Password reset email sent for user <%s> to <%s>",
                             user.login, user.email)


class ResUsersDummy(models.Model):
    _name = 'res.users.dummy'
    _description = 'Res Users Dummy'

    def _get_subscription_token(self):
        return str(uuid.uuid4())

    name = fields.Char(string='Name', required=True)
    email = fields.Char(string='Email', required=True)
    company = fields.Char(string='Company', required=True)
    subscription_id = fields.Many2one('saas.subscription',
                                      string='Subscription',
                                      required=False, copy=False)
    subscription_token = fields.Char(
        string='Subscription Token',
        default=lambda self: self._get_subscription_token(),
        copy=False, readonly=True, required=True)
    active = fields.Boolean(default=True)
    ip_address = fields.Char(string='Visitor IP Address', readonly=True)
    country_id = fields.Many2one('res.country', string='Visitor Country',
                                 readonly=True)
    tz = fields.Char(string='Timezone', readonly=True)
    is_staging = fields.Boolean(string='Is Staging?', default=False)
    mail_ids = user_ids = fields.One2many('mail.mail', 'res_id',
                                          string='Emails', copy=False)
    pivo_phone = fields.Char('Phone', required=True)
    password = fields.Char(compute='_compute_password', inverse='_set_password',
        invisible=True, copy=False, store=True)
    internal_password = fields.Char(string="Internal Password",
                                    invisible=True, copy=False)

    @api.model
    def subscription(self, values):
        subscription_token = False
        # We Remove the starting & ending trail spaces if any from domain
        if values:
            new_subscription = self.create(values)
            subscription_token = new_subscription.subscription_token
        return subscription_token

    def send_verification_email(self):
        template = self.env.ref(
            'pivotino_website.mail_template_subscription_account_verification',
            raise_if_not_found=False)
        for user in self:
            template.send_mail(user.id, force_send=True)

    def _crypt_context(self):
        """ Passlib CryptContext instance used to encrypt and verify
        passwords. Can be overridden if technical, legal or political matters
        require different kdfs than the provided default.

        Requires a CryptContext as deprecation and upgrade notices are used
        internally
        """
        return DEFAULT_CRYPT_CONTEXT

    def _compute_password(self):
        for user in self:
            user.password = ''

    def _set_password(self):
        ctx = self._crypt_context()
        for user in self:
            cipher = encrypt('AIM', user.password)
            new_cip = base64.b64encode(cipher)
            str_cipher = new_cip.decode('utf-8')
            self.env.cr.execute(
                'UPDATE res_users_dummy SET internal_password=%s WHERE id=%s',
                (str_cipher, uid)
            )
            self._set_encrypted_password(user.id, ctx.encrypt(user.password))

    def _set_encrypted_password(self, uid, pw):
        assert self._crypt_context().identify(pw) != 'plaintext'

        self.env.cr.execute(
            'UPDATE res_users_dummy SET password=%s WHERE id=%s',
            (pw, uid)
        )
        self.invalidate_cache(['password'], [uid])

    def _set_internal_password(self):
        for user in self:
            cipher = encrypt('AIM', user.password)
            self.env.cr.execute(
                'UPDATE res_users_dummy SET internal_password=%s WHERE id=%s',
                (cipher, user.id)
            )
