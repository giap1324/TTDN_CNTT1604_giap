# -*- coding: utf-8 -*-
"""
🎯 COST OPTIMIZATION AI - AI Ra quyết định bảo trì
Mục đích: Nên bảo trì hay thay mới? Bảo trì bây giờ hay sau?
Sử dụng: Rule-based + Machine Learning + Decision Analysis
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
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class AssetCostOptimization(models.Model):
    _name = 'asset.cost.optimization'
    _description = 'AI Ra quyết định tối ưu chi phí'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
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
        required=True,
        ondelete='cascade'
    )
    
    category_id = fields.Many2one(
        'asset.category',
        string='Danh mục',
        related='asset_id.category_id',
        store=True
    )
    
    analysis_date = fields.Datetime(
        string='Ngày phân tích',
        default=fields.Datetime.now,
        required=True
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )
    
    # ===== THÔNG TIN TÀI SẢN =====
    asset_age_years = fields.Float(
        string='Tuổi tài sản (năm)',
        digits=(10, 1),
        help='Số năm từ khi mua'
    )
    
    expected_lifespan = fields.Float(
        string='Tuổi thọ dự kiến (năm)',
        digits=(10, 1),
        default=5.0
    )
    
    remaining_life_percent = fields.Float(
        string='Tuổi thọ còn lại (%)',
        compute='_compute_remaining_life',
        store=True
    )
    
    purchase_price = fields.Monetary(
        string='Giá mua',
        related='asset_id.purchase_price',
        readonly=True
    )
    
    current_value = fields.Float(
        string='Giá trị hiện tại',
        digits=(16, 0),
        compute='_compute_current_value',
        store=True,
        help='Giá trị sau khấu hao'
    )
    
    # ===== CHI PHÍ BẢO TRÌ =====
    total_maintenance_cost = fields.Float(
        string='Tổng chi phí bảo trì',
        digits=(16, 0),
        help='Tổng chi phí bảo trì từ trước đến nay'
    )
    
    avg_annual_maintenance = fields.Float(
        string='Chi phí BT trung bình/năm',
        digits=(16, 0)
    )
    
    last_year_maintenance = fields.Float(
        string='Chi phí BT năm gần nhất',
        digits=(16, 0)
    )
    
    maintenance_count = fields.Integer(
        string='Số lần bảo trì'
    )
    
    maintenance_trend = fields.Selection([
        ('decreasing', '📉 Giảm'),
        ('stable', '➡️ Ổn định'),
        ('increasing', '📈 Tăng'),
        ('rapid_increase', '🚀 Tăng nhanh')
    ], string='Xu hướng chi phí')
    
    # ===== PHÂN TÍCH CHI PHÍ =====
    cost_to_value_ratio = fields.Float(
        string='Tỷ lệ BT/Giá trị (%)',
        digits=(10, 2),
        help='Tổng chi phí bảo trì / Giá mua × 100'
    )
    
    annual_cost_ratio = fields.Float(
        string='Chi phí BT/năm (%)',
        digits=(10, 2),
        help='Chi phí BT trung bình / Giá mua × 100'
    )
    
    replacement_cost = fields.Float(
        string='Chi phí thay mới',
        digits=(16, 0),
        help='Ước tính chi phí mua tài sản thay thế'
    )
    
    projected_3year_maintenance = fields.Float(
        string='Dự kiến BT 3 năm tới',
        digits=(16, 0),
        help='Ước tính chi phí bảo trì 3 năm tới'
    )
    
    # ===== QUYẾT ĐỊNH AI =====
    decision = fields.Selection([
        ('maintain_now', '🔧 Bảo trì ngay'),
        ('maintain_later', '⏰ Bảo trì sau'),
        ('major_repair', '🔨 Đại tu'),
        ('replace', '🔄 Thay mới'),
        ('monitor', '👁️ Theo dõi'),
        ('dispose', '🗑️ Thanh lý')
    ], string='Quyết định', required=True, default='monitor')
    
    decision_confidence = fields.Float(
        string='Độ tin cậy (%)',
        digits=(10, 1),
        help='Độ tin cậy của quyết định AI'
    )
    
    urgency = fields.Selection([
        ('low', '🟢 Thấp'),
        ('medium', '🟡 Trung bình'),
        ('high', '🟠 Cao'),
        ('critical', '🔴 Khẩn cấp')
    ], string='Mức độ khẩn cấp', default='low')
    
    # ===== SO SÁNH KINH TẾ =====
    maintain_cost_5year = fields.Float(
        string='Chi phí BT 5 năm',
        digits=(16, 0),
        help='Dự kiến chi phí nếu tiếp tục bảo trì 5 năm'
    )
    
    replace_cost_5year = fields.Float(
        string='Chi phí thay mới 5 năm',
        digits=(16, 0),
        help='Chi phí thay mới + BT tài sản mới 5 năm'
    )
    
    savings_if_replace = fields.Float(
        string='Tiết kiệm nếu thay',
        digits=(16, 0),
        compute='_compute_savings',
        store=True
    )
    
    break_even_months = fields.Integer(
        string='Thời gian hoàn vốn (tháng)',
        help='Số tháng để chi phí thay mới được bù đắp'
    )
    
    # ===== LÝ DO & KHUYẾN NGHỊ =====
    decision_reasons = fields.Text(
        string='Lý do quyết định',
        help='Các yếu tố dẫn đến quyết định'
    )
    
    recommendations = fields.Html(
        string='Khuyến nghị chi tiết'
    )
    
    alternative_options = fields.Text(
        string='Phương án thay thế'
    )
    
    # ===== THỜI GIAN TỐI ƯU =====
    optimal_maintenance_date = fields.Date(
        string='Ngày BT tối ưu',
        help='Thời điểm bảo trì tối ưu về chi phí'
    )
    
    next_decision_date = fields.Date(
        string='Ngày đánh giá lại',
        help='Thời điểm nên chạy lại phân tích'
    )
    
    # ===== TRẠNG THÁI =====
    state = fields.Selection([
        ('draft', '📝 Nháp'),
        ('analyzed', '🔍 Đã phân tích'),
        ('approved', '✅ Đã duyệt'),
        ('executed', '✔️ Đã thực hiện'),
        ('cancelled', '❌ Hủy')
    ], string='Trạng thái', default='draft')
    
    @api.depends('asset_id', 'decision')
    def _compute_display_name(self):
        for rec in self:
            decision_labels = dict(self._fields['decision'].selection)
            decision_text = decision_labels.get(rec.decision, '')
            rec.display_name = f"{rec.asset_id.name} - {decision_text}" if rec.asset_id else "New Analysis"
    
    @api.depends('asset_age_years', 'expected_lifespan')
    def _compute_remaining_life(self):
        for rec in self:
            if rec.expected_lifespan > 0:
                remaining = ((rec.expected_lifespan - rec.asset_age_years) / rec.expected_lifespan) * 100
                rec.remaining_life_percent = max(0, min(100, remaining))
            else:
                rec.remaining_life_percent = 0
    
    @api.depends('purchase_price', 'asset_age_years', 'expected_lifespan')
    def _compute_current_value(self):
        """Tính giá trị hiện tại theo khấu hao đường thẳng"""
        for rec in self:
            if rec.purchase_price and rec.expected_lifespan > 0:
                depreciation_rate = rec.asset_age_years / rec.expected_lifespan
                depreciation_rate = min(depreciation_rate, 1.0)  # Max 100%
                # Giá trị còn lại tối thiểu 10%
                rec.current_value = rec.purchase_price * max(0.1, 1 - depreciation_rate)
            else:
                rec.current_value = rec.purchase_price or 0
    
    @api.depends('maintain_cost_5year', 'replace_cost_5year')
    def _compute_savings(self):
        for rec in self:
            rec.savings_if_replace = rec.maintain_cost_5year - rec.replace_cost_5year
    
    # ===== PHÂN TÍCH CHÍNH =====
    def action_analyze(self):
        """🎯 Chạy phân tích và đưa ra quyết định AI"""
        self.ensure_one()
        
        if not self.asset_id:
            raise UserError(_("Vui lòng chọn tài sản để phân tích"))
        
        # 1. Thu thập dữ liệu
        self._collect_asset_data()
        
        # 2. Phân tích xu hướng chi phí
        self._analyze_cost_trend()
        
        # 3. So sánh kinh tế
        self._economic_comparison()
        
        # 4. Ra quyết định AI
        self._make_decision()
        
        # 5. Tạo khuyến nghị
        self._generate_recommendations()
        
        self.state = 'analyzed'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('✅ Phân tích hoàn tất'),
                'message': _('Quyết định: %s (Độ tin cậy: %.1f%%)') % (
                    dict(self._fields['decision'].selection).get(self.decision),
                    self.decision_confidence
                ),
                'type': 'success',
            }
        }
    
    def _collect_asset_data(self):
        """Thu thập dữ liệu tài sản"""
        asset = self.asset_id
        
        # Tuổi tài sản
        if asset.purchase_date:
            age_days = (datetime.now().date() - asset.purchase_date).days
            self.asset_age_years = age_days / 365.25
        else:
            self.asset_age_years = 0
        
        # Tuổi thọ dự kiến theo category (hoặc mặc định)
        category_lifespan = {
            'computer': 4,
            'vehicle': 8,
            'furniture': 10,
            'equipment': 6,
            'electronics': 5,
        }
        if asset.category_id:
            cat_code = (asset.category_id.code or '').lower()
            self.expected_lifespan = category_lifespan.get(cat_code, 5)
        
        # Chi phí thay mới (ước tính tăng 10% so với giá mua)
        self.replacement_cost = (asset.purchase_price or 0) * 1.1
        
        # Lấy lịch sử bảo trì
        MaintenanceHistory = self.env['asset.maintenance.history']
        histories = MaintenanceHistory.search([
            ('asset_id', '=', asset.id),
            ('state', '=', 'done')
        ], order='maintenance_date asc')
        
        self.maintenance_count = len(histories)
        self.total_maintenance_cost = sum(histories.mapped('actual_cost'))
        
        # Chi phí theo năm
        if self.asset_age_years > 0:
            self.avg_annual_maintenance = self.total_maintenance_cost / max(1, self.asset_age_years)
        
        # Chi phí năm gần nhất
        one_year_ago = datetime.now().date() - timedelta(days=365)
        recent = histories.filtered(lambda h: h.maintenance_date >= one_year_ago)
        self.last_year_maintenance = sum(recent.mapped('actual_cost'))
        
        # Tỷ lệ chi phí
        if asset.purchase_price and asset.purchase_price > 0:
            self.cost_to_value_ratio = (self.total_maintenance_cost / asset.purchase_price) * 100
            self.annual_cost_ratio = (self.avg_annual_maintenance / asset.purchase_price) * 100
    
    def _analyze_cost_trend(self):
        """Phân tích xu hướng chi phí bảo trì"""
        MaintenanceHistory = self.env['asset.maintenance.history']
        histories = MaintenanceHistory.search([
            ('asset_id', '=', self.asset_id.id),
            ('state', '=', 'done')
        ], order='maintenance_date asc')
        
        if len(histories) < 3:
            self.maintenance_trend = 'stable'
            return
        
        # Chia thành 2 nửa và so sánh
        mid = len(histories) // 2
        first_half = histories[:mid]
        second_half = histories[mid:]
        
        avg_first = sum(first_half.mapped('actual_cost')) / len(first_half)
        avg_second = sum(second_half.mapped('actual_cost')) / len(second_half)
        
        if avg_first == 0:
            change_ratio = 0
        else:
            change_ratio = (avg_second - avg_first) / avg_first
        
        if change_ratio < -0.2:
            self.maintenance_trend = 'decreasing'
        elif change_ratio < 0.2:
            self.maintenance_trend = 'stable'
        elif change_ratio < 0.5:
            self.maintenance_trend = 'increasing'
        else:
            self.maintenance_trend = 'rapid_increase'
    
    def _economic_comparison(self):
        """So sánh kinh tế giữa bảo trì và thay mới"""
        # Dự kiến chi phí BT 3 năm tới
        if self.maintenance_trend == 'rapid_increase':
            growth_rate = 1.5  # Tăng 50%/năm
        elif self.maintenance_trend == 'increasing':
            growth_rate = 1.2  # Tăng 20%/năm
        elif self.maintenance_trend == 'decreasing':
            growth_rate = 0.9  # Giảm 10%/năm
        else:
            growth_rate = 1.05  # Tăng 5%/năm (lạm phát)
        
        annual = self.avg_annual_maintenance or (self.last_year_maintenance or 0)
        
        # Dự kiến 3 năm
        self.projected_3year_maintenance = sum([
            annual * (growth_rate ** i) for i in range(1, 4)
        ])
        
        # Chi phí nếu tiếp tục BT 5 năm
        self.maintain_cost_5year = sum([
            annual * (growth_rate ** i) for i in range(1, 6)
        ])
        
        # Chi phí thay mới + BT tài sản mới 5 năm
        # Giả định tài sản mới BT ít hơn 70%
        new_asset_annual_bt = annual * 0.3
        self.replace_cost_5year = self.replacement_cost + (new_asset_annual_bt * 5)
        
        # Thời gian hoàn vốn
        if annual > new_asset_annual_bt:
            monthly_savings = (annual - new_asset_annual_bt) / 12
            if monthly_savings > 0:
                self.break_even_months = int(self.replacement_cost / monthly_savings)
            else:
                self.break_even_months = 999
        else:
            self.break_even_months = 999
    
    def _make_decision(self):
        """🎯 AI ra quyết định dựa trên nhiều yếu tố"""
        score = {
            'maintain_now': 0,
            'maintain_later': 0,
            'major_repair': 0,
            'replace': 0,
            'monitor': 0,
            'dispose': 0
        }
        
        reasons = []
        
        # ===== YẾU TỐ 1: TUỔI THỌ =====
        if self.remaining_life_percent < 10:
            score['replace'] += 40
            score['dispose'] += 30
            reasons.append("⚠️ Tuổi thọ còn lại rất thấp (<10%)")
        elif self.remaining_life_percent < 30:
            score['replace'] += 25
            score['major_repair'] += 20
            reasons.append("📉 Tuổi thọ còn lại thấp (<30%)")
        elif self.remaining_life_percent > 70:
            score['maintain_later'] += 20
            score['monitor'] += 15
            reasons.append("✅ Tài sản còn mới (>70% tuổi thọ)")
        
        # ===== YẾU TỐ 2: TỶ LỆ CHI PHÍ BT =====
        if self.cost_to_value_ratio > 100:
            score['replace'] += 50
            reasons.append("🚨 Chi phí BT đã vượt giá trị tài sản!")
        elif self.cost_to_value_ratio > 70:
            score['replace'] += 35
            score['major_repair'] += 15
            reasons.append("⚠️ Chi phí BT >70% giá trị")
        elif self.cost_to_value_ratio > 50:
            score['major_repair'] += 25
            reasons.append("📊 Chi phí BT >50% giá trị")
        elif self.cost_to_value_ratio < 20:
            score['maintain_later'] += 20
            score['monitor'] += 15
            reasons.append("✅ Chi phí BT hợp lý (<20%)")
        
        # ===== YẾU TỐ 3: XU HƯỚNG CHI PHÍ =====
        if self.maintenance_trend == 'rapid_increase':
            score['replace'] += 30
            score['major_repair'] += 20
            reasons.append("🚀 Chi phí BT tăng nhanh")
        elif self.maintenance_trend == 'increasing':
            score['maintain_now'] += 15
            score['major_repair'] += 10
            reasons.append("📈 Chi phí BT đang tăng")
        elif self.maintenance_trend == 'decreasing':
            score['monitor'] += 20
            reasons.append("📉 Chi phí BT đang giảm")
        
        # ===== YẾU TỐ 4: SO SÁNH KINH TẾ 5 NĂM =====
        if self.savings_if_replace > 0:
            if self.savings_if_replace > self.replacement_cost * 0.5:
                score['replace'] += 40
                reasons.append(f"💰 Thay mới tiết kiệm {self.savings_if_replace:,.0f} VND trong 5 năm")
            elif self.savings_if_replace > self.replacement_cost * 0.2:
                score['replace'] += 25
                reasons.append("💡 Thay mới có lợi về kinh tế")
        else:
            score['maintain_later'] += 20
            reasons.append("💵 Tiếp tục BT có lợi hơn thay mới")
        
        # ===== YẾU TỐ 5: THỜI GIAN HOÀN VỐN =====
        if self.break_even_months < 12:
            score['replace'] += 30
            reasons.append(f"⏱️ Hoàn vốn nhanh ({self.break_even_months} tháng)")
        elif self.break_even_months < 24:
            score['replace'] += 15
            reasons.append(f"📅 Hoàn vốn trong 2 năm")
        elif self.break_even_months > 60:
            score['maintain_later'] += 25
            reasons.append("⏳ Hoàn vốn >5 năm - tiếp tục BT")
        
        # ===== YẾU TỐ 6: TẦN SUẤT BẢO TRÌ =====
        if self.asset_age_years > 0:
            bt_per_year = self.maintenance_count / self.asset_age_years
            if bt_per_year > 6:
                score['replace'] += 25
                score['major_repair'] += 15
                reasons.append(f"🔄 Tần suất BT cao ({bt_per_year:.1f} lần/năm)")
            elif bt_per_year > 4:
                score['maintain_now'] += 15
                reasons.append("📊 Tần suất BT trung bình cao")
        
        # ===== XÁC ĐỊNH QUYẾT ĐỊNH =====
        max_score = max(score.values())
        decision = max(score, key=score.get)
        
        # Độ tin cậy dựa trên khoảng cách điểm
        scores_sorted = sorted(score.values(), reverse=True)
        if len(scores_sorted) > 1 and max_score > 0:
            gap = scores_sorted[0] - scores_sorted[1]
            self.decision_confidence = min(95, 50 + gap)
        else:
            self.decision_confidence = 50
        
        self.decision = decision
        self.decision_reasons = "\n".join(reasons)
        
        # Xác định mức độ khẩn cấp
        if decision in ['replace', 'dispose'] and self.remaining_life_percent < 10:
            self.urgency = 'critical'
        elif decision == 'maintain_now' or (decision == 'replace' and self.cost_to_value_ratio > 100):
            self.urgency = 'high'
        elif decision == 'major_repair':
            self.urgency = 'medium'
        else:
            self.urgency = 'low'
        
        # Thời điểm BT tối ưu
        if decision == 'maintain_now':
            self.optimal_maintenance_date = fields.Date.today()
        elif decision == 'maintain_later':
            self.optimal_maintenance_date = fields.Date.today() + timedelta(days=90)
        
        # Ngày đánh giá lại
        self.next_decision_date = fields.Date.today() + timedelta(days=180)
    
    def _generate_recommendations(self):
        """Tạo khuyến nghị chi tiết"""
        decision = self.decision
        
        recommendations = {
            'maintain_now': """
                <h4>🔧 Khuyến nghị: Bảo trì ngay</h4>
                <ul>
                    <li>Lên lịch bảo trì trong 7-14 ngày tới</li>
                    <li>Kiểm tra toàn diện tình trạng thiết bị</li>
                    <li>Thay thế các linh kiện hao mòn</li>
                    <li>Cập nhật lịch bảo trì định kỳ</li>
                </ul>
                <p><strong>Lý do:</strong> Việc bảo trì kịp thời sẽ ngăn ngừa hư hỏng lớn và kéo dài tuổi thọ tài sản.</p>
            """,
            'maintain_later': """
                <h4>⏰ Khuyến nghị: Lên lịch bảo trì sau</h4>
                <ul>
                    <li>Tài sản vẫn hoạt động tốt</li>
                    <li>Lên lịch bảo trì định kỳ sau 2-3 tháng</li>
                    <li>Theo dõi các dấu hiệu bất thường</li>
                    <li>Chuẩn bị ngân sách cho lần BT tiếp theo</li>
                </ul>
                <p><strong>Lý do:</strong> Chưa cần thiết bảo trì ngay, tiết kiệm chi phí mà không ảnh hưởng hoạt động.</p>
            """,
            'major_repair': """
                <h4>🔨 Khuyến nghị: Đại tu thiết bị</h4>
                <ul>
                    <li>Thực hiện bảo trì tổng thể</li>
                    <li>Thay thế nhiều linh kiện chính</li>
                    <li>Xem xét nâng cấp một số bộ phận</li>
                    <li>Dự trù ngân sách cao hơn bình thường</li>
                </ul>
                <p><strong>Lý do:</strong> Đại tu sẽ giúp kéo dài đáng kể tuổi thọ tài sản so với việc thay mới.</p>
            """,
            'replace': f"""
                <h4>🔄 Khuyến nghị: Thay mới tài sản</h4>
                <ul>
                    <li>Chi phí thay mới ước tính: <strong>{self.replacement_cost:,.0f} VND</strong></li>
                    <li>Tiết kiệm 5 năm nếu thay: <strong>{self.savings_if_replace:,.0f} VND</strong></li>
                    <li>Thời gian hoàn vốn: <strong>{self.break_even_months} tháng</strong></li>
                    <li>Lập kế hoạch mua sắm và thanh lý</li>
                </ul>
                <p><strong>Lý do:</strong> Tiếp tục bảo trì không còn hiệu quả kinh tế. Thay mới sẽ tiết kiệm chi phí dài hạn.</p>
            """,
            'monitor': """
                <h4>👁️ Khuyến nghị: Theo dõi</h4>
                <ul>
                    <li>Tài sản đang hoạt động bình thường</li>
                    <li>Tiếp tục sử dụng và theo dõi</li>
                    <li>Đánh giá lại sau 3-6 tháng</li>
                    <li>Ghi nhận các sự cố nếu có</li>
                </ul>
                <p><strong>Lý do:</strong> Chưa có dấu hiệu cần can thiệp. Tiếp tục theo dõi để có quyết định đúng thời điểm.</p>
            """,
            'dispose': f"""
                <h4>🗑️ Khuyến nghị: Thanh lý tài sản</h4>
                <ul>
                    <li>Giá trị còn lại ước tính: <strong>{self.current_value:,.0f} VND</strong></li>
                    <li>Lập biên bản thanh lý</li>
                    <li>Tìm đơn vị thu mua hoặc xử lý</li>
                    <li>Cập nhật sổ sách tài sản</li>
                </ul>
                <p><strong>Lý do:</strong> Tài sản đã hết tuổi thọ kinh tế. Tiếp tục sử dụng sẽ gây lãng phí và rủi ro.</p>
            """
        }
        
        self.recommendations = recommendations.get(decision, "Không có khuyến nghị")
        
        # Phương án thay thế
        alternatives = []
        if decision != 'maintain_now':
            alternatives.append("• Bảo trì phòng ngừa định kỳ")
        if decision != 'replace':
            alternatives.append(f"• Thay mới với chi phí {self.replacement_cost:,.0f} VND")
        if decision not in ['dispose', 'replace']:
            alternatives.append("• Kéo dài sử dụng và theo dõi sát")
        
        self.alternative_options = "\n".join(alternatives) if alternatives else "Không có phương án thay thế phù hợp"
    
    # ===== BATCH ANALYSIS =====
    @api.model
    def analyze_all_assets(self):
        """Phân tích tất cả tài sản đang hoạt động"""
        Asset = self.env['asset']
        assets = Asset.search([('state', '=', 'in_use')])
        
        created = 0
        for asset in assets:
            # Kiểm tra đã có phân tích trong 30 ngày chưa
            existing = self.search([
                ('asset_id', '=', asset.id),
                ('analysis_date', '>=', datetime.now() - timedelta(days=30))
            ], limit=1)
            
            if not existing:
                analysis = self.create({
                    'asset_id': asset.id,
                })
                analysis.action_analyze()
                created += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('✅ Phân tích hoàn tất'),
                'message': _('Đã phân tích %d tài sản') % created,
                'type': 'success',
            }
        }
    
    def action_approve(self):
        """Duyệt quyết định"""
        self.write({'state': 'approved'})
    
    def action_execute(self):
        """Đánh dấu đã thực hiện"""
        self.write({'state': 'executed'})
    
    def action_cancel(self):
        """Hủy"""
        self.write({'state': 'cancelled'})
