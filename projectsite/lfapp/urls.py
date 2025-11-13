from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_view, name='landing'),
    path('login/', views.landing_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('home/', views.home_view, name='home'),
    path('lost/', views.lost_items_view, name='lost_items'),
    path('found/', views.found_items_view, name='found_items'),
    path('post-lost/', views.post_lost_item_view, name='post_lost'),
    path('post-found/', views.post_found_item_view, name='post_found'),
    path('admin/', views.admin_dashboard_view, name='admin_dashboard'),
]

