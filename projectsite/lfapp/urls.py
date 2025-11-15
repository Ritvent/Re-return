from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_view, name='landing'),
    path('login/', views.landing_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('home/', views.home_view, name='home'),
    path('lost/', views.lost_items_view, name='lost_items'),
    path('found/', views.found_items_view, name='found_items'),
    path('claimed/', views.claimed_items_view, name='claimed_items'),
    path('post-lost/', views.post_lost_item_view, name='post_lost'),
    path('post-found/', views.post_found_item_view, name='post_found'),
    path('edit/<int:item_id>/', views.edit_item_view, name='edit_item'),
    path('toggle-listing/<int:item_id>/', views.toggle_item_listing_view, name='toggle_listing'),
    path('delete/<int:item_id>/', views.delete_item_view, name='delete_item'),
    path('message/<int:item_id>/', views.send_message_view, name='send_message'),
    path('messages/inbox/', views.messages_inbox_view, name='messages_inbox'),
    path('messages/sent/', views.messages_sent_view, name='messages_sent'),
    path('admin/', views.admin_dashboard_view, name='admin_dashboard'),
]

