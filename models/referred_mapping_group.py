# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ThaReferredMappingGroup(models.Model):
    _name = 'tha.referred.mapping.group'
    _description = 'Referred Fee Mapping Group'
    _order = 'sequence, id'

    name = fields.Char(string='Group Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    rule_ids = fields.One2many(
        'tha.referred.mapping.rule', 'group_id', string='Rules')
    rule_count = fields.Integer(
        string='Rule Count', compute='_compute_rule_count', store=True)

    @api.depends('rule_ids')
    def _compute_rule_count(self):
        for group in self:
            group.rule_count = len(group.rule_ids)

</parameter>