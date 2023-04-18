from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bd import request_mysql


def profile_menu(my_id):
    count_messages = request_mysql(f"SELECT COUNT(id) as count_messages "
                                   f"FROM message WHERE is_viewed = 0 AND to_id = {my_id}")['count_messages']
    count_friends = request_mysql(f"SELECT COUNT(id) as count_friends "
                                  f"FROM friendship WHERE is_accepted = 1 AND "
                                  f"(from_id = {my_id} OR to_id = {my_id})")['count_friends']
    count_notifies = request_mysql(f"SELECT COUNT(id) as count_notifies FROM friendship "
                                   f"WHERE is_viewed = 0 AND (is_accepted = 0 AND is_denied = 0 AND to_id = {my_id}) OR "
                                   f"(is_accepted = 0 AND is_denied = 1 AND from_id = {my_id})")['count_notifies']

    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton("Поиск пользователей", callback_data="profile_search"),
        ],
        [
            InlineKeyboardButton(f"Сообщения ({count_messages})", callback_data="getMessages_"),
            InlineKeyboardButton(f"Уведомления ({count_notifies})", callback_data="profile_notifies"),
        ],
        [
            InlineKeyboardButton(f"Друзья ({count_friends})", callback_data="friends_"),
            InlineKeyboardButton("О себе", callback_data="profile_about_me"),
        ],
    ])


def search_menu(my_id):
    my_country = request_mysql(f"SELECT id FROM country WHERE "
                               f"id = (SELECT country_id FROM user WHERE user.id = {my_id})")['id']
    countries = request_mysql(f"SELECT COUNT(u.id) as count_users, c.id, c.name "
                              f"FROM user u JOIN country c ON c.id = u.country_id "
                              f"WHERE u.id != {my_id} GROUP BY c.id", False)

    buttons = [
        [{
            'text': f"{'В моей стране' if country['id'] == my_country else country['name']} ({country['count_users']})",
            'callback_data': f"listUsers_{country['id']}"
        }]
        for country in countries
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def notifies_menu(my_id):
    count_requests_friend = request_mysql(f"SELECT COUNT(id) as count_requests_friend FROM friendship "
                                          f"WHERE to_id = {my_id} AND is_denied = 0 AND is_accepted = 0")[
        'count_requests_friend']

    count_rejects_friend = request_mysql(f"SELECT COUNT(id) as count_rejects_friend FROM friendship "
                                         f"WHERE from_id = {my_id} AND is_denied = 1 AND is_accepted = 0")[
        'count_rejects_friend']

    buttons = []
    if count_requests_friend:
        buttons += [{"text": f"Запросы на дружбу ({count_requests_friend})", 'callback_data': 'requestFriend_request'}]
    if count_rejects_friend:
        buttons += [{"text": f"Отказы на дружбу ({count_rejects_friend})", 'callback_data': 'requestFriend_reject'}]

    return InlineKeyboardMarkup(inline_keyboard=[
        buttons
    ])
