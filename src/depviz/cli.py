"""Интерфейс командной строки depviz."""

import argparse
import sys
from pathlib import Path

from depviz.apk import load_apk_repository
from depviz.config import format_config, load_config
from depviz.errors import DepVizError, RepositoryError
from depviz.graph import build_graph
from depviz.render import ascii_tree, to_mermaid, to_svg
from depviz.repository import load_test_repository

MERMAID_SUFFIX = ".mmd"
FAILURE = 1


def parse_args(argv):
    """Разбирает аргументы командной строки."""
    parser = argparse.ArgumentParser(
        prog="depviz",
        description="Визуализация графа зависимостей пакетов Alpine (apk).")
    parser.add_argument("config", help="путь к CSV-файлу конфигурации")
    parser.add_argument(
        "--show-config", action="store_true",
        help="вывести параметры конфигурации в формате ключ-значение")
    parser.add_argument(
        "--direct", action="store_true",
        help="вывести только прямые зависимости (или зависимые пакеты)")
    return parser.parse_args(argv)


def load_repository(config):
    """Загружает тестовый или реальный репозиторий по конфигурации."""
    if config.test_mode:
        return load_test_repository(config.repository)
    return load_apk_repository(config.repository)


def write_text(path, text):
    """Записывает текстовый файл, создавая каталоги при необходимости."""
    target = Path(path)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    except OSError as error:
        raise DepVizError(f"не удалось записать {path}: {error}") from error


def print_direct(repository, config):
    """Выводит прямые зависимости (или зависимые пакеты) пакета."""
    if not repository.has_package(config.package):
        raise RepositoryError(f"пакет «{config.package}» не найден")
    if config.reverse:
        items = repository.dependents(config.package)
        title = "Пакеты, напрямую зависящие от"
    else:
        items = repository.dependencies(config.package)
        title = "Прямые зависимости пакета"
    print(f"{title} {config.package}:")
    for item in items:
        print(f"  {item}")


def print_cycles(graph):
    """Выводит найденные циклические зависимости."""
    for cycle in graph.cycles:
        print("Циклическая зависимость: " + " -> ".join(cycle))


def report(graph, config):
    """Выводит результаты анализа и сохраняет изображение графа."""
    kind = "обратных зависимостей" if graph.reverse else "зависимостей"
    print(f"Граф {kind} пакета {graph.root}: вершин {len(graph.edges)}, "
          f"рёбер {sum(map(len, graph.edges.values()))}")
    if config.ascii_tree:
        print(ascii_tree(graph), end="")
    print_cycles(graph)
    mermaid_path = Path(config.output).with_suffix(MERMAID_SUFFIX)
    write_text(mermaid_path, to_mermaid(graph))
    write_text(config.output, to_svg(graph))
    print(f"Mermaid-описание: {mermaid_path}")
    print(f"Изображение (SVG): {config.output}")


def run(args):
    """Выполняет работу инструмента по аргументам командной строки."""
    config = load_config(args.config)
    if args.show_config:
        print("\n".join(format_config(config)))
    repository = load_repository(config)
    if args.direct:
        print_direct(repository, config)
        return
    graph = build_graph(repository, config.package, config.max_depth,
                        config.filter, config.reverse)
    report(graph, config)


def main(argv=None):
    """Точка входа; возвращает код завершения процесса."""
    try:
        sys.stdout.reconfigure(errors="replace")
    except AttributeError:
        pass
    try:
        run(parse_args(argv))
    except DepVizError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return FAILURE
    return 0
