from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor

TOKEN = "1491491937:AAHabrqm-4uunRftJb6zBeZCt_QwWthG9b8"
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


if __name__ == "__main__" :
    executor.start_polling(dp, skip_updates=True)