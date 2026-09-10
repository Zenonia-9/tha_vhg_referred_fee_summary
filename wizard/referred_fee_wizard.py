# -*- coding: utf-8 -*-
import re
from odoo import models, fields, api
from odoo.exceptions import UserError


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

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_ids = self.env.context.get('active_ids', [])
        if not active_ids:
            return res

        bills = self.env['account.move'].browse(active_ids)
        if not bills:
            return res

        # Validate same vendor
        partners = bills.mapped('partner_id')
        if len(partners) > 1:
            raise UserError(
                'All selected bills must belong to the same vendor. '
                'Found %d different vendors.' % len(partners))

        res['bill_ids'] = [(6, 0, active_ids)]
        res['partner_id'] = partners[0].id if partners else False
        res['date_from'] = min(bills.mapped('invoice_date')) if bills.mapped('invoice_date') else False
        res['date_to'] = max(bills.mapped('invoice_date')) if bills.mapped('invoice_date') else False

        return res

    def _parse_vendor_ref(self, vendor_ref):
        """Extract the description part from vendor_ref.
        Format: 'Referred Fee - Holter ECG  (ECG), 150105 PHYO MYINT, U'
        Returns the middle part between 'Referred Fee - ' and the first comma.
        """
        if not vendor_ref:
            return ''
        prefix = 'Referred Fee - '
        if vendor_ref.startswith(prefix):
            remainder = vendor_ref[len(prefix):]
        else:
            remainder = vendor_ref
        # Take everything before the first comma
        comma_idx = remainder.find(',')
        if comma_idx > 0:
            return remainder[:comma_idx].strip()
        return remainder.strip()

    def _match_rule(self, rule, description):
        """Check if a single rule matches the description."""
        value = rule.value or ''
        desc = description or ''
        if rule.rule_type == 'exact':
            return desc == value
        elif rule.rule_type == 'contains':
            return value.lower() in desc.lower()
        elif rule.rule_type == 'starts_with':
            return desc.lower().startswith(value.lower())
        elif rule.rule_type == 'ends_with':
            return desc.lower().endswith(value.lower())
        return False

    def _evaluate_group_rules(self, group, description):
        """Evaluate all rules in a group with AND/OR connectors.
        Returns True if the description matches the group.
        """
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

    def _compute_summary(self):
        """Compute group summary and unmatched bills from selected bills."""
        self.ensure_one()
        GroupLine = self.env['tha.referred.fee.wizard.line']
        UnmatchedLine = self.env['tha.referred.fee.wizard.unmatched']

        # Clear existing lines
        self.group_line_ids.unlink()
        self.unmatched_line_ids.unlink()

        groups = self.env['tha.referred.mapping.group'].search([], order='sequence, id')
        group_amounts = {g.id: 0.0 for g in groups}
        unmatched_bills = []

        for bill in self.bill_ids:
            description = self._parse_vendor_ref(bill.ref)
            amount = bill.amount_total_signed if bill.move_type == 'in_invoice' else -bill.amount_total_signed

            matched = False
            for group in groups:
                if self._evaluate_group_rules(group, description):
                    group_amounts[group.id] += amount
                    matched = True
                    break

            if not matched:
                unmatched_bills.append({
                    'wizard_id': self.id,
                    'move_id': bill.id,
                    'move_name': bill.name,
                    'partner_id': bill.partner_id.id,
                    'ref': bill.ref,
                    'amount': amount,
                })

        # Create group summary lines
        group_lines = []
        for group in groups:
            if group_amounts[group.id] != 0.0:
                group_lines.append({
                    'wizard_id': self.id,
                    'group_id': group.id,
                    'group_name': group.name,
                    'amount': group_amounts[group.id],
                })
        if group_lines:
            GroupLine.create(group_lines)

        # Create unmatched lines
        if unmatched_bills:
            UnmatchedLine.create(unmatched_bills)

    def action_compute(self):
        """Compute the summary when wizard opens or refreshes."""
        self._compute_summary()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'tha.referred.fee.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_print_pdf(self):
        """Print PDF report."""
        self._compute_summary()
        return self.env.ref(
            'tha_vhg_referred_fee_summary.action_report_referred_fee_pdf'
        ).report_action(self)

    def action_print_excel(self):
        """Print Excel report as downloadable file."""
        import base64
        from ..report.referred_fee_excel_report import generate_xlsx
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

</parameter>