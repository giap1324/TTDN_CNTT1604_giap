# -*- coding: utf-8 -*-

import requests
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class TelegramHelper(models.AbstractModel):
    _name = 'telegram.helper'
    _description = 'Telegram Integration Helper'

    @api.model
    def get_bot_token(self):
        """Lấy Telegram Bot Token từ cấu hình"""
        return self.env['ir.config_parameter'].sudo().get_param('nhan_su.telegram_bot_token', '')

    @api.model
    def send_message(self, chat_id, message, parse_mode='HTML'):
        """
        Gửi tin nhắn đến Telegram
        :param chat_id: ID của chat/user/group Telegram
        :param message: Nội dung tin nhắn (hỗ trợ HTML formatting)
        :param parse_mode: Định dạng tin nhắn ('HTML', 'Markdown', hoặc None)
        :return: True nếu gửi thành công, False nếu thất bại
        """
        bot_token = self.get_bot_token()
        
        if not bot_token:
            _logger.warning('❌ Telegram Bot Token chưa được cấu hình!')
            return False
        
        if not chat_id:
            _logger.warning('❌ Telegram Chat ID trống!')
            return False
        
        url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
        
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': parse_mode
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                _logger.info(f'✅ Đã gửi thông báo Telegram đến chat_id: {chat_id}')
                return True
            else:
                _logger.error(f'❌ Lỗi gửi Telegram: {response.status_code} - {response.text}')
                return False
                
        except requests.exceptions.RequestException as e:
            _logger.error(f'❌ Lỗi kết nối Telegram API: {str(e)}')
            return False
    
    @api.model
    def send_message_with_buttons(self, chat_id, message, buttons):
        """
        Gửi tin nhắn với inline keyboard buttons
        :param chat_id: ID của chat/user/group Telegram
        :param message: Nội dung tin nhắn
        :param buttons: List của list buttons [[{'text': 'Button 1', 'callback_data': 'data1'}]]
        :return: True nếu gửi thành công, False nếu thất bại
        """
        bot_token = self.get_bot_token()
        
        if not bot_token or not chat_id:
            return False
        
        url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
        
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML',
            'reply_markup': {
                'inline_keyboard': buttons
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    @api.model
    def format_booking_notification(self, booking):
        """
        Định dạng thông báo đặt phòng cho Telegram
        :param booking: record meeting.room.booking
        :return: Chuỗi HTML formatted
        """
        state_emoji = {
            'draft': '📝',
            'pending': '⏳',
            'confirmed': '✅',
            'in_progress': '🔄',
            'completed': '🏁',
            'cancelled': '❌'
        }
        
        state_text = {
            'draft': 'Nháp',
            'pending': 'Chờ duyệt',
            'confirmed': 'Đã xác nhận',
            'in_progress': 'Đang diễn ra',
            'completed': 'Hoàn thành',
            'cancelled': 'Đã hủy'
        }
        
        emoji = state_emoji.get(booking.state, '📋')
        state_name = state_text.get(booking.state, booking.state)
        
        # Format thời gian
        start_time = fields.Datetime.context_timestamp(booking, booking.start_time)
        end_time = fields.Datetime.context_timestamp(booking, booking.end_time)
        
        message = f"""
🏢 <b>THÔNG BÁO ĐẶT PHÒNG HỌP</b>

{emoji} <b>Trạng thái:</b> {state_name}
📋 <b>Mã đặt phòng:</b> {booking.name}
💬 <b>Chủ đề:</b> {booking.subject}

🚪 <b>Phòng:</b> {booking.room_id.name}
📍 <b>Vị trí:</b> {booking.room_id.location_id.name if booking.room_id.location_id else 'N/A'}

👤 <b>Người tổ chức:</b> {booking.organizer_id.name}
📝 <b>Người đặt:</b> {booking.booker_id.name}

📅 <b>Bắt đầu:</b> {start_time.strftime('%d/%m/%Y %H:%M')}
⏱️ <b>Kết thúc:</b> {end_time.strftime('%d/%m/%Y %H:%M')}
⏳ <b>Thời lượng:</b> {booking.duration:.1f} giờ

👥 <b>Số người dự kiến:</b> {booking.expected_attendees}
"""
        
        if booking.description:
            message += f"\n📝 <b>Mô tả:</b>\n{booking.description[:200]}"
        
        if booking.has_conflict:
            message += f"\n\n⚠️ <b>CẢNH BÁO:</b> Phát hiện {booking.conflict_count} xung đột thời gian!"
        
        return message.strip()
    
    @api.model
    def test_connection(self, chat_id=None):
        """
        Test kết nối Telegram Bot
        :param chat_id: Chat ID để test (nếu không có sẽ lấy từ admin)
        :return: Dict với kết quả test
        """
        bot_token = self.get_bot_token()
        
        if not bot_token:
            return {
                'success': False,
                'message': '❌ Telegram Bot Token chưa được cấu hình!'
            }
        
        # Test Bot API
        url = f'https://api.telegram.org/bot{bot_token}/getMe'
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'message': f'❌ Bot Token không hợp lệ: {response.text}'
                }
            
            bot_info = response.json().get('result', {})
            bot_name = bot_info.get('username', 'Unknown')
            
            # Nếu có chat_id, thử gửi tin nhắn test
            if chat_id:
                test_msg = f'✅ <b>Test Connection Successful!</b>\n\nBot: @{bot_name}\nTime: {fields.Datetime.now()}'
                success = self.send_message(chat_id, test_msg)
                
                if success:
                    return {
                        'success': True,
                        'message': f'✅ Kết nối thành công!\nBot: @{bot_name}\nĐã gửi tin nhắn test đến chat_id: {chat_id}'
                    }
                else:
                    return {
                        'success': False,
                        'message': f'⚠️ Bot hoạt động nhưng không thể gửi tin đến chat_id: {chat_id}'
                    }
            else:
                return {
                    'success': True,
                    'message': f'✅ Bot Token hợp lệ!\nBot: @{bot_name}'
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'message': f'❌ Lỗi kết nối: {str(e)}'
            }
