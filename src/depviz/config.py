"""Загрузка и проверка конфигурации из CSV-файла."""

import csv
from dataclasses import asdict, dataclass
from pathlib import Path

from depviz.errors import ConfigError

PAIR_SIZE = 2
FIRST_ROW = 1
SINGLE = 1
MIN_DEPTH = 0
SVG_SUFFIX = ".svg"
URL_PREFIXES = ("http://", "https://")
HEADER_NAMES = ("key", "parameter", "ключ", "параметр")
TRUE_VALUES = ("true", "1", "yes", "да")
FALSE_VALUES = ("false", "0", "no", "нет")
REQUIRED_KEYS = ("package", "repository")
OPTIONAL_DEFAULTS = {
    "test_mode": "false",
    "output": "graph.svg",
    "ascii_tree": "false",
    "max_depth": "3",
    "filter": "",
    "reverse": "false",
}
KNOWN_KEYS = REQUIRED_KEYS + tuple(OPTIONAL_DEFAULTS)


@dataclass(frozen=True)
class Config:
    """Параметры, настраиваемые пользователем."""

    package: str
    repository: str
    test_mode: bool
    output: str
    ascii_tree: bool
    max_depth: int
    filter: str
    reverse: bool


def read_rows(path):
    """Читает все строки CSV-файла."""
    try:
        with open(path, encoding="utf-8-sig", newline="") as handle:
            return list(csv.reader(handle))
    except (OSError, UnicodeDecodeError, csv.Error) as error:
        raise ConfigError(
            f"не удалось прочитать файл {path}: {error}") from error


def rows_to_pairs(rows):
    """Преобразует строки CSV вида «ключ,значение» в словарь."""
    pairs = {}
    for number, row in enumerate(rows, start=FIRST_ROW):
        if not "".join(row).strip():
            continue
        if len(row) != PAIR_SIZE:
            raise ConfigError(
                f"строка {number}: ожидается формат «ключ,значение»")
        key, value = row[0].strip(), row[1].strip()
        if number == FIRST_ROW and key.lower() in HEADER_NAMES:
            continue
        if key not in KNOWN_KEYS:
            raise ConfigError(f"строка {number}: неизвестный параметр {key}")
        if key in pairs:
            raise ConfigError(f"строка {number}: параметр {key} повторён")
        pairs[key] = value
    return pairs


def parse_bool(key, text):
    """Разбирает логическое значение параметра."""
    lowered = text.lower()
    if lowered in TRUE_VALUES:
        return True
    if lowered in FALSE_VALUES:
        return False
    raise ConfigError(
        f"{key}: ожидается true или false, получено «{text}»")


def parse_depth(text):
    """Разбирает максимальную глубину анализа."""
    try:
        depth = int(text)
    except ValueError as error:
        raise ConfigError(
            f"max_depth: ожидается целое число, получено «{text}»"
        ) from error
    if depth < MIN_DEPTH:
        raise ConfigError("max_depth: глубина не может быть отрицательной")
    return depth


def parse_output(text):
    """Проверяет имя файла с изображением графа."""
    if not text.lower().endswith(SVG_SUFFIX) or text.lower() == SVG_SUFFIX:
        raise ConfigError(
            f"output: имя файла должно оканчиваться на .svg, «{text}»")
    return text


def validate_repository(package, repository, test_mode):
    """Проверяет имя пакета и адрес (или путь) репозитория."""
    if len(package.split()) != SINGLE:
        raise ConfigError("package: имя пакета не должно содержать пробелов")
    if test_mode and not Path(repository).is_file():
        raise ConfigError(
            f"repository: файл тестового репозитория не найден: {repository}")
    if not test_mode and not repository.startswith(URL_PREFIXES):
        raise ConfigError(
            "repository: ожидается URL (http:// или https://), "
            f"получено «{repository}»")


def build_config(pairs):
    """Собирает и проверяет объект конфигурации."""
    missing = [key for key in REQUIRED_KEYS if not pairs.get(key)]
    if missing:
        raise ConfigError(
            "не заданы обязательные параметры: " + ", ".join(missing))
    values = dict(OPTIONAL_DEFAULTS)
    values.update(
        {key: val for key, val in pairs.items() if val or key == "filter"})
    config = Config(
        package=values["package"],
        repository=values["repository"],
        test_mode=parse_bool("test_mode", values["test_mode"]),
        output=parse_output(values["output"]),
        ascii_tree=parse_bool("ascii_tree", values["ascii_tree"]),
        max_depth=parse_depth(values["max_depth"]),
        filter=values["filter"],
        reverse=parse_bool("reverse", values["reverse"]),
    )
    validate_repository(config.package, config.repository, config.test_mode)
    return config


def load_config(path):
    """Загружает конфигурацию из CSV-файла."""
    return build_config(rows_to_pairs(read_rows(path)))


def format_config(config):
    """Возвращает параметры в виде строк «ключ = значение»."""
    return [f"{key} = {value}" for key, value in asdict(config).items()]
