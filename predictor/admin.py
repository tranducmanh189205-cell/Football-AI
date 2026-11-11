from django.contrib import admin
from django.apps import apps

# Tự động lấy tất cả các bảng trong app predictor và đưa lên trang Admin
app_models = apps.get_app_config('predictor').get_models()

for model in app_models:
    try:
        admin.site.register(model)
    except admin.sites.AlreadyRegistered:
        pass
