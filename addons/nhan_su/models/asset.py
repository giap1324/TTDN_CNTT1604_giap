# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date, datetime


class Asset(models.Model):
    _name = 'asset'
    _description = 'Tài Sản'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'asset_code'

    # Thông tin cơ bản
    asset_code = fields.Char(
        string='Mã tài sản',
        required=True,
        copy=False,
        default=lambda self: self._generate_asset_code(),
        tracking=True
    )
    name = fields.Char(string='Tên tài sản', required=True, tracking=True)
    category_id = fields.Many2one(
        'asset.category',
        string='Danh mục',
        required=True,
        tracking=True
    )
    location_id = fields.Many2one(
        'asset.location',
        string='Vị trí',
        tracking=True
    )

    # Thông tin chi tiết
    brand = fields.Char(string='Thương hiệu', tracking=True)
    model = fields.Char(string='Model', tracking=True)
    serial_number = fields.Char(string='Số seri', tracking=True)
    purchase_date = fields.Date(string='Ngày mua', tracking=True)
    purchase_price = fields.Monetary(string='Giá mua', tracking=True)
    current_value = fields.Monetary(
        string='Giá trị hiện tại',
        compute='_compute_current_value',
        store=True
    )
    warranty_expiry = fields.Date(string='Ngày hết bảo hành', tracking=True)
    
    # Người quản lý (tích hợp với nhân sự)
    manager_id = fields.Many2one(
        'hr.employee.extended',
        string='Người quản lý',
        tracking=True,
        help='Nhân viên chịu trách nhiệm quản lý tài sản này'
    )
    assigned_to_id = fields.Many2one(
        'hr.employee.extended',
        string='Người được giao',
        tracking=True,
        help='Nhân viên đang sử dụng tài sản này'
    )

    # Trạng thái
    state = fields.Selection([
        ('available', 'Sẵn sàng'),
        ('in_use', 'Đang sử dụng'),
        ('maintenance', 'Bảo trì'),
        ('damaged', 'Hư hỏng'),
        ('disposed', 'Đã thanh lý')
    ], string='Trạng thái', default='available', tracking=True)

    # Lịch sử sử dụng
    usage_history_ids = fields.One2many(
        'asset.usage.history',
        'asset_id',
        string='Lịch sử sử dụng'
    )

    # File đính kèm
    image = fields.Binary(string='Hình ảnh', attachment=True)
    documents = fields.Many2many(
        'ir.attachment',
        'asset_document_rel',
        'asset_id',
        'attachment_id',
        string='Tài liệu đính kèm'
    )

    # Tiền tệ
    currency_id = fields.Many2one(
        'res.currency',
        string='Tiền tệ',
        default=lambda self: self.env.company.currency_id
    )

    # Ghi chú
    notes = fields.Text(string='Ghi chú', tracking=True)

    @api.depends('purchase_date', 'purchase_price')
    def _compute_current_value(self):
        """Tính giá trị hiện tại (khấu hao đơn giản)"""
        for record in self:
            if record.purchase_price and record.purchase_date:
                # Khấu hao 10% mỗi năm
                years = (date.today() - record.purchase_date).days / 365.25
                depreciation = min(years * 0.1, 0.9)  # Tối đa 90%
                record.current_value = record.purchase_price * (1 - depreciation)
            else:
                record.current_value = 0

    def _generate_asset_code(self):
        """Tự động tạo mã tài sản"""
        sequence = self.env['ir.sequence'].next_by_code('asset') or 'TS001'
        return sequence

    def action_assign(self):
        """Gán tài sản cho nhân viên"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Gán tài sản',
            'res_model': 'asset.assign.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_asset_id': self.id}
        }

    def action_maintenance(self):
        """Chuyển trạng thái sang bảo trì"""
        for record in self:
            record.state = 'maintenance'

    def action_return(self):
        """Trả tài sản về kho"""
        for record in self:
            record.write({
                'state': 'available',
                'assigned_to_id': False
            })

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.asset_code} - {record.name}"
            result.append((record.id, name))
        return result
