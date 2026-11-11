from django.contrib import admin
from django.apps import apps

# Tự động quét và đưa tất cả các bảng trong app predictor lên trang Admin
app_models = apps.get_app_config('predictor').get_models()
for model in app_models:
    try:
        admin.site.register(model)
    except admin.sites.AlreadyRegistered:
        pass
