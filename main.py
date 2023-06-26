import os
from telegram import Bot
from telegram.ext import Updater, CommandHandler
from bot.controllers import TaskController


TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')


def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    updater = Updater(bot=bot, use_context=True)
    task_controller = TaskController()
    dp = updater.dispatcher
    dp.add_handler(task_controller.get_conversation_handler())

    conv_handler = task_controller.get_conversation_handler()
    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler('start', task_controller.start))
    dp.add_handler(CommandHandler('add', task_controller.add))
    dp.add_handler(CommandHandler('done', task_controller.done))
    dp.add_handler(CommandHandler('delete', task_controller.delete))
    dp.add_handler(CommandHandler('list', task_controller.list))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
