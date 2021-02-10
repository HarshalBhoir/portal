from odoo import api, fields, models, _
import json
import requests
import urllib3
import logging
from subprocess import Popen, PIPE

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_logger = logging.getLogger(__name__)


class TemplateInstanceWizard(models.TransientModel):
    _name = "template.instance.wizard"
    _description = "Template Instance Wizard"

    version = fields.Many2one('template.version')
    is_staging = fields.Boolean(string='Is Staging?', default=False)
    instance_name = fields.Char(string='Instance Name')

    def create_instance(self):
        config = self.env['rancher.api.config'].search(
            [('default', '=', True)])
        try:
            proc = Popen(['php',
                          '/opt/pivotino/SaaS-Web-Portal/pivotino_cpanel/dns_api.php',
                          self.instance_name], stdout=PIPE)
            script_response = proc.stdout.read()
            cpanel_response = script_response.decode("utf-8")
            if cpanel_response == '1':
                _logger.info('Added A record--------------------------')
        except Exception:
            pass
        header = {'Content-Type': 'application/json',
                  'Accept': 'application/json',
                  'Authorization': 'bearer {0}'.format(config.api_token)}
        if self.is_staging:
            answers = {
                "domain.name": self.instance_name + '.pivotino.com',
                "pivotino.pvc_name": config.staging_pvc,
                "odoo.database.host": config.staging_db_host,
            }
            namespace = config.staging_namespace
        else:
            answers = {"domain.name": self.instance_name + '.pivotino.com'}
            namespace = config.namespace

        app_data = {
            'externalId': 'catalog://?catalog={cluster}/{catalog_name}&type=clusterCatalog&template={app_name}&version={app_version}'.format(
                cluster=config.cluster_id,
                catalog_name=config.catalog_name,
                app_version=self.version.name,
                app_name=config.template_app_name),
            'answers': answers,
            'name': self.instance_name,
            'projectId': config.cluster_id + ':' + config.project_id,
            'targetNamespace': namespace,
            "wait": True,
            "timeout": 3600
        }
        app_data = json.dumps(app_data)
        app = requests.post(config.app_url, headers=header, data=app_data,
                            verify=False)
        _logger.info(
            "create template instance response-----------------------------------<%s>",
            app.content)
