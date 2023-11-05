import os
from textwrap import dedent
import requests
from datetime import datetime

ENDPOINT_USERS = 'https://json.medrocket.ru/users'
ENDPOINT_TODOS = 'https://json.medrocket.ru/todos'

'''
Добавил файл script_fixed.py, фиксы ниже. Желательно проверять его.
1) Фикс именования старого отчета для Linux (56 и 76 строки)
2) Убрал list() (105 строка в старом файле, 114 в новом)
'''


def get_data_from_endpoint(endpoint: str) -> []:
    try:
        response = requests.get(endpoint)
    except requests.exceptions.ConnectionError:
        print(f"API {endpoint} недоступно!")
        raise SystemExit

    if response.status_code == 200:
        return response.json()
    else:
        print(f"/{endpoint.split('/')[-1]} вернул статус код {response.status_code}")
        raise SystemExit


def get_todos_for_users() -> dict:
    data = get_data_from_endpoint(ENDPOINT_TODOS)
    todos = dict()

    for todo in data:
        userid = todo.get('userId')

        if userid is not None:
            todos.setdefault(userid, {'completed': [], 'not_completed': []})
            status = todo.get('completed')
            title = todo.get('title') or 'Тайтл не указан'

            if status:
                todos[userid]['completed'].append(title)
            elif status is not None:
                todos[userid]['not_completed'].append(title)

    return todos


def write_to_file(output: str, filename: str) -> None:
    with open(filename, "w", encoding="utf-8") as file:
        file.write(output)


def get_datetime_from_old_file(user_username: str) -> str:
    with open(f'tasks/{user_username}.txt', "r") as file:
        next(file)
        date = file.readline()[-17::]

    date_time_obj = datetime.strptime(date.strip(), '%d.%m.%Y %H:%M')

    return date_time_obj.strftime('%Y-%m-%dT%H.%M')  # Нельзя использовать ":" в названии файла (время)


def rename_old_file(user_username: str) -> None:
    date = get_datetime_from_old_file(user_username)
    old_file_path = f'tasks/{user_username}.txt'

    counter = 0
    while True:
        try:
            if counter:
                new_file_path = f'tasks/old_{user_username}_{date}_{counter}.txt'
            else:
                new_file_path = f'tasks/old_{user_username}_{date}.txt'
            os.rename(old_file_path, new_file_path)

        except FileExistsError:
            counter += 1
        else:
            break


def output_to_file(output: str, username: str) -> None:
    if not os.path.exists(f'tasks/{username}.txt'):
        filename = f'tasks/{username}.txt'
        write_to_file(output, filename)
    else:
        filename = f"tasks/{username}-temp.txt"
        write_to_file(output, filename)
        rename_old_file(username)
        os.rename(filename, f"tasks/{username}.txt")


def get_output_template(user: dict) -> str:
    company_name = user.get('company', {}).get('name') or '*Компания не указана'
    user_name = user.get('name')
    email = user.get('email') or '*Email не указан'
    date = datetime.now().strftime('%d.%m.%Y %H:%M')

    output = dedent(f'''\
    # Отчёт для {company_name}.
    {user_name} <{email}> {date}
    ''')

    return output


def todos_formatted(key: str, current_user_todos: dict) -> str:
    user_todos = current_user_todos[key]
    user_todos_formatted = list(map(lambda s: f"- {s[:46]}…" if len(s) > 46 else f"- {s}", user_todos))
    return '\n'.join(user_todos_formatted)


def get_tasks() -> None:
    todo_dict = get_todos_for_users()
    users = get_data_from_endpoint(ENDPOINT_USERS)

    if users and not os.path.exists('tasks'):
        os.mkdir('tasks')

    for user in users:
        user_id = user.get('id')
        user_username = user.get('username')

        user_todos = todo_dict.get(user_id)

        output = get_output_template(user)

        if user_todos is not None and user_username is not None:

            todos_completed_count = len(user_todos.get('completed'))
            todos_not_completed_count = len(user_todos.get('not_completed'))

            output += f'Всего задач: {todos_completed_count + todos_not_completed_count}\n'

            if todos_not_completed_count:
                output += f'\n## Актуальные задачи ({todos_not_completed_count}):\n'
                output += todos_formatted('not_completed', user_todos)

            if todos_completed_count:
                if todos_not_completed_count:
                    output += '\n'

                output += f'\n## Завершенные задачи ({todos_completed_count}):\n'
                output += todos_formatted('completed', user_todos)

        else:
            output += f'У пользователя нету задач.'

        output_to_file(output, user_username)

    print('Готово!!')


def main():
    get_tasks()


if __name__ == '__main__':
    main()
