import os
import random
import time

import django
import requests
import telebot
from telebot import types
from amplitude import Amplitude, BaseEvent

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'USDT_Buy_Bot.settings')
django.setup()
from bot.models import Users, Card, AdminMessage, Translations

bot = telebot.TeleBot(os.environ["BOT_API"])
amplitude = Amplitude("API-KEY")


def amplitude_add(from_user, acttion, user_id=False):
    if not user_id:
        user_id = from_user.id
    amplitude.track(
        BaseEvent(
            event_type=acttion,
            user_id=f"{user_id}",
            device_id=f"{user_id}",
            event_properties={
                "username": from_user.username,
                "first_name": from_user.first_name,
            }
        )
    )


def delite_history(user):
    messages_id = user.chat_history[:-1].split(',')
    for i in messages_id:
        try:
            bot.delete_message(user.tg_id, i)
        except Exception:
            pass
    user.chat_history = ''
    user.save()


def get_course():
    url = 'https://min-api.cryptocompare.com/data/price?fsym=USD&tsyms=RUB'
    response = requests.get(url).json()
    return response['RUB']


def button():
    markup = types.InlineKeyboardMarkup()
    chat = types.InlineKeyboardButton('💬Чат', url='https://t.me/easychatP2P')
    buy = types.InlineKeyboardButton('🟢Купить', callback_data='buy')
    balance = types.InlineKeyboardButton('💰Баланс', callback_data='balance')
    markup.add(buy)
    markup.add(balance)
    markup.add(chat)
    return markup


def output_step_two(chat_id, user, dollars, error=False):
    if error:
        text = 'Адрес введен неверно. Используйте сеть USDT-TRC20'
    else:
        text = '📬 Отлично! Укажите адрес, куда мы отправим доллары. Используйте сеть USDT-TRC20'
    markup = types.InlineKeyboardMarkup()
    menu = types.InlineKeyboardButton('Главное меню', callback_data='menu')
    markup.add(menu)
    msg = bot.send_message(chat_id=chat_id, text=text)
    user.chat_history += f'{msg.id},'
    user.method = f'adress_validate|{dollars}'
    user.save()


def output_step_one(chat_id, user, error=False):
    balance = str(user.balance).replace('.', ',')
    markup = types.InlineKeyboardMarkup()
    menu = types.InlineKeyboardButton('Главное меню', callback_data='menu')
    markup.add(menu)
    if user.balance > 0:
        if error == 'more':
            text = f'Вы ввели больше, чем есть на вашем счете\. Максимум для вывода {balance} долларов'
        elif error == 'invalid':
            text = f'Неправильный формат\. Используйте точку как разделитель, не используйте пробелы\. Введите повторно'
        else:
            text = '🧮 Введите количество долларов, которые вы хотите вывести\. \n' \
                   '🏼 _Для разделения_ между целым и частью используйте точку "\.", а не запятую ","\.'
        output_all = types.InlineKeyboardButton('📤 Вывести все', callback_data='output_all')
        markup.add(output_all)
        msg = bot.send_message(chat_id=chat_id, text=text, reply_markup=markup, parse_mode='MarkdownV2')
        user.chat_history += f'{msg.id},'
        user.method = 'dollars_output'
        user.save()
    else:
        input_balance = types.InlineKeyboardButton('Купить доллары', callback_data='buy')
        text = 'На вашем счету к сожалению нет долларов для вывода. Пополнить их можете, нажав на кнопку ниже'
        markup.add(input_balance)
        bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)


def menu_first(chat_id):
    text = '💵 Купите свой первый доллар в два касания!\n\n' \
           f'ℹ️ Курс за 1 доллар на сегодня: {get_course()} ₽'
    markup = button()
    bot.send_message(chat_id, text, reply_markup=markup)


def balance(chat_id, user):
    markup = types.InlineKeyboardMarkup()
    buy = types.InlineKeyboardButton('🟢 Купить еще', callback_data='buy')
    markup.add(buy)
    if user.balance:
        text = f'💰У вас {user.balance} цифровых долларов'
        output = types.InlineKeyboardButton('📤 Вывести', callback_data='output')
        markup.add(output)
    else:
        text = 'На вашем счету пока пусто. Покупаем?'
    menu = types.InlineKeyboardButton('🔙 Назад', callback_data='menu')
    markup.add(menu)
    bot.send_message(chat_id, text, reply_markup=markup)


