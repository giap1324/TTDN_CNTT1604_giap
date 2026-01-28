# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime


class AssetMaintenanceHistory(models.Model):
    _name = 'asset.maintenance.history'
    _description = 'Lịch Sử Bảo Trì Tài Sản'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'maintenance_date desc'

    # Tài sản
    asset_id = fields.Many2one(
        'asset',
        string='Tài sản',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    asset_category_id = fields.Many2one(
        'asset.category',
        related='asset_id.category_id',
        string='Danh mục',
        store=True
    )
    
    # Thông tin bảo trì
    maintenance_date = fields.Date(
        string='Ngày bảo trì',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    maintenance_type = fields.Selection([
        ('preventive', 'Bảo trì định kỳ'),
        ('corrective', 'Sửa chữa'),
        ('replacement', 'Thay thế'),
        ('inspection', 'Kiểm tra')
    ], string='Loại bảo trì', required=True, default='preventive', tracking=True)
    
    # Chi phí thực tế
    actual_cost = fields.Monetary(
        string='Chi phí thực tế',
        required=True,
        tracking=True,
        help='Chi phí bảo trì thực tế đã phát sinh'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Tiền tệ',
        default=lambda self: self.env.company.currency_id
    )
    
    # Liên kết với dự đoán
    prediction_id = fields.Many2one(
        'asset.maintenance.prediction',
        string='Dự đoán liên quan',
        ondelete='set null',
        help='Dự đoán AI đã tạo cho lần bảo trì này'
    )
    predicted_cost = fields.Monetary(
        string='Chi phí dự đoán',
        tracking=True,
        help='Chi phí bảo trì do AI dự đoán trước khi thực hiện'
    )
    cost_variance = fields.Monetary(
        string='Chênh lệch chi phí',
        compute='_compute_cost_variance',
        store=True,
        help='Chi phí thực tế - Chi phí dự đoán'
    )
    variance_percent = fields.Float(
        string='% Chênh lệch',
        compute='_compute_cost_variance',
        store=True,
        digits=(5, 2)
    )
    
    # Chi tiết công việc
    description = fields.Text(
        string='Mô tả công việc',
        required=True,
        tracking=True,
        help='Mô tả chi tiết công việc bảo trì đã thực hiện'
    )
    technician_id = fields.Many2one(
        'hr.employee.extended',
        string='Kỹ thuật viên',
        tracking=True
    )
    duration_hours = fields.Float(
        string='Thời gian (giờ)',
        tracking=True,
        help='Số giờ thực hiện bảo trì'
    )
    
    # Phụ tùng và vật tư
    parts_replaced = fields.Text(
        string='Phụ tùng thay thế',
        help='Danh sách phụ tùng/vật tư đã thay thế'
    )
    parts_cost = fields.Monetary(
        string='Chi phí phụ tùng',
        help='Tổng chi phí phụ tùng và vật tư'
    )
    labor_cost = fields.Monetary(
        string='Chi phí nhân công',
        help='Chi phí công lao động'
    )
    
    # Kết quả
    result = fields.Selection([
        ('success', 'Thành công'),
        ('partial', 'Một phần'),
        ('failed', 'Thất bại'),
        ('pending', 'Cần theo dõi')
    ], string='Kết quả', default='success', tracking=True)
    
    notes = fields.Text(string='Ghi chú')
    
    # Dự đoán cho lần tiếp theo
    next_predicted_date = fields.Date(
        string='Dự đoán lần tiếp theo',
        help='Ngày dự kiến bảo trì tiếp theo dựa trên lần này'
    )
    
    # Trạng thái
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('done', 'Hoàn thành'),
        ('cancelled', 'Hủy')
    ], string='Trạng thái', default='draft', tracking=True)

    @api.depends('actual_cost', 'predicted_cost')
    def _compute_cost_variance(self):
        for record in self:
            if record.predicted_cost and record.predicted_cost > 0 and record.actual_cost:
                record.cost_variance = record.actual_cost - record.predicted_cost
                record.variance_percent = (record.cost_variance / record.predicted_cost) * 100
            else:
                record.cost_variance = 0
                record.variance_percent = 0

    @api.model
    def create(self, vals):
        """Tự động lấy chi phí dự đoán từ AI khi tạo record mới"""
        record = super().create(vals)
        # Nếu chưa có predicted_cost, tự động lấy từ AI
        if not record.predicted_cost or record.predicted_cost == 0:
            record._auto_fill_predicted_cost()
        return record
    
    def write(self, vals):
        """Cập nhật predicted_cost nếu thay đổi asset_id"""
        res = super().write(vals)
        if 'asset_id' in vals:
            for record in self:
                if not record.predicted_cost or record.predicted_cost == 0:
                    record._auto_fill_predicted_cost()
        return res
    
    def _auto_fill_predicted_cost(self):
        """Tự động lấy chi phí dự đoán từ AI prediction mới nhất"""
        for record in self:
            if not record.asset_id:
                continue
            
            # Tìm dự đoán mới nhất cho tài sản này
            Prediction = self.env['asset.maintenance.prediction']
            prediction = Prediction.search([
                ('asset_id', '=', record.asset_id.id),
                ('state', '!=', 'cancelled')
            ], order='prediction_date desc', limit=1)
            
            if prediction and prediction.predicted_cost > 0:
                record.predicted_cost = prediction.predicted_cost
                record.prediction_id = prediction.id
    
    def action_update_predicted_cost(self):
        """Button để cập nhật chi phí dự đoán từ AI"""
        for record in self:
            record._auto_fill_predicted_cost()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('✅ Đã cập nhật'),
                'message': _('Đã lấy chi phí dự đoán từ AI'),
                'type': 'success',
            }
        }

    @api.constrains('actual_cost')
    def _check_actual_cost(self):
        for record in self:
            if record.actual_cost < 0:
                raise ValidationError(_('Chi phí thực tế phải lớn hơn hoặc bằng 0!'))

    @api.constrains('duration_hours')
    def _check_duration(self):
        for record in self:
            if record.duration_hours and record.duration_hours < 0:
                raise ValidationError(_('Thời gian phải lớn hơn 0!'))

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.asset_id.name} - {record.maintenance_date}"
            result.append((record.id, name))
        return result

    def action_done(self):
        """Đánh dấu hoàn thành và trigger retrain AI nếu đủ dữ liệu"""
        self.ensure_one()
        self.state = 'done'
        
        # Kiểm tra số lượng maintenance history
        total_history = self.search_count([('state', '=', 'done')])
        
        if total_history >= 50 and total_history % 10 == 0:
            # Mỗi 10 records mới, gợi ý retrain
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': '🤖 AI Training',
                    'message': f'Đã có {total_history} lịch sử bảo trì. Nên train lại AI để cải thiện độ chính xác!',
                    'type': 'info',
                    'sticky': True,
                    'next': {
                        'type': 'ir.actions.act_window',
                        'res_model': 'asset.maintenance.prediction',
                    }
                }
            }
        
        self.message_post(
            body=f"Hoàn thành bảo trì {self.maintenance_type}. Chi phí: {self.actual_cost:,.0f} {self.currency_id.symbol}"
        )

    def action_cancel(self):
        """Hủy bỏ"""
        self.ensure_one()
        self.state = 'cancelled'

    @api.model
    def get_accuracy_report(self):
        """Báo cáo độ chính xác của AI predictions"""
        histories = self.search([
            ('state', '=', 'done'),
            ('prediction_id', '!=', False),
            ('predicted_cost', '>', 0)
        ])
        
        if not histories:
            return {
                'total': 0,
                'message': 'Chưa có dữ liệu so sánh'
            }
        
        total = len(histories)
        accurate_count = len(histories.filtered(lambda h: abs(h.variance_percent) <= 20))
        accuracy_rate = (accurate_count / total) * 100
        avg_variance = sum(histories.mapped('variance_percent')) / total
        
        return {
            'total': total,
            'accurate_count': accurate_count,
            'accuracy_rate': accuracy_rate,
            'avg_variance_percent': avg_variance,
            'message': f'Độ chính xác AI: {accuracy_rate:.1f}% ({accurate_count}/{total} dự đoán trong khoảng ±20%)'
        }
