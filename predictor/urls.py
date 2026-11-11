from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path('history/delete/<int:item_id>/', views.delete_prediction_history, name='delete_prediction'),
    path('history/clear/', views.clear_all_history, name='clear_all_history'),
]