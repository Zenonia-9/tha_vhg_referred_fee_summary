# -*- coding: utf-8 -*-
"""Excel report helper — called from wizard action_print_excel."""
import io
from datetime import datetime
from odoo.exceptions import UserError

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None


def generate_xlsx(wizard):
    """Generate xlsx bytes from wizard group lines. Returns (content_bytes, filename)."""
    if not xlsxwriter:
        raise UserError('xlsxwriter library is required for Excel export.')

    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    sheet = workbook.add_worksheet('Referred Fees')

    hospital_fmt = workbook.add_format({
        'bold': True, 'font_size': 12, 'align': 'center', 'font_name': 'Arial'})
    title_fmt = workbook.add_format({
        'bold': True, 'font_size': 16, 'align': 'center', 'font_name': 'Arial'})
    meta_fmt = workbook.add_format({
        'font_size': 11, 'font_name': 'Arial'})
    meta_right_fmt = workbook.add_format({
        'font_size': 11, 'align': 'right', 'font_name': 'Arial'})
    date_fmt = workbook.add_format({
        'bold': True, 'align': 'center', 'font_size': 11, 'font_name': 'Arial'})
    dr_fmt = workbook.add_format({
        'bold': True, 'font_size': 11, 'underline': 1, 'font_name': 'Arial'})
    col_header_fmt = workbook.add_format({
        'bold': True, 'underline': 1, 'font_size': 11, 'font_name': 'Arial'})
    col_header_amt_fmt = workbook.add_format({
        'bold': True, 'underline': 1, 'font_size': 11, 'align': 'right', 'font_name': 'Arial'})
    amount_fmt = workbook.add_format({
        'num_format': '#,##0.00', 'align': 'right', 'font_size': 11, 'font_name': 'Arial'})
    desc_fmt = workbook.add_format({
        'font_size': 11, 'font_name': 'Arial', 'indent': 2})
    subtotal_fmt = workbook.add_format({
        'bold': True, 'bg_color': '#00FFFF',
        'num_format': '#,##0.00', 'align': 'right', 'font_size': 11, 'font_name': 'Arial'})
    subtotal_label_fmt = workbook.add_format({
        'bold': True, 'bg_color': '#00FFFF', 'align': 'center',
        'font_size': 11, 'font_name': 'Arial'})

    sheet.set_column('A:A', 42)
    sheet.set_column('B:B', 22)

    now = datetime.now()
    sheet.merge_range(0, 0, 0, 1, 'VICTORIA HOSPITAL', hospital_fmt)
    sheet.write(1, 0, '%s    %s' % (now.strftime('%H:%M'), now.strftime('%-d/%-m/%Y')), meta_fmt)
    sheet.merge_range(2, 0, 2, 1, 'Referred fees', title_fmt)

    date_from = wizard.date_from.strftime('%d-%b-%Y') if wizard.date_from else ''
    date_to = wizard.date_to.strftime('%d-%b-%Y') if wizard.date_to else ''
    sheet.merge_range(3, 0, 3, 1, 'Between %s And %s' % (date_from, date_to), date_fmt)

    sheet.write(5, 0, 'Dr Name: %s' % (wizard.partner_id.name or ''), dr_fmt)

    row = 7
    sheet.write(row, 0, 'Description', col_header_fmt)
    sheet.write(row, 1, 'Amount (MMK)', col_header_amt_fmt)
    row += 1

    total = 0.0
    for line in wizard.group_line_ids:
        sheet.write(row, 0, line.group_name or '', desc_fmt)
        sheet.write_number(row, 1, line.amount, amount_fmt)
        total += line.amount
        row += 1

    row += 1
    sheet.write(row, 0, 'Sub total:', subtotal_label_fmt)
    sheet.write_number(row, 1, total, subtotal_fmt)

    workbook.close()
    output.seek(0)
    content = output.read()
    filename = 'referred_fee_summary_%s_%s.xlsx' % (
        date_from.replace('-', ''), date_to.replace('-', ''))
    return content, filename
