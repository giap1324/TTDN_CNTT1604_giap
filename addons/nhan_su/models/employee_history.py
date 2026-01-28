# -*- coding: utf-8 -*-

from odoo import models, fields, api


class EmployeeHistory(models.Model):
    _name = 'employee.history'
    _description = 'Lịch Sử Thay Đổi Nhân Viên'
    _order = 'change_date desc'

    employee_id = fields.Many2one(
        'hr.employee.extended',
        string='Nhân viên',
        required=True,
        ondelete='cascade'
    )

    change_date = fields.Datetime(
        string='Ngày thay đổi',
        default=fields.Datetime.now,
        required=True
    )

    changed_by = fields.Many2one(
        'res.users',
        string='Người thay đổi',
        default=lambda self: self.env.user,
        required=True
    )

    change_type = fields.Selection([
        ('personal_info', 'Thông tin cá nhân'),
        ('work_info', 'Thông tin công việc'),
        ('contact_info', 'Thông tin liên hệ'),
        ('document', 'Tài liệu'),
        ('status', 'Trạng thái hồ sơ'),
        ('other', 'Khác')
    ], string='Loại thay đổi')

    changes = fields.Text(string='Chi tiết thay đổi')
    reason = fields.Text(string='Lý do thay đổi')
    approved_by = fields.Many2one('res.users', string='Người phê duyệt')

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.employee_id.name} - {record.change_date.strftime('%d/%m/%Y %H:%M')}"
            result.append((record.id, name))
        return result