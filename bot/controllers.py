from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
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
        STATUS, DELETION, ADD,
    ) = range(6)

    def __init__(self):
        self.model = Task()
        self.current_task = {}

    def get_button_list(self, tasks):
        """
        Кнопки меню
        """
        button_list = [
            InlineKeyboardButton("Add", callback_data='add_task'),
            InlineKeyboardButton("List", callback_data='list_task'),
        ]

        # Показывает кнопки отметок и удаления только при наличии задач
        if tasks:
            button_list.extend([
                InlineKeyboardButton("Done", callback_data='done_task'),
                InlineKeyboardButton("Delete", callback_data='delete_task'),
            ])

        return button_list

    def send_message_with_markup(self, context, chat_id, text, tasks):
        """
        Шаблон отправки ответного сообщения
        """
        button_list = self.get_button_list(tasks=tasks)
        reply_markup = InlineKeyboardMarkup([button_list])
        context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup
        )

    def start(self, update: Update, context: CallbackContext):
        """
        Инициирует чат с полльзователем
        """
        chat = update.effective_chat
        name = update.message.chat.first_name
        tasks = self.model.get_all_tasks(user_id=update.effective_user['id'])
        self.send_message_with_markup(
            context,
            chat.id,
            f"Приветствую, {name}! Я - бот-ассистент."
            "Моя цель помочь вам достичь ваших целей "
            "при помощи создания списка задач.",
            tasks
        )

    def add(self, update: Update, context: CallbackContext):
        user_id = update.callback_query.from_user.id

        # Ограничение на количество одновременных задач - 10
        if len(self.model.get_all_tasks(user_id)) < 10:
            self.current_task['user_id'] = user_id

            update.callback_query.message.reply_text(
                'Введите заголовок задачи',
            )
            # Убирает меню и избегает его дублирования
            update.callback_query.edit_message_reply_markup(reply_markup=None)

            return self.TITLE
        else:
            return update.callback_query.message.reply_text(
                'Вы достигли лимита'
            )

    def done(self, update: Update, context: CallbackContext):
        """
        Отмечает задачу как выполненную
        """
        query = update.callback_query
        user_id = query.from_user.id

        tasks = self.model.get_all_tasks(user_id=user_id)

        button_list = [
            InlineKeyboardButton(task[0], callback_data=f'done_{task[0]}')
            for task in tasks
        ]
        reply_markup = InlineKeyboardMarkup([button_list])

        query.edit_message_text(
            "Список всех задач:\n"
            f"{format_task_list(tasks)}\n"
            "Выберите:",
            reply_markup=reply_markup
        )

        return self.STATUS

    def delete(self, update: Update, context: CallbackContext):
        """
        Удаляет задачу по индексу
        """
        query = update.callback_query
        user_id = query.from_user.id

        tasks = self.model.get_all_tasks(user_id=user_id)

        button_list = [
            InlineKeyboardButton(task[0], callback_data=f'delete_{task[0]}')
            for task in tasks
        ]
        reply_markup = InlineKeyboardMarkup([button_list])

        query.edit_message_text(
            f"{format_task_list(tasks)}\nВыберите:",
            reply_markup=reply_markup
        )

        return self.DELETION

    def list(self, update: Update, context: CallbackContext):
        """
        Выводит список всех активных задач
        """
        query = update.callback_query
        user_id = query.from_user.id
        tasks = self.model.get_all_tasks(user_id=user_id)

        button_list = self.get_button_list(tasks=tasks)
        reply_markup = InlineKeyboardMarkup([button_list])

        if tasks:
            query.edit_message_text(
                text=f"Список всех задач:\n\n{format_task_list(tasks)}",
            )
            query.edit_message_reply_markup(
                reply_markup=reply_markup
            )
        else:
            query.edit_message_text(
                text="У вас нет активных задач.\n\nМеню:",
            )
            query.edit_message_reply_markup(
                reply_markup=reply_markup
            )


class TaskConversationHandler:
    def __init__(self, task_command_controller):
        self.task_command_controller = task_command_controller
        self.model = Task()
        self.current_task = {}

    def task_name(self, update: Update, context: CallbackContext):
        """
        Обрабатывает ввод имени задачи.
        """
        self.current_task['title'] = update.message.text
        update.message.reply_text('Введите описание задачи')
        return self.task_command_controller.DESCRIPTION

    def task_description(self, update: Update, context: CallbackContext):
        """
        Обрабатывает ввод описания задачи.
        """
        self.current_task['description'] = update.message.text
        update.message.reply_text('Укажите дедлайн задачи')
        return self.task_command_controller.DEADLINE

    def task_deadline(self, update: Update, context: CallbackContext):
        """
        Обрабатывает ввод дедлайна задачи.
        """
        self.current_task['user_id'] = update.message.from_user['id']
        chat = update.effective_chat

        self.current_task['deadline'] = update.message.text
        self.model.add_task(
            self.current_task['user_id'],
            self.current_task['title'],
            self.current_task['description'],
            self.current_task['deadline']
        )
        tasks = self.model.get_all_tasks(user_id=update.effective_user['id'])
        button_list = self.task_command_controller.get_button_list(tasks=tasks)
        reply_markup = InlineKeyboardMarkup([button_list])
        context.bot.send_message(
            chat_id=chat.id,
            text='Задача успешно добавлена!',
            reply_markup=reply_markup
        )
        return ConversationHandler.END

    def task_done(self, update: Update, context: CallbackContext):
        """
        Обрабатывает ввод индентификатора задачи
         и помечает задачи как выполненную
        """
        query = update.callback_query
        user_id = update.effective_user['id']
        task_id = query.data.split('_')[1]

        task = self.model.get_task(user_id=user_id, task_id=task_id)

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

            # Убирает меню и избегает его дублирования
            query.edit_message_reply_markup(reply_markup=None)
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

        tasks = self.model.get_all_tasks(user_id=user_id)
        button_list = self.task_command_controller.get_button_list(tasks=tasks)
        reply_markup = InlineKeyboardMarkup([button_list])
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Меню:",
            reply_markup=reply_markup
        )

        return ConversationHandler.END

    def task_delete(self, update: Update, context: CallbackContext):
        """
        Обрабатывает ввод индентификатора задачи и удаляет ее
        """
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

        tasks = self.model.get_all_tasks(user_id=user_id)
        button_list = self.task_command_controller.get_button_list(tasks=tasks)
        reply_markup = InlineKeyboardMarkup([button_list])
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Меню:",
            reply_markup=reply_markup
        )
        return ConversationHandler.END

    def get_conversation_handler(self):
        """
        Занимается обработкой и распределением логики команд
        """
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

            fallbacks=[],
        )
