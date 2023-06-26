from telegram import (
    Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    CommandHandler, CallbackContext, ConversationHandler, MessageHandler,
    Filters, CallbackQueryHandler
)
from bot.models import Task
from bot.views import format_task, format_task_list
from dotenv import load_dotenv

load_dotenv()


class TaskCommandController:
    # Хранилище состояний для хендлера
    (
        TITLE, DESCRIPTION, DEADLINE,
        STATUS, DELETION, ADD, CANCEL,
    ) = range(7)

    def __init__(self):
        self.model = Task()
        self.current_task = {}

    # Инициирует диалог с ботом
    def start(self, update: Update, context: CallbackContext):
        chat = update.effective_chat
        name = update.message.chat.first_name
        button_list = [
            InlineKeyboardButton("Add", callback_data='add_task'),
            InlineKeyboardButton("List", callback_data='list_task'),
        ]
        reply_markup = InlineKeyboardMarkup([button_list])
        context.bot.send_message(
            chat_id=chat.id,
            text=f"Приветствую, {name}! Я - бот-ассистент."
                 "Моя цель помочь вам достичь ваших целей "
                 "при помощи создания списка задач.",
            reply_markup=reply_markup
        )

    # Запускает процесс создания задачи
    def add(self, update: Update, context: CallbackContext):
        user_id = update.callback_query.from_user.id

        if len(self.model.get_all_tasks(user_id)) < 10:
            self.current_task['user_id'] = user_id

            button = ReplyKeyboardMarkup([['/cancel']], resize_keyboard=True)

            update.callback_query.message.reply_text(
                'Введите заголовок задачи',
                reply_markup=button
            )

            return self.TITLE
        else:
            return update.callback_query.message.reply_text(
                'Вы достигли лимита'
            )

    # Отменяет процесс создания задачи
    def cancel(self, update: Update, context: CallbackContext):
        chat = update.effective_chat
        button_list = [
            InlineKeyboardButton("Add", callback_data='add_task'),
            InlineKeyboardButton("Done", callback_data='done_task'),
            InlineKeyboardButton("Delete", callback_data='delete_task'),
            InlineKeyboardButton("List", callback_data='list_task'),
        ]
        reply_markup = InlineKeyboardMarkup([button_list])
        context.bot.send_message(
            chat_id=chat.id,
            text='Добавление задачи отменено',
            reply_markup=reply_markup
        )
        return ConversationHandler.END

    # Помечает задачу как выполненную
    def done(self, update: Update, context: CallbackContext):
        user_id = update.callback_query.from_user.id

        tasks = self.model.get_all_tasks(user_id=user_id)

        button_list = [
            InlineKeyboardButton(task[0], callback_data=f'done_{task[0]}')
            for task in tasks
        ]
        reply_markup = InlineKeyboardMarkup([button_list])

        update.callback_query.message.reply_text(
            "Выберите:", reply_markup=reply_markup
        )

        return self.STATUS

    # Удаляет задачу
    def delete(self, update: Update, context: CallbackContext):
        user_id = update.callback_query.from_user.id

        tasks = self.model.get_all_tasks(user_id=user_id)

        button_list = [
            InlineKeyboardButton(task[0], callback_data=f'delete_{task[0]}')
            for task in tasks
        ]
        reply_markup = InlineKeyboardMarkup([button_list])

        update.callback_query.message.reply_text(
            "Выберите:", reply_markup=reply_markup
        )

        return self.DELETION

    # Выводит список всех задач
    def list(self, update: Update, context: CallbackContext):
        chat = update.effective_chat
        button_list = [
            InlineKeyboardButton("Add", callback_data='add_task'),
            InlineKeyboardButton("Done", callback_data='done_task'),
            InlineKeyboardButton("Delete", callback_data='delete_task'),
            InlineKeyboardButton("List", callback_data='list_task'),
        ]
        reply_markup = InlineKeyboardMarkup([button_list])
        user_id = update.callback_query.from_user.id
        tasks = self.model.get_all_tasks(user_id)
        if tasks:
            context.bot.send_message(
                chat_id=chat.id,
                text=format_task_list(tasks),
                reply_markup=reply_markup
            )
        else:
            return context.bot.send_message(
                chat_id=chat.id,
                text="У вас нет активных задач.",
                reply_markup=reply_markup
            )

    def help():
        pass

    def menu():
        pass


