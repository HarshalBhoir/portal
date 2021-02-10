from odoo import api, fields, models, _
import os
import subprocess
from openerp.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


def get_parent_directory():
    parent_dir = os.path.dirname(os.path.realpath(__file__))
    result = parent_dir.split(os.sep)[:-1]
    return os.sep.join(result)


class RestorationConfig(models.Model):
    _name = 'backup.server.config'

    name = fields.Char(string="Name")
    dest_ip_address = fields.Char(string="Destination Server IP")
    dest_port_no = fields.Char(string="Destination Port Number")
    dest_username = fields.Char(string="Destination Login Username")
    su_password = fields.Char(string="Destination Superuser Password",
                              help="Kindly provide the superuser password for "
                                   "sudo command.")
    source_zip_path = fields.Char(string="Source Backup Zip File Path")
    dest_zip_path = fields.Char(string="Destination Backup Zip File Path")
    active = fields.Boolean('Active?', default=True)
    state = fields.Selection(
        [('draft', 'Draft Configuration'), ('not_connected', 'Not Connected'),
         ('connected', 'Established Connection')], 'Status', default='draft',
        copy=False)
    expire_days = fields.Char(string='Expire Days')

    def check_connection(self):
        """
        Check the connection to the destination server
        :return:
        """
        check_conn_script_path = get_parent_directory() + "/check_connection.sh"
        args = ['bash', check_conn_script_path, self.dest_ip_address,
                self.dest_port_no, self.dest_username]
        try:
            output = subprocess.check_output(args, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as exc:
            _logger.info(
                "Check Connection------------------------<%s>-----\n<%s>",
                exc.returncode, exc.output)
            self.write({'state': 'not_connected'})
        else:
            self.write({'state': 'connected'})
            _logger.info("Output--------------------------<%s>", output)

    def action_establish_connection(self):
        """
        Establish a public key authentication with the given details and credentials
        :return:
        """
        bash_script = get_parent_directory() + "/key_share.sh"
        args = ['bash', bash_script, self.dest_ip_address, self.dest_port_no,
                self.dest_username, self.su_password]
        try:
            output = subprocess.check_output(args, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as exc:
            _logger.info("Status : FAIL--------------<%s>-----\n<%s>",
                         exc.returncode, exc.output)
            raise UserError(_(
                'Not able to establish connection. Kindly ensure the details are provided correctly.'))
        else:
            _logger.info("Output--------------------------<%s>", output)
            self.write({'state': 'connected'})

    def copy_backup(self):
        """
        Backup zip file using curl command and copy to remote server using rsync command
        """
        users = self.env['res.users'].search([('domain', '!=', False)])
        config = self.search([('active', '=', True)])
        for user in users:
            copy_script = get_parent_directory() + "/copy.sh"
            remove_script = get_parent_directory() + "/remove_old_backup.sh"
            print("script------------------------", copy_script)
            args = ['bash', copy_script, config.dest_ip_address,
                    config.dest_port_no, config.dest_username,
                    config.source_zip_path, config.dest_zip_path, user.domain,
                    user.instance_url, user.db_master_password,
                    config.expire_days, remove_script]
            print("args-------------------------------", args)
            try:
                output = subprocess.check_output(args,
                                                 stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as exc:
                _logger.info("Status : FAIL COPY--------------<%s>-----\n<%s>",
                             exc.returncode, exc.output)
            else:
                _logger.info("Output--------------------------<%s>", output)
