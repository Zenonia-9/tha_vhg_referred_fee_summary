# VHG Referred Fee Summary

## Overview
Generates Referred Fee Summary reports (PDF and Excel) from selected vendor bills. Maps bill `vendor_ref` values to configurable groups using pre-imported exact-match rules, then aggregates amounts by group.

## Features
- Configurable mapping groups with pattern-matching rules (contains, starts with, ends with, exact match)
- AND/OR rule connectors within each group
- Pre-imported mapping data from Excel (16 groups, ~1200 item descriptions)
- Wizard with date range, partner, group summary preview, and unmatched bills list
- PDF report matching Victoria Hospital layout
- Excel export with same data structure
- "Referred Summary" button on account.move list view

## Requirements
- Odoo 19
- `account` module

## Installation
1. Place module in `custom_addons/` directory
2. Update Apps list
3. Install "VHG Referred Fee Summary"

## Configuration
- Navigate to Accounting > Configuration > Referred Summary > Referred Mapping
- Add/edit mapping groups and their rules
- Rules support: Contains, Starts with, Ends with, Exact match
- Rules can be combined with AND/OR connectors

## Usage
1. Go to Accounting > Vendors > Bills
2. Select multiple bills from the same vendor
3. Click "Referred Summary" button
4. Review group summary and unmatched bills
5. Click "Print PDF" or "Print Excel" to generate report

## Technical Details
- `tha.referred.mapping.group`: Group configuration model
- `tha.referred.mapping.rule`: Matching rules per group
- `tha.referred.fee.wizard`: TransientModel for report generation
- `tha.referred.fee.wizard.line`: Group summary lines
- `tha.referred.fee.wizard.unmatched`: Unmatched bills tracking

## Security
- Accountant group: Read/write on mapping, read on wizard
- Accounting Manager group: Full CRUD on all models

## Author
Thein Htoo Aung

## License
LGPL-3

</parameter>