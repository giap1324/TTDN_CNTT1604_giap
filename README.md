<h2 align="center">
	<a href="https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin">
	🎓 Faculty of Information Technology (DaiNam University)
	</a>
</h2>

<h2 align="center">
   HỆ THỐNG QUẢN LÝ TÀI SẢN & PHÒNG HỌP
</h2>

<div align="center">
	<p align="center">
		<img src="docs/aiotlab_logo.png" width="170"/>
		<img src="docs/fitdnu_logo.png" width="180"/>
		<img src="docs/dnu_logo.png" width="200"/>
	</p>

[![AIoTLab](https://img.shields.io/badge/AIoTLab-green?style=for-the-badge)](https://www.facebook.com/DNUAIoTLab)
[![Faculty of Information Technology](https://img.shields.io/badge/Faculty%20of%20Information%20Technology-blue?style=for-the-badge)](https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin)
[![DaiNam University](https://img.shields.io/badge/DaiNam%20University-orange?style=for-the-badge)](https://dainam.edu.vn)

</div>

---

## 1. Giới thiệu hệ thống

Hệ thống quản lý tài sản và phòng họp được xây dựng trên nền tảng **Odoo**, nhằm số hóa toàn bộ quy trình quản trị tài sản trong nhà trường/đơn vị và tối ưu hóa việc đặt lịch sử dụng phòng họp. Giải pháp tập trung vào việc chuẩn hóa dữ liệu, giảm thao tác thủ công và tăng tính minh bạch trong công tác quản lý.

### 1.1 Quản lý tài sản
- Quản lý danh mục, vị trí và trạng thái tài sản  
- Theo dõi lịch sử sử dụng, bảo trì, thanh lý  
- Quản lý chi phí vận hành và hiệu suất tài sản  
- Hỗ trợ kiểm kê, đối soát dữ liệu  

### 1.2 Quản lý phòng họp
- Đặt phòng theo lịch trực quan  
- Tránh trùng lịch, theo dõi phòng trống  
- Quản lý thiết bị đi kèm phòng họp  
- Thống kê mức độ sử dụng phòng  

**Mục tiêu** của hệ thống là nâng cao hiệu quả vận hành, tiết kiệm chi phí và tạo nền tảng mở rộng cho các chức năng nâng cao trong tương lai.

---

## 2. Công nghệ sử dụng

- Odoo  
- Python 3.8+  
- PostgreSQL  
- Docker Compose  
- Ubuntu  

![Ubuntu](https://img.shields.io/badge/Ubuntu-E95420?style=for-the-badge&logo=ubuntu&logoColor=white)
![GitLab](https://img.shields.io/badge/gitlab-%23181717.svg?style=for-the-badge&logo=gitlab&logoColor=white)
![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)

---

## 3. Giao diện hệ thống

Giao diện hệ thống được thiết kế theo phong cách hiện đại, trực quan và nhất quán, hỗ trợ tối đa cho các nghiệp vụ quản lý tài sản và đặt phòng họp. Thiết kế dựa trên nền tảng giao diện của Odoo, kết hợp tùy biến theo nghiệp vụ thực tế.


### 3.1 Giao diện quản lý tài sản

![Quản lý tài sản](docs/Screenshot%202026-01-28%20165341.png)

Theo dõi chi tiết thông tin tài sản: danh mục, vị trí, trạng thái, lịch sử sử dụng và bảo trì.

### 3.2 Giao diện quản lý phòng họp

![Quản lý phòng họp](docs/Screenshot%202026-01-28%20165419.png)

Hiển thị lịch phòng trực quan, giúp tránh trùng lịch và quản lý thiết bị đi kèm.

### 3.3 Giao diện đặt phòng họp

![Đặt phòng họp](docs/Screenshot%202026-01-28%20165434.png)

Người dùng có thể đặt phòng nhanh chóng, theo dõi lịch sử đặt và nhận thông báo khi có thay đổi.

---

## 4. Cài đặt môi trường và thư viện

### 4.1 Clone project

```bash
git clone https://gitlab.com/anhlta/odoo-fitdnu.git
cd odoo-fitdnu
```

### 4.2 Cài đặt thư viện hệ thống

```bash
sudo apt-get install libxml2-dev libxslt-dev libldap2-dev libsasl2-dev \
libssl-dev python3.10-dev python3.10-venv build-essential \
libffi-dev zlib1g-dev libpq-dev
```

### 4.3 Khởi tạo môi trường ảo

```bash
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 5. Setup Database

Khởi tạo database bằng Docker Compose:

```bash
docker-compose up -d
```

---

## 6. Cấu hình hệ thống

### 6.1 Tạo file `odoo.conf`

```ini
[options]
addons_path = addons
db_host = localhost
db_user = odoo
db_password = odoo
db_port = 5432
xmlrpc_port = 8069
```

Các tham số mở rộng:

* `-u <addons>`: cập nhật module
* `-d <database>`: chỉ định database
* `--dev=all`: bật chế độ developer

---

## 7. Chạy hệ thống

Truy cập địa chỉ sau để đăng nhập hệ thống:

```
http://localhost:8069/
```

---

## 8. Liên hệ

📌 Nếu bạn có câu hỏi hoặc cần hỗ trợ liên quan đến hệ thống:

* 🎓 **Đơn vị**: Khoa Công nghệ Thông tin – Đại học Đại Nam
* 📧 **Email**: [nguyennguyenvh09@gmail.com](mailto:nguyennguyenvh09@gmail.com)
* 🌐 **Website**: [https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin](https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin)
* 🔗 **GitLab**: [https://gitlab.com/anhlta/odoo-fitdnu](https://gitlab.com/anhlta/odoo-fitdnu)
* 💬 **AIoTLab**: [https://www.facebook.com/DNUAIoTLab](https://www.facebook.com/DNUAIoTLab)

---
