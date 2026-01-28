# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request


class HrEmployeeController(http.Controller):

    @http.route('/hr_employee/profile/<int:employee_id>', type='http', auth='user', website=True)
    def employee_profile(self, employee_id, **kwargs):
        """Xem hồ sơ nhân viên (cho nhân viên và quản lý)"""
        employee = request.env['hr.employee.extended'].sudo().browse(employee_id)
        if not employee.exists():
            return request.not_found()

        # Kiểm tra quyền truy cập
        current_user = request.env.user
        if not (current_user.has_group('hr.group_hr_manager') or
                current_user.has_group('hr.group_hr_user') or
                employee.user_id == current_user):
            return request.not_found()

        return request.render('nhan_su.employee_profile_template', {
            'employee': employee,
        })