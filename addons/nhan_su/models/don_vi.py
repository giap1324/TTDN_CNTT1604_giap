# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class DonVi(models.Model):
    _name = 'don_vi'
    _description = 'Đơn Vị'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'ma_don_vi'

    ma_don_vi = fields.Char(string='Mã đơn vị', required=True, tracking=True)
    ten_don_vi = fields.Char(string='Tên đơn vị', required=True, tracking=True)
    mo_ta = fields.Text(string='Mô tả', tracking=True)

    # Quan hệ
    nhan_vien_ids = fields.One2many(
        'hr.employee.extended',
        'department_id',
        string='Danh sách nhân viên'
    )

    # Computed fields
    employee_count = fields.Integer(
        string='Số lượng nhân viên',
        compute='_compute_employee_count',
        store=True
    )

    @api.depends('nhan_vien_ids')
    def _compute_employee_count(self):
        for record in self:
            record.employee_count = len(record.nhan_vien_ids)

    def action_view_employees(self):
        """Mở danh sách nhân viên của đơn vị"""
        return {
            'name': f'Nhân viên - {self.ten_don_vi}',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.employee.extended',
            'view_mode': 'kanban,tree,form',
            'domain': [('department_id', '=', self.id)],
            'context': {'default_department_id': self.id},
        }

    @api.constrains('ma_don_vi')
    def _check_ma_don_vi_unique(self):
        """Kiểm tra mã đơn vị không trùng"""
        for record in self:
            existing = self.search([
                ('ma_don_vi', '=', record.ma_don_vi),
                ('id', '!=', record.id)
            ])
            if existing:
                raise ValidationError(_('Mã đơn vị đã tồn tại!'))

    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.ma_don_vi}] {record.ten_don_vi}"
            result.append((record.id, name))
        return result
