from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    InlineKeyboardButton
from bd import request_mysql, cursor, conn
from aiogram.types import CallbackQuery


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
    send_message = State()


TOKEN = "1491491937:AAH-at3HhEmtF-LYCvSB3jm48h01Igjr1o0"
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
    user_bd = request_mysql(f"SELECT * FROM user WHERE id = {message.from_user.id}")

    if user_bd:
        count_users = \
            request_mysql(f"SELECT COUNT(1) AS count_users FROM user WHERE country_id = {user_bd['country_id']}", True)[
                "count_users"]

        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(f"Пользователи в моей стране ({count_users})",
                                         callback_data='userMenu_get_users', ),
                ],
                [
                    InlineKeyboardButton("О себе", callback_data='userMenu_about_me'),
                    InlineKeyboardButton(text="Кнопка 3", callback_data="userMenu_callback_data_3")
                ]
            ],
            row_widths=[1, 2]
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


@dp.message_handler(state=Dialog.send_message)
async def send_message(callback_query: CallbackQuery, state: FSMContext):


@dp.callback_query_handler(lambda c: c.data.startswith('actToUser_'))
async def action_to_user(callback_query: CallbackQuery, state: FSMContext):
    action = callback_query.data.replace('actToUser_', '')
    if action == 'send_message':
        await callback_query.message.answer("Напишите сообщение")
        await User.send_message.set()


@dp.callback_query_handler(lambda c: c.data.startswith('getUserById_'))
async def get_user_by_id(callback_query: CallbackQuery, state: FSMContext):
    id = callback_query.data.replace('getUserById_', '')
    markup = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton('Отправить сообщение', callback_data='actToUser_send_message'),
        InlineKeyboardButton('Подписаться', callback_data='actToUser_subscribe'),
    ]])
    await callback_query.message.answer(user_show(id), reply_markup=markup)


@dp.callback_query_handler(lambda c: c.data.startswith('userMenu_'))
async def my_profile_menu(callback_query: CallbackQuery, state: FSMContext):
    action = callback_query.data.replace('userMenu_', '')
    if action == 'about_me':
        await callback_query.message.answer(user_show(callback_query.from_user.id))
        await state.finish()
    if action == 'get_users':
        users_bd = request_mysql(
            f"SELECT * FROM `user` WHERE country_id = (SELECT country_id FROM user WHERE id = {callback_query.from_user.id})",
            False)
        if users_bd:
            markup = InlineKeyboardMarkup(button_width=1).add(
                *[InlineKeyboardButton(f"{user['first_name']} {user['last_name']}",
                                       callback_data=f"getUserById_{user['id']}") for user
                  in users_bd]
            )
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
