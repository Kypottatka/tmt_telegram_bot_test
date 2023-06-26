import os
from telegram import Bot
from telegram.ext import Updater, CommandHandler
from bot.controllers import TaskCommandController, TaskConversationHandler


TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')


def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    updater = Updater(bot=bot, use_context=True)
    task_command_controller = TaskCommandController()
    conversation_handler = TaskConversationHandler(
        task_command_controller=task_command_controller
    )
    conv_handler = conversation_handler.get_conversation_handler()
    dp = updater.dispatcher

    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler('start', task_command_controller.start))
    dp.add_handler(CommandHandler('add', task_command_controller.add))
    dp.add_handler(CommandHandler('done', task_command_controller.done))
    dp.add_handler(CommandHandler('delete', task_command_controller.delete))
    dp.add_handler(CommandHandler('list', task_command_controller.list))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
