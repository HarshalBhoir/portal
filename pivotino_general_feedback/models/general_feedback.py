# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class PositiveGeneralFeedback(models.Model):
    _name = "positive.general.feedback"
    _description = "General Feedbacks"

    username = fields.Char(string="Username")
    email = fields.Char(string="Email")
    domain = fields.Char(string="Domain")
    feedback_value = fields.Text(string="Questions")
    feedback_code = fields.Text(string="Feedback Code")
    selected_questions = fields.Char(string='Selected')
    type = fields.Char(string='Type')

    def update_positive_feedback(self, user_name, email, domain, add_feedback, feedback_tag):
        for tag in feedback_tag:
            code = tag['code']
            tags = self.env['general.feedback.tags'].search([('code', '=', code)], limit=1)
            tag_vals = {
                'username': user_name,
                'email': email,
                'domain': domain,
                'feedback_code': code or '',
                'feedback_value': tags.value or '',
                'selected_questions': tag['answer'],
                'type': 'Positive',
            }
            self.create(tag_vals)

        if add_feedback:
            add_vals = {
                'username': user_name,
                'email': email,
                'domain': domain,
                'additional_feedback': add_feedback,
                'type': 'Positive'
            }
            self.env['additional.general.feedback'].create(add_vals)

        return True

    def cron_update_positive_feedback(self, value_lst):
        for feedback in value_lst:
            tags = self.env['general.feedback.tags'].search(
                [('code', '=', feedback['code'])], limit=1)
            tag_vals = {
                'username': feedback['username'],
                'email': feedback['email'],
                'domain': feedback['domain'],
                'feedback_code': feedback['code'] or '',
                'feedback_value': tags.value or '',
                'selected_questions': feedback['selected'],
                'type': 'Positive',
            }
            self.create(tag_vals)
        return True


class NegativeGeneralFeedback(models.Model):
    _name = "negative.general.feedback"
    _description = "General Feedbacks"

    username = fields.Char(string="Username")
    email = fields.Char(string="Email")
    domain = fields.Char(string="Domain")
    feedback_value = fields.Text(string="Feedback Tag")
    feedback_code = fields.Text(string="Feedback Code")
    selected_questions = fields.Char(string='Selected')
    type = fields.Char(string='Type')

    def update_negative_feedback(self, user_name, email, domain, add_feedback, feedback_tag):
        for tag in feedback_tag:
            code = tag['code']
            tags = self.env['general.feedback.tags'].search(
                [('code', '=', code)], limit=1)
            tag_vals = {
                'username': user_name,
                'email': email,
                'domain': domain,
                'feedback_code': code or '',
                'feedback_value': tags.value or '',
                'selected_questions': tag['answer'],
                'type': 'Negative',
            }
            self.create(tag_vals)

        if add_feedback:
            add_vals = {
                'username': user_name,
                'email': email,
                'domain': domain,
                'additional_feedback': add_feedback,
                'type': 'Negative'
            }
            self.env['additional.general.feedback'].create(add_vals)

        return True

    def cron_update_negative_feedback(self, value_lst):
        for feedback in value_lst:
            tags = self.env['general.feedback.tags'].search(
                [('code', '=', feedback['code'])], limit=1)
            tag_vals = {
                'username': feedback['username'],
                'email': feedback['email'],
                'domain': feedback['domain'],
                'feedback_code': feedback['code'] or '',
                'feedback_value': tags.value or '',
                'selected_questions': feedback['selected'],
                'type': 'Negative',
            }
            self.create(tag_vals)
        return True


class AdditionalGeneralFeedback(models.Model):
    _name = "additional.general.feedback"
    _description = "Additional General Feedbacks"

    username = fields.Char(string="Username")
    email = fields.Char(string="Email")
    domain = fields.Char(string="Domain")
    additional_feedback = fields.Text(string="Additional Feedback")
    type = fields.Char(string="Types")

    def cron_update_additional_feedback(self, value_lst):
        for feedback in value_lst:
            add_vals = {
                'username': feedback['username'],
                'email': feedback['email'],
                'domain': feedback['domain'],
                'additional_feedback': feedback['additional_feedback'],
                'type': feedback['type']
            }
            self.create(add_vals)
        return True
