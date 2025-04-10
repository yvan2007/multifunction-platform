### users/admin.py
from django.contrib import admin
from .models import CustomUser, UserProfile, Address, Favorite, Message

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'is_manager', 'first_name', 'last_name']
    list_filter = ['is_manager']
    search_fields = ['username', 'email']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number']
    search_fields = ['user__username', 'bio']



@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'street', 'city', 'country', 'is_default', 'created_at']
    list_filter = ['is_default']
    search_fields = ['street', 'city', 'country']

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'created_at']
    search_fields = ['user__username', 'product__name']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'subject', 'sent_at', 'is_read']
    list_filter = ['is_read']
    search_fields = ['subject', 'body']