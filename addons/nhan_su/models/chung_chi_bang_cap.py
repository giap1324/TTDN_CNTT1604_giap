# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ChungChiBangCap(models.Model):
    _name = 'chung_chi_bang_cap'
    _description = 'Chứng Chỉ Bằng Cấp'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'ma_chung_chi_bang_cap'

    ma_chung_chi_bang_cap = fields.Char(string='Mã chứng chỉ/bằng cấp', required=True, tracking=True)
    ten_chung_chi_bang_cap = fields.Char(string='Tên chứng chỉ/bằng cấp', required=True, tracking=True)
    mo_ta = fields.Text(string='Mô tả', tracking=True)

    # Quan hệ - COMMENT TẠM THỜI vì model 'danh_sach_chung_chi_bang_cap' chưa tồn tại
    # danh_sach_chung_chi_bang_cap_ids = fields.One2many(
    #     'danh_sach_chung_chi_bang_cap',
    #     'chung_chi_bang_cap_id',
    #     string='Danh sách nhân viên có chứng chỉ'
    # )

    @api.constrains('ma_chung_chi_bang_cap')
    def _check_ma_unique(self):
        """Kiểm tra mã không trùng"""
        for record in self:
            existing = self.search([
                ('ma_chung_chi_bang_cap', '=', record.ma_chung_chi_bang_cap),
                ('id', '!=', record.id)
            ])
            if existing:
                raise ValidationError(_('Mã chứng chỉ/bằng cấp đã tồn tại!'))

    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.ma_chung_chi_bang_cap}] {record.ten_chung_chi_bang_cap}"
            result.append((record.id, name))
        return result
