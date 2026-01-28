# -*- coding: utf-8 -*-
"""
🔍 ANOMALY DETECTION - Phát hiện chi phí bất thường
Sử dụng: Isolation Forest + Z-Score + Statistical Analysis
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)

try:
    import numpy as np
    import pandas as pd
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    _logger.warning("sklearn not available. Install with: pip install scikit-learn")


class AssetAnomalyDetection(models.Model):
    _name = 'asset.anomaly.detection'
    _description = 'Phát hiện chi phí bất thường'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'detection_date desc, severity desc'
    _rec_name = 'display_name'

    # ===== THÔNG TIN CƠ BẢN =====
    display_name = fields.Char(
        string='Tên hiển thị',
        compute='_compute_display_name',
        store=True
    )
    
    asset_id = fields.Many2one(
        'asset',
        string='Tài sản',
        ondelete='cascade'
    )
    
    category_id = fields.Many2one(
        'asset.category',
        string='Danh mục',
        related='asset_id.category_id',
        store=True
    )
    
    detection_date = fields.Date(
        string='Ngày phát hiện',
        default=fields.Date.today,
        required=True
    )
    
    period_month = fields.Integer(
        string='Tháng',
        help='Tháng có chi phí bất thường'
    )
    
    period_year = fields.Integer(
        string='Năm',
        help='Năm có chi phí bất thường'
    )
    
    # ===== CHI PHÍ & PHÂN TÍCH =====
    actual_cost = fields.Float(
        string='Chi phí thực tế',
        digits=(16, 0),
        help='Chi phí trong tháng phát hiện bất thường'
    )
    
    expected_cost = fields.Float(
        string='Chi phí kỳ vọng',
        digits=(16, 0),
        help='Chi phí trung bình dự kiến'
    )
    
    deviation = fields.Float(
        string='Độ lệch (%)',
        compute='_compute_deviation',
        store=True,
        help='Phần trăm lệch so với kỳ vọng'
    )
    
    z_score = fields.Float(
        string='Z-Score',
        digits=(10, 2),
        help='Điểm Z chuẩn hóa. |Z| > 2: bất thường, |Z| > 3: rất bất thường'
    )
    
    isolation_score = fields.Float(
        string='Isolation Score',
        digits=(10, 4),
        help='Điểm từ Isolation Forest. Gần -1: rất bất thường'
    )
    
    # ===== MỨC ĐỘ NGHIÊM TRỌNG =====
    severity = fields.Selection([
        ('low', '🟡 Thấp'),
        ('medium', '🟠 Trung bình'),
        ('high', '🔴 Cao'),
        ('critical', '⚫ Nghiêm trọng')
    ], string='Mức độ', default='low', required=True)
    
    anomaly_type = fields.Selection([
        ('spike', '📈 Tăng đột biến'),
        ('unusual_pattern', '📊 Mẫu bất thường'),
        ('frequency', '🔄 Tần suất cao'),
        ('category_outlier', '📦 Outlier danh mục'),
        ('seasonal', '📅 Lệch mùa vụ')
    ], string='Loại bất thường', default='spike')
    
    # ===== TRẠNG THÁI XỬ LÝ =====
    state = fields.Selection([
        ('detected', '🔍 Phát hiện'),
        ('investigating', '🔎 Đang điều tra'),
        ('confirmed', '✅ Xác nhận'),
        ('false_positive', '❌ Báo động giả'),
        ('resolved', '✔️ Đã xử lý')
    ], string='Trạng thái', default='detected', required=True)
    
    # ===== GHI CHÚ =====
    description = fields.Text(
        string='Mô tả',
        help='Chi tiết về bất thường'
    )
    
    recommendation = fields.Text(
        string='Khuyến nghị',
        help='Đề xuất hành động'
    )
    
    investigation_notes = fields.Text(
        string='Ghi chú điều tra'
    )
    
    # ===== LIÊN KẾT =====
    maintenance_history_ids = fields.Many2many(
        'asset.maintenance.history',
        string='Lịch sử bảo trì liên quan'
    )
    
    @api.depends('asset_id', 'period_month', 'period_year', 'anomaly_type')
    def _compute_display_name(self):
        for rec in self:
            if rec.asset_id:
                rec.display_name = f"{rec.asset_id.name} - T{rec.period_month}/{rec.period_year}"
            else:
                rec.display_name = f"Toàn hệ thống - T{rec.period_month}/{rec.period_year}"
    
    @api.depends('actual_cost', 'expected_cost')
    def _compute_deviation(self):
        for rec in self:
            if rec.expected_cost and rec.expected_cost > 0:
                rec.deviation = ((rec.actual_cost - rec.expected_cost) / rec.expected_cost) * 100
            else:
                rec.deviation = 0
    
    # ===== ACTIONS =====
    def action_investigate(self):
        """Bắt đầu điều tra"""
        self.write({'state': 'investigating'})
    
    def action_confirm(self):
        """Xác nhận bất thường thực sự"""
        self.write({'state': 'confirmed'})
    
    def action_false_positive(self):
        """Đánh dấu là báo động giả"""
        self.write({'state': 'false_positive'})
    
    def action_resolve(self):
        """Đánh dấu đã xử lý"""
        self.write({'state': 'resolved'})
    
    # ===== PHÂN TÍCH CHÍNH =====
    @api.model
    def run_anomaly_detection(self):
        """
        🔍 Chạy phát hiện bất thường cho toàn hệ thống
        Sử dụng: Z-Score + Isolation Forest
        """
        if not SKLEARN_AVAILABLE:
            raise UserError(_("Cần cài đặt scikit-learn: pip install scikit-learn"))
        
        _logger.info("🔍 Bắt đầu phát hiện chi phí bất thường...")
        
        # Lấy dữ liệu 12 tháng gần nhất
        end_date = datetime.now()
        start_date = end_date - relativedelta(months=12)
        
        MaintenanceHistory = self.env['asset.maintenance.history']
        histories = MaintenanceHistory.search([
            ('maintenance_date', '>=', start_date.strftime('%Y-%m-%d')),
            ('maintenance_date', '<=', end_date.strftime('%Y-%m-%d')),
            ('state', '=', 'done'),
            ('actual_cost', '>', 0)
        ])
        
        if len(histories) < 10:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('⚠️ Không đủ dữ liệu'),
                    'message': _('Cần ít nhất 10 records lịch sử bảo trì để phân tích'),
                    'type': 'warning',
                }
            }
        
        # Tạo DataFrame
        data = []
        for h in histories:
            data.append({
                'id': h.id,
                'asset_id': h.asset_id.id if h.asset_id else 0,
                'asset_name': h.asset_id.name if h.asset_id else 'Unknown',
                'category_id': h.asset_id.category_id.id if h.asset_id and h.asset_id.category_id else 0,
                'date': h.maintenance_date,
                'month': h.maintenance_date.month,
                'year': h.maintenance_date.year,
                'cost': h.actual_cost,
                'parts_cost': h.parts_cost or 0,
                'labor_cost': h.labor_cost or 0,
                'duration': h.duration_hours or 0,
            })
        
        df = pd.DataFrame(data)
        
        anomalies_found = 0
        
        # ===== PHƯƠNG PHÁP 1: Z-SCORE THEO THÁNG =====
        anomalies_found += self._detect_monthly_zscore(df)
        
        # ===== PHƯƠNG PHÁP 2: ISOLATION FOREST =====
        anomalies_found += self._detect_isolation_forest(df)
        
        # ===== PHƯƠNG PHÁP 3: CATEGORY OUTLIERS =====
        anomalies_found += self._detect_category_outliers(df)
        
        _logger.info(f"✅ Hoàn tất! Phát hiện {anomalies_found} bất thường")
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('✅ Hoàn tất phân tích'),
                'message': _('Phát hiện %d chi phí bất thường') % anomalies_found,
                'type': 'success' if anomalies_found == 0 else 'warning',
            }
        }
    
    def _detect_monthly_zscore(self, df):
        """Phát hiện bất thường theo Z-Score hàng tháng"""
        anomalies = 0
        
        # Tổng chi phí theo tháng
        monthly = df.groupby(['year', 'month']).agg({
            'cost': 'sum',
            'id': 'count'
        }).reset_index()
        monthly.columns = ['year', 'month', 'total_cost', 'count']
        
        if len(monthly) < 3:
            return 0
        
        # Tính Z-Score
        mean_cost = monthly['total_cost'].mean()
        std_cost = monthly['total_cost'].std()
        
        if std_cost == 0:
            return 0
        
        monthly['z_score'] = (monthly['total_cost'] - mean_cost) / std_cost
        
        # Phát hiện bất thường (|Z| > 2)
        for _, row in monthly.iterrows():
            if abs(row['z_score']) > 2:
                # Xác định mức độ
                if abs(row['z_score']) > 3:
                    severity = 'critical'
                elif abs(row['z_score']) > 2.5:
                    severity = 'high'
                else:
                    severity = 'medium'
                
                # Kiểm tra đã tồn tại chưa
                existing = self.search([
                    ('period_month', '=', int(row['month'])),
                    ('period_year', '=', int(row['year'])),
                    ('anomaly_type', '=', 'spike'),
                    ('asset_id', '=', False)
                ], limit=1)
                
                if not existing:
                    self.create({
                        'period_month': int(row['month']),
                        'period_year': int(row['year']),
                        'actual_cost': row['total_cost'],
                        'expected_cost': mean_cost,
                        'z_score': row['z_score'],
                        'severity': severity,
                        'anomaly_type': 'spike' if row['z_score'] > 0 else 'unusual_pattern',
                        'description': f"Chi phí tháng {int(row['month'])}/{int(row['year'])} {'tăng' if row['z_score'] > 0 else 'giảm'} bất thường.\n"
                                      f"Z-Score: {row['z_score']:.2f}\n"
                                      f"Số lần bảo trì: {int(row['count'])}",
                        'recommendation': "Kiểm tra các giao dịch bảo trì trong tháng này.\n"
                                         "Đối chiếu với báo cáo kế toán.\n"
                                         "Xác minh tính hợp lệ của chi phí."
                    })
                    anomalies += 1
        
        return anomalies
    
    def _detect_isolation_forest(self, df):
        """Phát hiện bất thường bằng Isolation Forest"""
        anomalies = 0
        
        if len(df) < 20:
            return 0
        
        # Features cho Isolation Forest
        features = ['cost', 'parts_cost', 'labor_cost', 'duration']
        X = df[features].values
        
        # Chuẩn hóa
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Train Isolation Forest
        iso_forest = IsolationForest(
            contamination=0.1,  # 10% outliers
            random_state=42,
            n_estimators=100
        )
        
        predictions = iso_forest.fit_predict(X_scaled)
        scores = iso_forest.decision_function(X_scaled)
        
        df['iso_pred'] = predictions
        df['iso_score'] = scores
        
        # Lấy các outliers (prediction = -1)
        outliers = df[df['iso_pred'] == -1]
        
        for _, row in outliers.iterrows():
            # Xác định mức độ dựa trên score
            if row['iso_score'] < -0.3:
                severity = 'critical'
            elif row['iso_score'] < -0.2:
                severity = 'high'
            elif row['iso_score'] < -0.1:
                severity = 'medium'
            else:
                severity = 'low'
            
            # Kiểm tra đã tồn tại
            existing = self.search([
                ('asset_id', '=', row['asset_id']),
                ('period_month', '=', row['month']),
                ('period_year', '=', row['year']),
                ('anomaly_type', '=', 'unusual_pattern')
            ], limit=1)
            
            if not existing and row['asset_id']:
                self.create({
                    'asset_id': row['asset_id'],
                    'period_month': row['month'],
                    'period_year': row['year'],
                    'actual_cost': row['cost'],
                    'isolation_score': row['iso_score'],
                    'severity': severity,
                    'anomaly_type': 'unusual_pattern',
                    'description': f"Isolation Forest phát hiện mẫu chi phí bất thường.\n"
                                  f"Tài sản: {row['asset_name']}\n"
                                  f"Chi phí: {row['cost']:,.0f} VND\n"
                                  f"Isolation Score: {row['iso_score']:.4f}",
                    'recommendation': "Kiểm tra chi tiết giao dịch bảo trì.\n"
                                     "So sánh với các lần bảo trì trước.\n"
                                     "Xác minh nhà cung cấp và linh kiện."
                })
                anomalies += 1
        
        return anomalies
    
    def _detect_category_outliers(self, df):
        """Phát hiện outliers theo danh mục tài sản"""
        anomalies = 0
        
        if len(df) < 10:
            return 0
        
        # Phân tích theo category
        for category_id in df['category_id'].unique():
            if category_id == 0:
                continue
            
            cat_df = df[df['category_id'] == category_id]
            
            if len(cat_df) < 5:
                continue
            
            mean_cost = cat_df['cost'].mean()
            std_cost = cat_df['cost'].std()
            
            if std_cost == 0:
                continue
            
            # Tìm outliers trong category (Z > 2)
            for _, row in cat_df.iterrows():
                z = (row['cost'] - mean_cost) / std_cost
                
                if abs(z) > 2:
                    severity = 'high' if abs(z) > 2.5 else 'medium'
                    
                    existing = self.search([
                        ('asset_id', '=', row['asset_id']),
                        ('period_month', '=', row['month']),
                        ('period_year', '=', row['year']),
                        ('anomaly_type', '=', 'category_outlier')
                    ], limit=1)
                    
                    if not existing and row['asset_id']:
                        self.create({
                            'asset_id': row['asset_id'],
                            'period_month': row['month'],
                            'period_year': row['year'],
                            'actual_cost': row['cost'],
                            'expected_cost': mean_cost,
                            'z_score': z,
                            'severity': severity,
                            'anomaly_type': 'category_outlier',
                            'description': f"Chi phí cao bất thường so với cùng danh mục.\n"
                                          f"Chi phí: {row['cost']:,.0f} VND\n"
                                          f"Trung bình danh mục: {mean_cost:,.0f} VND\n"
                                          f"Z-Score: {z:.2f}",
                            'recommendation': "So sánh với tài sản cùng loại.\n"
                                             "Kiểm tra tuổi thọ và tình trạng tài sản.\n"
                                             "Xem xét thay thế nếu chi phí quá cao."
                        })
                        anomalies += 1
        
        return anomalies
    
    @api.model
    def get_anomaly_dashboard_data(self):
        """Lấy dữ liệu cho dashboard"""
        today = fields.Date.today()
        last_30_days = today - timedelta(days=30)
        
        # Thống kê
        total = self.search_count([])
        detected = self.search_count([('state', '=', 'detected')])
        investigating = self.search_count([('state', '=', 'investigating')])
        confirmed = self.search_count([('state', '=', 'confirmed')])
        
        # Theo mức độ
        critical = self.search_count([('severity', '=', 'critical'), ('state', 'not in', ['resolved', 'false_positive'])])
        high = self.search_count([('severity', '=', 'high'), ('state', 'not in', ['resolved', 'false_positive'])])
        
        # Tổng chi phí bất thường (chưa xử lý)
        unresolved = self.search([('state', 'not in', ['resolved', 'false_positive'])])
        total_anomaly_cost = sum(unresolved.mapped('actual_cost'))
        
        return {
            'total': total,
            'detected': detected,
            'investigating': investigating,
            'confirmed': confirmed,
            'critical': critical,
            'high': high,
            'total_anomaly_cost': total_anomaly_cost,
        }
