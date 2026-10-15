# -*- coding: utf-8 -*-
from odoo import models
from odoo.exceptions import UserError
from calendar import monthrange


def _month_bounds(dates):
    dates = [date for date in dates if date]
    if not dates:
        return False, False
    first = min(dates).replace(day=1)
    last_month = max(dates)
    last = last_month.replace(day=monthrange(last_month.year, last_month.month)[1])
    return first, last


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_open_referred_fee_summary(self):
        """Create the wizard so Group Summary / Unmatched are populated on open."""
        bills = self.filtered(lambda m: m.move_type in (
            'in_invoice', 'in_refund', 'in_receipt'))
        if not bills:
            raise UserError('Select at least one vendor bill.')

        partners = bills.mapped('partner_id')
        if len(partners) > 1:
            raise UserError(
                'All selected bills must belong to the same vendor. '
                'Found %d different vendors.' % len(partners))

        date_from, date_to = _month_bounds(bills.mapped('invoice_date'))
        wizard = self.env['tha.referred.fee.wizard'].create({
            'bill_ids': [(6, 0, bills.ids)],
            'partner_id': partners[:1].id if partners else False,
            'date_from': date_from,
            'date_to': date_to,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Referred Fee Summary',
            'res_model': 'tha.referred.fee.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }
