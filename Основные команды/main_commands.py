import os
import shlex
import csv
import base64
from datetime import datetime
import argparse #работа с аргументами командной строки
vfs_name = "mvfs"
vfs_physical_path = None
startup_script_path = None

class VFSNode:
    def __init__(self, name, is_directory=True, content=None, parent=None):
        self.name = name
        self.is_directory = is_directory #файл или папка
        self.content = {} if is_directory else (content if content else b'')
        self.parent = parent
    def get_path(self):
        path_parts = []
        cur = self
        while cur and cur.name:
            path_parts.append(cur.name)
            cur = cur.parent
        return '/' + '/'.join(reversed(path_parts))


class VFS:

    def __init__(self): #инициализация vfs в памяти
        self.root = VFSNode("") #корневая директория
        self.current_directory = self.root
        self.operations_count = 0
        self.total_files = 0
        self.total_dirs = 1 #с учетом корневой папки
        self.previous_directory = self.root #для команды cd

    def create_default(self): #создание vfs по умолчанию в памяти
        self.root = VFSNode("")
        self.current_directory = self.root
        self.previous_directory = self.root
        self.total_files = 0
        self.total_dirs = 1

        home = VFSNode("home", parent=self.root)
        self.root.content["home"] = home
        self.total_dirs += 1

        user = VFSNode("user", parent = home)
        home.content["user"] = user
        self.total_dirs += 1

        documents = VFSNode("documents", parent = user)
        user.content["documents"] = documents
        self.total_dirs += 1

        readme_content = b"Hello World"
        readme_file = VFSNode("README.txt", is_directory = False, content = readme_content, parent = user)
        user.content["README.txt"] = readme_file
        self.total_files += 1

        print("Создана VFS по умолчанию")

    def reset_to_default(self):
        print("Все данные текущей VFS будут потеряны")
        old_files = self.total_files
        old_dirs = self.total_dirs
        old_path = self.get_current_path()
        print("Сброс VFS")
        self.create_default()
        print(f"Предыдущая VFS: {old_dirs} папок, {old_files} файлов, путь: {old_path}")
        print(f"Текущая VFS: {self.total_dirs} папок, {self.total_files} файлов")
        print(f"Текущий путь: {self.get_current_path()}")

    def _split_path(self, path):
        if not path: return []
        path = path.replace('//', '/')
        parts = path.split('/')
        if parts and parts[0] == "":
            clean_parts = [""] + [part for part in parts[1:] if part]
        else:
            clean_parts = [part for part in parts if part]
        return clean_parts
    
    def _resolve_path(self, path_parts, create_missing=False):
        #Найти узел по пути
        if not path_parts:
            return self.current_directory
        cur = self.root if path_parts[0] =="" else self.current_directory
        for part in path_parts:
            if part == "":
                continue
            if part == ".":
                continue
            if part == "..": #переход на ур выше
                if cur.parent is not None:
                    cur=cur.parent
                continue
            if part in cur.content:
                cur = cur.content[part] #переход к следующему узлу
            elif create_missing:
                #узел не найден но разрешено создание
                new_node = VFSNode(name=part, is_directory=True, parent=cur)
                cur.content[part] = new_node
                cur = new_node #добавляем ноый узел в содержимое
                self.total_dirs += 1
            else:
                return None
        return cur
    
    def load_from_csv(self, csv_path):
        try:
            # Полностью сбрасываем VFS
            self.root = VFSNode("")
            self.current_directory = self.root
            self.previous_directory = self.root
            self.total_files = 0
            self.total_dirs = 1  # корневая директория
            
            with open(csv_path, mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)
                
                # Пропускаем заголовок
                headers = next(reader, None)
                print(f"Загружаем VFS из CSV. Заголовки: {headers}")
                
                for row_num, row in enumerate(reader, 2):
                    if not row or len(row) < 2:
                        continue
                        
                    path = row[0].strip()
                    is_directory_str = row[1].strip().lower()
                    content = row[2].strip() if len(row) > 2 else ""
                    
                    # Проверяем и преобразуем is_directory
                    if is_directory_str == 'true':
                        is_directory = True
                    elif is_directory_str == 'false':
                        is_directory = False
                    else:
                        print(f"Ошибка в строке {row_num}: неверное значение is_directory '{is_directory_str}'")
                        continue
                    
                    print(f"Создаем узел: путь='{path}', директория={is_directory}, контент='{content}'")
                    
                    # Создаем узел
                    success = self.create_node(path, is_directory, content)
                    if not success:
                        print(f"Предупреждение: не удалось создать узел '{path}'")
                        
            print(f"VFS загружена. Файлов: {self.total_files}, Папок: {self.total_dirs}")
            
        except FileNotFoundError:
            print(f"Ошибка: файл {csv_path} не найден")
            self.create_default()
        except Exception as e:
            print(f"Ошибка загрузки VFS из CSV: {e}")
            self.create_default()


    def create_node(self, path, is_directory, content=None):
        if path == "/":
        # Корневой узел уже создан
            return True
        #создание узла при загрузке из csv
        path_parts = self._split_path(path)
        if not path_parts:
            return False
        parent_parts = path_parts[:-1] #путь к род дир
        node_name = path_parts[-1] #имя узла
        parent = self._resolve_path(parent_parts, create_missing=True)
        #находим или создаем род директорию
        if not parent:
            return False
        if node_name in parent.content:
            return False #узел уже существует
        file_content = b""
        if not is_directory and content:
            if content.startswith('base64:'):
                try:
                    encoded_content = content[7:]
                    file_content = base64.b64decode(encoded_content)
                except Exception as e:
                    print(f"Ошибка декодирования base64: {e}")
            else:
                file_content = content.encode('utf-8')
        new_node = VFSNode( #создаем новый узел 
            name = node_name,
            is_directory=is_directory,
            content=file_content,
            parent=parent
        )
        parent.content[node_name] = new_node
        if is_directory:
            self.total_dirs += 1
        else:
            self.total_files += 1
        return True

    def get_current_path(self):
        path_parts = []
        cur = self.current_directory
        while cur and cur.name:
            path_parts.append(cur.name)
            cur = cur.parent
        if not path_parts:
            return "/"
        path_parts.reverse()
        return "/"+"/".join(path_parts)
    
    def change_directory(self, path):
        self.previous_directory = self.current_directory
        #сохр текущ дир как предыдущ
        if path == "~": #переход в дом. дир.
            target = self._resolve_path(["/", "home", "user"])
            if target and target.is_directory:
                self.current_directory = target
                return True
            else:
                print("Ошибка: домашняя директория не найдена")
                return False
        elif path == "-": #переход в предыдущ дир
            if self.previous_directory:
                self.current_directory, self.previous_directory = self.previous_directory, self.current_directory
                return True
            else:
                print("Ошибка, предыдущая директория не задана")
                return False
        elif path == ".":
            return True
        elif path == "/":
            self.current_directory = self.root
            return True
        path_parts = self._split_path(path)
        target = self._resolve_path(path_parts)
        if target is None:
            print(f"Ошибка, директория {path} не найдена")
            return False
        if not target.is_directory:
            print(f"Ошибка, {path} не является директорией")
            return False
        self.current_directory = target
        return True
    
    def list_directory(self, path="."):
        if path==".":
            target_dir = self.current_directory
        else:
            path_parts = self._split_path(path)
            target_dir = self._resolve_path(path_parts)
        if target_dir is None:
            print(f"Ошибка: путь {path} не найден")
            return None
        if not target_dir.is_directory:
            print(f"Ошибка, {path} не является директорией")
            return None
        items = list(target_dir.content.keys()) # Получаем и сортируем содержимое директории
        items.sort()
        return items
        

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
def execute_ls(vfs, tokens):
    path = tokens[1] if len(tokens) >1 else "."
    items = vfs.list_directory(path)
    if items is not None:
        for item in items:
            print(item)
        return True
    else:
        return False
