{
    'name': 'Database Automated Backup',
    'version': '1.1',
    'summary': 'Automated Database Backup from Server to Server',
    'author': "ONNET SOLUTIONS SDN BHD",
    'description': """A module that allows the user to perform database backup and copy the backup file to a remote server
                     in zip file format.The credentials of remote server will be needed to establish public key connection 
                     to transfer the file. In order to use this module, it is required to install rsync and sshpass. The 
                     command to install rysnc and sshpass.""",
    'website': 'http://www.on.net.my',
    'depends': [
        'base', 'mail'
    ],
    'data': [
        'views/db_auto_backup.xml',
        'security/ir.model.access.csv',
        'data/backup_cron.xml',
    ],
    'installable': True,
    'auto_install': False,
}