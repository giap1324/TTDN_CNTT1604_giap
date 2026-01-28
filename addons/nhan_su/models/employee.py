# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re
import unicodedata
from datetime import date, datetime


class HrEmployeeExtended(models.Model):
    _name = 'hr.employee.extended'
    _description = 'Thông Tin Nhân Viên Mở Rộng'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'employee_code'

    # Thông tin cơ bản
    name = fields.Char(string='Họ và tên đầy đủ', required=True, tracking=True)
    employee_code = fields.Char(
        string='Mã nhân viên',
        readonly=True,
        copy=False,
        default=lambda self: self._generate_employee_code(),
        tracking=True
    )

    # Thông tin cá nhân
    date_of_birth = fields.Date(string='Ngày sinh', tracking=True)
    gender = fields.Selection([
        ('male', 'Nam'),
        ('female', 'Nữ'),
        ('other', 'Khác')
    ], string='Giới tính', tracking=True)

    # CMND/CCCD
    identity_number = fields.Char(string='Số CMND/CCCD', tracking=True)
    identity_issued_date = fields.Date(string='Ngày cấp', tracking=True)
    identity_issued_place = fields.Char(string='Nơi cấp', tracking=True)

    # Địa chỉ
    permanent_address = fields.Text(string='Hộ khẩu thường trú', tracking=True)
    current_address = fields.Text(string='Chỗ ở hiện tại', tracking=True)

    # Liên hệ
    phone = fields.Char(string='Số điện thoại', tracking=True)
    personal_email = fields.Char(string='Email cá nhân', tracking=True)
    work_email = fields.Char(
        string='Email công ty',
        compute='_compute_work_email',
        store=True,
        tracking=True
    )

    # Tình trạng cá nhân
    marital_status = fields.Selection([
        ('single', 'Độc thân'),
        ('married', 'Đã kết hôn'),
        ('divorced', 'Ly hôn'),
        ('widowed', 'Góa phụ/Góa chồng')
    ], string='Tình trạng hôn nhân', tracking=True)

    ethnicity = fields.Char(string='Dân tộc', tracking=True)
    religion = fields.Char(string='Tôn giáo', tracking=True)

    # Thông tin công việc
    department_id = fields.Many2one(
        'don_vi',
        string='Phòng ban',
        tracking=True
    )
    job_title = fields.Char(string='Chức vụ/Vị trí', tracking=True)
    manager_id = fields.Many2one(
        'hr.employee',
        string='Cấp quản lý trực tiếp',
        tracking=True
    )
    hire_date = fields.Date(string='Ngày vào làm', tracking=True)
    contract_type = fields.Selection([
        ('permanent', 'Hợp đồng chính thức'),
        ('probation', 'Hợp đồng thử việc'),
        ('temporary', 'Hợp đồng thời vụ'),
        ('part_time', 'Hợp đồng bán thời gian')
    ], string='Loại hợp đồng', tracking=True)

    work_location = fields.Char(string='Địa điểm làm việc', tracking=True)
    work_shift = fields.Selection([
        ('morning', 'Ca sáng'),
        ('afternoon', 'Ca chiều'),
        ('night', 'Ca đêm'),
        ('flexible', 'Linh hoạt')
    ], string='Ca làm việc', tracking=True)

    # Học vấn và chuyên môn
    education_level = fields.Selection([
        ('high_school', 'Trung học phổ thông'),
        ('college', 'Cao đẳng'),
        ('university', 'Đại học'),
        ('master', 'Thạc sĩ'),
        ('phd', 'Tiến sĩ'),
        ('other', 'Khác')
    ], string='Trình độ học vấn', tracking=True)

    major = fields.Char(string='Chuyên ngành', tracking=True)
    school = fields.Char(string='Trường học', tracking=True)
    graduation_year = fields.Char(string='Năm tốt nghiệp', tracking=True)
    certificates = fields.Text(string='Bằng cấp, chứng chỉ', tracking=True)
    special_skills = fields.Text(string='Kỹ năng đặc biệt', tracking=True)

    # Thông tin liên hệ khẩn cấp
    emergency_contact_name = fields.Char(string='Họ tên người thân', tracking=True)
    emergency_contact_relationship = fields.Char(string='Mối quan hệ', tracking=True)
    emergency_contact_phone = fields.Char(string='Số điện thoại khẩn cấp', tracking=True)
    emergency_contact_address = fields.Text(string='Địa chỉ người thân', tracking=True)

    # Tài liệu đính kèm
    photo = fields.Binary(string='Ảnh 4x6', attachment=True)
    photo_filename = fields.Char(string='Tên file ảnh')

    identity_scan = fields.Binary(string='Scan CMND/CCCD', attachment=True)
    identity_scan_filename = fields.Char(string='Tên file CMND')

    diploma_scan = fields.Binary(string='Scan bằng cấp', attachment=True)
    diploma_scan_filename = fields.Char(string='Tên file bằng cấp')

    contract_scan = fields.Binary(string='Scan hợp đồng', attachment=True)
    contract_scan_filename = fields.Char(string='Tên file hợp đồng')

    health_check_scan = fields.Binary(string='Giấy khám sức khỏe', attachment=True)
    health_check_scan_filename = fields.Char(string='Tên file sức khỏe')

    # Trạng thái hồ sơ
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('pending', 'Chờ duyệt'),
        ('active', 'Hoạt động'),
        ('inactive', 'Không hoạt động'),
        ('terminated', 'Đã nghỉ việc')
    ], string='Trạng thái', default='draft', tracking=True)

    # Tài khoản hệ thống
    user_id = fields.Many2one(
        'res.users',
        string='Tài khoản hệ thống',
        readonly=True,
        tracking=True
    )
    username = fields.Char(string='Tên đăng nhập', readonly=True, tracking=True)
    password_temp = fields.Char(string='Mật khẩu tạm thời', readonly=True)

    # Telegram Integration
    telegram_chat_id = fields.Char(
        string='Telegram Chat ID',
        help='Chat ID của nhân viên trên Telegram để nhận thông báo',
        tracking=True
    )
    telegram_enabled = fields.Boolean(
        string='Bật thông báo Telegram',
        default=True,
        help='Cho phép gửi thông báo qua Telegram'
    )

    # Lịch sử thay đổi
    history_ids = fields.One2many(
        'employee.history',
        'employee_id',
        string='Lịch sử thay đổi'
    )

    # Additional fields
    notes = fields.Text(string='Ghi chú', tracking=True)
    history_count = fields.Integer(string='Số lượng lịch sử', compute='_compute_history_count')

    # Computed fields
    age = fields.Integer(string='Tuổi', compute='_compute_age', store=True)
    years_of_service = fields.Float(
        string='Số năm làm việc',
        compute='_compute_years_of_service',
        store=True
    )

    @api.depends('history_ids')
    def _compute_history_count(self):
        for record in self:
            record.history_count = len(record.history_ids)

    @api.depends('date_of_birth')
    def _compute_age(self):
        for record in self:
            if record.date_of_birth:
                today = date.today()
                record.age = today.year - record.date_of_birth.year - (
                    (today.month, today.day) < (record.date_of_birth.month, record.date_of_birth.day)
                )
            else:
                record.age = 0

    @api.depends('hire_date')
    def _compute_years_of_service(self):
        for record in self:
            if record.hire_date:
                today = date.today()
                delta = today - record.hire_date
                record.years_of_service = round(delta.days / 365.25, 1)
            else:
                record.years_of_service = 0

    @api.depends('name')
    def _compute_work_email(self):
        for record in self:
            if record.name:
                # Bỏ dấu tiếng Việt và tạo email công ty
                name_parts = record.name.lower().strip().split()
                if len(name_parts) >= 2:
                    first_name = self._remove_accents(name_parts[-1])  # Tên
                    last_name = '.'.join([self._remove_accents(p) for p in name_parts[:-1]])  # Họ
                    record.work_email = f"{first_name}.{last_name}@company.com"
                else:
                    record.work_email = f"{self._remove_accents(name_parts[0])}@company.com"
            else:
                record.work_email = False

    def _remove_accents(self, text):
        """Bỏ dấu tiếng Việt"""
        if not text:
            return text
        # Chuẩn hóa Unicode và bỏ dấu
        text = unicodedata.normalize('NFD', text)
        text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
        # Thay thế các ký tự đặc biệt tiếng Việt
        replacements = {
            'đ': 'd', 'Đ': 'D',
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text.lower()

    def _generate_employee_code(self):
        """Tự động tạo mã nhân viên: NV001, NV002..."""
        sequence = self.env['ir.sequence'].next_by_code('hr.employee.extended') or 'NV001'
        return sequence

    @api.constrains('identity_number')
    def _check_identity_number_unique(self):
        """Kiểm tra CMND/CCCD không trùng"""
        for record in self:
            if record.identity_number:
                existing = self.search([
                    ('identity_number', '=', record.identity_number),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(_('Số CMND/CCCD đã tồn tại trong hệ thống!'))

    @api.constrains('personal_email', 'work_email')
    def _check_emails(self):
        """Validate email format"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        for record in self:
            if record.personal_email and not re.match(email_pattern, record.personal_email):
                raise ValidationError(_('Email cá nhân không hợp lệ!'))
            if record.work_email and not re.match(email_pattern, record.work_email):
                raise ValidationError(_('Email công ty không hợp lệ!'))

    @api.constrains('phone', 'emergency_contact_phone')
    def _check_phone_format(self):
        """Validate phone number format"""
        phone_pattern = r'^(\+84|0)[3|5|7|8|9][0-9]{8}$'
        for record in self:
            if record.phone and not re.match(phone_pattern, record.phone):
                raise ValidationError(_('Số điện thoại không hợp lệ! Phải là số Việt Nam.'))
            if record.emergency_contact_phone and not re.match(phone_pattern, record.emergency_contact_phone):
                raise ValidationError(_('Số điện thoại khẩn cấp không hợp lệ!'))

    def action_activate_profile(self):
        """Kích hoạt hồ sơ nhân viên"""
        for record in self:
            if record.state == 'pending':
                # Tạo tài khoản người dùng
                self._create_user_account()
                # Cập nhật trạng thái
                record.write({'state': 'active'})
                # Gửi email chào mừng
                self._send_welcome_email()

    def action_deactivate_profile(self):
        """Hủy kích hoạt hồ sơ"""
        for record in self:
            record.state = 'inactive'

    def action_terminate_profile(self):
        """Đánh dấu đã nghỉ việc"""
        for record in self:
            record.state = 'terminated'

    def _create_user_account(self):
        """Tạo tài khoản người dùng Odoo"""
        for record in self:
            if not record.user_id and record.work_email:
                # Tạo username từ email
                username = record.work_email.split('@')[0]
                # Tạo mật khẩu ngẫu nhiên
                password = self._generate_temp_password()

                # Tạo user
                user_vals = {
                    'name': record.name,
                    'login': username,
                    'email': record.work_email,
                    'password': password,
                    'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
                }

                user = self.env['res.users'].create(user_vals)

                # Cập nhật thông tin
                record.write({
                    'user_id': user.id,
                    'username': username,
                    'password_temp': password,
                })

    def _generate_temp_password(self):
        """Tạo mật khẩu tạm thời"""
        import random
        import string
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for i in range(8))

    def _send_welcome_email(self):
        """Gửi email chào mừng"""
        for record in self:
            if record.work_email and record.password_temp:
                template = self.env.ref('nhan_su.email_template_welcome')
                if template:
                    template.send_mail(record.id, force_send=True)

    def write(self, vals):
        """Ghi đè để lưu lịch sử thay đổi"""
        # Lưu lịch sử trước khi thay đổi
        history_fields = self._get_history_tracked_fields()
        if any(key in vals for key in history_fields):
            for record in self:
                self._create_history_record(record, vals)

        return super(HrEmployeeExtended, self).write(vals)

    def _get_history_tracked_fields(self):
        """Các trường cần theo dõi lịch sử (dùng cho history tracking)"""
        return {
            'name', 'phone', 'personal_email', 'current_address',
            'marital_status', 'department_id', 'job_title', 'manager_id',
            'contract_type', 'work_location', 'work_shift'
        }

    def _create_history_record(self, record, changes):
        """Tạo bản ghi lịch sử"""
        history_vals = {
            'employee_id': record.id,
            'change_date': datetime.now(),
            'changed_by': self.env.user.id,
            'changes': str(changes),  # Có thể cải thiện format sau
        }
        self.env['employee.history'].create(history_vals)