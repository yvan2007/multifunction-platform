from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    # Authentication routes
    path('login/', views.login_view, name='login'),  # Custom login view
    path('manager-login/', views.manager_login_view, name='manager_login'),  # Manager login with 2FA
    path('logout/', auth_views.LogoutView.as_view(next_page='index'), name='logout'),  # Logout
    path('register/', views.register, name='register'),  # Registration

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
    path('manage-categories/', views.manage_categories, name='manage_categories'),
]