def menu_two(chat_id, username):
    text = f'👋🏼 С возвращением, {username} \n\n' \
           f'ℹ️ Курс за 1 доллар на сегодня: {get_course()} ₽' \
           f'\n\n🟢 Покупаем?'
    markup = button()
    user = Users.objects.get(tg_id=chat_id)
    output = types.InlineKeyboardButton('📤Вывести', callback_data='output')
    markup.add(output)
    bot.send_message(chat_id, text, reply_markup=markup)


def send_message_to_user(chat_id):
    text = '⏳ Ожидаем подтверждение продавца.\n' \
           'Обычно занимает до 4 минут'
    markup = types.InlineKeyboardMarkup()
    supprot = types.InlineKeyboardButton('Техническая поддержка', url='https://t.me/easycryptofounders')
    markup.add(supprot)
    user = Users.objects.get(tg_id=chat_id)
    msg = bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)
    user.chat_history += f'{msg.id},'
    user.save()


def buy_step_three(chat_id, amount, dollars):
    card = random.choice(Card.objects.all())
    str_amount = str(amount).replace('.', ',')
    link = 'https://telegra.ph/Kak-EasyCrypto-obespechivaet-bezopasnost-vashej-sdelki-01-15'
    text = f'ℹ Оплатите {str_amount} ₽\n\n' \
           f'💳 Номер карты для оплаты:` {card.number}` \n\n' \
           f'🏦 Банк {card.bank}\n\n' \
           f'👤 Получатель {card.owner}\n\n' \
           f'🔐 Как мы гарантируем безопасность ваших средств? [Узнайте за 3 минуты]({link})'
    markup = types.InlineKeyboardMarkup()
    supprot = types.InlineKeyboardButton('Поддержка', url='https://t.me/easycryptofounders')
    cansel_deal = types.InlineKeyboardButton('Отменить сделку', callback_data=f'menu')
    send_money = types.InlineKeyboardButton('🟢 Деньги отправил',
                                            callback_data=f'send_money|{amount}|{dollars}|{card.number}')
    markup.add(send_money)
    markup.add(supprot)
    markup.add(cansel_deal)
    msg = bot.send_message(chat_id=chat_id, text=text, reply_markup=markup, parse_mode='MarkdownV2',
                           disable_web_page_preview=True)
    user = Users.objects.get(tg_id=chat_id)
    user.chat_history += f'{msg.id},'
    user.save()


def buy_step_two(chat_id, dollars):
    course = get_course()
    amount = round(dollars * course, 2)
    text = f'ℹВы покупаете {dollars} долларов по курсу {course}₽ на сумму {amount}₽.\n' \
           f'❔Начинаем покупку?'
    markup = types.InlineKeyboardMarkup()
    start = types.InlineKeyboardButton('🟢 Начинаем!', callback_data=f'start|{amount}|{dollars}')
    menu = types.InlineKeyboardButton('🔙 Назад', callback_data='menu')
    markup.add(start)
    markup.add(menu)
    msg = bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)
    user = Users.objects.get(tg_id=chat_id)
    user.chat_history += f'{msg.id},'
    user.save()


def buy_step_one(chat_id, error=False):
    course = get_course()
    user = Users.objects.get(tg_id=chat_id)
    user.method = 'dollars_input'
    if error:
        text = "Введите число в корректном формате. Для разделителя используйте точку '.', не используйте пробел"
    else:
        text = f'ℹТекущий курс - {course}₽ за доллар.\n' \
               f'❔Сколько долларов покупаем?\n\n' \
               f'Выберите количество долларов ниже или напишите свое число'
    markup = types.InlineKeyboardMarkup()
    for i in range(1, 4):
        dollar = types.InlineKeyboardButton(f'🔘 {10 ** i}', callback_data=f'buy_dollar|{10 ** i}')
        markup.add(dollar)
    menu = types.InlineKeyboardButton('🔙 Назад', callback_data='menu')
    markup.add(menu)
    msg = bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)
    user.chat_history += f'{msg.id},'
    user.save()


