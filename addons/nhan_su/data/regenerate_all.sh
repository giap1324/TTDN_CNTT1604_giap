#!/bin/bash
# Script tự động clean và tạo lại dữ liệu

cd /home/giapdepzaii/odoo-fitdnu

echo "===================================================================="
echo "STEP 1: CLEAN OLD DATA"
echo "===================================================================="
python3 addons/nhan_su/data/clean_all_data.py

echo ""
echo "===================================================================="
echo "STEP 2: GENERATE NEW DATA"
echo "===================================================================="
python3 addons/nhan_su/data/demo_data_full.py

echo ""
echo "===================================================================="
echo "✅ DONE! Check Odoo UI to see data."
echo "===================================================================="
