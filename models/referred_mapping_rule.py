# -*- coding: utf-8 -*-
from odoo import models, fields


class ThaReferredMappingRule(models.Model):
    _name = 'tha.referred.mapping.rule'
    _description = 'Referred Fee Mapping Rule'
    _order = 'sequence, id'

    group_id = fields.Many2one(
        'tha.referred.mapping.group', string='Group',
        required=True, ondelete='cascade')
    rule_type = fields.Selection([
        ('contains', 'Contains'),
        ('starts_with', 'Starts with'),
        ('ends_with', 'Ends with'),
        ('exact', 'Exact match'),
    ], string='Rule Type', required=True, default='exact')
    value = fields.Char(string='Value', required=True)
    connector = fields.Selection([
        ('and', 'AND'),
        ('or', 'OR'),
    ], string='Connector', default='or',
        help='Logical connector to the previous rule (ignored for first rule)')
    sequence = fields.Integer(string='Sequence', default=10)