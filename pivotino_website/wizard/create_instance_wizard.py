from odoo import api, fields, models, _
import json
import requests
import urllib3
import logging
import string
import random
import os
import subprocess
import time
from subprocess import Popen, PIPE

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_logger = logging.getLogger(__name__)


def get_parent_directory(level):
    parent_dir = os.path.dirname(os.path.realpath(__file__))
    result = parent_dir.split(os.sep)[:-level]
    return os.sep.join(result)


class CreateInstanceWizard(models.TransientModel):
    _name = "create.instance.wizard"

    version = fields.Many2one('template.version', readonly=True)
    instance_name = fields.Char(string='Instance Name', readonly=True)
    instance_type = fields.Selection([('template', 'Template Instance'),
                                      ('free', 'Free Instance')],
                                     string='Instance Type')

    @api.model
    def default_get(self, fields):
        res = super(CreateInstanceWizard, self).default_get(fields)
        latest_version = self.env['template.version'].search([('latest', '=', True)])
        res.update({'version': latest_version.id})
        return res

    @api.onchange('instance_type')
    def onchange_instance_type(self):
        instance_seq = int(self.env['ir.config_parameter'].sudo().get_param(
            'pivotino.instance_sequence')) + 1
        if self.instance_type:
            if self.instance_type == 'template':
                prefix = self.version.template_prefix
                self.instance_name = prefix
            else:
                prefix = self.version.instance_prefix
                self.instance_name = prefix + '-' + str(instance_seq)

    def generate_password(self):
        alphanumeric = string.ascii_letters + string.digits
        return ''.join(
            (random.choice(alphanumeric) for i in range(8)))

    def add_dns(self, name):
        dns_php_file = get_parent_directory(2) + '/pivotino_cpanel/dns_api.php'
        try:
            proc = Popen(['php', dns_php_file, name], stdout=PIPE)
            script_response = proc.stdout.read()
            cpanel_response = script_response.decode("utf-8")
            if cpanel_response == '1':
                _logger.info('Added A record--------------------------')
        except Exception:
            pass

    def create_instance(self):
        config = self.env['rancher.api.config'].search(
            [('default', '=', True)])
        db_password = self.generate_password()
        max_db_count = int(self.env['ir.config_parameter'].sudo().get_param(
            'pivotino.max_db_count'))
        instance_seq = int(self.env['ir.config_parameter'].sudo().get_param(
            'pivotino.instance_sequence')) + 1
        latest_version = self.env['template.version'].search(
            [('latest', '=', True)])
        if self.instance_type and self.instance_type == 'template':
            instance_type = 'template'
            prefix = latest_version.template_prefix
            instance_name = prefix
        else:
            instance_type = 'free'
            prefix = latest_version.instance_prefix
            instance_name = prefix + '-' + str(instance_seq)

        self.add_dns(instance_name)

        header = {'Content-Type': 'application/json',
                  'Accept': 'application/json',
                  'Authorization': 'bearer {0}'.format(config.api_token)}
        subdomain = '.pivotino.com'
        url_header = 'https://'

        answers = {
            "domain.name": instance_name + '.pivotino.com',
            "pivotino.pvc_name": config.pvc,
            "odoo.database.host": config.db_host,
            "odoo.clone_template": config.clone_template,
            "odoo.saltpass": db_password,
        }
        namespace = config.namespace
        pgo_namespace = config.pgo_namespace
        service = config.db_service
        clone_template = config.clone_template

        app_data = {
            'externalId': 'catalog://?catalog={cluster}/{catalog_name}&type=clusterCatalog&template={app_name}&version={app_version}'.format(
                cluster=config.cluster_id,
                catalog_name=config.catalog_name,
                app_version=latest_version.name,
                app_name=config.template_app_name if instance_type == 'template' else config.app_name),
            'answers': answers,
            'name': instance_name,
            'projectId': config.cluster_id + ':' + config.project_id,
            'targetNamespace': namespace,
            "wait": True,
            "timeout": 3600
        }
        app_data = json.dumps(app_data)
        app = requests.post(config.app_url, headers=header, data=app_data,
                            verify=False)
        _logger.info(
            "create instance response-----------------------------------<%s>",
            app.content)
        _logger.info('app response code==============================<%s>', app.status_code)
        # if self.instance_type == 'template' and app.status_code == 201:
        #     _logger.info('Running template db script=====================')
        #     template_db_script = get_parent_directory() + "/template_db.sh"
        #     args = ['bash', template_db_script, pgo_namespace, service,
        #             instance_name, template_pwd]
        #     try:
        #         output = subprocess.check_output(args,
        #                                          stderr=subprocess.STDOUT)
        #     except subprocess.CalledProcessError as exc:
        #         _logger.info("Status : FAIL TO MAKE DB INTO TEMPLATE-------<%s>",
        #                      exc)
        #         pass
        if instance_type == 'free' and app.status_code == 201:
            instance = self.env['instance.details'].create({
                'name': instance_name,
                'is_free_instance': True,
                'db_user': instance_name,
                'db_master_password': instance_name + '.' + db_password,
                'instance_state': 'installing',
                'instance_url': url_header + instance_name + subdomain
            })
            self.env['ir.config_parameter'].sudo().set_param('pivotino.instance_sequence', instance_seq)

            time.sleep(10)
            for x in range(max_db_count):
                dns_name = instance_name + '-' + 'db' + str(x+1)
                self.add_dns(dns_name)
                rancher_script = get_parent_directory(1) + "/rancher_script.sh"
                print("script------------------------", rancher_script)
                args = ['bash', rancher_script, pgo_namespace, service,
                        dns_name, clone_template, instance.db_user, namespace]
                print("args-------------------------------", args)
                try:
                    output = subprocess.check_output(args,
                                                     stderr=subprocess.STDOUT)
                except subprocess.CalledProcessError as exc:
                    _logger.info("Status : FAIL TO CREATE DATABASE-------<%s>", exc)
                    pass

                db_record = self.env['database.details'].create({
                    'name': dns_name,
                    'instance_id': instance.id,
                    'db_url': url_header + dns_name + subdomain,
                })

                self.create_ingress(dns_name, subdomain, namespace,
                                    instance.name)

    def create_ingress(self, domain, subdomain, namespace, free_instance):
        config = self.env['rancher.api.config'].search(
            [('default', '=', True)])

        header = {'Content-Type': 'application/json',
                  'Accept': 'application/json',
                  'Authorization': 'bearer {0}'.format(config.api_token)}
        rules = [
            {
                "host": domain + subdomain,
                "paths": [
                    {
                        "path": "/",
                        "serviceId": namespace + ":service-" + free_instance,
                        "targetPort": 80,
                        "type": "/v3/project/schemas/httpIngressPath"
                    },
                    {
                        "path": "/longpolling",
                        "serviceId": namespace + ":service-" + free_instance,
                        "targetPort": 8072,
                        "type": "/v3/project/schemas/httpIngressPath"
                    }],
                "type": "/v3/project/schemas/ingressRule",
            }
        ]

        tls = [
            {
                "certificateId": namespace + ":" + config.ssl_cert,
                "hosts": [
                    domain + subdomain
                ],
                "type": "/v3/project/schemas/ingressTLS",
            }
        ]
        app_data = {
            "defaultBackend": None,
            "name": "ingress-" + domain,
            "namespaceId": namespace,
            "projectId": config.project_id,
            "rules": rules,
            "tls": tls
        }
        app_data = json.dumps(app_data)
        app = requests.post(
            config.ingress_url,
            headers=header, data=app_data,
            verify=False)
        _logger.info('response==============================<%s>', app.content)

    def _cron_create_instance(self):
        db_threshold = int(self.env['ir.config_parameter'].sudo().get_param(
            'pivotino.db_threshold'))

        available_instance = self.env['instance.details'].search([
            ('is_free_instance', '=', True),
            ('db_count', '!=', 0)])

        if len(available_instance) == 1:
            if available_instance[0].db_count <= db_threshold:
                self.create_instance()