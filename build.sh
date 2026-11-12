#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input

# Bắt buộc có 2 dòng này để tạo đủ các bảng của app predictor trên TiDB Cloud
python manage.py makemigrations predictor
python manage.py migrate

python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@gmail.com', 'Admin@123456')"
