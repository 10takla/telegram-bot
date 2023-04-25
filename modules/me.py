from aiogram.types import CallbackQuery
from loader import dp
from bd import request_mysql
from buttons.me import change
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def user_info(my_id):
    me_bd = request_mysql(f"SELECT u.age, u.status, u.description, c.name, "
                          f"CONCAT(u.first_name, ' ', u.last_name) AS full_name, "
                          f"CONCAT('+', c.code, ' ', u.phone) AS full_phone "
                          f"FROM user u JOIN country c ON c.id = u.country_id  WHERE u.id = {my_id}")

    tmp = {
        'full_name': 'Имя',
        'age': 'Возрост',
        'full_phone': 'Номер телефона',
        'name': 'Страна',
        'status': 'Статус',
        'description': 'Описание',
    }
    print(me_bd)
    data = [': '.join([value, str(me_bd[field])]) for field, value in tmp.items() if field in me_bd.keys()]
    return '\n'.join(data)


@dp.callback_query_handler(lambda c: c.data.startswith('meInfo_'))
async def change_do(call: CallbackQuery):
    my_id = call.from_user.id
    me_info = user_info(my_id)

    await call.message.answer(f"{me_info}", reply_markup=change)


@dp.callback_query_handler(lambda c: c.data.startswith('changeMe_'))
async def change_me(call: CallbackQuery):


    await call.message.answer('Что хотите изменить?')