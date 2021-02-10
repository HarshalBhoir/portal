from odoo import models, fields, api, _


class PivotinoFeedback(models.Model):
    _name = 'pivotino.feedback'
    _description = 'Pivotino Feedback Data'

    username = fields.Char(string="Username")
    email = fields.Char(string="Email")
    domain = fields.Char(string="Domain")
    feedback = fields.Text(string="Feedback")
    feedback_tag = fields.Text(string="Feedback Tag")
    is_satisfy = fields.Boolean(string='Satisfied', default=False)

    def cron_update_feedback(self, val_list):
        for feedback in val_list:
            vals = {
                'username': feedback['username'],
                'email': feedback['email'],
                'domain': feedback['domain'],
                'feedback': feedback['feedback'],
                'feedback_tag': feedback['tag'],
                'is_satisfy': feedback['is_satisfy'],
            }
            self.create(vals)
        return True
