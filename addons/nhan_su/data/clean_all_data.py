#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script xóa TOÀN BỘ dữ liệu demo (nhân sự, tài sản, danh mục)
Chạy: cd /home/giapdepzaii/odoo-fitdnu && python3 addons/nhan_su/data/clean_all_data.py
"""

import sys
import os

# Thêm đường dẫn Odoo
sys.path.insert(0, '/home/giapdepzaii/odoo-fitdnu')

from odoo import api, SUPERUSER_ID
import odoo

def clean_all_data(env):
    """Xóa TOÀN BỘ dữ liệu demo"""
    
    print("\n" + "="*60)
    print("🗑️  XÓA TOÀN BỘ DỮ LIỆU DEMO")
    print("="*60 + "\n")
    
    total_deleted = 0
    
    # === PHẦN 1: TÀI SẢN ===
    print("📦 [1/3] XÓA DỮ LIỆU TÀI SẢN")
    print("-" * 60)
    
    # 1.1 Xóa Maintenance History
    print("  🔧 Lịch sử bảo trì...", end=" ")
    count = env['asset.maintenance.history'].search_count([])
    if count > 0:
        env['asset.maintenance.history'].search([]).unlink()
        total_deleted += count
        print(f"✅ {count} records")
    else:
        print("⏭️  Trống")
    
    # 1.2 Xóa Maintenance Predictions
    print("  🤖 Dự đoán AI...", end=" ")
    count = env['asset.maintenance.prediction'].search_count([])
    if count > 0:
        env['asset.maintenance.prediction'].search([]).unlink()
        total_deleted += count
        print(f"✅ {count} records")
    else:
        print("⏭️  Trống")
    
    # 1.3 Xóa Assets
    print("  🏢 Tài sản...", end=" ")
    count = env['asset'].search_count([])
    if count > 0:
        env['asset'].search([]).unlink()
        total_deleted += count
        print(f"✅ {count} records")
    else:
        print("⏭️  Trống")
    
    # 1.4 Xóa Asset Categories
    print("  📁 Danh mục tài sản...", end=" ")
    count = env['asset.category'].search_count([])
    if count > 0:
        env['asset.category'].search([]).unlink()
        total_deleted += count
        print(f"✅ {count} records")
    else:
        print("⏭️  Trống")
    
    # 1.5 Xóa Asset Locations
    print("  📍 Địa điểm tài sản...", end=" ")
    count = env['asset.location'].search_count([])
    if count > 0:
        env['asset.location'].search([]).unlink()
        total_deleted += count
        print(f"✅ {count} records")
    else:
        print("⏭️  Trống")
    
    env.cr.commit()
    
    # === PHẦN 2: DANH MỤC CHUNG (xóa trước vì có FK với nhân sự) ===
    print("\n📚 [2/4] XÓA DANH MỤC CHUNG")
    print("-" * 60)
    
    # 2.1 Xóa Meeting Room Bookings (có FK đến employee)
    print("  📅 Đặt phòng họp...", end=" ")
    count = env['meeting.room.booking'].search_count([])
    if count > 0:
        env['meeting.room.booking'].search([]).unlink()
        total_deleted += count
        print(f"✅ {count} records")
    else:
        print("⏭️  Trống")
    
    # 2.2 Xóa Meeting Rooms
    print("  🏛️  Phòng họp...", end=" ")
    count = env['meeting.room'].search_count([])
    if count > 0:
        env['meeting.room'].search([]).unlink()
        total_deleted += count
        print(f"✅ {count} records")
    else:
        print("⏭️  Trống")
    
    env.cr.commit()
    
    # === PHẦN 3: NHÂN SỰ ===
    print("\n👥 [3/4] XÓA DỮ LIỆU NHÂN SỰ")
    print("-" * 60)
    
    # 2.1 Xóa Lịch sử thay đổi nhân viên
    print("  📜 Lịch sử thay đổi...", end=" ")
    count = env['employee.history'].search_count([])
    if count > 0:
        env['employee.history'].search([]).unlink()
        total_deleted += count
        print(f"✅ {count} records")
    else:
        print("⏭️  Trống")
    
    # 2.2 Xóa Lịch sử sử dụng tài sản
    print("  📋 Lịch sử sử dụng tài sản...", end=" ")
    count = env['asset.usage.history'].search_count([])
    if count > 0:
        env['asset.usage.history'].search([]).unlink()
        total_deleted += count
        print(f"✅ {count} records")
    else:
        print("⏭️  Trống")
    
    # 2.3 Xóa Nhân viên (chỉ xóa những người không phải admin/user hệ thống)
    print("  👤 Nhân viên...", end=" ")
    # Tìm những nhân viên có mã NV (demo data)
    employees = env['hr.employee.extended'].search([('employee_code', '=like', 'NV%')])
    count = len(employees)
    if count > 0:
        employees.unlink()
        total_deleted += count
        print(f"✅ {count} records")
    else:
        print("⏭️  Trống")
    
    env.cr.commit()
    
    # === PHẦN 4: DANH MỤC THAM CHIẾU ===
    print("\n📖 [4/4] XÓA DANH MỤC THAM CHIẾU")
    print("-" * 60)
    
    # 3.1 Xóa Meeting Room Bookings
    print("  📅 Đặt phòng họp...", end=" ")
    count = env['meeting.room.booking'].search_count([])
    if count > 0:
        env['meeting.room.booking'].search([]).unlink()
        total_deleted += count
        print(f"✅ {count} records")
    else:
        print("⏭️  Trống")
    
    # 3.2 Xóa Meeting Rooms
    print("  🏛️  Phòng họp...", end=" ")
    count = env['meeting.room'].search_count([])
    if count > 0:
        env['meeting.room'].search([]).unlink()
        total_deleted += count
        print(f"✅ {count} records")
    else:
        print("⏭️  Trống")
    
    # 3.1 Xóa Meeting Room Bookings
    print("  📅 Đặt phòng họp...", end=" ")
    count = env['meeting.room.booking'].search_count([])
    if count > 0:
        env['meeting.room.booking'].search([]).unlink()
        total_deleted += count
        print(f"✅ {count} records")
    else:
        print("⏭️  Trống")
    
    # 3.2 Xóa Meeting Rooms
    print("  🏛️  Phòng họp...", end=" ")
    count = env['meeting.room'].search_count([])
    if count > 0:
        env['meeting.room'].search([]).unlink()
        total_deleted += count
        print(f"✅ {count} records")
    else:
        print("⏭️  Trống")
    
    # 3.3 Xóa Chứng chỉ bằng cấp
    print("  🎓 Chứng chỉ bằng cấp...", end=" ")
    count = env['chung_chi_bang_cap'].search_count([])
    if count > 0:
        env['chung_chi_bang_cap'].search([]).unlink()
        total_deleted += count
        print(f"✅ {count} records")
    else:
        print("⏭️  Trống")
    
    # 3.4 Xóa Chức vụ
    print("  👔 Chức vụ...", end=" ")
    count = env['chuc_vu'].search_count([])
    if count > 0:
        env['chuc_vu'].search([]).unlink()
        total_deleted += count
        print(f"✅ {count} records")
    else:
        print("⏭️  Trống")
    
    # 3.5 Xóa Đơn vị
    print("  🏢 Đơn vị/Phòng ban...", end=" ")
    count = env['don_vi'].search_count([])
    if count > 0:
        env['don_vi'].search([]).unlink()
        total_deleted += count
        print(f"✅ {count} records")
    else:
        print("⏭️  Trống")
    
    env.cr.commit()
    
    # === PHẦN 5: FILE HỆ THỐNG ===
    print("\n💾 [5/5] XÓA FILE HỆ THỐNG")
    print("-" * 60)
    
    # 4.1 Xóa XGBoost model
    model_path = '/tmp/odoo_xgboost_maintenance_model.json'
    print(f"  🧠 AI Model...", end=" ")
    if os.path.exists(model_path):
        os.remove(model_path)
        print(f"✅ Đã xóa")
    else:
        print("⏭️  Không tồn tại")
    
    # Tổng kết
    print("\n" + "="*60)
    print("✨ KẾT QUẢ")
    print("="*60)
    print(f"📊 Tổng số records đã xóa: {total_deleted:,}")
    print("✅ Database đã được làm sạch!")
    print("\n💡 Bạn có thể chạy lại script tạo dữ liệu:")
    print("   python3 addons/nhan_su/data/demo_data_generator.py")
    print("="*60 + "\n")

if __name__ == '__main__':
    try:
        print("\n📦 Đang khởi động Odoo environment...")
        
        # Parse config
        odoo.tools.config.parse_config(['-c', 'odoo.conf', '-d', 'giapdepzaii'])
        
        # Tạo environment
        with odoo.api.Environment.manage():
            registry = odoo.registry('giapdepzaii')
            with registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                clean_all_data(env)
        
        print("✅ HOÀN TẤT!\n")
        
    except Exception as e:
        print(f"\n❌ LỖI: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
