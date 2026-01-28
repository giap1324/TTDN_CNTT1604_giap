# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ChucVu(models.Model):
    _name = 'chuc_vu'
    _description = 'Chức Vụ'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'ma_chuc_vu'

    ma_chuc_vu = fields.Char(string='Mã chức vụ', required=True, tracking=True)
    ten_chuc_vu = fields.Char(string='Tên chức vụ', required=True, tracking=True)
    mo_ta = fields.Text(string='Mô tả', tracking=True)

    # Quan hệ - COMMENT TẠM THỜI vì model 'lich_su_cong_tac' chưa tồn tại
    # lich_su_cong_tac_ids = fields.One2many(
    #     'lich_su_cong_tac',
    #     'chuc_vu_id',
    #     string='Lịch sử công tác'
    # )

    @api.constrains('ma_chuc_vu')
    def _check_ma_chuc_vu_unique(self):
        """Kiểm tra mã chức vụ không trùng"""
        for record in self:
            existing = self.search([
                ('ma_chuc_vu', '=', record.ma_chuc_vu),
                ('id', '!=', record.id)
            ])
            if existing:
                raise ValidationError(_('Mã chức vụ đã tồn tại!'))

    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.ma_chuc_vu}] {record.ten_chuc_vu}"
            result.append((record.id, name))
        return result
