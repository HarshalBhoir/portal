# -*- coding: utf-8 -*-
# Using in future for cron job
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class GeneralFeedbackTags(models.Model):
    _name = "general.feedback.tags"
    _description = "General Feedbacks Tags"

    value = fields.Char(string='Tag Value')
    type = fields.Selection([('positive', 'Positive'), ('negative', 'Negative')],
        string='Kanban State',)
    assigned = fields.Boolean(string='Currently in Used', copy=False,
                              default=False)
    code = fields.Char(string='Code', copy=False)

    @api.constrains('assigned')
    def _check_number_of_assigned(self):
        if self.search_count(
                [('type', '=', 'positive'), ('assigned', '=', True)]) > 6:
            raise UserError(
                _("You can't have more than six assigned positive tags."))

        if self.search_count(
                [('type', '=', 'negative'), ('assigned', '=', True)]) > 6:
            raise UserError(
                _("You can't have more than six assigned negative tags."))
