# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import logging
import random
import pickle
import os

_logger = logging.getLogger(__name__)

# Import ML libraries
try:
    import numpy as np
    import pandas as pd
    from xgboost import XGBRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import mean_absolute_error, r2_score
    ML_AVAILABLE = True
    XGBOOST_AVAILABLE = True
except ImportError as e:
    try:
        import numpy as np
        import pandas as pd
        from sklearn.model_selection import train_test_split
        from sklearn.linear_model import LinearRegression
        from sklearn.preprocessing import StandardScaler
        from sklearn.metrics import mean_absolute_error, r2_score
        ML_AVAILABLE = True
        XGBOOST_AVAILABLE = False
        _logger.warning(f"XGBoost not available ({e}). Install: pip3 install xgboost")
    except ImportError as e2:
        ML_AVAILABLE = False
        XGBOOST_AVAILABLE = False
        _logger.warning(f"ML libraries not available ({e2}). Install: pip3 install xgboost scikit-learn pandas numpy")

# Đường dẫn lưu model đã train
MODEL_PATH = '/tmp/xgboost_maintenance_model.pkl'
SCALER_PATH = '/tmp/xgboost_scaler.pkl'

# Flag để tránh train nhiều lần khi khởi động
_MODEL_INITIALIZED = False


class AssetMaintenancePrediction(models.Model):
    _name = 'asset.maintenance.prediction'
    _description = 'Dự Đoán Bảo Trì Tài Sản'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'prediction_date desc'

    # Tài sản
    asset_id = fields.Many2one('asset', string='Tài sản', required=True, ondelete='cascade')
    asset_category_id = fields.Many2one('asset.category', related='asset_id.category_id', string='Danh mục', store=True)
    
    @api.model
    def _auto_train_on_startup(self):
        """
        Tự động train XGBoost model khi khởi động Odoo
        Được gọi từ post_init_hook hoặc scheduled action
        """
        global _MODEL_INITIALIZED
        
        if _MODEL_INITIALIZED:
            _logger.info("🤖 XGBoost model đã được khởi tạo trước đó")
            return True
        
        if not XGBOOST_AVAILABLE:
            _logger.warning("⚠️ XGBoost không khả dụng, bỏ qua auto-train")
            return False
        
        if not os.path.exists(MODEL_PATH):
            _logger.info("🚀 Auto-training XGBoost model với 1000 dữ liệu...")
            try:
                self._train_xgboost_model()
                _MODEL_INITIALIZED = True
                _logger.info("✅ Auto-train XGBoost hoàn tất!")
                return True
            except Exception as e:
                _logger.error(f"❌ Lỗi auto-train: {e}")
                return False
        else:
            _logger.info("✅ XGBoost model đã tồn tại, sẵn sàng dự đoán")
            _MODEL_INITIALIZED = True
            return True
    
    @api.model
    def cron_auto_train_model(self):
        """
        Cron job: Auto-train AI model mỗi ngày
        Kiểm tra xem có đủ dữ liệu mới không, nếu có thì train lại
        """
        _logger.info("🤖 [CRON] Auto-train AI Model - Bắt đầu")
        
        if not XGBOOST_AVAILABLE:
            _logger.warning("⚠️ XGBoost không khả dụng, bỏ qua auto-train")
            return False
        
        # Kiểm tra có lịch sử bảo trì mới không
        history_count = self.env['asset.maintenance.history'].search_count([('state', '=', 'done')])
        
        if history_count < 50:
            _logger.info(f"ℹ️ Chỉ có {history_count} records, cần ít nhất 50 để train")
            return False
        
        # Kiểm tra có dữ liệu mới trong 7 ngày qua không
        week_ago = fields.Date.today() - timedelta(days=7)
        new_records = self.env['asset.maintenance.history'].search_count([
            ('state', '=', 'done'),
            ('maintenance_date', '>=', week_ago)
        ])
        
        if new_records == 0:
            _logger.info("ℹ️ Không có dữ liệu mới trong 7 ngày qua, bỏ qua train")
            return True
        
        _logger.info(f"🔥 Phát hiện {new_records} records mới, đang train lại model...")
        
        # Xóa model cũ
        if os.path.exists(MODEL_PATH):
            os.remove(MODEL_PATH)
        if os.path.exists(SCALER_PATH):
            os.remove(SCALER_PATH)
        
        # Train mới
        try:
            self._train_xgboost_model()
            _logger.info("✅ [CRON] Auto-train hoàn tất!")
            
            # Tự động dự đoán cho tất cả tài sản
            self._cron_predict_new_assets()
            
            return True
        except Exception as e:
            _logger.error(f"❌ [CRON] Lỗi auto-train: {e}")
            return False
    
    @api.model
    def _cron_retrain_model(self):
        """
        Scheduled action: Train lại model định kỳ (hàng tuần)
        Giúp model cập nhật với patterns mới
        """
        _logger.info("🔄 Cron job: Đang train lại XGBoost model...")
        
        if not XGBOOST_AVAILABLE:
            _logger.warning("⚠️ XGBoost không khả dụng")
            return False
        
        # Xóa model cũ
        if os.path.exists(MODEL_PATH):
            os.remove(MODEL_PATH)
        if os.path.exists(SCALER_PATH):
            os.remove(SCALER_PATH)
        
        # Train mới
        try:
            self._train_xgboost_model()
            _logger.info("✅ Cron: Train lại XGBoost thành công!")
            return True
        except Exception as e:
            _logger.error(f"❌ Cron error: {e}")
            return False
    
    @api.model
    def _cron_predict_new_assets(self):
        """
        Scheduled action: Tự động dự đoán cho tài sản chưa có prediction
        Chạy hàng ngày
        """
        _logger.info("🤖 Cron: Kiểm tra tài sản mới cần dự đoán...")
        
        # Tìm tài sản active chưa có prediction
        all_assets = self.env['asset'].search([
            ('state', 'in', ['available', 'in_use'])
        ])
        
        # Lấy danh sách asset đã có prediction
        predicted_asset_ids = self.search([]).mapped('asset_id.id')
        
        # Tìm tài sản chưa có prediction
        new_assets = all_assets.filtered(lambda a: a.id not in predicted_asset_ids)
        
        if not new_assets:
            _logger.info("✅ Không có tài sản mới cần dự đoán")
            return True
        
        _logger.info(f"🔍 Tìm thấy {len(new_assets)} tài sản mới, đang dự đoán...")
        
        count = 0
        for asset in new_assets:
            try:
                self.predict_maintenance_for_asset(asset.id)
                count += 1
            except Exception as e:
                _logger.error(f"❌ Lỗi dự đoán tài sản {asset.name}: {e}")
        
        _logger.info(f"✅ Cron: Đã dự đoán cho {count}/{len(new_assets)} tài sản mới")
        return True
    
    # Dự đoán
    prediction_date = fields.Date(string='Ngày dự đoán', default=fields.Date.today)
    next_maintenance_date = fields.Date(string='Ngày bảo trì tiếp theo (dự đoán)')
    predicted_cost = fields.Monetary(string='Chi phí dự kiến')
    confidence_score = fields.Float(string='Độ tin cậy (%)', digits=(5, 2))
    
    # Lý do
    prediction_reason = fields.Text(string='Lý do dự đoán')
    risk_level = fields.Selection([
        ('low', 'Thấp'),
        ('medium', 'Trung bình'),
        ('high', 'Cao'),
        ('critical', 'Nghiêm trọng')
    ], string='Mức độ rủi ro', default='low')
    
    # Thông tin bổ sung
    usage_hours = fields.Float(string='Số giờ sử dụng dự kiến')
    maintenance_type = fields.Selection([
        ('preventive', 'Bảo trì định kỳ'),
        ('corrective', 'Sửa chữa'),
        ('replacement', 'Thay thế')
    ], string='Loại bảo trì')
    
    # Trạng thái
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('predicted', 'Đã dự đoán'),
        ('scheduled', 'Đã lên lịch'),
        ('completed', 'Hoàn thành'),
        ('cancelled', 'Hủy')
    ], string='Trạng thái', default='draft')
    
    # Tiền tệ
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', 
                                   default=lambda self: self.env.company.currency_id)
    
    # Notes
    notes = fields.Text(string='Ghi chú')

    @api.model
    def predict_maintenance_for_asset(self, asset_id):
        """
     
        """
        if not ML_AVAILABLE:
            raise UserError(_('Thư viện ML chưa được cài đặt!\n\nChạy lệnh: pip3 install xgboost scikit-learn pandas numpy'))
        
        asset = self.env['asset'].browse(asset_id)
        if not asset.exists():
            raise ValidationError(_('Tài sản không tồn tại!'))
        
        # Kiểm tra và train model nếu chưa có
        if not os.path.exists(MODEL_PATH):
            _logger.info("🤖 XGBoost model chưa tồn tại. Đang train với 1000 dữ liệu giả lập...")
            self._train_xgboost_model()
        
        # Load model và dự đoán
        try:
            prediction = self._predict_with_xgboost(asset)
            return prediction
        except Exception as e:
            _logger.error(f"Lỗi khi dự đoán với XGBoost: {e}")
            return self._predict_by_rules(asset)

    @api.model
    def _get_real_training_data(self):
        """
        Lấy dữ liệu thật từ (ưu tiên theo thứ tự):
        1. Lịch sử bảo trì THỰC TẾ (asset.maintenance.history) - TỐT NHẤT
        
        Trả về DataFrame hoặc None nếu không đủ dữ liệu
        """
        _logger.info("🔍 Kiểm tra dữ liệu thật từ database...")
        
        # ƯU TIÊN 1: Lấy từ maintenance history (chi phí thực tế)
        MaintenanceHistory = self.env['asset.maintenance.history']
        histories = MaintenanceHistory.search([
            ('state', '=', 'done'),
            ('actual_cost', '>', 0)
        ])
        
        if len(histories) >= 50:
            _logger.info(f"✅ Sử dụng {len(histories)} MAINTENANCE HISTORY (dữ liệu THỰC TẾ tốt nhất!)")
            return self._build_dataframe_from_history(histories)
        
        # FALLBACK 2: Lấy từ predictions cũ
        _logger.info(f"⚠️ Chỉ có {len(histories)} maintenance history - chuyển sang predictions")
        predictions = self.search([
            ('state', '!=', 'cancelled'),
            ('predicted_cost', '>', 0)
        ])
        
        if len(predictions) < 50:
            _logger.info(f"⚠️ Chỉ có {len(predictions)} predictions - cần ít nhất 50 để train")
            return None
        
        data = []
        today = fields.Date.today()
        
        for pred in predictions:
            asset = pred.asset_id
            if not asset.exists():
                continue
            
            purchase_date = asset.purchase_date or today
            days_since_purchase = (today - purchase_date).days
            asset_value = asset.current_value or asset.purchase_price or 1000000
            
            # Map category
            category_name = asset.category_id.name.lower() if asset.category_id else ''
            category_type = 0  # Default: IT
            if 'computer' in category_name or 'máy' in category_name:
                category_type = 0
            elif 'furniture' in category_name or 'nội thất' in category_name or 'bàn' in category_name or 'ghế' in category_name:
                category_type = 1
            elif 'electronic' in category_name or 'điện' in category_name:
                category_type = 2
            else:
                category_type = 3
            
            # Usage intensity từ state và usage history
            state_intensity = {'available': 0.3, 'in_use': 0.8, 'maintenance': 0.5, 'disposed': 0.1}
            usage_intensity = state_intensity.get(asset.state, 0.5)
            
            # Đếm số lần đã predict (giả sử = số lần bảo trì)
            previous_count = self.search_count([('asset_id', '=', asset.id)]) - 1
            
            # Tính ngày từ lần predict trước
            last_pred = self.search([
                ('asset_id', '=', asset.id),
                ('id', '<', pred.id)
            ], order='create_date desc', limit=1)
            
            if last_pred and last_pred.prediction_date:
                last_maintenance_days = (pred.prediction_date - last_pred.prediction_date).days
            else:
                last_maintenance_days = 30
            
            # Target: Số ngày từ khi predict đến ngày bảo trì dự kiến
            if pred.next_maintenance_date and pred.prediction_date:
                days_to_maintenance = (pred.next_maintenance_date - pred.prediction_date).days
            else:
                days_to_maintenance = 60
            
            # Chi phí bảo trì
            maintenance_cost = pred.predicted_cost
            
            # Risk level
            risk_map = {'low': 0, 'medium': 1, 'high': 2, 'critical': 3}
            risk_level = risk_map.get(pred.risk_level, 1)
            
            data.append({
                'days_since_purchase': days_since_purchase,
                'asset_value': asset_value,
                'category_type': category_type,
                'usage_intensity': usage_intensity,
                'previous_maintenance_count': max(0, previous_count),
                'last_maintenance_days': last_maintenance_days,
                'days_to_maintenance': max(7, days_to_maintenance),
                'maintenance_cost': maintenance_cost,
                'risk_level': risk_level
            })
        
        if len(data) < 50:
            _logger.info(f"⚠️ Chỉ có {len(data)} records hợp lệ - cần ít nhất 50")
            return None
        
        _logger.info(f"✅ Đã lấy {len(data)} dữ liệu thật từ database")
        return pd.DataFrame(data)
    
    @api.model
    def _build_dataframe_from_history(self, histories):
        """
        Xây dựng DataFrame từ maintenance history (CHI PHÍ THỰC TẾ)
        Đây là nguồn data TỐT NHẤT cho training
        """
        data = []
        today = fields.Date.today()
        
        for history in histories:
            asset = history.asset_id
            if not asset.exists():
                continue
            
            # Tính features tại thời điểm bảo trì
            maintenance_date = history.maintenance_date
            purchase_date = asset.purchase_date or maintenance_date
            days_since_purchase = (maintenance_date - purchase_date).days
            asset_value = asset.current_value or asset.purchase_price or 1000000
            
            # Map category
            category_name = asset.category_id.name.lower() if asset.category_id else ''
            category_type = 0
            if 'computer' in category_name or 'máy' in category_name:
                category_type = 0
            elif 'furniture' in category_name or 'nội thất' in category_name or 'bàn' in category_name or 'ghế' in category_name:
                category_type = 1
            elif 'electronic' in category_name or 'điện' in category_name:
                category_type = 2
            else:
                category_type = 3
            
            # Usage intensity
            state_intensity = {'available': 0.3, 'in_use': 0.8, 'maintenance': 0.5, 'disposed': 0.1}
            usage_intensity = state_intensity.get(asset.state, 0.5)
            
            # Đếm số lần bảo trì trước đó
            previous_count = self.env['asset.maintenance.history'].search_count([
                ('asset_id', '=', asset.id),
                ('maintenance_date', '<', maintenance_date),
                ('state', '=', 'done')
            ])
            
            # Tính ngày từ lần bảo trì trước
            last_history = self.env['asset.maintenance.history'].search([
                ('asset_id', '=', asset.id),
                ('maintenance_date', '<', maintenance_date),
                ('state', '=', 'done')
            ], order='maintenance_date desc', limit=1)
            
            if last_history:
                last_maintenance_days = (maintenance_date - last_history.maintenance_date).days
            else:
                last_maintenance_days = 60  # Default cho tài sản chưa có lịch sử
            
            # Target: Số ngày đến lần bảo trì tiếp theo (dự đoán chu kỳ)
            # Dựa trên pattern chu kỳ bảo trì trước
            days_to_maintenance = max(15, min(180, last_maintenance_days))
            
            # CHI PHÍ THỰC TẾ (không phải dự đoán!)
            maintenance_cost = history.actual_cost
            
            # Risk level từ kết quả
            result_risk_map = {'success': 0, 'partial': 1, 'pending': 2, 'failed': 3}
            risk_level = result_risk_map.get(history.result, 1)
            
            data.append({
                'days_since_purchase': days_since_purchase,
                'asset_value': asset_value,
                'category_type': category_type,
                'usage_intensity': usage_intensity,
                'previous_maintenance_count': previous_count,
                'last_maintenance_days': last_maintenance_days,
                'days_to_maintenance': max(7, days_to_maintenance),
                'maintenance_cost': maintenance_cost,  # THỰC TẾ!
                'risk_level': risk_level
            })
        
        _logger.info(f"📦 Đã xây dựng {len(data)} records từ MAINTENANCE HISTORY (data thực tế)")
        return pd.DataFrame(data)
    
    @api.model
    def _generate_synthetic_data(self, n_samples=1000):
        """
        Tạo 1000 dữ liệu giả lập cho training XGBoost
        Mô phỏng các pattern bảo trì thực tế
        
        CHÚ Ý: Chỉ dùng khi không đủ dữ liệu thật (< 50 records)
        """
        np.random.seed(42)
        
        data = []
        for i in range(n_samples):
            # Features
            days_since_purchase = np.random.randint(1, 2000)  # 0-5.5 năm
            asset_value = np.random.uniform(500000, 100000000)  # 500K - 100M VND
            category_type = np.random.choice([0, 1, 2, 3])  # 0: IT, 1: Furniture, 2: Electronics, 3: Others
            usage_intensity = np.random.uniform(0.1, 1.0)  # Mức độ sử dụng
            previous_maintenance_count = np.random.randint(0, 20)
            last_maintenance_days = np.random.randint(0, 365)
            
            # Tính tuổi tài sản (tháng)
            age_months = days_since_purchase / 30
            
            # Target 1: Số ngày đến lần bảo trì tiếp theo
            # Logic: Tài sản cũ + sử dụng nhiều = bảo trì sớm hơn
            base_cycle = 90  # 3 tháng
            age_factor = max(0.3, 1 - (age_months / 60))  # Giảm dần theo tuổi
            usage_factor = 1 - (usage_intensity * 0.4)  # Sử dụng nhiều = giảm chu kỳ
            category_factor = [0.8, 1.2, 0.9, 1.0][category_type]  # IT cần bảo trì thường xuyên hơn
            
            days_to_maintenance = int(base_cycle * age_factor * usage_factor * category_factor)
            days_to_maintenance = max(15, min(180, days_to_maintenance))  # Giới hạn 15-180 ngày
            days_to_maintenance += np.random.randint(-10, 10)  # Thêm nhiễu
            
            # Target 2: Chi phí bảo trì
            # Logic: Dựa trên giá trị, tuổi, loại tài sản
            base_cost_percent = 0.05  # 5% giá trị
            age_cost_factor = 1 + (age_months / 24) * 0.5  # Tăng theo tuổi
            category_cost_factor = [1.5, 0.5, 1.2, 1.0][category_type]  # IT đắt hơn
            
            maintenance_cost = asset_value * base_cost_percent * age_cost_factor * category_cost_factor
            maintenance_cost *= np.random.uniform(0.8, 1.2)  # Thêm nhiễu ±20%
            
            # Target 3: Mức độ rủi ro (0: low, 1: medium, 2: high, 3: critical)
            risk_score = (age_months / 24) + (usage_intensity * 0.5) + (previous_maintenance_count * 0.1)
            if risk_score < 0.5:
                risk_level = 0
            elif risk_score < 1.0:
                risk_level = 1
            elif risk_score < 1.5:
                risk_level = 2
            else:
                risk_level = 3
            
            data.append({
                'days_since_purchase': days_since_purchase,
                'asset_value': asset_value,
                'category_type': category_type,
                'usage_intensity': usage_intensity,
                'previous_maintenance_count': previous_maintenance_count,
                'last_maintenance_days': last_maintenance_days,
                # Targets
                'days_to_maintenance': max(15, days_to_maintenance),
                'maintenance_cost': maintenance_cost,
                'risk_level': risk_level
            })
        
        return pd.DataFrame(data)

    @api.model
    def _train_xgboost_model(self):
        """
        Train XGBoost model:
        1. Ưu tiên dữ liệu THẬT từ lịch sử maintenance/predictions (nếu >= 50 records)
        2. Không dùng dữ liệu giả lập
        """
        if not XGBOOST_AVAILABLE:
            _logger.warning("XGBoost không khả dụng, sử dụng rule-based")
            return False
        
        # Thử lấy dữ liệu thật trước
        df = self._get_real_training_data()
        
        if df is None:
            _logger.warning("⚠️ Không đủ dữ liệu thật để train (cần >= 50 records). Bỏ qua training.")
            return False

        _logger.info(f"🚀 Training XGBoost với {len(df)} DỮ LIỆU THẬT từ database...")
        data_source = "real"
        
        # Features và targets
        feature_cols = ['days_since_purchase', 'asset_value', 'category_type', 
                       'usage_intensity', 'previous_maintenance_count', 'last_maintenance_days']
        X = df[feature_cols].values
        y_days = df['days_to_maintenance'].values
        y_cost = df['maintenance_cost'].values
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Train/test split
        X_train, X_test, y_days_train, y_days_test = train_test_split(
            X_scaled, y_days, test_size=0.2, random_state=42
        )
        _, _, y_cost_train, y_cost_test = train_test_split(
            X_scaled, y_cost, test_size=0.2, random_state=42
        )
        
        # Train XGBoost cho days prediction
        model_days = XGBRegressor(
            n_estimators=200,        # Tăng từ 100 → 200 trees
            max_depth=8,             # Tăng từ 6 → 8 để học phức tạp hơn
            learning_rate=0.05,      # Giảm từ 0.1 → 0.05 để học chậm hơn nhưng chính xác hơn
            subsample=0.85,          # Tăng từ 0.8 → 0.85
            colsample_bytree=0.85,   # Tăng từ 0.8 → 0.85
            min_child_weight=2,      # Thêm regularization
            random_state=42,
            verbosity=0
        )
        model_days.fit(X_train, y_days_train)
        
        # Train XGBoost cho cost prediction
        model_cost = XGBRegressor(
            n_estimators=200,        # Tăng từ 100 → 200 trees
            max_depth=8,             # Tăng từ 6 → 8
            learning_rate=0.05,      # Giảm từ 0.1 → 0.05
            subsample=0.85,          # Tăng từ 0.8 → 0.85
            colsample_bytree=0.85,   # Tăng từ 0.8 → 0.85
            min_child_weight=2,      # Thêm regularization
            random_state=42,
            verbosity=0
        )
        model_cost.fit(X_train, y_cost_train)
        
        # Đánh giá model
        y_days_pred = model_days.predict(X_test)
        y_cost_pred = model_cost.predict(X_test)
        
        days_mae = mean_absolute_error(y_days_test, y_days_pred)
        days_r2 = r2_score(y_days_test, y_days_pred)
        cost_mae = mean_absolute_error(y_cost_test, y_cost_pred)
        cost_r2 = r2_score(y_cost_test, y_cost_pred)
        
        _logger.info(f"📊 XGBoost Days Model - MAE: {days_mae:.2f} days, R²: {days_r2:.4f}")
        _logger.info(f"📊 XGBoost Cost Model - MAE: {cost_mae:,.0f} VND, R²: {cost_r2:.4f}")
        _logger.info(f"📦 Nguồn dữ liệu: {data_source.upper()} ({len(df)} samples)")
        
        # Lưu models với metrics
        with open(MODEL_PATH, 'wb') as f:
            pickle.dump({
                'days': model_days, 
                'cost': model_cost,
                'metrics': {
                    'days_r2': days_r2,
                    'cost_r2': cost_r2,
                    'days_mae': days_mae,
                    'cost_mae': cost_mae,
                    'trained_at': datetime.now().isoformat(),
                    'n_samples': len(df),
                    'data_source': data_source  # 'real' hoặc 'synthetic'
                }
            }, f)
        with open(SCALER_PATH, 'wb') as f:
            pickle.dump(scaler, f)
        
        _logger.info(f"✅ XGBoost models đã được lưu tại {MODEL_PATH}")
        return True

    def _predict_with_xgboost(self, asset):
        """
        Dự đoán sử dụng XGBoost model đã train
        """
        # Load models
        with open(MODEL_PATH, 'rb') as f:
            models = pickle.load(f)
        with open(SCALER_PATH, 'rb') as f:
            scaler = pickle.load(f)
        
        # Chuẩn bị features
        today = fields.Date.today()
        purchase_date = asset.purchase_date or today
        days_since_purchase = (today - purchase_date).days
        asset_value = asset.current_value or asset.purchase_price or 1000000
        
        # Map category to number
        category_map = {'computer': 0, 'furniture': 1, 'electronics': 2}
        category_name = asset.category_id.name.lower() if asset.category_id else ''
        category_type = 0  # Default: IT
        for key, val in category_map.items():
            if key in category_name:
                category_type = val
                break
        
        # Ước tính usage intensity từ state
        state_intensity = {'available': 0.3, 'in_use': 0.8, 'maintenance': 0.5, 'disposed': 0.1}
        usage_intensity = state_intensity.get(asset.state, 0.5)
        
        # Đếm số prediction trước đó
        previous_count = self.search_count([('asset_id', '=', asset.id)])
        
        # Last maintenance (giả sử 30 ngày nếu không có data)
        last_maintenance_days = 30
        
        # Tạo feature vector
        features = np.array([[
            days_since_purchase,
            asset_value,
            category_type,
            usage_intensity,
            previous_count,
            last_maintenance_days
        ]])
        
        # Scale features
        features_scaled = scaler.transform(features)
        
        # Predict
        days_to_maintenance = int(models['days'].predict(features_scaled)[0])
        predicted_cost = models['cost'].predict(features_scaled)[0]
        
        # Giới hạn hợp lý
        days_to_maintenance = max(7, min(180, days_to_maintenance))
        predicted_cost = max(0, predicted_cost)
        
        next_date = today + timedelta(days=days_to_maintenance)
        
        # Tính risk level
        age_months = days_since_purchase / 30
        risk_score = (age_months / 24) + (usage_intensity * 0.5) + (previous_count * 0.1)
        if risk_score < 0.5:
            risk_level = 'low'
        elif risk_score < 1.0:
            risk_level = 'medium'
        elif risk_score < 1.5:
            risk_level = 'high'
        else:
            risk_level = 'critical'
        
        # Tính confidence score ĐỘNG dựa trên R² thực tế của model
        metrics = models.get('metrics', {})
        days_r2 = metrics.get('days_r2', 0.85)
        cost_r2 = metrics.get('cost_r2', 0.82)
        
        # Confidence = Trung bình R² của 2 models * 100, điều chỉnh theo đặc điểm tài sản
        base_confidence = ((days_r2 + cost_r2) / 2) * 100
        
        # Điều chỉnh confidence dựa trên:
        # - Tài sản mới (ít data) → giảm confidence
        # - Tài sản có nhiều lần bảo trì trước → tăng confidence (có pattern rõ)
        if age_months < 3:
            confidence_adj = -10  # Tài sản quá mới, chưa đủ pattern
        elif age_months < 12:
            confidence_adj = -5   # Còn mới
        elif previous_count > 3:
            confidence_adj = 5    # Có nhiều data bảo trì → pattern rõ hơn
        else:
            confidence_adj = 0
        
        confidence = min(99, max(50, base_confidence + confidence_adj))
        
        # Tạo prediction record
        return self.create({
            'asset_id': asset.id,
            'next_maintenance_date': next_date,
            'predicted_cost': predicted_cost,
            'confidence_score': round(confidence, 1),
            'prediction_reason': f'🤖 XGBoost AI (R²={days_r2:.1%}, Data: {metrics.get("data_source", "unknown").upper()}): Dự đoán {days_to_maintenance} ngày, chi phí {predicted_cost:,.0f} VND. Tuổi: {age_months:.0f} tháng, mức sử dụng: {usage_intensity*100:.0f}%',
            'risk_level': risk_level,
            'maintenance_type': 'preventive' if days_to_maintenance > 30 else 'corrective',
            'state': 'predicted'
        })

    def _get_maintenance_history(self, asset):
        """Lấy lịch sử bảo trì (demo data)"""
        # TODO: Tích hợp với module maintenance thực tế
        return []

    def _train_and_predict(self, asset, history):
        """Fallback method - sử dụng XGBoost thay vì Linear Regression"""
        return self._predict_with_xgboost(asset)

    def _predict_by_rules(self, asset):
        """
        Dự đoán dựa trên rule-based khi không đủ dữ liệu
        Rules:
        - Tài sản mới (<6 tháng): Bảo trì sau 3 tháng, chi phí 5% giá trị
        - Tài sản trung bình (6-24 tháng): Bảo trì 2 tháng/lần, chi phí 10%
        - Tài sản cũ (>24 tháng): Bảo trì hàng tháng, chi phí 15-20%
        """
        today = fields.Date.today()
        purchase_date = asset.purchase_date or today
        age_months = (today - purchase_date).days / 30
        
        base_value = asset.current_value or asset.purchase_price or 1000000
        
        if age_months < 6:
            # Tài sản mới
            next_date = today + timedelta(days=90)
            cost = base_value * 0.05
            risk = 'low'
            reason = 'Tài sản mới, bảo trì định kỳ tiêu chuẩn'
        elif age_months < 24:
            # Tài sản trung bình
            next_date = today + timedelta(days=60)
            cost = base_value * 0.10
            risk = 'medium'
            reason = 'Tài sản đã qua sử dụng, cần bảo trì định kỳ'
        else:
            # Tài sản cũ
            next_date = today + timedelta(days=30)
            cost = base_value * 0.18
            risk = 'high'
            reason = 'Tài sản đã cũ, rủi ro hư hỏng cao'
        
        confidence = 60.0 if age_months < 6 else 70.0
        
        return self.create({
            'asset_id': asset.id,
            'next_maintenance_date': next_date,
            'predicted_cost': cost,
            'confidence_score': confidence,
            'prediction_reason': reason,
            'risk_level': risk,
            'maintenance_type': 'preventive',
            'state': 'predicted'
        })

    def action_retrain_model(self):
        """
        Train lại XGBoost model với dữ liệu mới
        Có thể gọi từ UI hoặc scheduled action
        """
        if not XGBOOST_AVAILABLE:
            raise UserError(_('XGBoost chưa được cài đặt!\n\nChạy lệnh: pip3 install xgboost'))
        
        # Xóa model cũ nếu có
        if os.path.exists(MODEL_PATH):
            os.remove(MODEL_PATH)
        if os.path.exists(SCALER_PATH):
            os.remove(SCALER_PATH)
        
        # Train lại
        success = self._train_xgboost_model()
        
        if success:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': '🤖 XGBoost AI',
                    'message': 'Đã train lại model thành công với 1000 dữ liệu!',
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            raise UserError(_('Không thể train model. Kiểm tra log để biết chi tiết.'))

    @api.model
    def get_model_info(self):
        """Lấy thông tin về model hiện tại"""
        info = {
            'xgboost_available': XGBOOST_AVAILABLE,
            'ml_available': ML_AVAILABLE,
            'model_trained': os.path.exists(MODEL_PATH),
            'model_path': MODEL_PATH,
        }
        
        if os.path.exists(MODEL_PATH):
            import os.path as osp
            info['model_size'] = osp.getsize(MODEL_PATH)
            info['model_modified'] = datetime.fromtimestamp(osp.getmtime(MODEL_PATH)).strftime('%Y-%m-%d %H:%M:%S')
        
        return info

    @api.model
    def batch_predict_all_assets(self):
        """Dự đoán hàng loạt cho tất cả tài sản active"""
        assets = self.env['asset'].search([
            ('state', 'in', ['available', 'in_use'])
        ])
        
        predictions = []
        for asset in assets:
            try:
                prediction = self.predict_maintenance_for_asset(asset.id)
                predictions.append(prediction)
            except Exception as e:
                _logger.error(f"Lỗi dự đoán cho tài sản {asset.name}: {e}")
        
        return {
            'type': 'ir.actions.act_window',
            'name': f'🤖 XGBoost AI: Dự đoán {len(predictions)} tài sản',
            'res_model': 'asset.maintenance.prediction',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', [p.id for p in predictions])],
            'context': {'create': False}
        }

    @api.model
    def analyze_spending_trends(self, months=12):
        """
        Phân tích xu hướng chi tiêu
        Trả về báo cáo chi phí bảo trì theo thời gian
        """
        end_date = fields.Date.today()
        start_date = end_date - timedelta(days=months * 30)
        
        predictions = self.search([
            ('prediction_date', '>=', start_date),
            ('prediction_date', '<=', end_date),
            ('state', '!=', 'cancelled')
        ])
        
        # Tổng hợp theo tháng
        monthly_costs = {}
        for pred in predictions:
            month_key = pred.prediction_date.strftime('%Y-%m')
            if month_key not in monthly_costs:
                monthly_costs[month_key] = 0
            monthly_costs[month_key] += pred.predicted_cost
        
        # Tính trung bình và dự đoán tương lai
        avg_monthly = sum(monthly_costs.values()) / len(monthly_costs) if monthly_costs else 0
        
        # Dự báo 3 tháng tới
        forecast = {}
        for i in range(1, 4):
            future_date = end_date + timedelta(days=i * 30)
            month_key = future_date.strftime('%Y-%m')
            # Simple forecast = average (có thể improve với time series)
            forecast[month_key] = avg_monthly * 1.05  # Tăng 5% mỗi tháng
        
        return {
            'historical': monthly_costs,
            'forecast': forecast,
            'avg_monthly': avg_monthly,
            'total_predicted': sum(monthly_costs.values())
        }

    def action_schedule_maintenance(self):
        """Tạo lịch bảo trì từ dự đoán"""
        self.ensure_one()
        
        if self.state != 'predicted':
            raise UserError(_('Chỉ có thể lên lịch cho dự đoán đã xác nhận!'))
        
        history = self._create_maintenance_schedule_record()
        self._send_maintenance_schedule_telegram(history)
        self.state = 'scheduled'
        
        self.message_post(
            body=f"Đã lên lịch bảo trì cho {self.asset_id.name} vào ngày {self.next_maintenance_date}. "
                 f"Chi phí dự kiến: {self.predicted_cost:,.0f} {self.currency_id.symbol}"
        )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': 'Đã lên lịch bảo trì thành công!',
                'type': 'success',
                'sticky': False,
            }
        }

    def _create_maintenance_schedule_record(self):
        """Tạo record lịch sử bảo trì ở trạng thái draft từ dự đoán"""
        self.ensure_one()

        History = self.env['asset.maintenance.history']

        existing = History.search([
            ('prediction_id', '=', self.id),
            ('asset_id', '=', self.asset_id.id),
            ('maintenance_date', '=', self.next_maintenance_date)
        ], limit=1)
        if existing:
            return existing

        technician = self.asset_id.manager_id or self.asset_id.assigned_to_id

        return History.create({
            'asset_id': self.asset_id.id,
            'maintenance_date': self.next_maintenance_date,
            'maintenance_type': self.maintenance_type or 'preventive',
            'actual_cost': 0,
            'predicted_cost': self.predicted_cost,
            'prediction_id': self.id,
            'description': f'Tự động lên lịch bảo trì từ dự đoán AI cho {self.asset_id.name}',
            'technician_id': technician.id if technician else False,
            'state': 'draft',
        })

    def _send_maintenance_schedule_telegram(self, history_record):
        """Gửi thông báo Telegram khi lên lịch bảo trì"""
        if not history_record:
            return False

        telegram_enabled = self.env['ir.config_parameter'].sudo().get_param(
            'nhan_su.telegram_notification_enabled', default=False
        )
        if not telegram_enabled:
            return False

        telegram_helper = self.env['telegram.helper']
        asset = self.asset_id
        recipients = self._get_maintenance_notification_recipients(asset)

        if not recipients:
            return False

        message = (
            "🛠️ <b>LỊCH BẢO TRÌ TỰ ĐỘNG</b>\n\n"
            f"📦 <b>Tài sản:</b> {asset.name}\n"
            f"🏷️ <b>Mã tài sản:</b> {asset.asset_code}\n"
            f"📅 <b>Ngày bảo trì:</b> {history_record.maintenance_date.strftime('%d/%m/%Y')}\n"
            f"🔧 <b>Loại bảo trì:</b> {history_record.maintenance_type}\n"
            f"💰 <b>Chi phí dự kiến:</b> {self.predicted_cost:,.0f} {self.currency_id.symbol}\n"
            f"⚠️ <b>Mức độ rủi ro:</b> {self.risk_level}\n"
        )

        for recipient in recipients:
            if recipient.telegram_chat_id and recipient.telegram_enabled:
                telegram_helper.send_message(recipient.telegram_chat_id, message)

        return True

    def _get_maintenance_notification_recipients(self, asset):
        """Lấy danh sách nhân viên nhận thông báo bảo trì"""
        recipients = self.env['hr.employee.extended']
        if asset.manager_id:
            recipients |= asset.manager_id
        if asset.assigned_to_id and asset.assigned_to_id not in recipients:
            recipients |= asset.assigned_to_id
        return recipients

    @api.model
    def cron_auto_schedule_maintenance(self, days_ahead=7):
        """
        Tự động lên lịch bảo trì cho các dự đoán sắp đến hạn và gửi Telegram
        """
        today = fields.Date.today()
        deadline = today + timedelta(days=days_ahead)

        preds = self.search([
            ('state', '=', 'predicted'),
            ('next_maintenance_date', '!=', False),
            ('next_maintenance_date', '<=', deadline)
        ])

        for pred in preds:
            history = pred._create_maintenance_schedule_record()
            pred._send_maintenance_schedule_telegram(history)
            pred.state = 'scheduled'

        return True

    def action_view_cost_trends(self):
        """Xem xu hướng chi phí"""
        trends = self.analyze_spending_trends(12)
        
        # Format số tiền dễ đọc
        def format_vnd(amount):
            if amount >= 1000000000:
                return f"{amount/1000000000:,.1f} tỷ VNĐ"
            elif amount >= 1000000:
                return f"{amount/1000000:,.1f} triệu VNĐ"
            else:
                return f"{amount:,.0f} VNĐ"
        
        # Tạo message text thuần
        forecast_total = sum(trends['forecast'].values()) if trends.get('forecast') else 0
        
        message = (
            f"📊 PHÂN TÍCH CHI PHÍ 12 THÁNG\n\n"
            f"💰 Tổng chi phí dự kiến: {format_vnd(trends['total_predicted'])}\n"
            f"📅 Trung bình/tháng: {format_vnd(trends['avg_monthly'])}\n"
            f"🔮 Dự báo 3 tháng tới: {format_vnd(forecast_total)}"
        )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': '📊 Xu Hướng Chi Phí Bảo Trì',
                'message': message,
                'type': 'info',
                'sticky': True,
            }
        }