def execute_cd(vfs, tokens):
    if len(tokens) > 2:
        print("Ошибка. Слишком много аргументов для команды cd")
        return
    path = tokens[1] if len(tokens) >1 else "~"
    if vfs.change_directory(path):
        print(f"Текущий путь {vfs.get_current_path()}")
def execute_vfs_init(vfs, tokens):
    if len(tokens)>1:
        print("Ошибка, команда vfs-init не принимает аргументов")
        return
    vfs.reset_to_default()

def execute_cat(vfs, tokens):
    if len(tokens) != 2:
        print("Использование: cat <файл>")
        return
    path = tokens[1]
    path_parts = vfs._split_path(path)
    target = vfs._resolve_path(path_parts)
    
    if not target:
        print(f"Ошибка: файл '{path}' не найден")
    elif target.is_directory:
        print(f"Ошибка: '{path}' является директорией")
    else:
        try:
            content = target.content
            if isinstance(content, bytes):
                content = content.decode('utf-8')
            print(content)
        except Exception as e:
            print(f"Ошибка чтения файла: {e}")

def execute_clear(vfs, tokens):
    if os.name == 'nt':
        os.system('cls') #для винды
    else:
        os.system('clear')
    return True

def execute_rev(vfs, tokens):
    if len(tokens) != 2:
        print("Использование: rev <строка>")
        return False
    input_string = tokens[1]
    reversed_string = input_string[::-1]
    print(reversed_string)
    return True

