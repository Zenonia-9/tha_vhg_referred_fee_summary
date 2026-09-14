# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools import format_date


class ThaReferredFeeWizard(models.TransientModel):
    _name = 'tha.referred.fee.wizard'
    _description = 'Referred Fee Summary Wizard'

    date_from = fields.Date(string='Start Date', readonly=True)
    date_to = fields.Date(string='End Date', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Vendor', readonly=True)
    bill_ids = fields.Many2many('account.move', string='Selected Bills')
    group_line_ids = fields.One2many(
        'tha.referred.fee.wizard.line', 'wizard_id', string='Group Summary')
    unmatched_line_ids = fields.One2many(
        'tha.referred.fee.wizard.unmatched', 'wizard_id', string='Unmatched Bills')

    @api.model_create_multi
    def create(self, vals_list):
        wizards = super().create(vals_list)
        for wizard in wizards:
            if wizard.bill_ids and not wizard.group_line_ids and not wizard.unmatched_line_ids:
                wizard._compute_summary()
        return wizards

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_ids = self.env.context.get('active_ids', [])
        if not active_ids:
            return res

        bills = self.env['account.move'].browse(active_ids)
        if not bills:
            return res

        partners = bills.mapped('partner_id')
        if len(partners) > 1:
            raise UserError(
                'All selected bills must belong to the same vendor. '
                'Found %d different vendors.' % len(partners))

        res['bill_ids'] = [(6, 0, active_ids)]
        res['partner_id'] = partners[0].id if partners else False
        dates = [d for d in bills.mapped('invoice_date') if d]
        res['date_from'] = min(dates) if dates else False
        res['date_to'] = max(dates) if dates else False

        group_vals, unmatched_vals = self._prepare_summary(bills)
        res['group_line_ids'] = [(0, 0, vals) for vals in group_vals]
        res['unmatched_line_ids'] = [(0, 0, vals) for vals in unmatched_vals]
        return res

    def _bill_ref(self, bill):
        return bill.vendor_ref or bill.ref or ''

    def _bill_amount(self, bill):
        """Fee amount as a positive figure (legacy report is unsigned)."""
        amount = bill.amount_total or 0.0
        if bill.move_type == 'in_refund':
            return -amount
        return amount

    # def _parse_vendor_ref(self, vendor_ref):
    #     """Extract the description part from vendor_ref.
    #     Format: 'Referred Fee - Holter ECG  (ECG), 150105 PHYO MYINT, U'
    #     Returns the middle part between 'Referred Fee - ' and the first comma.
    #     """
    #     if not vendor_ref:
    #         return ''
    #     prefix = 'Referred Fee - '
    #     if vendor_ref.startswith(prefix):
    #         remainder = vendor_ref[len(prefix):]
    #     else:
    #         remainder = vendor_ref
    #     comma_idx = remainder.find(',')
    #     if comma_idx > 0:
    #         return remainder[:comma_idx].strip()
    #     return remainder.strip()

    def _parse_vendor_ref(self, vendor_ref):
        """Extract the description part from vendor_ref.

        Expected format:
            Referred Fee - <DESCRIPTION>, <PATIENT ID> <PATIENT NAME>, <TYPE>

        Example:
            Referred Fee - Lumbar Spine (AP,LAT) (X-Ray), 658383 MYINT SOE , U

        Returns:
            Lumbar Spine (AP,LAT) (X-Ray)
        """
        if not vendor_ref:
            return ''

        prefix = 'Referred Fee - '
        if vendor_ref.startswith(prefix):
            remainder = vendor_ref[len(prefix):].strip()
        else:
            remainder = vendor_ref.strip()

        # The patient information starts with a numeric patient ID.
        # Find the comma followed by whitespace + digits.
        import re

        match = re.search(r',\s*\d+\s+', remainder)
        if match:
            return remainder[:match.start()].strip()

        # Fallback: if the expected patient ID pattern is not found,
        # return the whole remaining reference.
        return remainder

    def _match_rule(self, rule, description):
        value = rule.value or ''
        desc = description or ''
        if rule.rule_type == 'exact':
            return desc == value
        if rule.rule_type == 'contains':
            return value.lower() in desc.lower()
        if rule.rule_type == 'starts_with':
            return desc.lower().startswith(value.lower())
        if rule.rule_type == 'ends_with':
            return desc.lower().endswith(value.lower())
        return False

    def _evaluate_group_rules(self, group, description):
        rules = group.rule_ids.sorted('sequence')
        if not rules:
            return False

        result = self._match_rule(rules[0], description)
        for rule in rules[1:]:
            matched = self._match_rule(rule, description)
            if rule.connector == 'and':
                result = result and matched
            else:
                result = result or matched
        return result

    def _prepare_summary(self, bills):
        """Return (group_line_vals, unmatched_vals) without wizard_id."""
        groups = self.env['tha.referred.mapping.group'].search([], order='sequence, id')
        group_amounts = {g.id: 0.0 for g in groups}
        unmatched = []

        for bill in bills:
            description = self._parse_vendor_ref(self._bill_ref(bill))
            amount = self._bill_amount(bill)
            matched = False
            for group in groups:
                if self._evaluate_group_rules(group, description):
                    group_amounts[group.id] += amount
                    matched = True
                    break
            if not matched:
                unmatched.append({
                    'move_id': bill.id,
                    'move_name': bill.name,
                    'partner_id': bill.partner_id.id,
                    'ref': self._bill_ref(bill),
                    'amount': amount,
                })

        group_lines = []
        for group in groups:
            if group_amounts[group.id] != 0.0:
                group_lines.append({
                    'group_id': group.id,
                    'group_name': group.name,
                    'amount': group_amounts[group.id],
                })
        return group_lines, unmatched

    def _compute_summary(self):
        self.ensure_one()
        self.group_line_ids.unlink()
        self.unmatched_line_ids.unlink()
        group_vals, unmatched_vals = self._prepare_summary(self.bill_ids)
        if group_vals:
            self.env['tha.referred.fee.wizard.line'].create([
                dict(vals, wizard_id=self.id) for vals in group_vals
            ])
        if unmatched_vals:
            self.env['tha.referred.fee.wizard.unmatched'].create([
                dict(vals, wizard_id=self.id) for vals in unmatched_vals
            ])

    def _print_now(self):
        return fields.Datetime.context_timestamp(self, fields.Datetime.now())

    def print_time(self):
        return self._print_now().strftime('%H:%M')

    def print_date(self):
        now = self._print_now()
        return '%d/%d/%d' % (now.day, now.month, now.year)

    def print_date_from(self):
        return format_date(self.env, self.date_from, date_format='dd-MMM-yyyy') if self.date_from else ''

    def print_date_to(self):
        return format_date(self.env, self.date_to, date_format='dd-MMM-yyyy') if self.date_to else ''

    def print_subtotal(self):
        return sum(self.group_line_ids.mapped('amount'))

    def action_print_pdf(self):
        self.ensure_one()
        if not self.group_line_ids and self.bill_ids:
            self._compute_summary()
        return self.env.ref(
            'tha_vhg_referred_fee_summary.action_report_referred_fee_pdf'
        ).report_action(self)

    def action_print_excel(self):
        import base64
        from ..report.referred_fee_excel_report import generate_xlsx
        self.ensure_one()
        if not self.group_line_ids and self.bill_ids:
            self._compute_summary()
        content, filename = generate_xlsx(self)
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'datas': base64.b64encode(content),
            'res_model': self._name,
            'res_id': self.id,
            'type': 'binary',
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }
