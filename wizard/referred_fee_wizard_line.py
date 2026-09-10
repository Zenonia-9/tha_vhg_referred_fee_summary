# -*- coding: utf-8 -*-
from odoo import models, fields


class ThaReferredFeeWizardLine(models.TransientModel):
    _name = 'tha.referred.fee.wizard.line'
    _description = 'Referred Fee Wizard Group Line'

    wizard_id = fields.Many2one('tha.referred.fee.wizard', ondelete='cascade')
    group_id = fields.Many2one('tha.referred.mapping.group', string='Group')
    group_name = fields.Char(string='Description')
    amount = fields.Monetary(string='Amount (MMK)', currency_field='currency_id')
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.company.currency_id, readonly=True)