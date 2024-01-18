from django.db import models


class Users(models.Model):
    tg_id = models.CharField(max_length=64, verbose_name='Id пользователя')
    balance = models.IntegerField(default=0, verbose_name='Баланс пользователя')
    is_admin = models.BooleanField(default=False, verbose_name='Является ли пользователь админом')
    freeze_balance = models.IntegerField(default=0, verbose_name='Замороженный баланс')
    chat_history = models.CharField(max_length=2**13, default='', verbose_name='История чата')
    method = models.CharField(max_length=64, default='', verbose_name='Метод, который обрабатывается в input')


class Card(models.Model):
    number = models.CharField(max_length=64, verbose_name='Номер карты')
    bank = models.CharField(max_length=64, verbose_name='Название банка')
    owner = models.CharField(max_length=64, verbose_name='Держатель карты (вместо "." используйте ",")')

class AdminMessage(models.Model):
    verified = models.BooleanField(default=False, verbose_name='Проверена ли заявка')
    unique_number = models.CharField(max_length=128, verbose_name='Уникальный номер')
    messages_id = models.CharField(max_length=2**13, verbose_name='Номера сообщений админам')