from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from modules.start_menu import my_profile
from bd import save_mysql, request_mysql
from loader import dp


class SendMessages(StatesGroup):
    start = State()


@dp.callback_query_handler(lambda c: c.data.startswith('sendMessage_'))
async def messages_menu(call: CallbackQuery, state: FSMContext):
    user_id = call.data.replace('sendMessage_', '')
    markup = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('Отправить'), KeyboardButton('Отменить'))
    await call.message.answer("Отправьте сообщения", reply_markup=markup)
    await SendMessages.start.set()
    await state.update_data(user_id=user_id)


@dp.message_handler(state=SendMessages.start)
async def send_messages(message: types.Message, state: FSMContext):
    text = message.text
    my_id = message.from_user.id
    data = await state.get_data()
    user_id = data['user_id']

    messages = []
    if 'messages' in data.keys():
        messages = data['messages']

    if text == 'Отправить':
        tmp_text = ', '.join([f"('{i}', {my_id}, {user_id})" for i in messages])
        save_mysql(f"INSERT INTO message (text, from_id, to_id) VALUES {tmp_text}")
        await message.answer("Сообщения отправлены", reply_markup=ReplyKeyboardRemove())
        await my_profile(message)
        await state.finish()
        return
    if text == 'Отменить':
        await message.answer("Сообщения отменены", reply_markup=ReplyKeyboardRemove())
        await state.finish()
        return
    messages += [text]

    await state.update_data(messages=messages)
    await SendMessages.start.set()

@dp.callback_query_handler(lambda c: c.data.startswith('readMessages_'))
async def read_messages(call: CallbackQuery, state: FSMContext):
    my_id = call.from_user.id
    user_id = call.data.replace('readMessages_', '')
    messages = request_mysql(f"SELECT * FROM message WHERE is_viewed = 0 AND from_id = {user_id} AND to_id = {my_id}", False)

    for message in messages:
        await call.message.answer(message['text'])

    save_mysql(f"UPDATE message SET is_viewed = 1 WHERE is_viewed = 0 AND from_id = {user_id} AND to_id = {my_id}")