{
    'name': 'Pivotino General Feedback',
    'version': '13.0.1.0.0',
    'author': 'Onnet Consulting Sdn Bhd',
    'category': 'Tools',
    'description': """
Pivotino General Feedback
===========================
""",
    'website': 'https://on.net.my/',
    'depends': [
        'web',
        'pivotino_feedback',
    ],
    'data': [
        'data/feedback_tags_data.xml',
        
        'security/ir.model.access.csv',

        'views/feedback_views.xml',
    ],
    'installable': False,
    'auto_install': False,
    'application': False,
}