def check_user(chat_id, username=''):
    try:
        user = Users.objects.get(tg_id=chat_id)
    except Exception:
        user = Users.objects.create(tg_id=chat_id, username=username)
        menu_first(chat_id)
    else:
        menu_two(chat_id, username)


@bot.message_handler(commands=['start'])
def start(message):
    amplitude_add(message.from_user, 'start')
    username = message.from_user.first_name
    chat_id = message.chat.id
    try:
        user = Users.objects.get(tg_id=chat_id)
        user.method = ''
        user.save()
    except Exception:
        pass
    bot.delete_message(chat_id=chat_id, message_id=message.id)
    check_user(chat_id, username)


@bot.message_handler(commands=['balance'])
def balance_button(message):
    amplitude_add(message.from_user, 'balance')
    chat_id = message.chat.id
    user = Users.objects.get(tg_id=chat_id)
    balance(chat_id, user)


@bot.message_handler(content_types='text')
def input(message):
    chat_id = message.chat.id
    user = Users.objects.get(tg_id=chat_id)
    method = user.method
    if method == 'dollars_input':
        try:
            dollars = float(message.text)
            user.chat_history += f'{message.id},'
            delite_history(user)
            buy_step_two(chat_id=chat_id, dollars=dollars)
        except Exception:
            buy_step_one(chat_id, error=True)
    elif method == 'dollars_output':
        user.chat_history += f'{message.id},'
        user.save()
        delite_history(user)
        try:
            dollars = float(message.text)
            if dollars > user.balance:
                raise TypeError
        except ValueError:
            output_step_one(chat_id=chat_id, user=user, error='invalid')
        except TypeError:
            output_step_one(chat_id=chat_id, user=user, error='more')
        else:
            output_step_two(chat_id=chat_id, user=user, dollars=dollars)
    elif method.split('|')[0] == 'adress_validate':
        user.chat_history += f'{message.id},'
        user.save()
        delite_history(user)
        dollars = float(method.split('|')[1])
        try:
            address = message.text
            url = f"https://apilist.tronscan.org/api/account?address={address}&includeToken=true"
            headers = {"accept": "application/json"}
            response = requests.get(url, headers=headers)
            data = response.json()['trc20token_balances']
        except KeyError:
            output_step_two(chat_id=chat_id, user=user, dollars=dollars, error=True)
        else:
            text = f'🏁 Доллары готовы к отправке!\n' \
                   f'Будет отправлено: \n' \
                   f'{dollars} долларов\n' \
                   f'На адрес: {address}\n' \
                   f'❔Все верно?'
            markup = types.InlineKeyboardMarkup()
            edit_address = types.InlineKeyboardButton('📬 Изменить адрес', callback_data=f'edit_address|{dollars}')
            edit_dollars = types.InlineKeyboardButton('🧮 Изменить количество', callback_data='output')
            cansel_output = types.InlineKeyboardButton('🙅‍♂️ Отменить вывод', callback_data='menu')
            approve_output = types.InlineKeyboardButton('🟢 Да, отправляем',
                                                        callback_data=f'approve_output|{dollars}|{address}')
            markup.add(approve_output)
            markup.add(edit_address)
            markup.add(edit_dollars)
            markup.add(cansel_output)
            bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)
    else:
        bot.delete_message(chat_id=chat_id, message_id=message.id)


def delite_admin_messages(unique_number):
    messages = AdminMessage.objects.get(unique_number=unique_number).messages_id.split(',')
    for message in messages:
        admin_id = message.split()[0]
        message_id = message.split()[1]
        try:
            bot.delete_message(chat_id=admin_id, message_id=message_id)
        except Exception:
            pass


