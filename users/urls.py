# users/urls.py
from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    # Authentication routes
    path('login/', views.login_view, name='login'),
    path('manager-login/', views.manager_login_view, name='manager_login'),
    path('logout/', auth_views.LogoutView.as_view(next_page=reverse_lazy('users:login')), name='logout'),
    path('register/', views.register, name='register'),

    # Password reset flow
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='users/password_reset_done.html'
    ), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='users/password_reset_confirm.html',
        success_url=reverse_lazy('users:password_reset_complete')
    ), name='password_reset_confirm'),
    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='users/password_reset_complete.html'
    ), name='password_reset_complete'),

    # User profile and settings
    path('profile/', views.profile, name='profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('favorites/', views.favorites, name='favorites'),
    path('messages/', views.user_messages, name='messages'),
    path('orders/', views.orders, name='orders'),
    path('account-settings/', views.account_settings, name='account_settings'),

    # Password change flow
    path('password-change/', auth_views.PasswordChangeView.as_view(
        template_name='users/password_change.html',
        success_url=reverse_lazy('users:password_change_done')
    ), name='password_change'),
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='users/password_change_done.html'
    ), name='password_change_done'),

    # Manager-specific routes
    path('manager-dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('manage-articles/', views.manage_articles, name='manage_articles'),
    path('manage-articles/edit/<int:article_id>/', views.edit_article, name='edit_article'),
    path('manage-articles/add/', views.add_article, name='add_article'),
    path('manage-categories/', views.manage_categories, name='manage_categories'),
    path('manage-categories/edit/<int:category_id>/', views.edit_category, name='edit_category'),
    path('manage-categories/add/', views.add_category, name='add_category'),
    path('manage-products/', views.manage_products, name='manage_products'),
    path('manage-products/add/', views.add_product, name='add_product'),
    path('manage-products/edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('manage-orders/', views.manage_orders, name='manage_orders'),
    path('manage-orders/update/<int:order_id>/', views.manager_update_order_status, name='manager_update_order_status'),
    path('manage-orders/delete/<int:order_id>/', views.manager_delete_order, name='manager_delete_order'),
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/metadata/', views.get_notification_metadata, name='notification_metadata'),
    path('messages/', views.user_messages, name='messages'),
    path('compose-message/', views.compose_message, name='compose_message'),
    path('mark-read/<int:message_id>/', views.mark_message_read, name='mark_message_read'),
    path('delete-message/<int:message_id>/', views.delete_message, name='delete_message'),
    path('account-settings/', views.account_settings, name='account_settings'),
    path('add-address/', views.add_address, name='add_address'),
    path('set-default-address/<int:address_id>/', views.set_default_address, name='set_default_address'),
    path('delete-address/<int:address_id>/', views.delete_address, name='delete_address'),
    path('add-payment-method/', views.add_payment_method, name='add_payment_method'),
    path('set-default-payment-method/<int:method_id>/', views.set_default_payment_method, name='set_default_payment_method'),
    path('delete-payment-method/<int:method_id>/', views.delete_payment_method, name='delete_payment_method'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('favorites/', views.favorites_list, name='favorites_list'),
]