from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from bd import conn, cursor, request_mysql
from loader import dp
from modules.start_menu import my_profile


class Form(StatesGroup):
    id = State()
    first_name = State()
    last_name = State()
    age = State()
    country_id = State()
    phone = State()
    status = State()
    description = State()
    only_friends = State()


@dp.callback_query_handler(lambda c: c.data.startswith('regUser_'))
async def registration(callback: CallbackQuery, state: FSMContext):
    action = callback.data.replace('regUser_', '')

    if action == 'yes':
        await callback.message.answer(f"Введите имя")
        await Form.first_name.set()
    if action == 'no':
        await callback.message.answer(f"Окей")


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

        await message.answer("Выберите страну", reply_markup=markup)
        await Form.country_id.set()


@dp.callback_query_handler(lambda c: True, state=Form.country_id)
async def get_country_id(callback_query: CallbackQuery, state: FSMContext):
    await state.update_data(country_id=int(callback_query.data))
    code = request_mysql(f"SELECT code FROM country WHERE id = {callback_query.data}")["code"]
    await callback_query.message.answer(f"Введите свой номер телефона без +{code}")
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
    markup = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('Да'), KeyboardButton('Нет'))
    await message.answer("Получать сообщения только от друзей?", reply_markup=markup)
    await Form.only_friends.set()


@dp.message_handler(text=['Да', 'Нет'], state=Form.only_friends)
async def get_only_friends(message: types.Message, state: FSMContext):
    if message.text == 'Да ':
        await state.update_data(only_friends=1)
    if message.text == 'Нет ':
        await state.update_data(only_friends=0)

    user_form = await state.get_data()
    user_form["id"] = message.from_user.id
    if registrate(user_form):
        await message.answer("Вы зарегистрированы", reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer("Регистрация не прошла")

def registrate(data):
    keys = list(data.keys())
    values = list(data.values())

    sql = "INSERT INTO user (" + ",".join(keys) + ") VALUES (" + ",".join(["%s"] * len(values)) + ")"
    val = tuple(values)

    cursor.execute(sql, val)
    conn.commit()
    return True
