import uuid

from odoo import api, fields, models, _
from odoo.addons.http_routing.models.ir_http import slug, unslug
from odoo.exceptions import UserError


class SaasSubscription(models.Model):
    _name = 'saas.subscription'
    _inherit = ['website.published.mixin']
    _description = 'SaaS Subscription'
    _order = 'sequence, id'

    sequence = fields.Integer('Sequence',
                              help="Determine the display order",
                              index=True)
    active = fields.Boolean(default=True)
    name = fields.Char(string='Name', required=True,
                       translate=True, copy=False)
    code = fields.Char(string='Code', required=True,
                       copy=False)
    partner_ids = fields.One2many('res.partner', 'subscription_id',
                                  string='Subscribed Companies', copy=False)
    type = fields.Selection([('trial', 'Trial'), ('paid', 'Paid')],
                            string='Subscription Type', default='trial',
                            required=True, copy=False)
    duration = fields.Integer(string='Duration (in days)',
                              required=True, copy=False)
    price = fields.Float(string='Price (USD)', digits='Subscription Price',
                         copy=False)

    _sql_constraints = [
        ('code_uniq', 'unique(code)', "Code is already exists!"),
    ]

    @api.onchange('type')
    def _onchange_type(self):
        if self.type and self.type == 'trial':
            self.price = 0.0

    def _compute_website_url(self):
        super(SaasSubscription, self)._compute_website_url()
        for subscription in self:
            subscription.website_url = "/pivotino/subscription/list"

    def unlink(self):
        for sub_opt in self:
            if sub_opt.partner_ids:
                raise UserError(_("You cannot delete Subscription "
                                  "with active Users."))
        return super(SaasSubscription, self).unlink()


class SaasSubscriptionAddons(models.Model):
    _name = 'saas.subscription.addons'
    _inherit = ['website.published.mixin']
    _description = 'SaaS Subscription Add-ons'
    _order = 'sequence, id'

    sequence = fields.Integer('Sequence',
                              help="Determine the display order",
                              index=True)
    active = fields.Boolean(default=True)
    name = fields.Char(string='Name', required=True,
                       translate=True, copy=False)
    code = fields.Char(string='Code', required=True, copy=False)
    type = fields.Selection([('extension', 'Extension'),
                             ('promotion', 'Promotion')],
                            string='Add-ons Type', default='extension',
                            required=True, copy=False)
    price = fields.Float(string='Price (USD)', digits='Subscription Price',
                         copy=False)
    duration = fields.Integer(string='Duration (in days)', copy=False)
    partner_ids = fields.One2many('res.partner', 'subscription_id',
                                  string='Subscribed Companies', copy=False)

    _sql_constraints = [
        ('code_uniq', 'unique(code)', "Code is already exists!"),
    ]

    @api.onchange('type')
    def _onchange_type(self):
        if self.type and self.type == 'promotion':
            self.price = 0.0
        if self.type and self.type == 'extension':
            self.duration = 0

    def _compute_website_url(self):
        super(SaasSubscriptionAddons, self)._compute_website_url()
        for addons in self:
            addons.website_url = "/pivotino/subscription/addons/list"

    def unlink(self):
        for addon_opt in self:
            if addon_opt.user_ids:
                raise UserError(_("You cannot delete Subscription Add-ons "
                                  "with active Users."))
        return super(SaasSubscriptionAddons, self).unlink()


class SaasSubscriptionHistory(models.Model):
    _name = 'saas.subscription.history'
    _description = 'SaaS Subscription History'
    _order = 'subscription_date desc'

    partner_id = fields.Many2one('res.partner', string='Partner')
    sequence = fields.Integer('Sequence',
                              help="Determine the display order",
                              index=True)
    name = fields.Char(string='Name', readonly=True)
    code = fields.Char(string='Code', readonly=True)
    type = fields.Selection([('trial', 'Trial'), ('paid', 'Paid')],
                            string='Type', readonly=True)
    duration = fields.Integer(string='Duration (in days)', readonly=True)
    price = fields.Float(string='Price (USD)', digits='Subscription Price',
                         readonly=True)
    subscription_date = fields.Date(string='Date', readonly=True)
    validity_date = fields.Date(string='Valid Until', readonly=True)
