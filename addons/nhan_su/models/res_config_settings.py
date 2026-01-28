# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    telegram_bot_token = fields.Char(
        string='Telegram Bot Token',
        help='Token của Telegram Bot để gửi thông báo. Lấy từ @BotFather'
    )
    
    telegram_notification_enabled = fields.Boolean(
        string='Bật thông báo Telegram',
        default=False,
        help='Tự động gửi thông báo qua Telegram khi có đặt phòng'
    )
    
    telegram_test_chat_id = fields.Char(
        string='Test Chat ID',
        help='Chat ID để test gửi tin nhắn'
    )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        
        res.update(
            telegram_bot_token=params.get_param('nhan_su.telegram_bot_token', default=''),
            telegram_notification_enabled=params.get_param('nhan_su.telegram_notification_enabled', default=False),
            telegram_test_chat_id=params.get_param('nhan_su.telegram_test_chat_id', default=''),
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        params = self.env['ir.config_parameter'].sudo()
        
        params.set_param('nhan_su.telegram_bot_token', self.telegram_bot_token or '')
        params.set_param('nhan_su.telegram_notification_enabled', self.telegram_notification_enabled)
        params.set_param('nhan_su.telegram_test_chat_id', self.telegram_test_chat_id or '')

    def action_test_telegram_connection(self):
        """Test kết nối Telegram Bot"""
        self.ensure_one()
        
        telegram_helper = self.env['telegram.helper']
        result = telegram_helper.test_connection(self.telegram_test_chat_id)
        
        if result['success']:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Thành công!'),
                    'message': result['message'],
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            raise UserError(result['message'])
    
    def action_send_test_notification(self):
        """Gửi tin nhắn test đến tất cả nhân viên có telegram_chat_id"""
        self.ensure_one()
        
        employees = self.env['hr.employee.extended'].search([
            ('telegram_chat_id', '!=', False)
        ])
        
        if not employees:
            raise UserError(_('Không có nhân viên nào có Telegram Chat ID!'))
        
        telegram_helper = self.env['telegram.helper']
        success_count = 0
        
        for employee in employees:
            message = f"""
🔔 <b>TEST NOTIFICATION</b>

Xin chào <b>{employee.name}</b>!

Đây là tin nhắn test từ hệ thống Odoo.
Nếu bạn nhận được tin nhắn này, thông báo Telegram đã hoạt động! ✅

⏰ Thời gian: {fields.Datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
"""
            
            if telegram_helper.send_message(employee.telegram_chat_id, message):
                success_count += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Hoàn thành!'),
                'message': f'Đã gửi thành công {success_count}/{len(employees)} tin nhắn test',
                'type': 'success',
                'sticky': False,
            }
        }
