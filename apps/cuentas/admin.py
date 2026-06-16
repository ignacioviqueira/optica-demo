from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ("email", "username", "rol", "is_staff")
    fieldsets = UserAdmin.fieldsets + (
        ("Óptica", {"fields": ("rol",)}),
    )
