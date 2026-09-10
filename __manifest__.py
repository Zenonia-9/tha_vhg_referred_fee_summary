# -*- coding: utf-8 -*-
{
    'name': 'VHG Referred Fee Summary',
    'summary': 'Referred fee summary reports (PDF/Excel) with configurable group mapping from vendor bills.',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Accounting',
    'author': 'Thein Htoo Aung',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'anzer_odoo_integration',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/referred_mapping_data.xml',
        'views/referred_mapping_views.xml',
        'views/referred_fee_wizard_views.xml',
        'views/account_move_views.xml',
        'report/referred_fee_report.xml',
        'report/referred_fee_report_template.xml',
    ],
    'external_dependencies': {
        'python': ['xlsxwriter'],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}