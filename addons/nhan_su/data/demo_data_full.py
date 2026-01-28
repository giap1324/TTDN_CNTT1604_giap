#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script tạo dữ liệu giả lập HOÀN CHỈNH cho toàn bộ hệ thống
Chạy: cd /home/giapdepzaii/odoo-fitdnu && python3 addons/nhan_su/data/demo_data_full.py
"""

import sys
import os
import random
from datetime import datetime, timedelta

# Thêm đường dẫn Odoo
sys.path.insert(0, '/home/giapdepzaii/odoo-fitdnu')

from odoo import api, SUPERUSER_ID
import odoo

def generate_full_demo_data(env):
    """Tạo dữ liệu demo HOÀN CHỈNH và ĐỒNG BỘ"""
    
    print("\n" + "="*70)
    print("TẠO DỮ LIỆU DEMO HOÀN CHỈNH CHO TOÀN BỘ HỆ THỐNG")
    print("="*70 + "\n")
    
    # ============ PHẦN 1: CẤU TRÚC TỔ CHỨC ============
    print("[1/7] TẠO CẤU TRÚC TỔ CHỨC")
    print("-" * 70)
    
    # 1.1 Tạo Đơn vị/Phòng ban (cả don_vi và hr.department)
    print("  Tạo đơn vị/phòng ban...", end=" ")
    don_vi_data = [
        {'ten_don_vi': 'Ban Giám Đốc', 'ma_don_vi': 'BGD', 'mo_ta': 'Ban lãnh đạo điều hành'},
        {'ten_don_vi': 'Phòng Hành Chính', 'ma_don_vi': 'HC', 'mo_ta': 'Phòng hành chính nhân sự'},
        {'ten_don_vi': 'Phòng Kế Toán', 'ma_don_vi': 'KT', 'mo_ta': 'Phòng tài chính kế toán'},
        {'ten_don_vi': 'Phòng Kinh Doanh', 'ma_don_vi': 'KD', 'mo_ta': 'Phòng kinh doanh bán hàng'},
        {'ten_don_vi': 'Phòng Marketing', 'ma_don_vi': 'MKT', 'mo_ta': 'Phòng marketing truyền thông'},
        {'ten_don_vi': 'Phòng IT', 'ma_don_vi': 'IT', 'mo_ta': 'Phòng công nghệ thông tin'},
        {'ten_don_vi': 'Phòng Kỹ Thuật', 'ma_don_vi': 'TECH', 'mo_ta': 'Phòng kỹ thuật sản xuất'},
        {'ten_don_vi': 'Phòng Dịch Vụ Khách Hàng', 'ma_don_vi': 'DVKH', 'mo_ta': 'Chăm sóc khách hàng'},
    ]
    
    don_vi_objs = []
    department_objs = []
    for dv_data in don_vi_data:
        dv = env['don_vi'].create(dv_data)
        don_vi_objs.append(dv)
        
        # Tạo hr.department tương ứng cho nhân viên
        dept = env['hr.department'].create({
            'name': dv_data['ten_don_vi'],
            'company_id': 1,  # Default company
        })
        department_objs.append(dept)
    print(f"Done {len(don_vi_objs)} don vi + {len(department_objs)} departments")
    
    # 1.2 Tạo Chức vụ
    print("  Tạo chức vụ...", end=" ")
    chuc_vu_data = [
        {'ten_chuc_vu': 'Giám Đốc', 'ma_chuc_vu': 'GD', 'mo_ta': 'Giám đốc điều hành'},
        {'ten_chuc_vu': 'Phó Giám Đốc', 'ma_chuc_vu': 'PGD', 'mo_ta': 'Phó giám đốc'},
        {'ten_chuc_vu': 'Trưởng Phòng', 'ma_chuc_vu': 'TP', 'mo_ta': 'Trưởng phòng ban'},
        {'ten_chuc_vu': 'Phó Phòng', 'ma_chuc_vu': 'PP', 'mo_ta': 'Phó phòng'},
        {'ten_chuc_vu': 'Trưởng Nhóm', 'ma_chuc_vu': 'TN', 'mo_ta': 'Trưởng nhóm/team leader'},
        {'ten_chuc_vu': 'Nhân Viên Chính', 'ma_chuc_vu': 'NVC', 'mo_ta': 'Nhân viên chính thức'},
        {'ten_chuc_vu': 'Nhân Viên', 'ma_chuc_vu': 'NV', 'mo_ta': 'Nhân viên'},
        {'ten_chuc_vu': 'Thực Tập Sinh', 'ma_chuc_vu': 'TTS', 'mo_ta': 'Thực tập sinh'},
    ]
    
    chuc_vu_objs = []
    for cv_data in chuc_vu_data:
        cv = env['chuc_vu'].create(cv_data)
        chuc_vu_objs.append(cv)
    print(f"Done {len(chuc_vu_objs)} chuc vu")
    
    # 1.3 Tạo Chứng chỉ bằng cấp
    print("  Tạo chứng chỉ bằng cấp...", end=" ")
    chung_chi_data = [
        {'ten_chung_chi_bang_cap': 'Đại học Kinh tế', 'ma_chung_chi_bang_cap': 'DH_KT', 'mo_ta': 'Bằng cấp đại học'},
        {'ten_chung_chi_bang_cap': 'Đại học Công nghệ', 'ma_chung_chi_bang_cap': 'DH_CN', 'mo_ta': 'Bằng cấp đại học'},
        {'ten_chung_chi_bang_cap': 'Đại học Kỹ thuật', 'ma_chung_chi_bang_cap': 'DH_CNTT', 'mo_ta': 'Bằng cấp đại học'},
        {'ten_chung_chi_bang_cap': 'Thạc sĩ Quản trị', 'ma_chung_chi_bang_cap': 'THS_QT', 'mo_ta': 'Bằng cấp thạc sĩ'},
        {'ten_chung_chi_bang_cap': 'Kế toán trưởng', 'ma_chung_chi_bang_cap': 'KTT', 'mo_ta': 'Chứng chỉ hành nghề'},
        {'ten_chung_chi_bang_cap': 'PMP', 'ma_chung_chi_bang_cap': 'PMP', 'mo_ta': 'Chứng chỉ quản lý dự án'},
        {'ten_chung_chi_bang_cap': 'AWS Certified', 'ma_chung_chi_bang_cap': 'AWS', 'mo_ta': 'Chứng chỉ AWS'},
        {'ten_chung_chi_bang_cap': 'Google Analytics', 'ma_chung_chi_bang_cap': 'GA', 'mo_ta': 'Chứng chỉ GA'},
    ]
    
    chung_chi_objs = []
    for cc_data in chung_chi_data:
        cc = env['chung_chi_bang_cap'].create(cc_data)
        chung_chi_objs.append(cc)
    print(f"Done {len(chung_chi_objs)} chung chi")
    
    env.cr.commit()
    
    # ============ PHẦN 2: NHÂN SỰ ============
    print("\n[2/7] TẠO DỮ LIỆU NHÂN SỰ")
    print("-" * 70)
    
    print("  Tạo nhân viên...", end=" ")
    ho_dem = ['Nguyễn', 'Trần', 'Lê', 'Phạm', 'Hoàng', 'Huỳnh', 'Võ', 'Phan', 'Vũ', 'Đặng', 'Bùi', 'Đỗ', 'Hồ', 'Ngô', 'Dương']
    ten_lot = ['Văn', 'Thị', 'Minh', 'Hoàng', 'Thu', 'Anh', 'Đức', 'Hải', 'Thanh', 'Phương', 'Quang', 'Hồng', 'Tuấn', 'Linh']
    ten = ['An', 'Bình', 'Chi', 'Dũng', 'Hà', 'Huy', 'Khánh', 'Linh', 'Long', 'Mai', 'Nam', 'Nga', 'Phong', 'Quân', 'Sơn', 
           'Tâm', 'Trung', 'Tú', 'Uyên', 'Vân', 'Xuân', 'Yến', 'Đạt', 'Hằng', 'Hương']
    
    employee_objs = []
    num_employees = 30
    
    # Dùng tên ASCII cho email
    ascii_names = ['an', 'binh', 'chi', 'dung', 'ha', 'huy', 'khanh', 'linh', 'long', 'mai', 
                   'nam', 'nga', 'phong', 'quan', 'son', 'tam', 'trung', 'tu', 'uyen', 'van',
                   'xuan', 'yen', 'dat', 'hang', 'huong', 'tuan', 'thanh', 'minh', 'hoang', 'anh']
    
    for i in range(num_employees):
        ho = random.choice(ho_dem)
        lot = random.choice(ten_lot) if random.random() > 0.3 else ''
        name_part = random.choice(ten)
        full_name = f"{ho} {lot} {name_part}".strip().replace('  ', ' ')
        
        # Gán phòng ban và chức vụ ngẫu nhiên
        dept = random.choice(department_objs)
        position = random.choice(chuc_vu_objs)
        
        emp = env['hr.employee.extended'].create({
            'name': full_name,
            'phone': f"09{random.randint(10000000, 99999999)}",
            'personal_email': f"{ascii_names[i]}{i+1}@company.com",
            'hire_date': (datetime.now() - timedelta(days=random.randint(180, 1800))).strftime('%Y-%m-%d'),
            'contract_type': random.choice(['permanent', 'probation', 'temporary']),
            'department_id': dept.id,
            'job_title': position.ten_chuc_vu,  # Gán tên chức vụ
        })
        employee_objs.append(emp)
        
        if (i + 1) % 10 == 0:
            env.cr.commit()
    
    print(f"Done {len(employee_objs)} nhan vien")
    env.cr.commit()
    
    # ============ PHẦN 3: TÀI SẢN ============
    print("\n[3/7] TẠO DỮ LIỆU TÀI SẢN")
    print("-" * 70)
    
    # 3.1 Tạo Categories
    print("  Tạo danh mục tài sản...", end=" ")
    categories = [
        {'name': 'Máy tính', 'code': 'COMP', 'description': 'Máy tính để bàn và laptop'},
        {'name': 'Xe công ty', 'code': 'VEH', 'description': 'Xe ô tô công ty'},
        {'name': 'Máy in/Scan', 'code': 'PRINT', 'description': 'Máy in và máy photocopy'},
        {'name': 'Điều hòa', 'code': 'AC', 'description': 'Hệ thống điều hòa'},
        {'name': 'Thiết bị mạng', 'code': 'NET', 'description': 'Router, Switch, Modem'},
        {'name': 'Bàn ghế', 'code': 'FURN', 'description': 'Bàn ghế văn phòng'},
        {'name': 'Điện thoại', 'code': 'PHONE', 'description': 'Điện thoại di động'},
        {'name': 'Máy chiếu', 'code': 'PROJ', 'description': 'Máy chiếu phòng họp'},
    ]
    
    category_objs = []
    for cat_data in categories:
        cat = env['asset.category'].create(cat_data)
        category_objs.append(cat)
    print(f"Done {len(category_objs)} danh muc")
    
    # 3.2 Tạo Locations
    print("  Tạo địa điểm...", end=" ")
    locations = [
        {'name': 'Văn phòng Tầng 1', 'code': 'F1', 'description': 'Tầng 1 - Phòng hành chính'},
        {'name': 'Văn phòng Tầng 2', 'code': 'F2', 'description': 'Tầng 2 - Phòng kỹ thuật'},
        {'name': 'Văn phòng Tầng 3', 'code': 'F3', 'description': 'Tầng 3 - Phòng kinh doanh'},
        {'name': 'Văn phòng Tầng 4', 'code': 'F4', 'description': 'Tầng 4 - Ban giám đốc'},
        {'name': 'Kho tổng', 'code': 'WH', 'description': 'Kho lưu trữ thiết bị'},
        {'name': 'Bãi đỗ xe', 'code': 'PARK', 'description': 'Khu vực đỗ xe công ty'},
        {'name': 'Phòng Server', 'code': 'SVR', 'description': 'Phòng máy chủ'},
    ]
    
    location_objs = []
    for loc_data in locations:
        loc = env['asset.location'].create(loc_data)
        location_objs.append(loc)
    print(f"Done {len(location_objs)} dia diem")
    
    # 3.3 Tạo Assets (40-50 tài sản)
    print("  Tạo tài sản...", end=" ")
    asset_templates = [
        # Máy tính (15 chiếc)
        {'name': 'Dell Latitude 5420', 'category': 0, 'price_range': (15000000, 20000000), 'count': 4},
        {'name': 'HP ProBook 450 G8', 'category': 0, 'price_range': (12000000, 18000000), 'count': 3},
        {'name': 'Lenovo ThinkPad T14', 'category': 0, 'price_range': (18000000, 25000000), 'count': 3},
        {'name': 'MacBook Pro M1', 'category': 0, 'price_range': (30000000, 40000000), 'count': 2},
        {'name': 'Dell OptiPlex Desktop', 'category': 0, 'price_range': (10000000, 15000000), 'count': 3},
        
        # Xe công ty (5 chiếc)
        {'name': 'Toyota Camry', 'category': 1, 'price_range': (800000000, 1200000000), 'count': 2},
        {'name': 'Honda CR-V', 'category': 1, 'price_range': (900000000, 1100000000), 'count': 1},
        {'name': 'Mazda CX-5', 'category': 1, 'price_range': (850000000, 950000000), 'count': 1},
        {'name': 'Ford Ranger', 'category': 1, 'price_range': (750000000, 850000000), 'count': 1},
        
        # Máy in (6 chiếc)
        {'name': 'HP LaserJet Pro', 'category': 2, 'price_range': (5000000, 8000000), 'count': 3},
        {'name': 'Canon imageRUNNER', 'category': 2, 'price_range': (15000000, 25000000), 'count': 2},
        {'name': 'Epson L3150', 'category': 2, 'price_range': (3000000, 5000000), 'count': 1},
        
        # Điều hòa (8 chiếc)
        {'name': 'Daikin 2HP', 'category': 3, 'price_range': (10000000, 15000000), 'count': 3},
        {'name': 'Panasonic Inverter 1.5HP', 'category': 3, 'price_range': (8000000, 12000000), 'count': 3},
        {'name': 'LG Dual Inverter 2.5HP', 'category': 3, 'price_range': (12000000, 18000000), 'count': 2},
        
        # Thiết bị mạng (5 chiếc)
        {'name': 'Cisco Router RV340', 'category': 4, 'price_range': (8000000, 12000000), 'count': 2},
        {'name': 'TP-Link Switch 24 Port', 'category': 4, 'price_range': (3000000, 5000000), 'count': 2},
        {'name': 'Modem 4G Huawei', 'category': 4, 'price_range': (2000000, 3000000), 'count': 1},
        
        # Bàn ghế (5 bộ)
        {'name': 'Bộ bàn ghế văn phòng', 'category': 5, 'price_range': (3000000, 5000000), 'count': 5},
        
        # Điện thoại (4 chiếc)
        {'name': 'iPhone 13', 'category': 6, 'price_range': (15000000, 20000000), 'count': 2},
        {'name': 'Samsung Galaxy S21', 'category': 6, 'price_range': (12000000, 18000000), 'count': 2},
        
        # Máy chiếu (2 chiếc)
        {'name': 'Epson EB-X51', 'category': 7, 'price_range': (10000000, 15000000), 'count': 2},
    ]
    
    asset_objs = []
    asset_counter = 1
    
    for template in asset_templates:
        for i in range(template['count']):
            asset = env['asset'].create({
                'name': f"{template['name']} #{asset_counter:03d}",
                'category_id': category_objs[template['category']].id,
                'location_id': random.choice(location_objs).id,
                'purchase_date': (datetime.now() - timedelta(days=random.randint(180, 1095))).strftime('%Y-%m-%d'),
                'purchase_price': random.uniform(*template['price_range']),
                'state': random.choice(['available', 'in_use', 'in_use', 'in_use']),
                'notes': f"Thiết bị {template['name']}",
            })
            asset_objs.append(asset)
            asset_counter += 1
            
            if asset_counter % 15 == 0:
                env.cr.commit()
    
    env.cr.commit()
    print(f"Done {len(asset_objs)} tai san")
    
    # ============ PHẦN 4: LỊCH SỬ SỬ DỤNG TÀI SẢN ============
    print("\n[4/7] TẠO LỊCH SỬ SỬ DỤNG TÀI SẢN")
    print("-" * 70)
    
    print("  Tạo lịch sử giao/thu hồi tài sản...", end=" ")
    usage_records = []
    num_usage = random.randint(60, 80)
    
    for i in range(num_usage):
        asset = random.choice(asset_objs)
        employee = random.choice(employee_objs)
        
        date_from = datetime.now() - timedelta(days=random.randint(10, 700))
        
        # 70% đã thu hồi, 30% đang sử dụng
        if random.random() < 0.7:
            date_to = date_from + timedelta(days=random.randint(30, 365))
            state = 'returned'
        else:
            date_to = None
            state = 'active'
        
        usage = env['asset.usage.history'].create({
            'asset_id': asset.id,
            'employee_id': employee.id,
            'date_from': date_from.strftime('%Y-%m-%d %H:%M:%S'),
            'date_to': date_to.strftime('%Y-%m-%d %H:%M:%S') if date_to else False,
            'purpose': f"Giao {asset.name} cho {employee.name}",
            'state': state,
        })
        usage_records.append(usage)
        
        if (i + 1) % 20 == 0:
            env.cr.commit()
    
    env.cr.commit()
    print(f"Done {len(usage_records)} records")
    
    # ============ PHẦN 5: LỊCH SỬ BẢO TRÌ (NHIỀU DATA ĐỂ TRAIN AI) ============
    print("\n[5/7] TẠO LỊCH SỬ BẢO TRÌ (CHO AI TRAINING)")
    print("-" * 70)
    
    print("  Tạo lịch sử bảo trì...", end=" ")
    maintenance_descriptions = [
        'Bảo trì định kỳ theo kế hoạch',
        'Sửa chữa hỏng hóc phát hiện khi sử dụng',
        'Thay thế linh kiện hỏng',
        'Vệ sinh bảo dưỡng toàn bộ thiết bị',
        'Kiểm tra an toàn định kỳ',
        'Nâng cấp phần mềm/firmware',
        'Thay dầu máy và kiểm tra động cơ',
        'Kiểm tra lốp xe và hệ thống phanh',
        'Thay mực in và vệ sinh đầu in',
        'Vệ sinh lọc điều hòa và nạp gas',
        'Kiểm tra và cấu hình lại mạng',
        'Khắc phục sự cố không khởi động',
        'Xử lý vấn đề quá nhiệt',
        'Sửa chữa tiếng ồn bất thường',
        'Kiểm tra và thay pin CMOS',
        'Làm sạch quạt tản nhiệt',
        'Kiểm tra hệ thống điện',
        'Bảo dưỡng kết nối cáp',
    ]
    
    maintenance_types = ['preventive', 'corrective', 'replacement', 'inspection']
    
    # Tạo 500-800 records để AI có nhiều data training
    num_records = random.randint(500, 800)
    history_records = []
    
    for i in range(num_records):
        asset = random.choice(asset_objs)
        
        # Tạo ngày bảo trì trong quá khứ (từ 2 năm trước đến nay)
        maintenance_date = datetime.now() - timedelta(days=random.randint(1, 730))
        
        # Tính predicted cost dựa trên giá trị tài sản
        base_cost = asset.purchase_price * 0.01  # 1% giá trị tài sản
        predicted_cost = base_cost * random.uniform(0.5, 2.5)
        
        # Actual cost có độ lệch so với predicted
        # 60% dự đoán chính xác (sai lệch <20%)
        # 30% sai lệch vừa (20-40%)
        # 10% sai lệch nhiều (>40%)
        rand = random.random()
        if rand < 0.6:
            variance_factor = random.uniform(0.85, 1.15)  # ±15%
        elif rand < 0.9:
            variance_factor = random.uniform(0.7, 1.4)  # ±30%
        else:
            variance_factor = random.uniform(0.5, 1.8)  # ±50%
        
        actual_cost = predicted_cost * variance_factor
        
        # Chi tiết chi phí
        parts_cost = actual_cost * random.uniform(0.3, 0.7)
        labor_cost = actual_cost - parts_cost
        
        history = env['asset.maintenance.history'].create({
            'asset_id': asset.id,
            'maintenance_type': random.choice(maintenance_types),
            'description': random.choice(maintenance_descriptions),
            'maintenance_date': maintenance_date.strftime('%Y-%m-%d'),
            'actual_cost': actual_cost,
            'parts_cost': parts_cost,
            'labor_cost': labor_cost,
            'duration_hours': random.uniform(0.5, 8),
            'result': random.choice(['success', 'success', 'success', 'partial']),
            'notes': f"Bảo trì hoàn tất, thiết bị hoạt động tốt",
            'state': 'done',
        })
        history_records.append(history)
        
        # Commit thường xuyên hơn để tránh timeout
        if (i + 1) % 50 == 0:
            env.cr.commit()
            print(f"{i+1}...", end="", flush=True)
    
    env.cr.commit()
    print(f"Done {len(history_records)} records")
    
    # ============ PHẦN 6: PHÒNG HỌP VÀ ĐẶT PHÒNG ============
    print("\n[6/7] TẠO DỮ LIỆU PHÒNG HỌP")
    print("-" * 70)
    
    # 6.1 Tạo Phòng họp
    print("  Tạo phòng họp...", end=" ")
    meeting_rooms_data = [
        {'name': 'Phòng họp A1', 'capacity': 10},
        {'name': 'Phòng họp A2', 'capacity': 8},
        {'name': 'Phòng họp B1', 'capacity': 15},
        {'name': 'Phòng họp B2', 'capacity': 12},
        {'name': 'Phòng họp C1', 'capacity': 20},
        {'name': 'Phòng họp Hội đồng', 'capacity': 30},
    ]
    
    room_objs = []
    for room_data in meeting_rooms_data:
        room = env['meeting.room'].create({
            'name': room_data['name'],
            'capacity': room_data['capacity'],
            'location_id': random.choice(location_objs).id,
            'has_projector': True,
            'has_whiteboard': True,
            'has_wifi': True,
            'state': 'available',
        })
        room_objs.append(room)
    print(f"Done {len(room_objs)} phong")
    
    # 6.2 Tạo Lịch đặt phòng
    print("  Tạo lịch đặt phòng...", end=" ")
    booking_objs = []
    num_bookings = random.randint(15, 25)
    
    booking_subjects = ['Họp team', 'Họp khách hàng', 'Đào tạo nội bộ', 'Thảo luận dự án', 
                       'Họp Ban Giám Đốc', 'Review công việc', 'Họp phòng ban', 'Training']
    
    for i in range(num_bookings):
        room = random.choice(room_objs)
        booker = random.choice(employee_objs)
        
        # Đặt phòng trong 30 ngày qua và 30 ngày tới
        booking_date = datetime.now() + timedelta(days=random.randint(-30, 30))
        start_time = booking_date.replace(hour=random.choice([8, 9, 10, 13, 14, 15, 16]), minute=0, second=0)
        end_time = start_time + timedelta(hours=random.choice([1, 2, 3]))
        
        if start_time < datetime.now():
            state = random.choice(['confirmed', 'completed', 'completed'])
        else:
            state = 'confirmed'
        
        # Số người không vượt quá sức chứa phòng
        max_attendees = min(room.capacity, 20)
        expected_attendees = random.randint(3, max_attendees)
        
        booking = env['meeting.room.booking'].create({
            'room_id': room.id,
            'booker_id': booker.id,
            'organizer_id': booker.id,
            'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'subject': random.choice(booking_subjects),
            'description': f"Cuộc họp tại {room.name}",
            'expected_attendees': expected_attendees,
            'state': state,
        })
        booking_objs.append(booking)
    
    env.cr.commit()
    print(f"Done {len(booking_objs)} lich dat")
    
    # ============ PHẦN 7: THỐNG KÊ ============
    print("\n[7/7] THỐNG KÊ DỮ LIỆU")
    print("-" * 70)
    
    total_created = (len(don_vi_objs) + len(chuc_vu_objs) + len(chung_chi_objs) + 
                    len(employee_objs) + len(category_objs) + len(location_objs) +
                    len(asset_objs) + len(usage_records) + len(history_records) +
                    len(room_objs) + len(booking_objs))
    
    avg_maintenance_cost = sum(h.actual_cost for h in history_records) / len(history_records) if history_records else 0
    
    print(f"""
{'='*66}
         KẾT QUẢ TẠO DỮ LIỆU DEMO HOÀN CHỈNH
{'='*66}
CẤU TRÚC TỔ CHỨC:
   Don vi/Phong ban:        {len(don_vi_objs):3d}
   Chuc vu:                 {len(chuc_vu_objs):3d}
   Chung chi/Bang cap:      {len(chung_chi_objs):3d}

