from aiogram import types
from bd import request_mysql
from buttons.profile import profile_menu
from buttons.registratoin import reg_agrees
from loader import dp


@dp.message_handler(commands=['profile'])
async def my_profile(message: types.Message):
    my_id = message.from_user.id
    my_user = request_mysql(f"SELECT * FROM user WHERE id = {my_id}")

    if my_user:
        await message.answer(f"Привет, {my_user['first_name']} {my_user['last_name']}",
                             reply_markup=profile_menu(message.from_user.id))
    else:
        await message.answer(f"Вы не зарегистрированы. Продолжить?", reply_markup=reg_agrees)


@dp.message_handler(commands=['start'])
async def let_start(message: types.Message):
    await message.answer('Привет, для начала зайди в свой профиль /profile')
