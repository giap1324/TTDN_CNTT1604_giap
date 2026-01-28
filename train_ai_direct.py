#!/usr/bin/env python3
"""Train AI model trực tiếp qua XML-RPC"""
import xmlrpc.client
import os

# Kết nối
url = 'http://localhost:8069'
db = 'giapdepzaii'
username = 'admin'
password = 'admin'

print("🔌 Kết nối Odoo...")
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

print(f"✅ Đã kết nối (user_id={uid})\n")

# Xóa model cũ để force re-train
print("🗑️  Xóa model cũ...")
for f in ['/tmp/xgboost_maintenance_model.pkl', '/tmp/xgboost_scaler.pkl']:
    if os.path.exists(f):
        os.remove(f)
        print(f"   ✓ {os.path.basename(f)}")

print("\n🤖 TRAINING + PREDICTING:")
print("   📊 526 maintenance history records")
print("   🌲 200 trees (max_depth=8)")
print("   📉 learning_rate=0.05")
print("   ⏳ Đang xử lý...\n")

# batch_predict sẽ tự train nếu model chưa tồn tại
models.execute_kw(
    db, uid, password,
    'asset.maintenance.prediction', 'batch_predict_all_assets', []
)
print("✅ Training + Prediction hoàn tất!")

# Count
total = models.execute_kw(
    db, uid, password,
    'asset.maintenance.prediction', 'search_count', [[]]
)

print(f"\n✅ Hoàn tất! {total} dự đoán")
