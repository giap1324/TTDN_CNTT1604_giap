# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AssetLocation(models.Model):
    _name = 'asset.location'
    _description = 'Vị Trí Tài Sản'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Tên vị trí', required=True, tracking=True)
    code = fields.Char(string='Mã vị trí', tracking=True)
    address = fields.Text(string='Địa chỉ', tracking=True)
    description = fields.Text(string='Mô tả', tracking=True)
    
    # Quan hệ
    asset_ids = fields.One2many('asset', 'location_id', string='Danh sách tài sản')
    meeting_room_ids = fields.One2many('meeting.room', 'location_id', string='Danh sách phòng họp')

    def name_get(self):
        result = []
        for record in self:
            name = record.name
            if record.code:
                name = f"[{record.code}] {name}"
            # Thêm số phòng họp nếu có
            room_count = len(record.meeting_room_ids)
            if room_count > 0:
                # Nếu location được gắn code 'PARK' hoặc tên chứa 'Bãi đỗ xe',
                # hiển thị tên theo tầng (nếu có thông tin floor trong meeting.room)
                if (record.code and record.code.upper() == 'PARK') or ('bãi đỗ xe' in (record.name or '').lower()):
                    # Lấy floor phổ biến nhất từ các phòng họp liên quan
                    floors = [r.floor for r in record.meeting_room_ids.mapped(lambda r: r) if r.floor]
                    if floors:
                        # chọn floor xuất hiện nhiều nhất
                        from collections import Counter
                        floor_counter = Counter(floors)
                        common_floor, cnt = floor_counter.most_common(1)[0]
                        name = f"Văn phòng Tầng {common_floor} ({room_count} phòng)"
                    else:
                        name += f" ({room_count} phòng)"
                else:
                    name += f" ({room_count} phòng)"
            result.append((record.id, name))
        return result
