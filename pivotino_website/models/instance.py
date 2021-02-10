from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
import requests
import json
import pycountry
import urllib3
import xmlrpc.client
import ssl
import time
import os
from subprocess import Popen, PIPE

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_logger = logging.getLogger(__name__)

def get_parent_directory(level):
    parent_dir = os.path.dirname(os.path.realpath(__file__))
    result = parent_dir.split(os.sep)[:-level]
    return os.sep.join(result)

class InstanceDetails(models.Model):
    _name = 'instance.details'
    _description = "Instance Detail Info"

    name = fields.Char('Instance Name')
    db_count = fields.Integer('Database Available', compute="_compute_db_count", store=True)
    is_free_instance = fields.Boolean('Free Instance?', default=False)
    db_user = fields.Char('Database User')
    db_master_password = fields.Char(string='DB Master Password', readonly=True)
    db_ids = fields.One2many('database.details', 'instance_id', 'Databases')
    instance_state = fields.Selection([
        ('installing', 'Installing'),
        ('deploying', 'Deploying'),
        ('active', 'Active'),
        ('unavailable', 'Unavailable'),
    ], default='installing', string='Instance State')
    instance_url = fields.Char('Instance URL')

    @api.depends('db_ids', 'db_ids.partner_id')
    def _compute_db_count(self):
        for rec in self:
            db_ids = rec.db_ids.filtered(lambda x: not x.partner_id)
            rec.db_count = len(db_ids)

    @api.model
    def _cron_get_instance_state(self):
        instances = self.search([('instance_state', 'not in', ['active'])])
        while self.search_count([('instance_state', 'not in', ['active'])]) > 0:
            for instance in instances:
                instance.get_instance_state()
                time.sleep(5)
        return True

    def get_instance_state(self):
        config = self.env['rancher.api.config'].search(
            [('default', '=', True)])
        for instance in self:
            url = config.base_url + \
                  'project/{cluster_id}:{project_id}/apps/{project_id}:{domain}' \
                      .format(cluster_id=config.cluster_id,
                              project_id=config.project_id,
                              domain=instance.name)
            header = {'Content-Type': 'application/json',
                      'Accept': 'application/json',
                      'Authorization': 'bearer {0}'.format(
                          config.api_token)}
            response = requests.get(url, headers=header, verify=False)
            content_dict = json.loads(response.content)
            state = content_dict.get('state')
            _logger.info('instance state----------------------------<%s>, <%s>',
                         state, instance.name)
            if instance.instance_state != state:
                instance.write({'instance_state': state})
        return True

    def delete_instance(self):
        config = self.env['rancher.api.config'].search(
            [('default', '=', True)])
        header = {'Content-Type': 'application/json',
                  'Accept': 'application/json',
                  'Authorization': 'bearer {0}'.format(config.api_token)}
        for instance in self:
            app = requests.delete(
                config.app_url + config.project_id + ':' + instance.domain,
                headers=header, verify=False)


