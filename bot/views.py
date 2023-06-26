def format_task(task):
    return (f"Идентификатор: {task[0]}\n"
            f"Заголовок: {task[2]}\n"
            f"Описание: {task[3]}\n"
            f"Создана: {task[4]}\n"
            f"Дедлайн: {task[5]}\n"
            f"Статус: {task[6]}\n")


def format_task_list(tasks):
    return "\n\n".join(format_task(task) for task in tasks)
