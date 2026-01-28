# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime


class AssetUsageHistory(models.Model):
    _name = 'asset.usage.history'
    _description = 'Lịch Sử Sử Dụng Tài Sản'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_from desc'

    asset_id = fields.Many2one(
        'asset',
        string='Tài sản',
        required=True,
        ondelete='cascade'
    )
    employee_id = fields.Many2one(
        'hr.employee.extended',
        string='Nhân viên',
        required=True,
        tracking=True
    )
    date_from = fields.Datetime(string='Từ ngày', required=True, tracking=True)
    date_to = fields.Datetime(string='Đến ngày', tracking=True)
    purpose = fields.Text(string='Mục đích sử dụng', tracking=True)
    state = fields.Selection([
        ('active', 'Đang sử dụng'),
        ('returned', 'Đã trả'),
        ('lost', 'Mất'),
        ('damaged', 'Hư hỏng')
    ], string='Trạng thái', default='active', tracking=True)

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.asset_id.name} - {record.employee_id.name}"
            result.append((record.id, name))
        return result
