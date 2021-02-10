from odoo import api, fields, models, _
import xmlrpc.client
import ssl
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    subscription_company = fields.Boolean(string='Subscription Company')
    main_saas_user = fields.Many2one('res.partner', string='Main User')

    subscription_id = fields.Many2one('saas.subscription',
                                      string='Subscription',
                                      copy=False)
    addon_ids = fields.Many2many('saas.subscription.addons',
                                 string='Add-ons', copy=False)
    subscription_token = fields.Char(string='Subscription Token', copy=False, readonly=True)
    subscription_start_date = fields.Date(string='Valid From',
                                          readonly=True, copy=False)
    subscription_end_date = fields.Date(string='Valid Until',
                                        readonly=True, copy=False)
    instance_url = fields.Char(string='Instance URL', copy=False)
    ip_address = fields.Char(string='IP Address', readonly=True)
    subscription_history_ids = fields.One2many(
        'saas.subscription.history', 'partner_id',
        string='Subscription History', readonly=True, copy=False)
    is_staging = fields.Boolean(string='Is Staging?', default=False)
    database_id = fields.Many2one('database.details', 'Database')
    instance_id = fields.Many2one('instance.details', 'Instance')
    welcome_sent_count = fields.Integer(string='Number of Welcome Emails Sent',
                                        default=0, readonly=True)
    email_creation = fields.Boolean(string='Successful Email Creation',
                                         readonly=True, default=False)
    res_user_state = fields.Char(string='User Status', readonly=True)
    user_role = fields.Selection([
        ('user', 'User'),
        ('owner', 'Business Owner'),
    ], string='User Role', default=False, readonly=True)

    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        if not self.env.context.get('from_user'):
            for partner in self:
                user = self.env['res.users'].search([('partner_id', '=', partner.id)])
                if user:
                    if partner.active is False:
                        user.with_context(from_partner=True).write({
                            'active': False
                        })
                    else:
                        user.with_context(from_partner=True).write({
                            'active': True
                        })

        return res

    def unlink(self):
        if not self.env.context.get('from_user'):
            for partner in self:
                user = self.env['res.users'].search(
                    [('partner_id', '=', partner.id)])
                if user:
                    user.with_context(from_partner=True).unlink()
        return super().unlink()

    def get_analytic_tracking_data(self):
        result = ''
        for cust in self:
            url = cust.instance_url
            db = cust.domain
            username = 'admin'
            password = 'PZmam8rnEXkT5cnC'
            common = xmlrpc.client.ServerProxy(
                '{}/xmlrpc/2/common'.format(url), verbose=False,
                context=ssl._create_unverified_context())
            uid = common.authenticate(db, username, password, {})
            models = xmlrpc.client.ServerProxy(
                '{}/xmlrpc/2/object'.format(url), verbose=False,
                context=ssl._create_unverified_context())
            data = models.execute_kw(db, uid, password,
                                     'analytic.tracking', 'search_read',
                                     [[]],
                                     {'fields': ['name', 'value']})
            result += db + ' '
            for analytic_matrix in data:
                result += analytic_matrix['name'] + ':' + analytic_matrix[
                    'value'] + ','
            result += '\n'
        raise UserError(result)

    def send_verification_email(self):
        template = self.env.ref(
            'pivotino_website.mail_template_subscription_account_verification',
            raise_if_not_found=False)
        for partner in self:
            template.send_mail(partner.id, force_send=True)

    def send_welcome_email(self):
        template = self.env.ref(
            'pivotino_website.mail_template_subscription_welcome',
            raise_if_not_found=False)
        for partner in self:
            template.send_mail(partner.id, force_send=True)
            partner.welcome_sent_count += 1

