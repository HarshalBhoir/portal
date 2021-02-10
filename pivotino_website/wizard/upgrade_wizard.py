from odoo import api, fields, models, _
import json
import requests
import urllib3
import logging

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_logger = logging.getLogger(__name__)


class UpgradeWizard(models.TransientModel):
    _name = "upgrade.wizard"
    _description = 'Upgrade Wizard'

    user_ids = fields.Many2many('res.users')
    version = fields.Many2one('template.version')

    @api.model
    def default_get(self, fields):
        res = {}
        active_ids = self._context.get('active_ids')
        if active_ids:
            res = {'user_ids': active_ids}
        return res

    def upgrade_instance(self):
        config = self.env['rancher.api.config'].search(
            [('default', '=', True)])
        # is_staging_onenet = self.env[
        #     'ir.config_parameter'].sudo().get_param(
        #     'pivotino.pivotino_staging_onenet', False)
        # if is_staging_onenet:
        #     subdomain = 'onenet.com.my'
        # if is_staging:
        #     answers = {"domain.name": name + '.staging.pivotino.com',
        #                "pivotino.pvc_name": config.staging_pvc,
        #                "odoo.database.host": config.staging_db_host,
        #                "odoo.clone_template": config.staging_clone_template,
        #                }
        #     namespace = config.staging_namespace
        # else:
        #     answers = {"domain.name": name + '.pivotino.com',
        #                "odoo.clone_template": config.clone_template,
        #                }
        header = {'Content-Type': 'application/json',
                  'Accept': 'application/json',
                  'Authorization': 'bearer {0}'.format(config.api_token)}
        # app_data = {
        #     'externalId': 'catalog://?catalog={cluster}/{catalog_name}&type=clusterCatalog&template=pivotino-app&version={app_version}u'.format(
        #         cluster=config.cluster_id, catalog_name=config.catalog_name,
        #         app_version=self.version.name),
        #     'answers': {
        #         "odoo.image_name": 'pivotino/pivotino:{app_version}'.format(
        #             app_version=self.version.name),
        #         }}
        # app_data = json.dumps(app_data)
        for instance in self.user_ids:
            if instance.is_staging:
                answers = {
                    "domain.name": instance.domain + '.pivotino.com',
                    "odoo.image_name": 'pivotino/pivotino:v{app_version}'.format(
                        app_version=self.version.name),
                    "pivotino.pvc_name": config.staging_pvc,
                    "odoo.database.host": config.staging_db_host,
                }
            elif config.is_onenet:
                answers = {"domain.name": instance.domain + '.onenet.com.my',
                           "odoo.image_name": 'onnetdocker20/pivotino:{app_version}'.format(
                               app_version=self.version.name),
                           "letsencrypt.enable": 'false'}
            else:
                answers = {"domain.name": instance.domain + '.pivotino.com',
                           "odoo.image_name": 'pivotino/pivotino:v{app_version}'.format(
                               app_version=self.version.name), }

            app_data = {
                'externalId': 'catalog://?catalog={cluster}/{catalog_name}&type=clusterCatalog&template={app_name}&version={app_version}u'.format(
                    cluster=config.cluster_id,
                    catalog_name=config.catalog_name,
                    app_version=self.version.name,
                    app_name=config.app_name),
                'answers': answers,
            }
            app_data = json.dumps(app_data)
            app = requests.post(
                config.app_url + config.project_id + ':' + instance.domain + '?action=upgrade',
                headers=header, data=app_data,
                verify=False)
            _logger.info(
                "upgrade response-----------------------------------<%s>",
                app.content)