def execute_tac(vfs, tokens):
    if len(tokens)!=2:
        print("Использование: tac <файл>")
        return False
    path = tokens[1]
    path_parts = vfs._split_path(path)
    target = vfs._resolve_path(path_parts)
    if not target:
        print( f"Ошибка: файл {path} не найден")
        return False
    if target.is_directory:
        print(f"Ошибка: {path} является директорией")
        return False
    try:
        content = target.content
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        lines = content.split('\n')
        for line in reversed(lines):
            print(line)
        return True
    except Exception as e:
        print(f"Ошибка чтения файла: {e}")
        return False

def run(vfs, script_mode = False, script_lines = None):
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
            print("  cat <файл>      - показать содержимое файла")
            print("  clear            - очистить экран")
            print("  rev <строка>     - перевернуть строку")
            print("  tac <файл>       - вывести файл в обратном порядке")
            print("  vfs-init        - сброс VFS к состоянию по умолчанию")
            print("  exit            - выход из программы")
            print("  help            - показать справку")
        elif command == "ls":
            execute_ls(vfs, parsed_tokens)
        elif command == "cd":
            execute_cd(vfs, parsed_tokens)
        elif command=="vfs-init":
            execute_vfs_init(vfs, parsed_tokens)
        elif command == "cat":
            execute_cat(vfs, parsed_tokens)
        elif command == "clear":
            execute_clear(vfs, parsed_tokens)
        elif command == "rev":
            execute_rev(vfs, parsed_tokens)
        elif command == "tac":
            execute_tac(vfs, parsed_tokens)
        else:
            print(f"Ошибка: неизвестная команда '{command}'")
            print("Введите 'help' для списка команд")


def run_startup_script(script_path, vfs):
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
                tokens = split_command(cleaned_line)
                parsed_tokens = [parse(token) for token in tokens]
                command = parsed_tokens[0]
                print(f"mvfs $ {cleaned_line}")
                if command == "exit":
                    print("Выход из скрипта")
                    break
                elif command == "ls":
                    execute_ls(vfs, parsed_tokens)
                elif command == "cd":
                    execute_cd(vfs, parsed_tokens)
                elif command =="vfs-init":
                    execute_vfs_init(vfs, parsed_tokens)
                elif command == "cat":
                    execute_cat(vfs, parsed_tokens)
                elif command == "clear":
                    execute_clear(vfs, parsed_tokens)
                elif command == "rev":
                    execute_rev(vfs, parsed_tokens)
                elif command == "tac":
                    execute_tac(vfs, parsed_tokens)
                elif command == "help":
                    print("Доступные команды:")
                    print("  ls [аргументы]  - список файлов")
                    print("  cd [директория] - смена директории")
                    print("  cat <файл>      - показать содержимое файла")
                    print("  clear            - очистить экран")
                    print("  rev <строка>     - перевернуть строку")
                    print("  tac <файл>       - вывести файл в обратном порядке")
                    print("  vfs-init        - сброс VFS к состоянию по умолчанию")
                    print("  exit            - выход из программы")
                    print("  help            - показать справку")
                elif command == "exit":
                    print("Выход из скрипта")
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
    vfs = VFS()
    if vfs_physical_path is not None:
        print(f"Загрузка VFS из файла: {vfs_physical_path}")
        vfs.load_from_csv(vfs_physical_path)
    else:
        print("Создание VFS по умолчанию в памяти")
        vfs.create_default()
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
        run_startup_script(startup_script_path, vfs)
        print("Стартовый скрипт завершен")
        print()
    run(vfs)
if __name__ == "__main__":
    main()