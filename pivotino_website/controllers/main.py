import logging
import requests
import urllib3
import json
import random
import string
import re
import werkzeug
import werkzeug.exceptions
import werkzeug.utils
from datetime import timedelta
from odoo import fields, http, _
from odoo.addons.pivotino_website.models.res_users import SubscriptionError
from odoo.addons.web.controllers.main import ensure_db, Home
from odoo.exceptions import UserError
from odoo.http import request

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_logger = logging.getLogger(__name__)


class PivotinoHome(Home):

    # Code needs inside Pivotino Instance(s)
    # --------------------------------------
    # @http.route('/web/pivotino/invoke-session', type='http', auth="none")
    # def web_client_share_session(self, **kw):
    #     if kw.get('pivotino_share_session') and kw['pivotino_share_session'] == '1' and \
    #             kw.get('login') and kw.get('password'):
    #         login = kw['login']
    #         password = kw['password']
    #         pivotino_portal_uid = int(kw['portal_id'])
    #
    #         uid = request.session.authenticate(request.session.db, login, password)
    #         request.params['login_success'] = True
    #
    #         user = request.env['res.users'].sudo().browse(uid)
    #         user.pivotino_portal_uid = pivotino_portal_uid
    #         return werkzeug.utils.redirect('/web')
    #     else:
    #         return werkzeug.utils.redirect('https://pivotino.com')

    # Code needs inside Pivotino Portal
    # ---------------------------------
    @http.route('/web/pivotino/invoke-session', type='http', auth="none")
    def web_client_share_session(self, **kw):
        if kw.get('pivotino_share_session') and kw['pivotino_share_session'] == '1' and \
                kw.get('login') and kw.get('password'):
            login = kw['login']
            password = kw['password']

            uid = request.session.authenticate(request.session.db, login, password)
            request.params['login_success'] = True
            # Redirect to user management from user instance
            return werkzeug.utils.redirect('/my/user')
        else:
            return werkzeug.utils.redirect('https://pivotino.com')

    @http.route()
    def web_login(self, *args, **kw):
        ensure_db()
        response = super(PivotinoHome, self).web_login(*args, **kw)
        if request.params['login_success']:
            user = request.env['res.users'].sudo().browse(request.session.uid)
            if user.partner_id and user.partner_id.parent_id and user.partner_id.parent_id.subscription_company:
                subscription_company = user.partner_id.parent_id
                instance_url = subscription_company.instance_url
                instance_auth_url = instance_url + '/web/session/authenticate'
                instance_share_session_url = instance_url + '/web/pivotino/invoke-session'
                instance_db = subscription_company.database_id.name

                data = {
                    'jsonrpc': '2.0',
                    'params': {
                        'context': {},
                        'db': instance_db,
                        'login': request.params['login'],
                        'password': request.params['password'],
                    },
                }
                headers = {
                    'Content-type': 'application/json'
                }

                auth = requests.post(instance_auth_url, data=json.dumps(data), headers=headers)
                if auth.status_code != 200:
                    return http.local_redirect('/web/')

                auth_content = auth.content.decode("UTF-8")
                auth_content_json = json.loads(auth_content)
                pivotino_instance_uid = auth_content_json['result']['uid']

                redirect_url = instance_share_session_url + '?pivotino_share_session=1&uid=' + str(
                    pivotino_instance_uid) + '&login=' + request.params['login'] + \
                    '&password=' + request.params['password'] + '&portal_id=' + str(user.id)
                return werkzeug.utils.redirect(redirect_url)
        return response


