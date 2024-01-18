from django.contrib import admin
from .models import Users, Card


@admin.register(Users)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'tg_id']

@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    pass