class DatabaseDetails(models.Model):
    _name = 'database.details'
    _description = "Database Detail Info"

    name = fields.Char('Database Name')
    instance_id = fields.Many2one('instance.details', 'Instance')
    db_url = fields.Char('Instance URL(DB)')
    partner_id = fields.Many2one('res.partner', 'Partner')

    def preconfigure(self):
        config = self.env['rancher.api.config'].search(
            [('default', '=', True)])
        for database in self:
            url = database.db_url
            db = database.name
            username = 'admin'
            if config.is_onenet:
                password = 'admin'
            else:
                password = 'PZmam8rnEXkT5cnC'
            db_main_user = database.partner_id.main_saas_user
            common = xmlrpc.client.ServerProxy(
                '{}/xmlrpc/2/common'.format(url), verbose=False,
                context=ssl._create_unverified_context())
            country_id = db_main_user.country_id
            if not country_id:
                country_id = self.env.ref('base.my')

            _logger.info('country_id----------------------------<%s>',
                         country_id.name)

            user_country = country_id.name
            name = 'l10n_'
            if user_country:
                country = pycountry.countries.search_fuzzy(
                    user_country)
                for x in country:
                    if x.alpha_2:
                        name += x.alpha_2.lower()
                    else:
                        name = 'l10n_generic_coa'

            _logger.info('name-----------------------------------<%s>',
                         name)

            currency_id = country_id.currency_id

            _logger.info(
                'currency_id------------------------------<%s>',
                currency_id)

            user = database.name
            cpanel_response = ''
            cpanel_api_php = get_parent_directory(2) + '/pivotino_cpanel/cpanel_api.php'
            try:
                proc = Popen(['php', cpanel_api_php, user], stdout=PIPE)
                script_response = proc.stdout.read()
                cpanel_response = script_response.decode("utf-8")
                if cpanel_response == '1':
                    db_main_user.email_creation = True
            except Exception:
                pass
            uid = False
            while not uid:
                uid = common.authenticate(db, username, password, {})
            models = xmlrpc.client.ServerProxy(
                '{}/xmlrpc/2/object'.format(url), verbose=False,
                context=ssl._create_unverified_context())
            company_id = models.execute_kw(db, uid, password,
                                           'res.company', 'search',
                                           [[]], {'limit': 1})

            _logger.info(
                'search company done--------------------------')

            instance_user_id = models.execute_kw(db, uid, password, 'res.users',
                                              'create',
                                              [{
                                                  'name': db_main_user.name,
                                                  'login': db_main_user.email,
                                                  'email': db_main_user.email,
                                                  # 'login_date_1': False,
                                                  # 'user_role': 'owner',
                                                  'tz': db_main_user.tz,
                                                  'main_user': True,
                                                  'cust_email_creation': db_main_user.email_creation,
                                              }])

            _logger.info(
                'create res user done------------------------')

            user_id = db_main_user.user_ids.ids[0]

            self.env.cr.execute(
                'select password, internal_password from res_users where id=%s',
                (user_id,))
            result = self.env.cr.fetchone()
            models.execute_kw(db, uid, password, 'res.users',
                              'api_set_password', [result, instance_user_id])

            _logger.info(
                'set user password done------------------------')
            # models.execute_kw(db, uid, password, 'res.users', 'write',
            #                   [uid, {
            #                       'login_date_1': False,
            #                       'first_log_bool': False,
            #                   }])
            #
            # _logger.info(
            #     'change first login---------------------------')

            # unlink sale target if there is any
            sale_target_ids = models.execute_kw(db, uid, password,
                                                'sale.target',
                                                'search', [[]])

            _logger.info('search sale target--------------------')

            if len(sale_target_ids) > 0:
                for target_id in sale_target_ids:
                    models.execute_kw(db, uid, password, 'sale.target',
                                      'unlink', [[target_id]])

            _logger.info('delete sale target-------------------')

            if cpanel_response == '1':
                models.execute_kw(db, uid, password, 'ir.mail_server',
                                  'create',
                                  [{
                                      'name': 'Outgoing Mail',
                                      'smtp_host': 'customer.pivotino.com',
                                      'smtp_encryption': 'starttls',
                                      'smtp_port': 587,
                                      'smtp_user': user + '@customer.pivotino.com',
                                      'smtp_pass': 'gE1(Re@t|Ve',
                                  }])

            _logger.info(
                'create email------------------------------------')

            models.execute_kw(db, uid, password, 'res.users',
                              'install_l10n_coa_module',
                              [name])

            _logger.info(
                'install module----------------------------------')

            models.execute_kw(db, uid, password, 'res.company',
                              'write',
                              [company_id, {
                                  'name': db_main_user.parent_id.name,
                                  'currency_id': currency_id.id,
                                  'email': db_main_user.email
                              }])

            _logger.info(
                'change company-----------------------------------')

            # TODO: Temporary on hold
            # models.execute_kw(db, uid, password, 'res.users',
            #                   'insert_preconfigured_data_from_provision',
            #                   [uid, database.name, database.db_url])
            #
            # _logger.info(
            #     'call preconfigured data function-----------------------------------')
