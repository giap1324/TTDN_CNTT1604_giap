# -*- coding: utf-8 -*-
{
    'name': '👥 Quản Lý Nhân Sự - Modern UI',
    'version': '2.0.0',
    'category': 'Human Resources',
    'summary': '🎨 Quản lý hồ sơ nhân viên với giao diện hiện đại và đẹp mắt',
    'description': """
        Module quản lý nhân sự toàn diện với GIAO DIỆN HIỆN ĐẠI:
        
        🎨 GIAO DIỆN MỚI:
        ===============
        - Dashboard thống kê với gradient đẹp mắt
        - Kanban view hiển thị thẻ nhân viên
        - Form view với icon và card layout
        - Tree view với màu sắc phân biệt trạng thái
        - Responsive design (Desktop, Tablet, Mobile)
        - Animation và hover effects
        
        📋 QUẢN LÝ NHÂN VIÊN:
        ====================
        - Quản lý hồ sơ nhân viên đầy đủ
        - Upload tài liệu và ảnh đại diện
        - Lịch sử thay đổi chi tiết
        - Tạo tài khoản tự động
        - Thông tin liên hệ khẩn cấp
        
        🏢 QUẢN LÝ TÀI SẢN:
        ==================
        - Quản lý tài sản và điều phối phòng họp
        - AI dự đoán bảo trì với XGBoost
        - Phát hiện bất thường chi phí
        - Tối ưu hóa chi phí tài sản
        
        📱 TÍCH HỢP:
        ===========
        - Thông báo Telegram tự động
        - Tích hợp với module HR Odoo
        - Email công ty tự động
    """,
    'author': 'HR Department',
    'website': '',
    'depends': [
        'base',
        'hr',
        'mail',
        'web',
    ],
    'external_dependencies': {
        'python': ['requests'],
    },
    'data': [
        'security/ir.model.access.csv',
        'data/employee_sequence.xml',
        'data/contract_sequence.xml',
        'data/asset_sequence.xml',
        'data/email_template.xml',
        'data/ir_cron.xml',
        'data/ai_cron.xml',
        'data/ir_cron_data.xml',
        'data/telegram_cron.xml',
        'data/telegram_config.xml',
        'views/don_vi.xml',
        'views/chuc_vu.xml',
        'views/chung_chi_bang_cap.xml',
        'views/don_vi_modern.xml',
        'views/chuc_vu_modern.xml',
        'views/chung_chi_bang_cap_modern.xml',
        'views/employee_views.xml',
        'views/employee_views_pro.xml',
        'views/employee_views_modern.xml',
        'views/employee_form_modern.xml',
        'views/asset_category_views.xml',
        'views/asset_location_views.xml',
        'views/asset_views.xml',
        'views/asset_views_pro.xml',
        'views/asset_ai_views.xml',
        'views/asset_ai_advanced_views.xml',
        'views/asset_ai_dashboard_views.xml',
        'views/asset_maintenance_history_views.xml',
        'views/meeting_room_views.xml',
        'views/meeting_room_views_pro.xml',
        'views/meeting_room_booking_views.xml',
        'views/meeting_room_booking_views_pro.xml',
        'views/meeting_room_booking_views_modern.xml',
        'views/telegram_config_views.xml',
        'views/menu.xml',
        'views/asset_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'nhan_su/static/src/css/ai_dashboard.css',
            'nhan_su/static/src/css/hr_modern.css',
            'nhan_su/static/src/css/hr_components.css',
            'nhan_su/static/src/css/booking_modern.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
