from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup

from bd import request_mysql, cursor, save_mysql
from buttons.users import user_menu
from loader import dp


@dp.callback_query_handler(lambda c: c.data.startswith('getMessages_'))
async def get_users_by_messages(call: CallbackQuery, state: FSMContext):
    my_id = call.from_user.id
    users_bd = request_mysql(f"SELECT COUNT(m.id) as count_messages, u.* FROM message m "
                             f"JOIN user u ON u.id = m.from_id WHERE to_id = {my_id} GROUP BY u.id", False)

    if users_bd:
        buttons = [[{
            'text': f"{user['first_name']} {user['last_name']} ({user['count_messages']})",
            'callback_data': f"getUser_{user['id']}"
        }] for user in users_bd]

        markup = InlineKeyboardMarkup(inline_keyboard=buttons)
        await call.message.edit_text("Выберрите пользователя", reply_markup=markup)
    else:
        await call.message.edit_text("Сообщений нет")


@dp.callback_query_handler(lambda c: c.data.startswith('requestFriend_'))
async def get_users_by_request_friendship(call: CallbackQuery):
    action = call.data.replace('requestFriend_', '')
    my_id = call.from_user.id
    if action == 'request':
        users_bd = request_mysql(f"SELECT * FROM user WHERE "
                                 f"id IN (SELECT from_id FROM friendship WHERE to_id = {my_id} "
                                 f"AND is_accepted = 0 AND is_denied = 0)", False)

        buttons = [[{
            'text': f"{user['first_name']} {user['last_name']}",
            'callback_data': f"getUser_{user['id']}"
        }] for user in users_bd]

        save_mysql(f"UPDATE friendship SET is_viewed = 1 WHERE is_denied = 0 AND is_viewed = 0 AND to_id = {my_id}")
    if action == 'resolve':
        users_bd = request_mysql(f"SELECT * FROM user WHERE "
                                 f"id IN (SELECT from_id FROM friendship WHERE to_id = {my_id} "
                                 f"AND is_accepted = 0 AND is_denied = 1)", False)

        buttons = [[{
            'text': f"{user['first_name']} {user['last_name']}",
            'callback_data': f"getUser_{user['id']}"
        }] for user in users_bd]

        save_mysql(f"UPDATE friendship SET is_viewed = 1 WHERE is_denied = 1 AND is_viewed = 0 AND to_id = {my_id}")

    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await call.message.edit_text("Выберите пользователя", reply_markup=markup)


@dp.callback_query_handler(lambda c: c.data.startswith('friends_'))
async def get_friends(call: CallbackQuery):
    my_id = call.from_user.id
    users_bd = request_mysql(f"SELECT * FROM user WHERE "
                             f"id IN (SELECT from_id FROM friendship WHERE is_accepted = 1 "
                             f"AND to_id = {my_id}) OR "
                             f"id IN (SELECT to_id  FROM friendship "
                             f"WHERE is_accepted = 1 AND from_id = {my_id})", False)
    if users_bd:
        buttons = [[{
            'text': f"{user['first_name']} {user['last_name']}",
            'callback_data': f"getUser_{user['id']}"
        }] for user in users_bd]

        markup = InlineKeyboardMarkup(inline_keyboard=buttons)
        await call.message.edit_text("Друзья", reply_markup=markup)
    else:
        await call.message.edit_text("Друзьей нет")

@dp.callback_query_handler(lambda c: c.data.startswith('listUsers_'))
async def get_users_by_country(call: CallbackQuery):
    country_id = call.data.replace('listUsers_', '')
    my_id = call.from_user.id
    users_bd = request_mysql(f"SELECT * FROM user WHERE id != {my_id} AND country_id = {country_id}", False)

    buttons = [[{
        'text': f"{user['first_name']} {user['last_name']}",
        'callback_data': f"getUser_{user['id']}"
    }] for user in users_bd]

    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await call.message.edit_text("Выбери пользователя", reply_markup=markup)


@dp.callback_query_handler(lambda c: c.data.startswith('getUser_'))
async def get_user(call: CallbackQuery):
    user_id = call.data.replace('getUser_', '')

    user_bd = request_mysql(f"SELECT * FROM user WHERE id = {user_id}")
    await call.message.edit_text(f"{user_bd['first_name']} {user_bd['last_name']}",
                                 reply_markup=user_menu(call.from_user.id, user_id))


@dp.callback_query_handler(lambda c: c.data.startswith('friendship_'))
async def friendship_actions(call: CallbackQuery):
    action = call.data.replace('friendship_', '')
    my_id = call.from_user.id

    if action.startswith('add_'):
        user_id = action.replace('add_', '')
        save_mysql(f"UPDATE friendship SET is_accepted = 1, is_denied = 0 "
                   f"WHERE (from_id = {my_id} AND to_id = {user_id}) OR (to_id = {my_id} AND from_id = {user_id})")

    if action.startswith('create_'):
        user_id = action.replace('create_', '')
        save_mysql(f"INSERT INTO friendship (from_id, to_id) VALUES ({my_id}, {user_id})")

    if action.startswith('delete_'):
        user_id = action.replace('delete_', '')
        save_mysql(f"DELETE FROM friendship "
                   f"WHERE (from_id = {my_id} AND to_id = {user_id}) OR (to_id = {my_id} AND from_id = {user_id})")

    if action.startswith('reject_'):
        user_id = action.replace('reject_', '')
        save_mysql(f"UPDATE friendship SET is_accepted = 0, is_denied = 1 "
                   f"WHERE to_id = {my_id} AND from_id = {user_id}")

    if action.startswith('accept_'):
        user_id = action.replace('accept_', '')
        save_mysql(f"UPDATE friendship SET is_accepted = 1, is_denied = 0 "
                   f"WHERE to_id = {my_id} AND from_id = {user_id}")
