# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta

class MeetingRoomBooking(models.Model):
    _name = 'meeting.room.booking'
    _description = 'Đặt Phòng Họp'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_time desc'

    # Thông tin cơ bản
    name = fields.Char(string='Mã đặt phòng', readonly=True, copy=False, default='New')
    room_id = fields.Many2one('meeting.room', string='Phòng họp', required=True, tracking=True)
    booker_id = fields.Many2one(
        'hr.employee.extended',
        string='Người đặt',
        required=True,
        default=lambda self: self._get_current_employee(),
        tracking=True
    )
    organizer_id = fields.Many2one('hr.employee.extended', string='Người tổ chức', required=True, tracking=True)

    # Thời gian
    start_time = fields.Datetime(string='Thời gian bắt đầu', required=True, tracking=True)
    end_time = fields.Datetime(string='Thời gian kết thúc', required=True, tracking=True)
    duration = fields.Float(string='Thời lượng (giờ)', compute='_compute_duration', store=True)
    
    # Thông tin cuộc họp
    subject = fields.Char(string='Chủ đề cuộc họp', required=True, tracking=True)
    description = fields.Text(string='Mô tả', tracking=True)
    expected_attendees = fields.Integer(string='Số người dự kiến', tracking=True)
    
    # Người tham dự
    attendee_ids = fields.Many2many(
        'hr.employee.extended',
        'meeting_booking_attendee_rel',
        'booking_id',
        'employee_id',
        string='Người tham dự'
    )
    
    # Trạng thái
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('pending', 'Chờ duyệt'),
        ('confirmed', 'Đã xác nhận'),
        ('in_progress', 'Đang diễn ra'),
        ('completed', 'Hoàn thành'),
        ('cancelled', 'Đã hủy')
    ], string='Trạng thái', default='draft', tracking=True, required=True)

    # === QUẢN LÝ THIẾT BỊ ===
    equipment_ids = fields.Many2many(
        'asset',
        'meeting_booking_equipment_rel',
        'booking_id',
        'asset_id',
        string='Thiết bị yêu cầu',
        domain="[('location_id', '=', room_location_id), ('state', '=', 'available')]"
    )
    room_location_id = fields.Many2one('asset.location', related='room_id.location_id', string='Vị trí phòng')
    equipment_notes = fields.Text(string='Ghi chú thiết bị')
    equipment_prepared = fields.Boolean(string='Thiết bị đã chuẩn bị', default=False)
    equipment_checked_by = fields.Many2one('res.users', string='Người kiểm tra thiết bị')
    equipment_checked_date = fields.Datetime(string='Ngày kiểm tra')
    
    # === PHÊ DUYỆT ===
    require_approval = fields.Boolean(string='Yêu cầu phê duyệt', compute='_compute_require_approval', store=True)
    approval_level = fields.Selection([
        ('manager', 'Quản lý'),
        ('director', 'Giám đốc'),
        ('admin', 'Hành chính')
    ], string='Cấp phê duyệt', compute='_compute_approval_level', store=True)
    approved_by_id = fields.Many2one('res.users', string='Người phê duyệt', readonly=True, tracking=True)
    approved_date = fields.Datetime(string='Ngày phê duyệt', readonly=True)
    rejection_reason = fields.Text(string='Lý do từ chối')
    
    # Check-in/Check-out
    check_in_time = fields.Datetime(string='Check-in')
    check_out_time = fields.Datetime(string='Check-out')
    auto_cancel_if_no_checkin = fields.Boolean(string='Tự động hủy nếu không check-in', default=True)
    
    # Màu cho calendar
    color = fields.Integer(string='Màu', compute='_compute_color')
    
    # === THỐNG KÊ ===
    actual_attendees = fields.Integer(string='Số người thực tế')
    rating = fields.Selection([
        ('1', 'Rất tệ'),
        ('2', 'Tệ'),
        ('3', 'Trung bình'),
        ('4', 'Tốt'),
        ('5', 'Xuất sắc')
    ], string='Đánh giá')
    feedback = fields.Text(string='Phản hồi')
    
    # Xung đột
    has_conflict = fields.Boolean(string='Có xung đột', compute='_compute_has_conflict')
    conflict_count = fields.Integer(string='Số xung đột', compute='_compute_has_conflict')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('meeting.room.booking') or 'New'
        
        # Tự động phê duyệt khi tạo mới (auto-approve)
        if vals.get('state', 'draft') == 'draft':
            vals['state'] = 'confirmed'
            vals['approved_by_id'] = self.env.user.id
            vals['approved_date'] = fields.Datetime.now()
        
        booking = super(MeetingRoomBooking, self).create(vals)
        
        # Gửi thông báo xác nhận
        booking._send_confirmation_notification()
        
        # Gửi thông báo Telegram khi tạo đặt phòng mới
        booking._send_telegram_notification('created')
        
        return booking
    
    def write(self, vals):
        """Override write để gửi thông báo khi trạng thái thay đổi"""
        old_state = self.state
        result = super(MeetingRoomBooking, self).write(vals)
        
        # Gửi thông báo nếu trạng thái thay đổi
        if 'state' in vals and vals['state'] != old_state:
            self._send_telegram_notification('state_changed', old_state=old_state)
        
        return result

    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        for record in self:
            if record.start_time and record.end_time:
                delta = record.end_time - record.start_time
                record.duration = delta.total_seconds() / 3600
            else:
                record.duration = 0

    @api.depends('state')
    def _compute_color(self):
        color_map = {
            'draft': 7,
            'pending': 4,
            'confirmed': 10,
            'in_progress': 9,
            'completed': 1,
            'cancelled': 1
        }
        for record in self:
            record.color = color_map.get(record.state, 0)

    @api.depends('duration', 'expected_attendees')
    def _compute_require_approval(self):
        """Tự động xác định cần phê duyệt hay không"""
        for record in self:
            # Yêu cầu phê duyệt nếu: thời gian > 4h hoặc > 20 người
            record.require_approval = record.duration > 4 or record.expected_attendees > 20

    @api.depends('require_approval', 'expected_attendees')
    def _compute_approval_level(self):
        """Xác định cấp phê duyệt"""
        for record in self:
            if not record.require_approval:
                record.approval_level = False
            elif record.expected_attendees > 50:
                record.approval_level = 'director'
            elif record.expected_attendees > 20:
                record.approval_level = 'manager'
            else:
                record.approval_level = 'admin'

    # === KIỂM TRA XUNG ĐỘT THỜI GIAN ===
    @api.depends('room_id', 'start_time', 'end_time', 'state')
    def _compute_has_conflict(self):
        """Tính toán xung đột"""
        for record in self:
            # Bỏ qua NewId (record chưa được save)
            if not record.id or isinstance(record.id, models.NewId):
                record.has_conflict = False
                record.conflict_count = 0
                continue
                
            if record.state in ['cancelled'] or not record.room_id or not record.start_time or not record.end_time:
                record.has_conflict = False
                record.conflict_count = 0
                continue
            
            conflicts = self._get_conflicting_bookings(record)
            record.has_conflict = bool(conflicts)
            record.conflict_count = len(conflicts)

    def _get_conflicting_bookings(self, record):
        """Lấy danh sách booking xung đột"""
        # Build base domain for overlapping bookings in same room
        domain = [
            ('room_id', '=', record.room_id.id),
            ('state', 'not in', ['cancelled', 'completed']),
            '|', '|',
            '&', ('start_time', '<=', record.start_time), ('end_time', '>', record.start_time),
            '&', ('start_time', '<', record.end_time), ('end_time', '>=', record.end_time),
            '&', ('start_time', '>=', record.start_time), ('end_time', '<=', record.end_time)
        ]

        # If the record is already persisted in DB, exclude itself from the search.
        # New records created in the client have temporary ids like 'NewId_xxx' which
        # are not valid integers for SQL and will break the query if passed directly.
        if record.exists() and record.id:
            domain.insert(0, ('id', '!=', record.id))

        return self.search(domain)

    @api.constrains('start_time', 'end_time')
    def _check_time_validity(self):
        """Kiểm tra tính hợp lệ của thời gian"""
        for record in self:
            if record.start_time and record.end_time:
                if record.end_time <= record.start_time:
                    raise ValidationError(_('Thời gian kết thúc phải sau thời gian bắt đầu!'))
                
                if record.duration < 0.25:
                    raise ValidationError(_('Thời gian họp tối thiểu là 15 phút!'))
                
                if record.duration > 12:
                    raise ValidationError(_('Thời gian họp tối đa là 12 giờ!'))

    @api.constrains('room_id', 'start_time', 'end_time', 'state')
    def _check_room_availability(self):
        """Kiểm tra xung đột lịch - BLOCK nếu có xung đột với booking đã xác nhận"""
        for record in self:
            if record.state in ['cancelled', 'completed']:
                continue
            
            conflicts = self._get_conflicting_bookings(record)
            if conflicts:
                # Lọc chỉ các booking đã confirmed hoặc đang diễn ra
                confirmed_conflicts = conflicts.filtered(lambda b: b.state in ['confirmed', 'in_progress'])
                
                if confirmed_conflicts:
                    # Có xung đột với booking đã xác nhận -> BLOCK
                    conflict_info = '\n'.join([
                        f"• {b.name} - {b.subject} ({b.start_time.strftime('%d/%m/%Y %H:%M')} - {b.end_time.strftime('%H:%M')})"
                        for b in confirmed_conflicts[:5]  # Chỉ hiển thị 5 booking đầu
                    ])
                    raise ValidationError(
                        _('❌ Phòng "%s" đã có lịch họp trong khoảng thời gian này!\n\n'
                          'Các booking xung đột:\n%s\n\n'
                          'Vui lòng chọn thời gian khác hoặc phòng khác.')
                        % (record.room_id.name, conflict_info)
                    )
                else:
                    # Chỉ xung đột với booking draft/pending -> Cảnh báo
                    conflict_info = '\n'.join([
                        f"• {b.name} - {b.subject} ({b.start_time.strftime('%d/%m/%Y %H:%M')} - {b.end_time.strftime('%H:%M')}) - Trạng thái: {dict(b._fields['state'].selection).get(b.state)}"
                        for b in conflicts
                    ])
                    record.message_post(
                        body=f"⚠️ Cảnh báo: Phòng có {len(conflicts)} yêu cầu đặt phòng khác trong thời gian này:\n{conflict_info}",
                        message_type='comment'
                    )

    @api.constrains('expected_attendees', 'room_id')
    def _check_room_capacity(self):
        """Kiểm tra sức chứa phòng"""
        for record in self:
            if record.expected_attendees and record.room_id and record.room_id.capacity:
                if record.expected_attendees > record.room_id.capacity:
                    raise ValidationError(
                        _('Số người dự kiến (%d) vượt quá sức chứa của phòng (%d người)!\n\n'
                          'Vui lòng giảm số người hoặc chọn phòng lớn hơn.')
                        % (record.expected_attendees, record.room_id.capacity)
                    )

    # === WORKFLOW PHÊ DUYỆT ===
    def action_submit_for_approval(self):
        """Gửi yêu cầu phê duyệt"""
        for record in self:
            if record.state != 'draft':
                raise UserError(_('Chỉ có thể gửi phê duyệt ở trạng thái Nháp!'))
            
            # Kiểm tra xung đột nghiêm trọng trước khi submit
            conflicts = self._get_conflicting_bookings(record)
            confirmed_conflicts = conflicts.filtered(lambda b: b.state == 'confirmed')
            if confirmed_conflicts:
                raise ValidationError(
                    _('Không thể gửi phê duyệt vì có booking đã xác nhận xung đột!\n\n'
                      'Vui lòng chọn thời gian khác.')
                )
            
            record.write({'state': 'pending'})
            record._notify_approvers()
        return True

    def action_approve(self):
        """Phê duyệt đặt phòng"""
        for record in self:
            if record.state != 'pending':
                raise UserError(_('Chỉ có thể phê duyệt booking ở trạng thái Chờ duyệt!'))
            
            record.write({
                'state': 'confirmed',
                'approved_by_id': self.env.user.id,
                'approved_date': fields.Datetime.now()
            })
            record._send_confirmation_email()
        return True

    def action_reject(self):
        """Từ chối đặt phòng"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Từ chối đặt phòng',
            'res_model': 'meeting.booking.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_booking_ids': self.ids}
        }

    # === QUẢN LÝ THIẾT BỊ ===
    def action_prepare_equipment(self):
        """Đánh dấu thiết bị đã chuẩn bị"""
        for record in self:
            if not record.equipment_ids:
                raise UserError(_('Không có thiết bị nào được yêu cầu!'))
            
            # Kiểm tra thiết bị còn available không
            unavailable = record.equipment_ids.filtered(lambda e: e.state != 'available')
            if unavailable:
                raise UserError(
                    _('Các thiết bị sau không còn sẵn sàng:\n%s')
                    % '\n'.join(unavailable.mapped('name'))
                )
            
            record.write({
                'equipment_prepared': True,
                'equipment_checked_by': self.env.user.id,
                'equipment_checked_date': fields.Datetime.now()
            })
            
            # Chuyển trạng thái thiết bị sang in_use
            record.equipment_ids.write({'state': 'in_use'})
        return True

    def action_return_equipment(self):
        """Trả lại thiết bị"""
        for record in self:
            record.equipment_ids.write({'state': 'available'})
            record.write({'equipment_prepared': False})
        return True

    def action_report_equipment_issue(self):
        """Báo cáo sự cố thiết bị"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Báo cáo sự cố thiết bị',
            'res_model': 'equipment.issue.report.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_booking_id': self.id,
                'default_equipment_ids': [(6, 0, self.equipment_ids.ids)]
            }
        }

    # === CHECK-IN/CHECK-OUT ===
    def action_check_in(self):
        """Check-in cuộc họp"""
        for record in self:
            if record.state != 'confirmed':
                raise UserError(_('Chỉ có thể check-in booking đã xác nhận!'))
            
            record.write({
                'state': 'in_progress',
                'check_in_time': fields.Datetime.now()
            })
            
            # Chuẩn bị thiết bị tự động nếu chưa
            if record.equipment_ids and not record.equipment_prepared:
                record.action_prepare_equipment()
        return True

    def action_check_out(self):
        """Check-out cuộc họp"""
        for record in self:
            if record.state != 'in_progress':
                raise UserError(_('Chỉ có thể check-out booking đang diễn ra!'))
            
            record.write({
                'state': 'completed',
                'check_out_time': fields.Datetime.now()
            })
            
            # Trả lại thiết bị tự động
            if record.equipment_ids and record.equipment_prepared:
                record.action_return_equipment()
            
            # Mở form đánh giá
            return record.action_feedback()
        return True

    def action_feedback(self):
        """Mở form đánh giá"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Đánh giá cuộc họp',
            'res_model': 'meeting.booking.feedback.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_booking_id': self.id}
        }

    def action_cancel(self):
        """Hủy đặt phòng"""
        for record in self:
            if record.state in ['completed', 'cancelled']:
                raise UserError(_('Không thể hủy booking đã hoàn thành hoặc đã hủy!'))
            
            record.write({'state': 'cancelled'})
            
            # Trả lại thiết bị nếu có
            if record.equipment_prepared:
                record.action_return_equipment()
            
            record._send_cancellation_email()
        return True

    # === GỢI Ý PHÒNG THAY THẾ ===
    def action_suggest_alternatives(self):
        """Gợi ý phòng thay thế"""
        self.ensure_one()
        
        RoomModel = self.env['meeting.room']
        
        # Tìm phòng phù hợp về sức chứa
        suitable_rooms = RoomModel.search([
            ('capacity', '>=', self.expected_attendees or 1),
            ('state', '=', 'available')
        ])
        
        # Lọc phòng không xung đột
        free_rooms = []
        for room in suitable_rooms:
            # Tạo booking tạm để kiểm tra
            temp_booking = self.new({
                'room_id': room.id,
                'start_time': self.start_time,
                'end_time': self.end_time,
                'state': 'draft'
            })
            
            conflicts = self._get_conflicting_bookings(temp_booking)
            if not conflicts:
                free_rooms.append(room.id)
        
        if not free_rooms:
            raise UserError(
                _('Không tìm thấy phòng trống phù hợp!\n\n'
                  'Vui lòng thử:\n'
                  '• Chọn khung giờ khác\n'
                  '• Giảm số người tham dự\n'
                  '• Liên hệ hành chính để hỗ trợ')
            )
        
        return {
            'type': 'ir.actions.act_window',
            'name': f'Phòng gợi ý ({len(free_rooms)} phòng)',
            'res_model': 'meeting.room',
            'view_mode': 'kanban,tree,form',
            'domain': [('id', 'in', free_rooms)],
            'context': {
                'search_default_available': 1,
                'suggested_for_booking': self.id
            }
        }

    # === NOTIFICATIONS ===
    def _notify_approvers(self):
        """Thông báo cho người phê duyệt"""
        # TODO: Implement notification
        pass

    def _send_confirmation_notification(self):
        """Gửi thông báo xác nhận đặt phòng thành công"""
        self.ensure_one()
        
        # Tạo message xác nhận trong chatter
        message_body = f"""
            <div style="background: #d4edda; padding: 15px; border-radius: 8px; border-left: 4px solid #28a745;">
                <h3 style="color: #155724; margin: 0 0 10px 0;">✅ ĐẶT PHÒNG THÀNH CÔNG!</h3>
                <table style="width: 100%; color: #155724;">
                    <tr><td><strong>Mã đặt phòng:</strong></td><td>{self.name}</td></tr>
                    <tr><td><strong>Phòng:</strong></td><td>{self.room_id.name}</td></tr>
                    <tr><td><strong>Chủ đề:</strong></td><td>{self.subject}</td></tr>
                    <tr><td><strong>Thời gian:</strong></td><td>{self.start_time.strftime('%d/%m/%Y %H:%M')} - {self.end_time.strftime('%H:%M')}</td></tr>
                    <tr><td><strong>Số người:</strong></td><td>{self.expected_attendees or 'Chưa xác định'}</td></tr>
                    <tr><td><strong>Người đặt:</strong></td><td>{self.booker_id.name}</td></tr>
                    <tr><td><strong>Trạng thái:</strong></td><td>✔ Đã xác nhận (Tự động duyệt)</td></tr>
                </table>
            </div>
        """
        
        self.message_post(
            body=message_body,
            message_type='notification',
            subtype_xmlid='mail.mt_note'
        )
        
        # Tạo activity nhắc nhở trước 30 phút
        if self.start_time:
            reminder_time = self.start_time - timedelta(minutes=30)
            if reminder_time > fields.Datetime.now():
                self.activity_schedule(
                    'mail.mail_activity_data_todo',
                    date_deadline=reminder_time.date(),
                    summary=f'Nhắc nhở: Cuộc họp "{self.subject}" sắp bắt đầu',
                    user_id=self.booker_id.user_id.id if self.booker_id.user_id else self.env.user.id
                )

    def _send_confirmation_email(self):
        """Gửi email xác nhận"""
        # TODO: Implement email sending
        pass

    def _send_cancellation_email(self):
        """Gửi email hủy"""
        # TODO: Implement email sending
        pass

    def _get_current_employee(self):
        """Lấy nhân viên hiện tại"""
        return self.env['hr.employee.extended'].search([
            ('user_id', '=', self.env.user.id)
        ], limit=1).id

    # === AUTO ACTIONS ===
    @api.model
    def _cron_auto_cancel_no_checkin(self):
        """Tự động hủy booking không check-in sau 15 phút"""
        now = fields.Datetime.now()
        bookings = self.search([
            ('state', '=', 'confirmed'),
            ('auto_cancel_if_no_checkin', '=', True),
            ('start_time', '<', now - timedelta(minutes=15)),
            ('check_in_time', '=', False)
        ])
        
        for booking in bookings:
            booking.write({
                'state': 'cancelled',
                'rejection_reason': 'Tự động hủy do không check-in sau 15 phút'
            })
            booking.message_post(
                body='🚫 Booking tự động bị hủy do không check-in đúng giờ.',
                message_type='notification'
            )

    @api.model
    def _cron_auto_complete(self):
        """Tự động hoàn thành booking đã kết thúc"""
        now = fields.Datetime.now()
        bookings = self.search([
            ('state', '=', 'in_progress'),
            ('end_time', '<', now)
        ])
        
        for booking in bookings:
            booking.action_check_out()

    @api.model
    def _check_ongoing_meetings(self):
        """Cập nhật trạng thái cuộc họp đang diễn ra"""
        now = fields.Datetime.now()
        
        # Tự động chuyển sang in_progress
        confirmed_meetings = self.search([
            ('state', '=', 'confirmed'),
            ('start_time', '<=', now),
            ('end_time', '>', now)
        ])
        
        for meeting in confirmed_meetings:
            meeting.write({'state': 'in_progress'})
    
    # === TELEGRAM NOTIFICATION ===
    def _send_telegram_notification(self, event_type, old_state=None):
        """
        Gửi thông báo Telegram cho người liên quan
        :param event_type: Loại sự kiện ('created', 'state_changed', 'reminder')
        :param old_state: Trạng thái cũ (nếu là state_changed)
        """
        self.ensure_one()
        
        # Kiểm tra xem có bật thông báo Telegram không
        telegram_enabled = self.env['ir.config_parameter'].sudo().get_param(
            'nhan_su.telegram_notification_enabled', default=False
        )
        
        if not telegram_enabled:
            return
        
        telegram_helper = self.env['telegram.helper']
        
        # Lấy danh sách người nhận thông báo
        recipients = self._get_telegram_recipients()
        
        if not recipients:
            return
        
        # Tạo nội dung thông báo
        message = telegram_helper.format_booking_notification(self)
        
        # Thêm thông tin về sự kiện
        if event_type == 'created':
            message = '🆕 <b>ĐẶT PHÒNG MỚI</b>\n\n' + message
        elif event_type == 'state_changed':
            state_names = {
                'draft': 'Nháp',
                'pending': 'Chờ duyệt',
                'confirmed': 'Đã xác nhận',
                'in_progress': 'Đang diễn ra',
                'completed': 'Hoàn thành',
                'cancelled': 'Đã hủy'
            }
            old_state_name = state_names.get(old_state, old_state)
            new_state_name = state_names.get(self.state, self.state)
            message = f'🔄 <b>CẬP NHẬT ĐẶT PHÒNG</b>\n\n📊 Trạng thái: {old_state_name} → {new_state_name}\n\n' + message
        elif event_type == 'reminder':
            message = '⏰ <b>NHẮC NHỞ CUỘC HỌP</b>\n\n' + message
        
        # Gửi thông báo đến từng người
        for recipient in recipients:
            if recipient.telegram_chat_id and recipient.telegram_enabled:
                telegram_helper.send_message(recipient.telegram_chat_id, message)
    
    def _get_telegram_recipients(self):
        """
        Lấy danh sách người nhận thông báo Telegram
        :return: recordset hr.employee.extended
        """
        self.ensure_one()
        
        recipients = self.env['hr.employee.extended']
        
        # Người đặt phòng
        if self.booker_id:
            recipients |= self.booker_id
        
        # Người tổ chức
        if self.organizer_id and self.organizer_id != self.booker_id:
            recipients |= self.organizer_id
        
        # Người tham dự
        if self.attendee_ids:
            recipients |= self.attendee_ids
        
        # Người quản lý phòng (nếu có)
        if self.room_id.manager_id and self.room_id.manager_id.id:
            manager_employee = self.env['hr.employee.extended'].search([
                ('name', '=', self.room_id.manager_id.name)
            ], limit=1)
            if manager_employee:
                recipients |= manager_employee
        
        return recipients.filtered(lambda r: r.telegram_chat_id and r.telegram_enabled)
    
    def action_send_telegram_reminder(self):
        """Gửi nhắc nhở qua Telegram (có thể gọi thủ công hoặc từ cron)"""
        for booking in self:
            booking._send_telegram_notification('reminder')
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Thành công!'),
                'message': _('Đã gửi nhắc nhở đến %s người') % len(self._get_telegram_recipients()),
                'type': 'success',
                'sticky': False,
            }
        }
    
    @api.model
    def _cron_send_meeting_reminders(self):
        """
        Cron job: Gửi nhắc nhở trước 30 phút
        Chạy mỗi 15 phút
        """
        now = fields.Datetime.now()
        reminder_time = now + timedelta(minutes=30)
        
        # Tìm các booking sắp diễn ra trong 30-45 phút nữa
        upcoming_bookings = self.search([
            ('state', '=', 'confirmed'),
            ('start_time', '>=', now),
            ('start_time', '<=', reminder_time)
        ])
        
        for booking in upcoming_bookings:
            booking._send_telegram_notification('reminder')

        
        # Tự động chuyển sang in_progress nếu đã check-in và đến giờ bắt đầu
        confirmed_bookings = self.search([
            ('state', '=', 'confirmed'),
            ('check_in_time', '!=', False),
            ('start_time', '<=', now),
            ('end_time', '>', now)
        ])
        for booking in confirmed_bookings:
            booking.write({'state': 'in_progress'})
        
        # Tự động hủy nếu không check-in
        self._cron_auto_cancel_no_checkin()
        
        # Tự động hoàn thành nếu đã qua giờ kết thúc
        self._cron_auto_complete()
