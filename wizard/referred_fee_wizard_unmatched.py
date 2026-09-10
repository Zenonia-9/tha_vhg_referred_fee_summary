# -*- coding: utf-8 -*-
from odoo import models, fields


class ThaReferredFeeWizardUnmatched(models.TransientModel):
    _name = 'tha.referred.fee.wizard.unmatched'
    _description = 'Referred Fee Wizard Unmatched Bill'

    wizard_id = fields.Many2one('tha.referred.fee.wizard', ondelete='cascade')
    move_id = fields.Many2one('account.move', string='Bill')
    move_name = fields.Char(string='Number')
    partner_id = fields.Many2one('res.partner', string='Vendor')
    ref = fields.Char(string='Reference')
    amount = fields.Monetary(string='Amount (MMK)', currency_field='currency_id')
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.company.currency_id, readonly=True)