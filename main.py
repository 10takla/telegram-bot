from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    InlineKeyboardButton
from aiogram.utils import executor

from bd import request_mysql, cursor, conn


class Form(StatesGroup):
    id = State()
    first_name = State()
    last_name = State()
    age = State()
    country_id = State()
    phone = State()
    status = State()
    description = State()


class Dialog(StatesGroup):
    agree_reg = State()


class User(StatesGroup):
    id = State()
    send_message = State()


TOKEN = "1491491937:AAHabrqm-4uunRftJb6zBeZCt_QwWthG9b8"
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


@dp.message_handler(text="")
async def handle_message(message: types.Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Начать")
            ]
        ],
        resize_keyboard=True
    )

    # Отправляем сообщение с клавиатурой
    await message.answer("Привет! Нажми на кнопку, чтобы начать", reply_markup=keyboard)


@dp.message_handler(commands=['start'])
async def auth_user(message: types.Message):
    if message.from_user.is_bot: return
    my_id = message.from_user.id
    user_bd = request_mysql(f"SELECT * FROM user WHERE id = {my_id}")

    if user_bd:
        count_messages = \
            request_mysql(
                f"SELECT COUNT(1) AS count_messages FROM message WHERE to_id = {my_id} AND is_viewed = 0")[
                'count_messages']
        count_friend_requests = request_mysql(f"SELECT COUNT(id) as count_friend_requests "
                                              f"FROM friendship WHERE to_id = {my_id} AND is_accepted = 0 AND is_denied = 0")[
            'count_friend_requests']
        count_friends = request_mysql(f"SELECT COUNT(1) as count_friends FROM friendship WHERE is_accepted = 1 AND "
                                      f"(from_id = {my_id} OR to_id = {my_id})")[
            'count_friends']
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(f"Поиск пользователей", callback_data='userMenu_search_users', ),
                ],
                [
                    InlineKeyboardButton("О себе", callback_data='userMenu_about_me'),
                    InlineKeyboardButton(f"Друзья ({count_friends})", callback_data='userMenu_friends'),
                ],
                [
                    InlineKeyboardButton(text=f"Сообщения ({count_messages})", callback_data="userMenu_check_messages"),
                    InlineKeyboardButton(f"Заявки в друзья ({count_friend_requests})",
                                         callback_data='userMenu_friend_requests'), ]
            ],
            row_widths=[1, 2, 1]
        )
        await message.answer(f"Привет, {user_bd['first_name']} {user_bd['last_name']}!", reply_markup=markup)
    else:
        await Dialog.agree_reg.set()
        markup = ReplyKeyboardMarkup(resize_keyboard=True).add(
            KeyboardButton("Да"),
            KeyboardButton("Нет"),
        )
        await message.answer("Вы еще не зарегистрированы. Продолжить?", reply_markup=markup)


def user_show(id):
    user_bd = request_mysql(f"SELECT * FROM user WHERE id = {id}")
    users = [f"{filed}: {value}" for filed, value in user_bd.items()]
    return '\n'.join(users)


@dp.message_handler(state=User.send_message)
async def send_message(message: types.Message, state: FSMContext):
    user_id = (lambda x: x.get('user_id', None))(await state.get_data('user_id'))
    cursor.execute(
        f"INSERT INTO message (text, from_id, to_id) VALUES ('{message.text}', {message.from_user.id}, {user_id})")
    conn.commit()
    await state.set_state(None)


@dp.callback_query_handler(lambda c: c.data.startswith('actToUser_'))
async def action_to_user(callback_query: CallbackQuery, state: FSMContext):
    action = callback_query.data.replace('actToUser_', '')
    if action == 'send_message':
        await callback_query.message.answer("Напишите сообщение")
        await User.send_message.set()
    if action == 'offer_friendship':
        user_id = (lambda x: x.get('user_id', None))(await state.get_data('user_id'))
        cursor.execute(f"INSERT INTO friendship (from_id, to_id) VALUES({callback_query.from_user.id}, {user_id})")
        conn.commit()


@dp.callback_query_handler(lambda c: c.data.startswith('getUserById_'))
async def get_user_by_id(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.data.replace('getUserById_', '')
    await state.update_data(user_id=user_id)
    markup = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton('Отправить сообщение', callback_data='actToUser_send_message'),
        InlineKeyboardButton('Добавить в друзья', callback_data='actToUser_offer_friendship'),
    ]])
    await callback_query.message.answer(user_show(user_id), reply_markup=markup)


