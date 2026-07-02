from django.urls import path

from . import views

app_name = 'main'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('api/shorten/', views.shorten_view, name='shorten'),
    path('api/urls/<slug:short_code>/delete/', views.delete_url_view, name='delete_url'),
    path('api/urls/<slug:short_code>/toggle/', views.toggle_url_view, name='toggle_url'),
    path('api/urls/<slug:short_code>/qr/', views.qr_view, name='qr'),
    path('api/urls/<slug:short_code>/stats/', views.stats_api_view, name='stats_api'),
    path('stats/<slug:short_code>/', views.stats_view, name='stats'),
    # Diqqat: bu eng umumiy pattern — har doim ro'yxat oxirida turishi kerak
    path('<slug:short_code>/', views.redirect_view, name='redirect'),
]
