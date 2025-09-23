import os
import re
import shlex
import argparse #работа с аргументами командной строки
vfs_name = "mvfs"
vfs_physical_path = None
startup_script_path = None

def parse(input_str):
    result = ""
    pos = 0
    length = len(input_str)
    while pos < length:
        # обработка формата ${VAR}
        if pos + 1 < length and input_str[pos] == '$' and input_str[pos + 1] == '{':
            end = input_str.find('}', pos + 2)
            if end != -1:
                var_name = input_str[pos + 2:end]
                env_value = os.getenv(var_name)
                if env_value:
                    result += env_value
                else:
                    result += "${" + var_name + "}"
                pos = end + 1
                continue
        # обработка формата $VAR
        elif input_str[pos] == '$' and pos + 1 < length:
            var_start = pos + 1
            var_end = var_start
            while var_end < length and (input_str[var_end].isalnum() or input_str[var_end] == '_'):
                var_end += 1
            var_name = input_str[var_start:var_end]
            env_value = os.getenv(var_name)
            if env_value:
                result += env_value
            else:
                result += "$" + var_name
            pos = var_end
            continue
        result += input_str[pos]
        pos += 1
    return result
def split_command(input_str):
    try:
        # Используем shlex для корректного разбиения команд с кавычками
        return shlex.split(input_str)
    except:
        return input_str.split()
def execute_ls(tokens):
    output = "Команда ls выполнена"
    if len(tokens) > 1:
        output += " с аргументами: " + " ".join(tokens[1:])
    print(output)
def execute_cd(tokens):
    if len(tokens) > 2:
        print("Ошибка. Слишком много аргументов для команды cd")
        return
    if len(tokens) > 1:
        if tokens[1] == "-":
            print("Команда cd выполнена. Переход в предыдущую директорию")
        elif tokens[1] == "~":
            print("Команда cd выполнена. Переход в домашнюю директорию")
        else:
            print(f"Команда cd выполнена. Переход в директорию: {tokens[1]}")
    else:
        print("Команда cd выполнена. Переход в домашнюю директорию")

def run(script_mode = False, script_lines = None):
    print("Эмулятор командной строки UNIX")
    print("Напишите 'exit' для выхода или 'help' для справки")
    while True:
        try:
            user_input = input(f"{vfs_name} $ ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nВыход из эмулятора. Пока.")
            break
        if not user_input:
            continue
        tokens = split_command(user_input)
        if not tokens:
            continue
        # Парсим все токены
        parsed_tokens = [parse(token) for token in tokens]
        command = parsed_tokens[0]
        if command == "exit":
            print("Выход из эмулятора. Пока.")
            break
        elif command == "help":
            print("Доступные команды:")
            print("  ls [аргументы]  - список файлов")
            print("  cd [директория] - смена директории")
            print("  exit            - выход из программы")
            print("  help            - показать справку")
        elif command == "ls":
            execute_ls(parsed_tokens)
        elif command == "cd":
            execute_cd(parsed_tokens)
        else:
            print(f"Ошибка: неизвестная команда '{command}'")
            print("Введите 'help' для списка команд")

def run_startup_script(script_path):
    if script_path is None:
        return True
    if not os.path.isfile(script_path): #проверка существования файла
        print(f"Ошибка: стартовый скрипт {script_path} не найден")
        return False
    try:
        with open(script_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            print(f"Выполнение стартового скрипта: {script_path}")
            line_number = 0 #счетчик строк для ошибок
            for line in lines:
                line_number+=1
                cleaned_line = line.strip() #без пробелов в начале и в конце
                if not cleaned_line or cleaned_line.startswith('#'):
                    continue
                print(f"Выполняется команда: {cleaned_line}")
                tokens = split_command(cleaned_line)
                parsed_tokens = [parse(token) for token in tokens]
                command = parsed_tokens[0]
                if command == "exit":
                    print("Выход из скрипта")
                    break
                elif command == "ls":
                    execute_ls(parsed_tokens)
                elif command == "cd":
                    execute_cd(parsed_tokens)
                else:
                    print(f"Ошибка: неизвестная команда {command}")
    except FileNotFoundError:
        print(f"Ошибка: файл '{script_path}' не найден.")
    except Exception as e:
        print(f"Ошибка выполнения скрипта на строке {line_number}: {e}")


def parse_arguments():
    parser = argparse.ArgumentParser(description='Эмулятор виртуальной файловой системы UNIX') #разбиваем параметры на части
    parser.add_argument( #добавляем аргумент для пути к vfs
        '--vfs-path',
        type=str, #после аргумента идет строка
        help='Путь к физическом расположению vfs'
    )
    parser.add_argument( #добавляем аргумент для скрипта
        '--script',
        type = str,
        help = 'Путь к стартовому скрипту для выполнения команд эмулятора'
    )
    args = parser.parse_args() #Парсим аргументы, создает объект с (vfs_path='/tmp', script='init.vfs')
    return args


def main():
    global vfs_physical_path, startup_script_path
    print()
    print("Эмулятор виртуальной файловой системы UNIX")
    args = parse_arguments()
    vfs_physical_path = args.vfs_path
    startup_script_path = args.script
    print()
    print("Параметры конфигурации:")
    if vfs_physical_path is not None:
        print(f"Физический путь vfs: {vfs_physical_path}")
    else:
        print("Физический путь vfs не указан")
    if startup_script_path is not None:
        print(f"Стартовый скрипт: {startup_script_path}")
    else:
        print("Стартовый скрипт не указан")
    print()
    print("Эмулятор готов к работе")
    if startup_script_path:
        print()
        print("Запуск стартового скрипта")
        run_startup_script(startup_script_path)
        print("Стартовый скрипт завершен")
        print()
if __name__ == "__main__":
    main()
    run()
