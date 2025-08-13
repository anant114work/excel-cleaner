from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('process/', views.process_file, name='process_file'),
    path('download/', views.download_file, name='download_file'),
]