def approve_or_cansel_input(chat_id, unique_number, dollars, amount, approved=True):
    delite_admin_messages(unique_number=unique_number)
    markup = types.InlineKeyboardMarkup(row_width=1)
    balance = types.InlineKeyboardButton('💰 Баланс', callback_data='balance')
    menu = types.InlineKeyboardButton('Главное меню', callback_data='menu')
    markup.add(balance, menu)
    if approved:
        user = Users.objects.get(tg_id=chat_id)
        user.balance += float(dollars)
        user.save()
        text = f'✅ Вы купили {dollars} долларов на сумму {amount}₽'
        bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)
    else:
        text = f'Продавец не подтвердил ваш перевод в размере {amount}₽ на покупку {dollars}'
        bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)


def send_input_to_admin(chat_id, dollars, amount, card, transactions_id):
    unique_number = str(chat_id) + str(time.time())
    admins = Users.objects.filter(is_admin=True)
    text = f'Пользователь отправил {amount}₽ для покупки {dollars} долларов на карту номер {card}'
    markup = types.InlineKeyboardMarkup()
    approve = types.InlineKeyboardButton('✅Одобрить',
                                         callback_data=f'approve|{chat_id}|{dollars}|{amount}|{unique_number}|{transactions_id}')
    cansel = types.InlineKeyboardButton('❌Отклонить',
                                        callback_data=f'cansel|{chat_id}|{dollars}|{amount}|{unique_number}|{transactions_id}')
    ban = types.InlineKeyboardButton('Забанить пользователя', callback_data=f'ban|{chat_id}|{transactions_id}')
    markup.add(approve)
    markup.add(cansel)
    markup.add(ban)
    messages_id = ''
    for admin in admins:
        msg = bot.send_message(chat_id=admin.tg_id, text=text, reply_markup=markup)
        messages_id += f'{admin.tg_id} {msg.id},'
    AdminMessage.objects.create(
        unique_number=unique_number,
        messages_id=messages_id[:-1]
    )


def ban_message(chat_id):
    markup = types.InlineKeyboardMarkup()
    supprot = types.InlineKeyboardButton('Техническая поддержка', url='https://t.me/easycryptofounders')
    markup.add(supprot)
    text = f'Вы бали забанены за спам. Если вы хотите получить разблокировку, то напишите поддержке, сообщив им ваш ID - {chat_id}'
    bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)


def send_output_to_user(chat_id, dollars, adress):
    text = 'Готово!\n' \
           f'Вы отправили: {dollars} долларов\n' \
           f'Адрес: {adress}'
    markup = button()
    bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)


