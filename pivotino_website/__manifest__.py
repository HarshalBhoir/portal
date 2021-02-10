{
    'name': 'Pivotino Website',
    'version': '14.0.1.0.0',
    'author': 'Anonymous',
    'category': 'Hidden',
    'description': """
Pivotino Website
================
""",
    'website': 'https://www.pivotino.com/',
    'depends': ['auth_oauth', 'website_crm', 'pivotino_web', 'intl_phone_field'],
    'data': [
        'security/ir.model.access.csv',
        'data/email_template.xml',
        'data/cron.xml',
        'data/subscription_data.xml',
        'data/ir_config_parameter.xml',

        'wizard/upgrade_wizard.xml',
        'wizard/create_instance_wizard.xml',

        'views/templates.xml',
        'views/portal_templates.xml',
        'views/auth_signup_login_templates.xml',
        'views/res_users_views.xml',
        'views/res_partner_views.xml',
        'views/saas_subscription_views.xml',
        'views/rancher_api.xml',
        'views/website_saas_subscription_templates.xml',
        'views/user_management_templates.xml',
        'views/instance.xml',

        'views/pages/footer.xml',
    ],
    'installable': True,
    'auto_install': False,
}