NHÂN SỰ:
   Nhan vien:               {len(employee_objs):3d}

TÀI SẢN:
   Danh muc tai san:        {len(category_objs):3d}
   Dia diem:                {len(location_objs):3d}
   Tai san:                 {len(asset_objs):3d}
   Lich su su dung:         {len(usage_records):3d}
   Lich su bao tri:         {len(history_records):3d}

PHÒNG HỌP:
   Phong hop:                {len(room_objs):2d}
   Lich dat phong:          {len(booking_objs):3d}

CHI PHÍ BẢO TRÌ TRUNG BÌNH:
   {avg_maintenance_cost:>15,.0f} VND/lan

TỔNG RECORDS TẠO:          {total_created:3d}
{'='*66}

DU LIEU DA SAN SANG CHO:
   • Quan ly nhan su day du
   • Quan ly tai san chi tiet  
   • Train AI voi {len(history_records)} records lich su bao tri
   • Phan tich chi phi va xu huong
   
BUOC TIEP THEO:
   1. Vao menu "Du Doan Bao Tri AI"
   2. Nhan nut "Train AI Model"
   3. AI se hoc tu {len(history_records)} records thuc te!
   
Du lieu: {(datetime.now() - timedelta(days=730)).strftime('%d/%m/%Y')} - {datetime.now().strftime('%d/%m/%Y')}
""")

if __name__ == '__main__':
    try:
        print("\nDang khoi dong Odoo environment...")
        
        # Parse config
        odoo.tools.config.parse_config(['-c', 'odoo.conf', '-d', 'giapdepzaii'])
        
        # Tạo environment
        with odoo.api.Environment.manage():
            registry = odoo.registry('giapdepzaii')
            with registry.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                generate_full_demo_data(env)
        
        print("\nHOAN TAT! Du lieu da duoc tao thanh cong.\n")
        
    except Exception as e:
        print(f"\nLOI: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
