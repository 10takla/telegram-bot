from aiogram.types import CallbackQuery

from buttons.profile import search_menu, notifies_menu
from loader import dp


@dp.callback_query_handler(lambda c: c.data.startswith('profile_'))
async def profile_actions(call: CallbackQuery):
    action = call.data.replace('profile_', '')
    if action == 'search':
        await call.message.edit_text('Выберите страну', reply_markup=search_menu(call.from_user.id))
        pass
    if action == 'messages':
        pass
    if action == 'notifies':
        await call.message.edit_text('Уведомления', reply_markup=notifies_menu(call.from_user.id))
        pass
    if action == 'about_me':
        pass