@dp.callback_query_handler(lambda c: c.data.startswith('readMessageByUser_'))
async def read_message(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.data.replace('readMessageByUser_', '')
    messages = request_mysql(
        f"SELECT * FROM message WHERE from_id = {user_id} AND to_id = {callback_query.from_user.id}", False)
    for message in messages:
        await callback_query.message.answer(message['text'])
    cursor.execute(
        f"UPDATE message SET is_viewed = 1 WHERE from_id = {user_id} AND to_id = {callback_query.from_user.id}")
    conn.commit()


@dp.callback_query_handler(lambda c: c.data.startswith('getCountry_'))
async def get_country(callback_query: CallbackQuery, state: FSMContext):
    country_id = callback_query.data.replace('getCountry_', '')
    users_bd = request_mysql(
        f"SELECT * FROM `user` WHERE country_id = {country_id} AND id != {callback_query.from_user.id}",
        False)
    if users_bd:
        markup = InlineKeyboardMarkup(button_width=1).add(
            *[InlineKeyboardButton(f"{user['first_name']} {user['last_name']}",
                                   callback_data=f"getUserById_{user['id']}") for user in users_bd]
        )
        await callback_query.message.answer("Выберите пользователя", reply_markup=markup)
    else:
        await callback_query.message.answer("Пользователей нет")


@dp.callback_query_handler(lambda c: c.data.startswith('friendshipAct_'))
async def act_friendship(callback_query: CallbackQuery, state: FSMContext):
    action = callback_query.data.replace('friendshipAct_', '')
    user_id = (lambda x: x.get('user_id', None))(await state.get_data('user_id'))
    if action == 'accept':
        cursor.execute(f"UPDATE friendship SET is_accepted = 1 "
                       f"WHERE from_id = {user_id} AND to_id = {callback_query.from_user.id}")
    if action == 'denied':
        cursor.execute(f"UPDATE friendship SET is_denied = 1 "
                       f"WHERE from_id = {user_id} AND to_id = {callback_query.from_user.id}")
    conn.commit()


@dp.callback_query_handler(lambda c: c.data.startswith('menuFriendship_'))
async def menu_friendship(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.data.replace('menuFriendship_', '')
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton('Принять', callback_data='friendshipAct_accept'),
            InlineKeyboardButton('Отказать', callback_data='friendshipAct_denied'),
        ]
    ])
    await callback_query.message.answer("апрарп", reply_markup=markup)
    await state.update_data(user_id=user_id)


@dp.callback_query_handler(lambda c: c.data.startswith('userMenu_'))
async def my_profile_menu(callback_query: CallbackQuery, state: FSMContext):
    action = callback_query.data.replace('userMenu_', '')
    my_id = callback_query.from_user.id
    if action == 'search_users':
        def request_text(sym):
            return f"SELECT c.id, c.name, COUNT(u.id) as count_users FROM country c JOIN user u ON c.id = u.country_id " \
                   f"WHERE c.id {sym} (SELECT country_id FROM user WHERE user.id = {my_id}) " \
                   f"GROUP BY c.id, c.name ORDER BY count_users DESC;"

        country_me = request_mysql(request_text('='))
        countries = request_mysql(request_text('!='), False)

        markup = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(f"Пользователи в моей стране ({country_me['count_users']})",
                                     callback_data=f"getCountry_{country_me['id']}")
            ],
            [
                InlineKeyboardButton(f"{country['name']} ({country['count_users']})",
                                     callback_data=f"getCountry_{country['id']}") for country in countries
            ]
        ],
            row_widths=[1, ])
        await callback_query.message.answer(f"Где искать", reply_markup=markup)
    if action == 'about_me':
        await callback_query.message.answer(user_show(my_id))
        await state.finish()
    if action == 'friends':
        # friends = request_mysql(f"SELECT * FROM user WHERE id IN (SELECT id", False)
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [

            ]
        ])
        await callback_query.message.answer("Выберите друга", reply_markup=markup)
    if action == 'check_messages':
        users_bd = request_mysql(f"SELECT u.id, u.first_name, u.last_name, COUNT(m.id) as count_messages FROM user u " \
                                 f"JOIN message m ON u.id = m.from_id WHERE u.id = "
                                 f"(SELECT from_id FROM message WHERE to_id = {my_id} AND is_viewed = 0 "
                                 f"GROUP BY from_id) GROUP BY u.id, u.first_name, u.last_name;",
                                 False)
        if users_bd:
            markup = InlineKeyboardMarkup(button_width=1).add(
                *[InlineKeyboardButton(f"{user['first_name']} {user['last_name']} - {user['count_messages']} сообщения",
                                       callback_data=f"readMessageByUser_{user['id']}") for user in users_bd]
            )
            await callback_query.message.answer("Выберите пользователя", reply_markup=markup)
        else:
            await callback_query.message.answer("Пользователей нет")
    if action == 'friend_requests':
        users_bd = request_mysql(f"SELECT * FROM user WHERE id IN "
                                 f"(SELECT from_id FROM friendship "
                                 f"WHERE to_id = {my_id} "
                                 f"AND is_accepted = 0 AND is_denied = 0)", False)
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(f"{user['first_name']} {user['last_name']}",
                                     callback_data=f"menuFriendship_{user['id']}") for user in users_bd
            ]
        ])
        await callback_query.message.answer("Выберите пользователя", reply_markup=markup)


