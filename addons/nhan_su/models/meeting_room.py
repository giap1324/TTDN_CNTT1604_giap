# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class MeetingRoom(models.Model):
    _name = 'meeting.room'
    _description = 'Phòng Họp'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    # Thông tin cơ bản
    name = fields.Char(string='Tên phòng', required=True, tracking=True)
    code = fields.Char(
        string='Mã phòng',
        required=True,
        copy=False,
        default=lambda self: self._generate_room_code(),
        tracking=True
    )
    location_id = fields.Many2one(
        'asset.location',
        string='Vị trí',
        tracking=True
    )
    floor = fields.Char(string='Tầng')
    capacity = fields.Integer(string='Sức chứa (người)', required=True, default=10, tracking=True)
    area = fields.Float(string='Diện tích (m²)')
    manager_id = fields.Many2one('res.users', string='Người quản lý', tracking=True)
    image = fields.Binary(string='Hình ảnh')

    # Trạng thái
    state = fields.Selection([
        ('available', 'Sẵn sàng'),
        ('maintenance', 'Đang bảo trì'),
        ('unavailable', 'Không khả dụng')
    ], string='Trạng thái', default='available', tracking=True, required=True)

    # === THIẾT BỊ CÓ SẴN ===
    has_projector = fields.Boolean(string='Máy chiếu', default=False)
    has_screen = fields.Boolean(string='Màn hình TV', default=False)
    has_sound_system = fields.Boolean(string='Hệ thống âm thanh', default=False)
    has_wifi = fields.Boolean(string='Wifi', default=True)
    has_whiteboard = fields.Boolean(string='Bảng trắng', default=True)
    has_video_conference = fields.Boolean(string='Thiết bị họp trực tuyến', default=False)
    has_air_conditioner = fields.Boolean(string='Điều hòa', default=True)

    equipment_notes = fields.Text(string='Ghi chú thiết bị')
    notes = fields.Text(string='Ghi chú')

    # Danh sách booking
    booking_ids = fields.One2many('meeting.room.booking', 'room_id', string='Lịch đặt phòng')
    
    # Thống kê
    booking_count = fields.Integer(string='Số lần đặt', compute='_compute_booking_count')
    current_booking_id = fields.Many2one('meeting.room.booking', string='Booking hiện tại', compute='_compute_current_booking')
    is_busy = fields.Boolean(string='Đang bận', compute='_compute_current_booking')

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Mã phòng phải là duy nhất!'),
        ('capacity_positive', 'CHECK(capacity > 0)', 'Sức chứa phải lớn hơn 0!')
    ]

    @api.model
    def _generate_room_code(self):
        """Tự động tạo mã phòng"""
        sequence = self.env['ir.sequence'].next_by_code('meeting.room') or '001'
        return f'ROOM-{sequence}'

    @api.depends('booking_ids')
    def _compute_booking_count(self):
        for room in self:
            room.booking_count = len(room.booking_ids)

    @api.depends('booking_ids', 'booking_ids.state', 'booking_ids.start_time', 'booking_ids.end_time')
    def _compute_current_booking(self):
        now = fields.Datetime.now()
        for room in self:
            current_booking = self.env['meeting.room.booking'].search([
                ('room_id', '=', room.id),
                ('state', '=', 'in_progress'),
                ('start_time', '<=', now),
                ('end_time', '>=', now)
            ], limit=1)
            room.current_booking_id = current_booking
            room.is_busy = bool(current_booking)

    def action_maintenance(self):
        """Chuyển sang trạng thái bảo trì"""
        for room in self:
            room.write({'state': 'maintenance'})
        return True

    def action_available(self):
        """Chuyển về trạng thái sẵn sàng"""
        for room in self:
            room.write({'state': 'available'})
        return True

    def action_view_bookings(self):
        """Xem danh sách booking của phòng"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Lịch đặt phòng - {self.name}',
            'res_model': 'meeting.room.booking',
            'view_mode': 'calendar,tree,form',
            'domain': [('room_id', '=', self.id)],
            'context': {
                'default_room_id': self.id,
                'search_default_confirmed': 1
            }
        }

    def action_create_booking(self):
        """Tạo booking mới cho phòng này"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Đặt phòng mới',
            'res_model': 'meeting.room.booking',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_room_id': self.id,
            }
        }

    @api.model
    def get_available_rooms(self, start_time, end_time, min_capacity=0, equipment=None):
        """
        Tìm phòng còn trống trong khoảng thời gian
        :param start_time: Thời gian bắt đầu
        :param end_time: Thời gian kết thúc
        :param min_capacity: Sức chứa tối thiểu
        :param equipment: Dict các thiết bị cần thiết
        :return: recordset of available rooms
        """
        domain = [
            ('state', '=', 'available'),
            ('capacity', '>=', min_capacity)
        ]
        
        # Thêm filter thiết bị
        if equipment:
            if equipment.get('projector'):
                domain.append(('has_projector', '=', True))
            if equipment.get('screen'):
                domain.append(('has_screen', '=', True))
            if equipment.get('sound_system'):
                domain.append(('has_sound_system', '=', True))
            if equipment.get('video_conference'):
                domain.append(('has_video_conference', '=', True))
        
        all_rooms = self.search(domain)
        
        # Lọc phòng không bị xung đột
        available_rooms = self.env['meeting.room']
        for room in all_rooms:
            conflicting_bookings = self.env['meeting.room.booking'].search([
                ('room_id', '=', room.id),
                ('state', 'not in', ['cancelled', 'completed']),
                '|', '|',
                '&', ('start_time', '<=', start_time), ('end_time', '>', start_time),
                '&', ('start_time', '<', end_time), ('end_time', '>=', end_time),
                '&', ('start_time', '>=', start_time), ('end_time', '<=', end_time)
            ])
            if not conflicting_bookings:
                available_rooms |= room
        
        return available_rooms

    def name_get(self):
        """Hiển thị tên phòng kèm sức chứa trong dropdown (ví dụ: "Phòng họp A (10 chỗ)")"""
        result = []
        for room in self:
            name = room.name or ''
            if room.capacity:
                name = f"{name} ({room.capacity} chỗ)"
            result.append((room.id, name))
        return result
