from django.contrib import admin
from .models import Users, Card, Translations


@admin.register(Users)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'tg_id', 'username', 'balance']

@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    pass

@admin.register(Translations)
class TranslationsAdmin(admin.ModelAdmin):
    pass