# Блок для приема параметров задач
class TaskConversationHandler:
    def __init__(self, task_command_controller):
        self.task_command_controller = task_command_controller
        self.model = Task()
        self.current_task = {}

    def task_name(self, update: Update, context: CallbackContext):
        self.current_task['title'] = update.message.text
        update.message.reply_text('Введите описание задачи')
        return self.task_command_controller.DESCRIPTION

    def task_description(self, update: Update, context: CallbackContext):
        self.current_task['description'] = update.message.text
        update.message.reply_text('Укажите дедлайн задачи')
        return self.task_command_controller.DEADLINE

    def task_deadline(self, update: Update, context: CallbackContext):
        self.current_task['user_id'] = update.message.from_user['id']
        chat = update.effective_chat
        button_list = [
            InlineKeyboardButton("Add", callback_data='add_task'),
            InlineKeyboardButton("Done", callback_data='done_task'),
            InlineKeyboardButton("Delete", callback_data='delete_task'),
            InlineKeyboardButton("List", callback_data='list_task'),
        ]
        reply_markup = InlineKeyboardMarkup([button_list])
        self.current_task['deadline'] = update.message.text
        self.model.add_task(
            self.current_task['user_id'],
            self.current_task['title'],
            self.current_task['description'],
            self.current_task['deadline']
        )
        context.bot.send_message(
            chat_id=chat.id,
            text='Задача успешно добавлена!',
            reply_markup=reply_markup
        )
        return ConversationHandler.END

    def task_done(self, update: Update, context: CallbackContext):
        query = update.callback_query
        user_id = update.effective_user['id']
        task_id = query.data.split('_')[1]

        task = self.model.get_task(user_id=user_id, task_id=task_id)

        button_list = [
            InlineKeyboardButton("Add", callback_data='add_task'),
            InlineKeyboardButton("Done", callback_data='done_task'),
            InlineKeyboardButton("Delete", callback_data='delete_task'),
            InlineKeyboardButton("List", callback_data='list_task'),
        ]
        reply_markup = InlineKeyboardMarkup([button_list])
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            reply_markup=reply_markup
        )

        if task and task[6] == 'Выполнено':
            query.answer()
            query.edit_message_text(
                "Эта задача уже выполнена."
            )
        elif task:
            self.model.mark_as_done(user_id, task_id)
            updated_task = self.model.get_task(
                user_id=user_id,
                task_id=task_id
            )
            query.answer()
            query.edit_message_text(
                "Достижение: Задача помечена как 'Выполнена'!\n\n"
                f"{format_task(updated_task)}"
            )
        else:
            query.answer()
            query.edit_message_text(
                "Такой задачи не существует! "
                "Пожалуйста, предоставьте идентификатор задачи."
            )

        return ConversationHandler.END

    def task_delete(self, update: Update, context: CallbackContext):
        query = update.callback_query
        user_id = update.effective_user['id']
        task_id = query.data.split('_')[1]

        task = self.model.get_task(user_id=user_id, task_id=task_id)

        if task:
            self.model.delete_task(user_id, task_id)
            query.answer()
            query.edit_message_text("Задача успешно удалена!")
        else:
            query.answer()
            query.edit_message_text(
                "Такой задачи не существует! "
                "Пожалуйста, предоставьте идентификатор задачи."
            )

        return ConversationHandler.END

    def get_conversation_handler(self):
        return ConversationHandler(
            entry_points=[
                CommandHandler(
                    'start',
                    self.task_command_controller.start
                ),

                CallbackQueryHandler(
                    self.task_command_controller.add,
                    pattern='^add_task$'
                ),
                CallbackQueryHandler(
                    self.task_command_controller.done,
                    pattern='^done_task$'
                ),
                CallbackQueryHandler(
                    self.task_command_controller.delete,
                    pattern='^delete_task$'
                ),
                CallbackQueryHandler(
                    self.task_command_controller.list,
                    pattern='^list_task$'
                ),

                CommandHandler(
                    'cancel',
                    self.task_command_controller.cancel
                )
                ],

            states={
                self.task_command_controller.STATUS: [CallbackQueryHandler(
                    self.task_done,
                    pattern='^done_')],
                self.task_command_controller.DELETION: [CallbackQueryHandler(
                    self.task_delete,
                    pattern='^delete_')],

                self.task_command_controller.TITLE: [MessageHandler(
                    Filters.text & ~Filters.command,
                    self.task_name)],
                self.task_command_controller.DESCRIPTION: [MessageHandler(
                    Filters.text & ~Filters.command,
                    self.task_description)],
                self.task_command_controller.DEADLINE: [MessageHandler(
                    Filters.text & ~Filters.command,
                    self.task_deadline)],
            },

            fallbacks=[CommandHandler(
                'cancel',
                self.task_command_controller.cancel
            )],
        )
