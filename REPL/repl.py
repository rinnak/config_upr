import os
import re
import shlex
vfs_name = "mvfs"
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
        # Fallback: простое разбиение по пробелам
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
def run():
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


if __name__ == "__main__":
    run()