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
    path('messages/thread/<int:message_id>/', views.message_thread_view, name='message_thread'),
    path('messages/delete/<int:message_id>/', views.delete_message_view, name='delete_message'),
    path('dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('moderation/', views.admin_moderation_queue_view, name='admin_moderation'),
    path('moderation/approve/<int:item_id>/', views.admin_quick_approve_view, name='admin_quick_approve'),
    path('moderation/reject/<int:item_id>/', views.admin_quick_reject_view, name='admin_quick_reject'),
    path('complete/<int:item_id>/', views.mark_item_complete_view, name='mark_complete'),
    path('dashboard/users/', views.admin_user_management_view, name='admin_users'),
    path('dashboard/users/promote/<int:user_id>/', views.admin_promote_user_view, name='admin_promote_user'),
]

