# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AssetCategory(models.Model):
    _name = 'asset.category'
    _description = 'Danh Mục Tài Sản'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Tên danh mục', required=True, tracking=True)
    code = fields.Char(string='Mã danh mục', required=True, tracking=True)
    description = fields.Text(string='Mô tả', tracking=True)
    
    # Quan hệ
    asset_ids = fields.One2many('asset', 'category_id', string='Danh sách tài sản')

    @api.constrains('code')
    def _check_code_unique(self):
        """Kiểm tra mã danh mục không trùng"""
        for record in self:
            existing = self.search([
                ('code', '=', record.code),
                ('id', '!=', record.id)
            ])
            if existing:
                raise ValidationError(_('Mã danh mục đã tồn tại!'))

    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.code}] {record.name}"
            result.append((record.id, name))
        return result
