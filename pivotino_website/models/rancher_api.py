from odoo import api, fields, models, _
from odoo.exceptions import UserError


class RancherApiConfig(models.Model):
    _name = 'rancher.api.config'
    _description = "Rancher API Configuration"

    name = fields.Char(string='Description')
    base_url = fields.Char(string='Base URL')
    cluster_id = fields.Char(string='Cluster ID')
    project_id = fields.Char(string='Project ID')
    api_token = fields.Char(string='API Token')
    catalog_name = fields.Char(string='Catalog')
    namespace_url = fields.Char(string='Namespace URL', store=True,
                                compute='compute_url')
    app_url = fields.Char(string='APP URL', store=True, compute='compute_url')
    default = fields.Boolean(string='Default', default=False)
    app_version = fields.Many2one('template.version', string='Version')
    app_name = fields.Char(string="App Name")
    template_app_name = fields.Char(string="Template App Name")
    namespace = fields.Char(string='Namespace')
    staging_namespace = fields.Char(string='Staging Namespace')
    pvc = fields.Char(string='Persistent Volume Claim')
    staging_pvc = fields.Char(string='Staging Persistent Volume Claim')
    db_host = fields.Char(string='Database Host')
    staging_db_host = fields.Char(string='Staging Database Host')
    postgres_user = fields.Char(string='Postgres User')
    staging_postgres_user = fields.Char(string='Staging Postgres User')
    postgres_pass = fields.Char(string='Postgres Password')
    staging_postgres_pass = fields.Char(string='Staging Postgres Password')
    clone_template = fields.Char(string='Clone Template Name', related='app_version.template_prefix', readonly=False)
    staging_clone_template = fields.Char(string='Staging Clone Template Name')
    db_service = fields.Char(string='Database Service Name')
    staging_db_service = fields.Char(string='Staging Database Service Name')
    is_onenet = fields.Boolean(string='Is Onenet?', defalt=False)
    ingress_url = fields.Char(string='Ingress API Endpoint')
    pgo_namespace = fields.Char(string='PGO Namespace')
    staging_pgo_namespace = fields.Char(string='Staging PGO Namespace')
    ssl_cert = fields.Char(string='SSL Cert Name')

    @api.depends('base_url', 'cluster_id', 'project_id')
    def compute_url(self):
        for rec in self:
            if rec.base_url and rec.cluster_id and rec.project_id:
                rec.namespace_url = rec.base_url + 'cluster/{0}/namespaces' \
                    .format(rec.cluster_id)
                rec.app_url = rec.base_url + 'projects/{cluster_id}:{project_id}/apps/' \
                    .format(cluster_id=rec.cluster_id, project_id=rec.project_id)
                rec.ingress_url = rec.base_url + 'project/{cluster_id}:{project_id}/ingresses/' \
                    .format(cluster_id=rec.cluster_id, project_id=rec.project_id)

    @api.constrains('default')
    def check_default(self):
        if self.search_count([('default', '=', True)]) > 1:
            raise UserError(_("You can't have more than one default config."))


class TemplateVersion(models.Model):
    _name = 'template.version'
    _description = "Helm Chart Template Version"

    name = fields.Char("Template Version")
    description = fields.Char("Description")
    instance_prefix = fields.Char("Instance Prefix")
    template_prefix = fields.Char("Template Prefix")
    latest = fields.Boolean('Latest Version?')
