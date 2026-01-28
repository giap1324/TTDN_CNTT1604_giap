# 🚀 Hướng Dẫn Cập Nhật Giao Diện Mới

## Các bước cập nhật module

### 1. Kiểm tra file đã thêm

Đảm bảo các file sau đã được tạo:

```
addons/nhan_su/
├── static/src/css/
│   ├── ai_dashboard.css (đã có)
│   ├── hr_modern.css (MỚI ✨)
│   └── hr_components.css (MỚI ✨)
├── views/
│   ├── employee_views_modern.xml (MỚI ✨)
│   ├── employee_form_modern.xml (MỚI ✨)
│   └── menu.xml (đã cập nhật)
├── models/
│   └── employee.py (đã cập nhật - thêm notes, history_count)
├── __manifest__.py (đã cập nhật)
├── MODERN_UI_README.md (MỚI ✨)
└── UPDATE_GUIDE.md (file này)
```

### 2. Restart Odoo Server

#### Nếu dùng systemd:
```bash
sudo systemctl restart odoo
# Hoặc
sudo service odoo restart
```

#### Nếu dùng Docker:
```bash
cd /home/giapdepzaii/odoo-fitdnu
docker-compose restart
```

#### Nếu chạy trực tiếp:
```bash
# Dừng Odoo (Ctrl + C)
# Sau đó chạy lại
./odoo-bin -c odoo.conf
```

### 3. Cập nhật module trong Odoo

1. **Đăng nhập Odoo** với tài khoản Admin

2. **Bật Developer Mode**:
   - Vào **Settings** → **Activate Developer Mode**
   - Hoặc thêm `?debug=1` vào URL

3. **Cập nhật danh sách Apps**:
   - Vào **Apps**
   - Click **Update Apps List**
   - Confirm

4. **Upgrade Module**:
   - Tìm module **"Quản Lý Nhân Sự"**
   - Click vào module
   - Click nút **"Upgrade"**
   - Đợi quá trình upgrade hoàn tất

### 4. Xóa Cache Browser

Để thấy CSS mới, cần xóa cache:

**Chrome/Edge:**
- Press `Ctrl + Shift + Delete`
- Chọn "Cached images and files"
- Click Clear data

**Firefox:**
- Press `Ctrl + Shift + Delete`
- Chọn "Cache"
- Click Clear Now

**Hoặc Hard Refresh:**
- `Ctrl + F5` (Windows/Linux)
- `Cmd + Shift + R` (Mac)

### 5. Kiểm tra giao diện mới

1. **Mở module Nhân Sự**:
   - Click vào icon **"👥 Quản lý Nhân sự"**

2. **Xem Dashboard**:
   - Click **"📊 Dashboard"** trong menu
   - Kiểm tra các card thống kê màu gradient

3. **Xem Kanban View**:
   - Click **"👤 Quản lý Nhân viên"**
   - Mặc định hiển thị Kanban (thẻ)
   - Kiểm tra card nhân viên đẹp mắt

4. **Xem Form View**:
   - Click vào một nhân viên hoặc tạo mới
   - Kiểm tra icon, card layout, màu sắc

5. **Xem Tree View**:
   - Chuyển sang view List (icon ☰)
   - Kiểm tra header gradient, row coloring

## 🔍 Troubleshooting

### CSS không load?

**Giải pháp 1**: Restart Odoo và xóa cache browser

**Giải pháp 2**: Rebuild assets
```bash
./odoo-bin -c odoo.conf -d your_database -u nhan_su --stop-after-init
```

**Giải pháp 3**: Xóa assets trong database
```sql
DELETE FROM ir_attachment WHERE name LIKE '%web.assets%';
```

### View không hiển thị?

1. Kiểm tra file XML có lỗi syntax không:
```bash
xmllint views/employee_views_modern.xml
```

2. Kiểm tra log Odoo:
```bash
tail -f /var/log/odoo/odoo-server.log
```

3. Upgrade lại module với force:
```bash
./odoo-bin -c odoo.conf -d your_database -u nhan_su --stop-after-init
```

### Lỗi "field not found"?

Nếu gặp lỗi trường không tồn tại:

1. Kiểm tra model `employee.py` đã có trường:
   - `notes`
   - `history_count`

2. Cập nhật database:
```bash
# Vào Odoo
./odoo-bin -c odoo.conf -u nhan_su
```

### Menu không có icon?

Icon có thể không hiển thị nếu:
1. Browser không hỗ trợ emoji
2. Font không có emoji

**Giải pháp**: Thay emoji bằng icon FontAwesome:
```xml
<!-- Thay vì -->
<menuitem name="👥 Nhân viên"/>

<!-- Dùng -->
<menuitem name="Nhân viên" icon="fa-users"/>
```

## 📝 Checklist sau khi update

- [ ] Odoo đã restart
- [ ] Module đã upgrade
- [ ] Browser cache đã xóa
- [ ] Dashboard hiển thị đẹp
- [ ] Kanban view có card đẹp
- [ ] Form view có icon và màu sắc
- [ ] Tree view có gradient header
- [ ] Menu có icon emoji hoặc FA
- [ ] CSS animation hoạt động
- [ ] Responsive trên mobile

## 🎉 Thành công!

Nếu tất cả checklist đều pass, bạn đã cập nhật thành công giao diện mới!

Giao diện hiện đại với:
- ✅ Màu sắc gradient đẹp mắt
- ✅ Card và shadow hiện đại
- ✅ Icon rõ ràng, dễ hiểu
- ✅ Animation mượt mà
- ✅ Responsive design
- ✅ Badge trạng thái màu sắc
- ✅ Hover effects

## 📞 Liên hệ hỗ trợ

Nếu gặp vấn đề, liên hệ:
- **Email**: support@company.com
- **Hotline**: 0123-456-789
- **Telegram**: @support_bot

---

**Updated**: 2026-01-25  
**Version**: 2.0.0
