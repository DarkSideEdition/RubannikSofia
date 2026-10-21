"""Ядро эмулятора: разбор команд, их выполнение и стартовый скрипт."""

import getpass
import shlex

MAX_CD_ARGS = 1
DEFAULT_USER = "user"
PARSE_ERRORS = {
    "No closing quotation": "незакрытая кавычка",
    "No escaped character": "обрыв экранирования в конце строки",
}


class ShellError(Exception):
    """Ошибка выполнения команды эмулятора."""


def current_user():
    """Возвращает имя текущего пользователя реальной ОС."""
    try:
        return getpass.getuser()
    except (KeyError, OSError):
        return DEFAULT_USER


def describe_error(err):
    """Возвращает короткое описание системной ошибки."""
    return getattr(err, "strerror", None) or str(err)


class Shell:
    """Эмулятор оболочки; весь вывод передаётся в функцию out(текст)."""

    def __init__(self, vfs, out):
        """Создаёт оболочку над VFS с функцией вывода строки out."""
        self.vfs = vfs
        self.out = out
        self.cwd = "/"
        self.running = True
        self.user = current_user()
        self.commands = {
            "ls": self.cmd_ls,
            "cd": self.cmd_cd,
            "exit": self.cmd_exit,
            "vfs-info": self.cmd_vfs_info,
            "vfs-tree": self.cmd_vfs_tree,
        }

    def prompt(self):
        """Возвращает приглашение к вводу с именем VFS."""
        return f"{self.user}@{self.vfs.name}:{self.cwd}$ "

    @staticmethod
    def parse(line):
        """Разбирает строку на команду и аргументы (кавычки учитываются)."""
        try:
            tokens = shlex.split(line, posix=True)
        except ValueError as err:
            reason = PARSE_ERRORS.get(str(err), str(err))
            raise ShellError(f"ошибка разбора: {reason}") from err
        if not tokens:
            return None, []
        return tokens[0], tokens[1:]

    def execute(self, line):
        """Выполняет строку; при ошибке возбуждает ShellError."""
        name, args = self.parse(line)
        if name is None:
            return
        handler = self.commands.get(name)
        if handler is None:
            raise ShellError(f"{name}: команда не найдена")
        handler(args)

    def submit(self, line, where=""):
        """Выводит введённую строку, выполняет её и сообщает об ошибке.

        Возвращает True, если команда выполнена без ошибок.
        """
        self.out(self.prompt() + line)
        try:
            self.execute(line)
        except ShellError as err:
            self.out(f"Ошибка{where}: {err}")
            return False
        return True

    @staticmethod
    def no_args(name, args):
        """Проверяет, что команда name вызвана без аргументов."""
        if args:
            raise ShellError(f"{name}: команда не принимает аргументов")

    def cmd_ls(self, args):
        """Заглушка ls: выводит имя команды и аргументы."""
        self.out(f"ls: аргументы {args}")

    def cmd_cd(self, args):
        """Заглушка cd: выводит имя команды и аргументы."""
        if len(args) > MAX_CD_ARGS:
            raise ShellError("cd: слишком много аргументов")
        self.out(f"cd: аргументы {args}")

    def cmd_exit(self, args):
        """Завершает работу эмулятора."""
        self.no_args("exit", args)
        self.running = False

    def cmd_vfs_info(self, args):
        """Служебная команда: сводка о загруженной VFS."""
        self.no_args("vfs-info", args)
        dirs, files, total = self.vfs.stats()
        self.out(f"VFS:        {self.vfs.name}")
        self.out(f"Источник:   {self.vfs.source or '(не задан)'}")
        self.out(f"Каталогов:  {dirs}")
        self.out(f"Файлов:     {files}")
        self.out(f"Объём:      {total} байт")

    def cmd_vfs_tree(self, args):
        """Служебная команда: дерево всей VFS."""
        self.no_args("vfs-tree", args)
        for line in self.vfs.tree_lines():
            self.out(line)

    def run_script(self, script_path):
        """Выполняет стартовый скрипт, имитируя диалог с пользователем.

        Ошибочные строки пропускаются. Возвращает число ошибок.
        """
        try:
            with open(script_path, encoding="utf-8-sig") as source:
                lines = source.read().splitlines()
        except (OSError, UnicodeDecodeError) as err:
            self.out(f"Ошибка: не удалось прочитать стартовый скрипт "
                     f"'{script_path}': {describe_error(err)}")
            return 1
        errors = 0
        for number, raw in enumerate(lines, start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if not self.submit(line, f" в скрипте (строка {number})"):
                errors += 1
            if not self.running:
                break
        return errors