def send_output_to_admin(chat_id, dollars, adress, transactions_id):
    unique_number = str(chat_id) + str(time.time())
    dollars1 = str(round(dollars * 0.98, 2)).replace('.', ',')
    admins = Users.objects.filter(is_admin=True)
    text = f'Пользователь {chat_id} создал заявку на вывод {dollars1} долларов на адрес `{adress}`'
    markup = types.InlineKeyboardMarkup()
    approve = types.InlineKeyboardButton('✅Подтвердить отправку',
                                         callback_data=f'out_approve|{chat_id}|{round(dollars * 0.98, 2)}|{unique_number}|{transactions_id}')
    ban = types.InlineKeyboardButton('Забанить пользователя', callback_data=f'ban|{chat_id}|{transactions_id}')
    markup.add(approve)
    markup.add(ban)
    messages_id = ''
    for admin in admins:
        msg = bot.send_message(chat_id=admin.tg_id, text=text, reply_markup=markup, parse_mode='MarkdownV2')
        messages_id += f'{admin.tg_id} {msg.id},'
    AdminMessage.objects.create(
        unique_number=unique_number,
        messages_id=messages_id[:-1]
    )


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    username = call.from_user.first_name
    message_id = call.message.id
    chat_id = call.message.chat.id
    user = Users.objects.get(tg_id=call.from_user.id)
    user.method = ''
    if not user.username:
        user.username = call.from_user.username
        user.save()
    if call.message:
        data = call.data
        user.chat_history += f'{message_id},'
        user.save()
        delite_history(user)
        if user.is_ban:
            ban_message(chat_id)
        elif data == 'menu':
            check_user(chat_id, username)

        elif data == 'balance':
            amplitude_add(call.from_user, 'balance')
            balance(chat_id, user)

        elif data == 'buy':
            amplitude_add(call.from_user, 'buy_usd')
            buy_step_one(chat_id=chat_id)

        elif data.split('|')[0] == 'buy_dollar':
            dollars = float(data.split('|')[1])
            buy_step_two(chat_id=chat_id, dollars=dollars)

        elif data.split('|')[0] == 'start':
            amount = float(data.split('|')[1])
            dollars = float(data.split('|')[2])
            buy_step_three(chat_id=chat_id, dollars=dollars, amount=amount)

        elif data.split('|')[0] == 'send_money':
            amount = float(data.split('|')[1])
            dollars = float(data.split('|')[2])
            number_card = data.split('|')[3]
            transactions = Translations.create(
                type='Покупка',
                number_dollars=dollars
            )
            send_input_to_admin(chat_id=chat_id, dollars=dollars, amount=amount, card=number_card, transactions_id=transactions.id)
            send_message_to_user(chat_id=chat_id)

        elif data.split('|')[0] == 'cansel':
            user_chat_id = data.split('|')[1]
            dollars = float(data.split('|')[2])
            amplitude_add(call.from_user, f'Cansel replenishment balance {dollars}$', user_chat_id)
            amount = float(data.split('|')[3])
            unique_number = data.split('|')[4]
            transaction_id = data.split('|')[5]
            transaction = Translations.objects.get(id=transaction_id)
            transaction.status = 'Отказано'
            transaction.save()
            approve_or_cansel_input(chat_id=user_chat_id, dollars=dollars, amount=amount, unique_number=unique_number,
                                    approved=False)
        elif data == 'output':
            amplitude_add(call.from_user, f'Output balance')
            output_step_one(chat_id=chat_id, user=user)

        elif data == 'output_all':
            output_step_two(chat_id=chat_id, user=user, dollars=user.balance)

        elif data.split('|')[0] == 'approve':
            user_chat_id = data.split('|')[1]
            dollars = float(data.split('|')[2])
            amplitude_add(call.from_user, f'Approve replenishment balance {dollars}$', user_chat_id)
            amount = float(data.split('|')[3])
            unique_number = data.split('|')[4]
            transaction_id = data.split('|')[5]
            transaction = Translations.objects.get(id=transaction_id)
            transaction.status = 'Одобрено'
            transaction.save()
            approve_or_cansel_input(chat_id=user_chat_id, dollars=dollars, amount=amount, unique_number=unique_number)

        elif data.split('|')[0] == 'edit_address':
            dollars = float(data.split('|')[1])
            output_step_two(chat_id=chat_id, user=user, dollars=dollars)

        elif data.split('|')[0] == 'approve_output':
            dollars = float(data.split('|')[1])
            adress = data.split('|')[2]
            user.balance -= dollars
            user.freeze_balance += dollars
            user.save()
            transactions = Translations.create(
                type='Вывод',
                number_dollars=dollars
            )
            send_output_to_admin(chat_id=chat_id, dollars=dollars, adress=adress, transactions_id=transactions)
            send_output_to_user(chat_id=chat_id, adress=adress, dollars=dollars)

        elif data.split('|')[0] == 'out_approve':
            user_chat_id = data.split('|')[1]
            dollars = float(data.split('|')[2])
            amplitude_add(call.from_user, f'Approve output balance {dollars}$', user_chat_id)
            unique_number = data.split('|')[3]
            transaction_id = data.split('|')[4]
            transaction = Translations.objects.get(id=transaction_id)
            transaction.status = 'Одобрено'
            transaction.save()
            usr = Users.objects.get(tg_id=user_chat_id)
            usr.freeze_balance -= dollars
            usr.save()
            delite_admin_messages(unique_number=unique_number)

        elif data.split('|')[0] == 'ban':
            transaction_id = data.split('|')[2]
            transaction = Translations.objects.get(id=transaction_id)
            transaction.status = 'Пользователя заблокировали'
            transaction.save()
            user_id = data.split('|')[1]
            usr = Users.objects.get(tg_id=user_id)
            usr.is_ban = True
            usr.save()
            ban_message(chat_id=user_id)

        else:
            check_user(chat_id)


bot.polling(none_stop=True)