@dp.message_handler(text=['Да', 'Нет'], state=Dialog.agree_reg)
async def button_callback(message: types.Message, state: FSMContext):
    if message.text == 'Да':
        await message.answer("Введите имя", reply_markup=ReplyKeyboardRemove())
        await Form.first_name.set()
    elif message.text == 'Нет':
        await message.answer('Вы выбрали "Нет"', reply_markup=ReplyKeyboardRemove())


def registration(data):
    keys = list(data.keys())
    values = list(data.values())

    sql = "INSERT INTO user (" + ",".join(keys) + ") VALUES (" + ",".join(["%s"] * len(values)) + ")"
    val = tuple(values)

    cursor.execute(sql, val)
    conn.commit()
    return True


@dp.message_handler(state=Form.first_name)
async def get_first_name(message: types.Message, state: FSMContext):
    if message.text.isalpha():
        await state.update_data(first_name=message.text[0].upper() + message.text[1:])
        await message.answer("Введите фамилию")
        await Form.last_name.set()
    else:
        await message.answer("Введите имя правильно")
        await Form.first_name.set()


@dp.message_handler(state=Form.last_name)
async def get_last_name(message: types.Message, state: FSMContext):
    if message.text.isalpha():
        await state.update_data(last_name=message.text[0].upper() + message.text[1:])
        await message.answer("Сколько вам лет?")
        await Form.age.set()
    else:
        await message.answer("Введите фамилию правильно")
        await Form.last_name.set()


@dp.message_handler(state=Form.age)
async def get_age(message: types.Message, state: FSMContext):
    if message.text.isalpha() or len(message.text) > 3:
        await message.answer("Введите свой действительный возраст")
        await Form.age.set()
    else:
        await state.update_data(age=int(message.text))
        countries_bd = request_mysql("SELECT * from country", False)
        markup = InlineKeyboardMarkup(button_width=2).add(
            *[InlineKeyboardButton(country["name"], callback_data=country["id"]) for country in countries_bd]
        )
        await message.answer("Выберите вашу страну?", reply_markup=markup)
        await Form.country_id.set()


@dp.callback_query_handler(lambda c: True, state=Form.country_id)
async def get_country_id(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(country_id=int(callback_query.data))
    code = request_mysql(f"SELECT code FROM country WHERE id = {callback_query.data}")["code"]
    await bot.send_message(callback_query.from_user.id, f"Введите свой номер телефона без +{code}")
    await Form.phone.set()


@dp.message_handler(state=Form.phone)
async def get_phone(message: types.Message, state: FSMContext):
    phone = message.text.replace(' ', '')
    if phone.isalpha() or len(phone) != 10:
        await message.answer("Введите номер парвильно")
        await Form.phone.set()
    else:
        await state.update_data(phone=phone)
        await message.answer("Ваш статус")
        await Form.status.set()


@dp.message_handler(state=Form.status)
async def get_status(message: types.Message, state: FSMContext):
    await state.update_data(status=message.text)
    await message.answer("Расскажите о себе")
    await Form.description.set()


@dp.message_handler(state=Form.description)
async def get_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    user_form = await state.get_data()
    user_form["id"] = message.from_user.id
    if registration(user_form):
        await auth_user(message)
    else:
        await message.answer("Не получилось зарегаться")
        await auth_user(message)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
