import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    CommandHandler, CallbackContext, ConversationHandler, MessageHandler,
    Filters
)
from bot.models import Task
from bot.views import format_task_list
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')


class TaskController:
    TITLE, DESCRIPTION, DEADLINE = range(3)

    def __init__(self):
        self.model = Task()
        self.current_task = {}

    def start(self, update: Update, context: CallbackContext):
        chat = update.effective_chat
        name = update.message.chat.first_name
        button = ReplyKeyboardMarkup([['/add', '/list']], resize_keyboard=True)
        context.bot.send_message(
            chat_id=chat.id,
            text=f"Приветствую, {name}! Я - бот-ассистент."
                 "Моя цель помочь вам достичь ваших целей "
                 "при помощи создания списка задач.",
            reply_markup=button
        )

    def add(self, update: Update, context: CallbackContext):
        user_id = update.message.from_user['id']
        chat = update.effective_chat
        button = ReplyKeyboardMarkup([['/cancel']], resize_keyboard=True)
        if len(self.model.get_all_tasks(user_id)) < 10:
            self.current_task['user_id'] = user_id
            context.bot.send_message(
                chat_id=chat.id,
                text='Введите заголовок задачи',
                reply_markup=button
            )
            return TaskController.TITLE
        return context.bot.send_message(
                chat_id=chat.id,
                text='Вы достигли лимита',
                reply_markup=button
            )

    def task_name(self, update: Update, context: CallbackContext):
        self.current_task['title'] = update.message.text
        update.message.reply_text('Введите описание задачи')
        return TaskController.DESCRIPTION

    def task_description(self, update: Update, context: CallbackContext):
        self.current_task['description'] = update.message.text
        update.message.reply_text('Укажите дедлайн задачи')
        return TaskController.DEADLINE

    def task_deadline(self, update: Update, context: CallbackContext):
        chat = update.effective_chat
        button = ReplyKeyboardMarkup([['/add', '/list']], resize_keyboard=True)
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
            reply_markup=button
        )
        return ConversationHandler.END

    # Выводит список всех задач
    def list(self, update: Update, context: CallbackContext):
        chat = update.effective_chat
        button = ReplyKeyboardMarkup(
            [['/add', '/done', '/delete']], resize_keyboard=True
        )
        user_id = update.message.from_user['id']
        tasks = self.model.get_all_tasks(user_id)
        formatted_tasks = format_task_list(tasks)
        context.bot.send_message(
            chat_id=chat.id,
            text=formatted_tasks,
            reply_markup=button
        )

    # Помечает задачу как выполненную
    def done(self, update: Update, context: CallbackContext):
        user_id = update.message.from_user['id']
        task_id = context.args[0] if context.args else None
        if task_id is not None:
            try:
                self.model.mark_task_as_done(user_id, task_id)
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Достижение: Задача помечена как 'Выполнена'!"
                )
            except Exception as e:
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"Возникла ошибка: {str(e)}"
                )
        else:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Пожалуйста, предоставьте идентификатор задачи."
            )

    # Удаляет задачу
    def delete(self, update: Update, context: CallbackContext):
        user_id = update.message.from_user['id']
        task_id = context.args[0] if context.args else None
        button = ReplyKeyboardMarkup(
            [['/done', '/delete']], resize_keyboard=True
        )
        if task_id is not None:
            try:
                self.model.delete_task(user_id, task_id)
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Задача успешно удалена!",
                    reply_markup=button
                )
            except Exception as e:
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"Такой задачи не существует: {str(e)}"
                )
        else:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Пожалуйста, предоставьте идентификатор задачи."
            )

    def cancel(self, update: Update, context: CallbackContext):
        chat = update.effective_chat
        button = ReplyKeyboardMarkup([['/add', '/list']], resize_keyboard=True)
        self.current_task = {}
        context.bot.send_message(
            chat_id=chat.id,
            text='Добавление задачи отменено',
            reply_markup=button
        )
        return ConversationHandler.END

    def get_conversation_handler(self):
        return ConversationHandler(
            entry_points=[CommandHandler('add', self.add)],
            states={
                TaskController.TITLE: [MessageHandler(
                    Filters.text & ~Filters.command, self.task_name)],
                TaskController.DESCRIPTION: [MessageHandler(
                    Filters.text & ~Filters.command, self.task_description)],
                TaskController.DEADLINE: [MessageHandler(
                    Filters.text & ~Filters.command, self.task_deadline)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)],
        )
