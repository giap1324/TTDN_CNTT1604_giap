# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

try:
    import numpy as np
    import pandas as pd
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False


class AssetCostAnalysis(models.TransientModel):
    """Wizard để phân tích chi phí và dự đoán"""
    _name = 'asset.cost.analysis.wizard'
    _description = 'Phân Tích Chi Phí Tài Sản'

    # Bộ lọc
    category_ids = fields.Many2many('asset.category', string='Danh mục')
    location_ids = fields.Many2many('asset.location', string='Vị trí')
    date_from = fields.Date(string='Từ ngày', default=lambda self: fields.Date.today() - timedelta(days=365))
    date_to = fields.Date(string='Đến ngày', default=fields.Date.today)
    
    # Tùy chọn dự đoán
    forecast_months = fields.Integer(string='Số tháng dự báo', default=3)
    include_replacement = fields.Boolean(string='Bao gồm chi phí thay thế', default=True)
    
    # Kết quả (computed)
    total_current_value = fields.Monetary(string='Tổng giá trị hiện tại', compute='_compute_analysis')
    total_predicted_cost = fields.Monetary(string='Tổng chi phí dự kiến', compute='_compute_analysis')
    high_risk_count = fields.Integer(string='Số tài sản rủi ro cao', compute='_compute_analysis')
    avg_monthly_cost = fields.Monetary(string='Chi phí TB/tháng', compute='_compute_analysis')
    
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    
    analysis_result = fields.Text(string='Kết quả phân tích', compute='_compute_analysis')

    @api.depends('category_ids', 'location_ids', 'date_from', 'date_to')
    def _compute_analysis(self):
        """Tính toán phân tích"""
        for wizard in self:
            # Lấy danh sách tài sản theo bộ lọc
            domain = [('state', 'in', ['available', 'in_use', 'maintenance'])]
            
            if wizard.category_ids:
                domain.append(('category_id', 'in', wizard.category_ids.ids))
            if wizard.location_ids:
                domain.append(('location_id', 'in', wizard.location_ids.ids))
            
            assets = self.env['asset'].search(domain)
            
            # Tính toán
            total_value = sum(assets.mapped('current_value'))
            
            # Lấy predictions
            predictions = self.env['asset.maintenance.prediction'].search([
                ('asset_id', 'in', assets.ids),
                ('state', '!=', 'cancelled')
            ])
            
            total_predicted = sum(predictions.mapped('predicted_cost'))
            high_risk = predictions.filtered(lambda p: p.risk_level in ['high', 'critical'])
            
            # Tính chi phí trung bình
            months_diff = (wizard.date_to - wizard.date_from).days / 30
            avg_monthly = total_predicted / months_diff if months_diff > 0 else 0
            
            wizard.total_current_value = total_value
            wizard.total_predicted_cost = total_predicted
            wizard.high_risk_count = len(high_risk)
            wizard.avg_monthly_cost = avg_monthly
            
            # Tạo báo cáo text
            wizard.analysis_result = wizard._generate_report(assets, predictions, high_risk)

    def _generate_report(self, assets, predictions, high_risk):
        """Tạo báo cáo chi tiết"""
        # Xử lý trường hợp không có tài sản
        if not assets:
            return """
📊 BÁO CÁO PHÂN TÍCH CHI PHÍ TÀI SẢN
{"="*60}

⚠️ KHÔNG CÓ DỮ LIỆU

Không tìm thấy tài sản nào phù hợp với bộ lọc đã chọn.
Vui lòng:
   • Chọn danh mục tài sản khác
   • Điều chỉnh khoảng thời gian
   • Kiểm tra tài sản đã được tạo chưa
"""
        
        avg_value_per_asset = self.total_current_value / len(assets) if len(assets) > 0 else 0
        risk_percentage = (len(high_risk) / len(assets) * 100) if len(assets) > 0 else 0
        
        report = f"""
📊 BÁO CÁO PHÂN TÍCH CHI PHÍ TÀI SẢN
{"="*60}

1. TỔNG QUAN
   • Số lượng tài sản: {len(assets)}
   • Tổng giá trị: {self.total_current_value:,.0f} VNĐ
   • Giá trị TB/tài sản: {avg_value_per_asset:,.0f} VNĐ

2. DỰ ĐOÁN CHI PHÍ BẢO TRÌ
   • Tổng chi phí dự kiến: {self.total_predicted_cost:,.0f} VNĐ
   • Chi phí TB/tháng: {self.avg_monthly_cost:,.0f} VNĐ
   • Chi phí dự báo {self.forecast_months} tháng: {self.avg_monthly_cost * self.forecast_months:,.0f} VNĐ

3. ĐÁNH GIÁ RỦI RO
   • Tài sản rủi ro cao: {len(high_risk)}/{len(assets)}
   • Tỷ lệ: {risk_percentage:.1f}%

4. KHUYẾN NGHỊ
"""
        # Thêm khuyến nghị
        if len(high_risk) > len(assets) * 0.3:
            report += "   ⚠️ Cảnh báo: >30% tài sản có rủi ro cao!\n"
            report += "   → Nên lên kế hoạch thay thế hoặc bảo trì khẩn cấp\n"
        
        if self.avg_monthly_cost > self.total_current_value * 0.05:
            report += "   ⚠️ Chi phí bảo trì cao (>5% giá trị)\n"
            report += "   → Xem xét tối ưu hóa quy trình bảo trì\n"
        
        report += "\n" + "="*60
        
        return report

    def action_generate_predictions(self):
        """Tạo dự đoán cho tất cả tài sản trong phạm vi"""
        self.ensure_one()
        
        # Lấy danh sách tài sản
        domain = [('state', 'in', ['available', 'in_use'])]
        if self.category_ids:
            domain.append(('category_id', 'in', self.category_ids.ids))
        if self.location_ids:
            domain.append(('location_id', 'in', self.location_ids.ids))
        
        assets = self.env['asset'].search(domain)
        
        # Tạo predictions
        PredictionModel = self.env['asset.maintenance.prediction']
        created_predictions = []
        
        for asset in assets:
            try:
                prediction = PredictionModel.predict_maintenance_for_asset(asset.id)
                created_predictions.append(prediction.id)
            except Exception as e:
                _logger.error(f"Lỗi tạo prediction cho {asset.name}: {e}")
        
        return {
            'type': 'ir.actions.act_window',
            'name': f'Dự đoán ({len(created_predictions)} tài sản)',
            'res_model': 'asset.maintenance.prediction',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', created_predictions)],
            'target': 'current',
        }

    def action_export_report(self):
        """Xuất báo cáo ra file"""
        self.ensure_one()
        
        # TODO: Tạo Excel report với pandas
        raise UserError(_('Chức năng xuất báo cáo đang được phát triển.\n\n'
                         'Bạn có thể copy nội dung từ trường "Kết quả phân tích"'))

    def action_schedule_all_maintenance(self):
        """Lên lịch bảo trì cho tất cả tài sản rủi ro cao"""
        self.ensure_one()
        
        # Lấy predictions rủi ro cao
        domain = [
            ('risk_level', 'in', ['high', 'critical']),
            ('state', '=', 'predicted')
        ]
        
        if self.category_ids:
            domain.append(('asset_category_id', 'in', self.category_ids.ids))
        
        high_risk_predictions = self.env['asset.maintenance.prediction'].search(domain)
        
        if not high_risk_predictions:
            raise UserError(_('Không có tài sản rủi ro cao cần lên lịch!'))
        
        # Schedule all
        for pred in high_risk_predictions:
            pred.action_schedule_maintenance()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': f'Đã lên lịch bảo trì cho {len(high_risk_predictions)} tài sản!',
                'type': 'success',
                'sticky': False,
            }
        }


# Removed AssetCategory extension to avoid database issues
# Can be added later when needed
