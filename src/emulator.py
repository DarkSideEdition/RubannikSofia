"""Эмулятор командной оболочки ОС с графическим интерфейсом (вариант 16).

Этап 1: окно, парсер с кавычками, ls и cd (заглушки), exit.
Этап 2: параметры --vfs и --script, отладочный вывод, стартовый скрипт.
Этап 3: VFS из CSV-файла, целиком в памяти.
"""

import argparse
import os

from shell import Shell
from vfs import Vfs, VfsError, load as load_vfs

NOT_SET = "(не задан)"


def parse_args(argv=None):
    """Разбирает параметры командной строки."""
    parser = argparse.ArgumentParser(
        description="Эмулятор командной оболочки ОС (GUI)")
    parser.add_argument("--vfs", metavar="PATH",
                        help="путь к CSV-файлу с VFS")
    parser.add_argument("--script", metavar="PATH",
                        help="путь к стартовому скрипту")
    return parser.parse_args(argv)


def config_lines(args):
    """Возвращает строки отладочного вывода заданных параметров."""
    return [
        "Параметры эмулятора:",
        f"  VFS путь:          {args.vfs or NOT_SET}",
        f"  Стартовый скрипт:  {args.script or NOT_SET}",
    ]


def build_vfs(path):
    """Загружает VFS; при ошибке возвращает пустую VFS и сообщения."""
    if not path:
        return Vfs(), []
    try:
        return load_vfs(path), []
    except VfsError as err:
        name = os.path.basename(os.path.normpath(path))
        notes = [f"Ошибка VFS: {err}", "Эмулятор запущен с пустой VFS."]
        return Vfs(name, path), notes


def run_startup(shell, script_path):
    """Выполняет стартовый скрипт и сообщает об итоге."""
    errors = shell.run_script(script_path)
    if errors:
        shell.out(f"Стартовый скрипт выполнен с ошибками: {errors}")


def main(argv=None):
    """Точка входа: создаёт окно, оболочку и запускает цикл событий."""
    from gui import ShellWindow

    args = parse_args(argv)
    vfs, notes = build_vfs(args.vfs)
    window = ShellWindow(vfs.name)
    shell = Shell(vfs, window.write)
    window.bind_shell(shell)
    for line in config_lines(args) + notes:
        window.write(line)
    if args.script:
        window.schedule(lambda: run_startup(shell, args.script))
    window.run()


if __name__ == "__main__":
    main()
