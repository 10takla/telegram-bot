from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bd import request_mysql


def user_menu(my_id, user_id):
    buttons = []

    friendship = request_mysql(
        f"SELECT * FROM friendship WHERE "
        f"((from_id = {my_id} AND to_id={user_id}) OR (to_id = {my_id} AND from_id={user_id}))")

    only_friends = request_mysql(f"SELECT only_friends FROM user WHERE id = {user_id}")['only_friends']

    if only_friends and (not friendship or not friendship["is_accepted"]):
        buttons.append({
            'text': 'Чат только с дрезьями',
            'callback_data': f'none_{user_id}'
        })
    else:
        buttons.append({
            'text': 'Отправить сообщение',
            'callback_data': f'sendMessage_{user_id}'
        })

    if friendship is None:
        buttons.append({
            'text': 'Добавить в друзья',
            'callback_data': f'friendship_create_{user_id}'
        })

    if friendship and friendship['is_accepted']:
        buttons.append({
            'text': 'Удалить из друзей',
            'callback_data': f'friendship_delete_{user_id}'
        })
    if friendship and not friendship['is_accepted'] and not friendship['is_denied'] and friendship['from_id'] == my_id:
        buttons.append({
            'text': 'Отменить запрос дружбы',
            'callback_data': f'friendship_delete_{user_id}'
        })
    if friendship and not friendship['is_accepted'] and not friendship['is_denied'] and friendship['to_id'] == my_id:
        buttons.append({
            'text': 'Принять дружбу',
            'callback_data': f'friendship_accept_{user_id}'
        })
        buttons.append({
            'text': 'Отказать в дружбе',
            'callback_data': f'friendship_reject_{user_id}'
        })

    if friendship and friendship['is_denied'] and friendship['from_id'] == my_id:
        buttons.append({
            'text': 'Не хочет с вами дружить',
            'callback_data': f'friendship_none_{user_id}'
        })

    count_messages = request_mysql(f"SELECT COUNT(id) as count_messages FROM message "
                                   f"WHERE is_viewed = 0 AND from_id = {user_id} AND to_id = {my_id}")['count_messages']

    if count_messages:
        buttons.append({
            'text': f'Новые сообщения ({count_messages})',
            'callback_data': f'readMessages_{user_id}'
        })

    return InlineKeyboardMarkup(inline_keyboard=[buttons])