class AuthSubscriptionPivotino(http.Controller):

    # @http.route('/pivotino/auto-suggest-domain', type='json',
    #             auth='public', website=True, sitemap=False)
    # def auto_suggest_domain(self, company=False):
    #     auto_suggestion = ''
    #     if company:
    #         # Make it lower-case & replace the blank space with hyphen
    #         company = company.replace(' ', '-').lower()
    #         company_len = len(company)
    #
    #         if company_len < 3:
    #             auto_suggestion = company + str(random.randint(111, 999))
    #         elif company_len > 15:
    #             company_lst = company.split('-')
    #             if len(company_lst[0]) < 3:
    #                 auto_suggestion = company_lst[0] + \
    #                                   str(random.randint(111, 999))
    #             elif len(company_lst[0]) > 11:
    #                 auto_suggestion = company_lst[0][:7]
    #             else:
    #                 auto_suggestion = company_lst[0]
    #         else:
    #             auto_suggestion = company
    #     if request.env["res.users"].sudo().search([("domain", "=",
    #                                                 auto_suggestion)]):
    #         if len(auto_suggestion) > 11:
    #             auto_suggestion = auto_suggestion[:7]
    #         auto_suggestion = auto_suggestion + str(random.randint(111, 999))
    #     return auto_suggestion
    def list_providers(self):
        try:
            providers = request.env['auth.oauth.provider'].sudo().search_read([('enabled', '=', True)])
        except Exception:
            providers = []
        for provider in providers:
            return_url = request.httprequest.url_root + 'auth_oauth/signin'
            state = self.get_state(provider)
            params = dict(
                response_type='token',
                client_id=provider['client_id'],
                redirect_uri=return_url,
                scope=provider['scope'],
                state=json.dumps(state),
            )
            provider['auth_link'] = "%s?%s" % (provider['auth_endpoint'], werkzeug.urls.url_encode(params))
        return providers

    def get_state(self, provider):
        redirect = request.params.get('redirect') or 'web'
        if not redirect.startswith(('//', 'http://', 'https://')):
            redirect = '%s%s' % (request.httprequest.url_root, redirect[1:] if redirect[0] == '/' else redirect)
        state = dict(
            d=request.session.db,
            p=provider['id'],
            r=werkzeug.urls.url_quote_plus(redirect),
        )
        token = request.params.get('token')
        if token:
            state['t'] = token
        return state


    @http.route('/pivotino/subscription/verify', type='http',
                auth='public', website=True, sitemap=False)
    def web_email_verification_success(self, *args, **kw):
        param = request.params.copy()
        user_token = param.get('token')
        UserDummy = request.env['res.users.dummy']
        user_sudo = UserDummy.sudo().search([
            ('subscription_token', '=', user_token)
        ], limit=1)
        # check if user already verified their email
        if not user_sudo.active:
            return request.render(
                'pivotino_website.email_verification_success')
        config = request.env['rancher.api.config'].search(
            [('default', '=', True)])
        if not config:
            raise UserError(_("No API config found! Please configure one!"))

        User = request.env['res.users']
        user = User.sudo().create({
            'name': user_sudo.name,
            'login': user_sudo.email,
            'email': user_sudo.email,
            'groups_id': [(6, 0, [request.env.ref('base.group_portal').id])],
            'dummy_user_id': user_sudo.id,
        })
        request.env.cr.execute('select password, internal_password from res_users_dummy where id=%s',
                            (user_sudo.id,))
        result = request.env.cr.fetchone()
        request.env.cr.execute(
            'UPDATE res_users SET password=%s, internal_password=%s WHERE id=%s',
            (result[0], result[1], user.id)
        )

        # Get the duration from Subscription
        duration_days = 0
        if user_sudo.subscription_id:
            duration_days = user_sudo.subscription_id.duration

        # Create the Subscription Company (res.partner)
        subscription_company = request.env['res.partner'].sudo().create({
            'name': user_sudo.company,
            'company_type': 'company',
            'subscription_company': True,
            'subscription_start_date': fields.Date.today(),
            'subscription_end_date':
                fields.Date.today() + timedelta(days=+duration_days),
            'is_staging': user_sudo.is_staging,
            'subscription_id':
                user_sudo.subscription_id and user_sudo.subscription_id.id,
            'subscription_token': user_token,
        })

        # Assign the company to related partner field
        user.partner_id.write({
            'name': user_sudo.name,
            'email': user_sudo.email,
            'phone': user_sudo.pivo_phone,
            'company_type': 'person',
            'parent_id': subscription_company.id,
            'ip_address': user_sudo.ip_address,
            'country_id': user_sudo.country_id and user_sudo.country_id.id,
            'tz': user_sudo.tz,
        })

        available_instance = request.env['instance.details'].search([
            ('is_free_instance', '=', True),
            ('db_count', '!=', 0)], order="id asc")[0]

        if available_instance:
            reserve_db = request.env['database.details'].search([
                ('instance_id', '=', available_instance.id),
                ('partner_id', '=', False)], order="id asc")[0]
            reserve_db.partner_id = subscription_company.id
            subscription_company.instance_url = reserve_db.db_url
            subscription_company.database_id = reserve_db.id
            subscription_company.instance_id = available_instance.id
        else:
            raise UserError('No more available instance, '
                            'please wait a moment while we create '
                            'more free instance')

        # Assign Main SaaS User under Company Profile
        subscription_company.main_saas_user = user.partner_id.id

        # Mark the User (New Subscription) as Archive,
        # as this user already converted as Real User
        user_sudo.active = False

        # Call preconfigure function to preconfigure client db
        reserve_db.preconfigure()

        subscription_company.send_welcome_email()

        return request.render(
            'pivotino_website.email_verification_success')

    @http.route('/pivotino/subscription/thankyou', type='http',
                auth='public', website=True, sitemap=False)
    def web_auth_subscription_success(self, qcontext=None, *args, **kw):

        if not qcontext:
            return request.redirect('/pivotino/subscription/get-started')
        return request.render(
            'pivotino_website.auth_subscription_success', qcontext)

    @http.route('/pivotino/subscription/resend', type='json',
                auth='public', website=True, sitemap=False)
    def web_auth_subscription_resend(self, qcontext=None, *args, **kw):
        qcontext = request.params.copy()
        UserDummy = request.env['res.users.dummy']
        user_sudo = UserDummy.sudo().search([
            ('email', '=', qcontext.get('email')),
            ('subscription_token', '=', qcontext.get('subscription_token'))
        ], limit=1)
        template = request.env.ref(
            'pivotino_website.'
            'mail_template_subscription_account_verification',
            raise_if_not_found=False)
        if user_sudo and template:
            template.sudo().with_context(
                auth_verification=werkzeug.url_encode(
                    {'auth_verification':
                         user_sudo.subscription_token}),
            ).send_mail(user_sudo.id, force_send=True)
            return True
        return False

    @http.route('/pivotino/subscription/get-started', type='http',
                auth='public', website=True, sitemap=False)
    def web_auth_subscription(self, *args, **kw):
        qcontext = request.params.copy()
        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                self.do_subscribe_pivotino(qcontext)
                # Send an email verification link through email
                if qcontext.get('subscription_token'):
                    subscription_token = qcontext.get('subscription_token')
                    email = qcontext.get('email')
                    UserDummy = request.env['res.users.dummy']
                    user_sudo = UserDummy.sudo().search([
                        ('email', '=', email),
                        ('subscription_token', '=', subscription_token)
                    ], limit=1)
                    template = request.env.ref(
                        'pivotino_website.'
                        'mail_template_subscription_account_verification',
                        raise_if_not_found=False)
                    if user_sudo and template:
                        template.sudo().with_context(
                            auth_verification=werkzeug.url_encode(
                                {'auth_verification':
                                     user_sudo.subscription_token}),
                        ).send_mail(user_sudo.id, force_send=True)
                return self.web_auth_subscription_success(qcontext,
                                                          *args, **kw)
            except UserError as e:
                qcontext['error'] = e.name or e.value

        # Get all active & published Subscription
        subscription_opts = request.env['saas.subscription'].sudo().search([
            ('active', '=', True), ('is_published', '=', True)],
            order='sequence')
        providers = self.list_providers()
        qcontext.update({
            'subscription_opts': subscription_opts,
            'providers': providers
        })

        response = request.render('pivotino_website.auth_subscription',
                                  qcontext)
        response.headers['X-Frame-Options'] = 'DENY'

        return response

    @http.route('/pivotino/subscription/list',
                type='http', auth="user", website=True)
    def subscription_list(self, **kwargs):
        subscription_obj = request.env['saas.subscription']
        subscriptions = subscription_obj.sudo().search([], order='sequence')

        return request.render("pivotino_website.subscription_list", {
            'subscriptions': subscriptions,
        })

    @http.route('/pivotino/subscription/addons/list',
                type='http', auth="user", website=True)
    def subscription_addons_list(self, **kwargs):
        subscription_addons_obj = request.env['saas.subscription.addons']
        addons = subscription_addons_obj.sudo().search([], order='sequence')

        return request.render("pivotino_website.subscription_addons_list", {
            'addons': addons,
        })

    @http.route('/my/subscriptions', type='http',
                auth="user", website=True)
    def portal_my_subscriptions(self, **kw):
        user = request.env.user

        values = {
            'default_url': '/my/subscriptions',
            'page_name': 'pivo_subscription',
            'breadcrumb_name': 'Subscriptions',
            'user': user,
            'subscription': user and user.subscription_id,
            'start_date': user and user.subscription_start_date,
            'end_date': user and user.subscription_end_date,
            'instance_url': user and user.instance_url,
            'addon_ids': user and user.addon_ids,
            'subscription_history_ids': user and user.subscription_history_ids,
        }
        return request.render("pivotino_website.portal_my_subscriptions",
                              values)

    @http.route('/my/user', type='http',
                auth="user", website=True)
    def portal_my_user_management(self, **kw):
        user = request.env.user
        parent_company = request.env['res.partner'].search([('main_saas_user', '=', user.partner_id.id), ('subscription_company', '=', True)])
        active_users = request.env['res.partner'].search([('parent_id', '=', parent_company.id), ('active', '=', True), ('res_user_state', 'in', ('Pending', 'Active'))])

        values = {
            'default_url': '/my/user',
            'page_name': 'pivo_user_management',
            'breadcrumb_name': 'Manage Users',
            'user': user,
            'subscription': user and user.subscription_id,
            'active_users': active_users,
            'start_date': user and user.subscription_start_date,
            'end_date': user and user.subscription_end_date,
            'instance_url': user and user.instance_url,
            'addon_ids': user and user.addon_ids,
            'subscription_history_ids': user and user.subscription_history_ids,
        }
        return request.render("pivotino_website.portal_my_user_management",
                              values)

    def do_subscribe_pivotino(self, qcontext):
        values = {key: qcontext.get(key) for key in
                  ('subscription_id', 'first_name', 'last_name', 'email',
                   'pivo_phone', 'company', 'is_staging', 'password')}
        values['name'] = values.get('first_name') + '' + values.get('last_name')
        del values['first_name']
        del values['last_name']
        _logger.info('is_staging-------------------------------<%s>',
                     values['is_staging'])
        if not values:
            raise UserError(_("The form was not properly filled in."))
        if qcontext.get("email", False):
            domain = re.search("@yahoo", qcontext['email'])
            if domain:
                raise UserError(_("Currently, Pivotino is not support "
                                  "Yahoo email.\n"
                                  "Please, use another email address."))
        if request.env["res.users"].sudo().search([("login", "=",
                                                    qcontext.get("email"))]):
            raise UserError(_("Another user is already registered "
                              "using this email address."))

        # Add the IP & Country info inside `qcontext`
        ip_address = request.httprequest.remote_addr
        if ip_address:
            values['ip_address'] = ip_address

        country_code = request.session.geoip and request.session.geoip.get(
            'country_code') or False
        if country_code:
            country = request.env['res.country'].sudo().search(
                [('code', '=', country_code)], limit=1)
            if country:
                values['country_id'] = country.id

        # add tz code inside `qcontext`
        tz_code = request.env.context.get('tz') or False
        if tz_code:
            values['tz'] = tz_code

        subscription_token = self._subscribe_with_values(values)
        qcontext['subscription_token'] = subscription_token
        request.env.cr.commit()

    def _subscribe_with_values(self, values):
        subscription_token = request.env['res.users.dummy']. \
            sudo().subscription(values)
        request.env.cr.commit()  # need to commit the current transaction
        if not subscription_token:
            raise SubscriptionError(_('Subscription Failed.'))
        return subscription_token

    # def instance_provision(self, name, is_staging, db_password, namespace, clone_template):
    #     # Create dns record
    #     # cpanel_response = ''
    #     config = request.env['rancher.api.config'].search(
    #         [('default', '=', True)])
    #     if not config:
    #         raise UserError(_("No API config found! Please configure one!"))
    #     if is_staging:
    #         answers = {"domain.name": name + '.pivotino.com',
    #                    "pivotino.pvc_name": config.staging_pvc,
    #                    "odoo.database.host": config.staging_db_host,
    #                    "odoo.clone_template": clone_template,
    #                    "odoo.saltpass": db_password,
    #                    }
    #     elif config.is_onenet:
    #         answers = {"domain.name": 'onenet.com.my---xip.io',
    #                    "letsencrypt.enable": 'false',
    #                    "odoo.saltpass": db_password,
    #                    "odoo.clone_template": clone_template,
    #                    }
    #     else:
    #         answers = {"domain.name": name + '.pivotino.com',
    #                    "odoo.clone_template": clone_template,
    #                    "odoo.saltpass": db_password,
    #                    }
    #
    #     header = {'Content-Type': 'application/json',
    #               'Accept': 'application/json',
    #               'Authorization': 'bearer {0}'.format(config.api_token)}
    #     app_data = {
    #         'externalId': 'catalog://?catalog={cluster}/{catalog}&type=''clusterCatalog&template={app_name}&version={app_version}'.format(
    #             cluster=config.cluster_id, catalog=config.catalog_name,
    #             app_version=config.app_version, app_name=config.app_name),
    #         'name': name,
    #         'projectId': config.cluster_id + ':' + config.project_id,
    #         'targetNamespace': namespace,
    #         'answers': answers,
    #         "wait": True,
    #         "timeout": 3600}
    #     app_data = json.dumps(app_data)
    #     app = requests.post(config.app_url, headers=header, data=app_data,
    #                         verify=False)
    #     _logger.info("app response---------------------------------<%s>",
    #                  app.content)

    def generate_password(self):
        alphanumeric = string.ascii_letters + string.digits
        return ''.join(
            (random.choice(alphanumeric) for i in range(8)))
