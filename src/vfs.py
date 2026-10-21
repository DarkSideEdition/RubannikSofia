"""Виртуальная файловая система (VFS), загружаемая из CSV в память.

Формат CSV (первая строка - заголовок): path,type,encoding,content.
Вложенность задаётся полным путём элемента, например /docs/a/b.txt.
"""

import base64
import binascii
import csv
import os

REQUIRED_FIELDS = ("path", "type")
TYPE_DIR = "dir"
TYPE_FILE = "file"
ENC_TEXT = "text"
ENC_BASE64 = "base64"
FIELD_LIMIT = 1 << 28
DEFAULT_NAME = "vfs"
DOT_PARTS = (".", "..")


class VfsError(Exception):
    """Ошибка загрузки или обработки VFS."""


class Node:
    """Элемент VFS: каталог или файл."""

    def __init__(self, name, is_dir, data=b""):
        """Создаёт элемент с именем, признаком каталога и данными."""
        self.name = name
        self.is_dir = is_dir
        self.data = data
        self.children = {}

    def size(self):
        """Возвращает размер файла в байтах (для каталога - 0)."""
        return len(self.data)


def split_path(path):
    """Разбирает абсолютный путь VFS на список имён."""
    path = (path or "").strip()
    if not path.startswith("/"):
        raise VfsError(f"путь должен начинаться с '/': '{path}'")
    parts = [part for part in path.split("/") if part]
    if any(part in DOT_PARTS for part in parts):
        raise VfsError(f"недопустимый компонент пути: '{path}'")
    return parts


def decode_content(row):
    """Преобразует содержимое строки CSV в байты по столбцу encoding."""
    encoding = (row.get("encoding") or ENC_TEXT).strip().lower()
    content = row.get("content") or ""
    if encoding == ENC_TEXT:
        return content.encode("utf-8")
    if encoding == ENC_BASE64:
        try:
            return base64.b64decode(content, validate=True)
        except (binascii.Error, ValueError) as err:
            raise VfsError(f"некорректный base64: {err}") from err
    raise VfsError(f"неизвестная кодировка '{encoding}'")


def check_header(fields):
    """Проверяет, что в заголовке CSV есть обязательные столбцы."""
    missing = [name for name in REQUIRED_FIELDS if name not in (fields or [])]
    if missing:
        raise VfsError("в заголовке CSV нет столбцов: " + ", ".join(missing))


def _tree_label(node):
    """Возвращает подпись элемента для вывода дерева."""
    if node.is_dir:
        return node.name + "/"
    return f"{node.name} ({node.size()} Б)"


def _add_tree(node, prefix, lines):
    """Рекурсивно добавляет в lines строки дерева для потомков node."""
    items = sorted(node.children.values(),
                   key=lambda item: (not item.is_dir, item.name))
    for child in items:
        last = child is items[-1]
        branch = "└── " if last else "├── "
        lines.append(prefix + branch + _tree_label(child))
        if child.is_dir:
            _add_tree(child, prefix + ("    " if last else "│   "), lines)


class Vfs:
    """Дерево каталогов и файлов, целиком хранящееся в памяти."""

    def __init__(self, name=DEFAULT_NAME, source=None):
        """Создаёт пустую VFS с именем и путём к источнику (если есть)."""
        self.name = name
        self.source = source
        self.root = Node("", True)

    def ensure_dir(self, parts):
        """Возвращает каталог по списку имён, создавая недостающие."""
        node = self.root
        for name in parts:
            child = node.children.get(name)
            if child is None:
                child = Node(name, True)
                node.children[name] = child
            elif not child.is_dir:
                raise VfsError(f"'{name}' уже существует и не каталог")
            node = child
        return node

    def add_file(self, parts, data):
        """Добавляет файл с данными; родительские каталоги создаются."""
        full = "/" + "/".join(parts)
        if not parts:
            raise VfsError("корень не может быть файлом")
        parent = self.ensure_dir(parts[:-1])
        if parts[-1] in parent.children:
            raise VfsError(f"элемент '{full}' уже существует")
        parent.children[parts[-1]] = Node(parts[-1], False, data)

    def add_row(self, row, line):
        """Добавляет в VFS элемент, описанный строкой CSV."""
        try:
            parts = split_path(row.get("path"))
            kind = (row.get("type") or "").strip().lower()
            if kind == TYPE_DIR:
                self.ensure_dir(parts)
            elif kind == TYPE_FILE:
                self.add_file(parts, decode_content(row))
            else:
                raise VfsError(f"неизвестный тип '{kind}'")
        except VfsError as err:
            raise VfsError(f"строка {line}: {err}") from err

    def stats(self):
        """Возвращает (каталогов, файлов, байт) без учёта корня."""
        dirs = files = total = 0
        stack = list(self.root.children.values())
        while stack:
            node = stack.pop()
            if node.is_dir:
                dirs += 1
                stack.extend(node.children.values())
            else:
                files += 1
                total += node.size()
        return dirs, files, total

    def tree_lines(self):
        """Возвращает строки текстового дерева всей VFS."""
        lines = ["/"]
        _add_tree(self.root, "", lines)
        return lines


def load(path):
    """Загружает VFS из CSV-файла целиком в память и возвращает Vfs."""
    csv.field_size_limit(FIELD_LIMIT)
    name = os.path.basename(os.path.normpath(path))
    result = Vfs(name, path)
    try:
        with open(path, encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            check_header(reader.fieldnames)
            for row in reader:
                result.add_row(row, reader.line_num)
    except OSError as err:
        raise VfsError(f"не удалось открыть '{path}': {err.strerror}") from err
    except (csv.Error, UnicodeDecodeError) as err:
        raise VfsError(f"некорректный CSV '{path}': {err}") from err
    return result
