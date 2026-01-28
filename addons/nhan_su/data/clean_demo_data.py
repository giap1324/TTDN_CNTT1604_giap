#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script xóa sạch dữ liệu demo
Chạy script này trong Odoo shell hoặc Python:
./odoo-bin shell -c odoo.conf -d giapdepzaii
>>> exec(open('addons/nhan_su/data/clean_demo_data.py').read())

Hoặc:
cd /home/giapdepzaii/odoo-fitdnu
python3 addons/nhan_su/data/clean_demo_data.py
"""

import sys
import os

def clean_demo_data(env):
    """Xóa tất cả dữ liệu demo"""
    
    print("🗑️  Bắt đầu xóa dữ liệu demo...\n")
    
    # 1. Xóa Maintenance History
    print("🔧 Xóa lịch sử bảo trì...")
    history_count = env['asset.maintenance.history'].search_count([])
    if history_count > 0:
        histories = env['asset.maintenance.history'].search([])
        histories.unlink()
        print(f"  ✅ Đã xóa {history_count} maintenance history records")
    else:
        print("  ⏭️  Không có maintenance history nào")
    
    # 2. Xóa Maintenance Predictions
    print("\n🤖 Xóa dự đoán AI...")
    prediction_count = env['asset.maintenance.prediction'].search_count([])
    if prediction_count > 0:
        predictions = env['asset.maintenance.prediction'].search([])
        predictions.unlink()
        print(f"  ✅ Đã xóa {prediction_count} AI predictions")
    else:
        print("  ⏭️  Không có predictions nào")
    
    # 3. Xóa Assets
    print("\n🏢 Xóa tài sản...")
    asset_count = env['asset'].search_count([])
    if asset_count > 0:
        assets = env['asset'].search([])
        assets.unlink()
        print(f"  ✅ Đã xóa {asset_count} assets")
    else:
        print("  ⏭️  Không có assets nào")
    
    # 4. Xóa Categories
    print("\n📁 Xóa danh mục...")
    category_count = env['asset.category'].search_count([])
    if category_count > 0:
        categories = env['asset.category'].search([])
        categories.unlink()
        print(f"  ✅ Đã xóa {category_count} categories")
    else:
        print("  ⏭️  Không có categories nào")
    
    # 5. Xóa Locations
    print("\n📍 Xóa địa điểm...")
    location_count = env['asset.location'].search_count([])
    if location_count > 0:
        locations = env['asset.location'].search([])
        locations.unlink()
        print(f"  ✅ Đã xóa {location_count} locations")
    else:
        print("  ⏭️  Không có locations nào")
    
    # 6. Xóa XGBoost model file (nếu có)
    print("\n🧠 Xóa AI model file...")
    model_path = '/tmp/odoo_xgboost_maintenance_model.json'
    if os.path.exists(model_path):
        os.remove(model_path)
        print(f"  ✅ Đã xóa file: {model_path}")
    else:
        print(f"  ⏭️  File không tồn tại: {model_path}")
    
    env.cr.commit()
    
    print("""
╔══════════════════════════════════════════╗
║         XÓA DỮ LIỆU THÀNH CÔNG         ║
╠══════════════════════════════════════════╣
║ ✅ Maintenance History đã xóa            ║
║ ✅ AI Predictions đã xóa                 ║
║ ✅ Assets đã xóa                         ║
║ ✅ Categories đã xóa                     ║
║ ✅ Locations đã xóa                      ║
║ ✅ AI Model file đã xóa                  ║
╚══════════════════════════════════════════╝

💡 Bạn có thể chạy lại script tạo dữ liệu:
   python3 addons/nhan_su/data/demo_data_generator.py
""")


# Chạy nếu được gọi trực tiếp từ Python (không phải Odoo shell)
if __name__ == '__main__':
    try:
        # Kiểm tra xem có trong Odoo environment không
        env
        clean_demo_data(env)
        print("\n✅ HOÀN TẤT!\n")
    except NameError:
        # Không có env - chạy từ command line
        print("📦 Đang khởi động Odoo environment...")
        
        # Thêm đường dẫn Odoo vào sys.path
        odoo_path = '/home/giapdepzaii/odoo-fitdnu'
        if odoo_path not in sys.path:
            sys.path.insert(0, odoo_path)
        
        from odoo import api, SUPERUSER_ID
        import odoo
        
        # Parse config
        config_file = os.path.join(odoo_path, 'odoo.conf')
        database = 'giapdepzaii'
        
        odoo.tools.config.parse_config(['-c', config_file, '-d', database])
        
        # Tạo environment
        with odoo.api.Environment.manage():
            registry = odoo.registry(database)
            with registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                clean_demo_data(env)
        
        print("\n✅ HOÀN TẤT! Dữ liệu đã được xóa sạch.\n")
