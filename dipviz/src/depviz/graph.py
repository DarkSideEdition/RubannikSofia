"""Построение графа зависимостей: DFS без рекурсии, циклы, глубина."""

from dataclasses import dataclass

from depviz.errors import GraphError

ROOT_DEPTH = 0
STEP = 1
WHITE, GRAY, BLACK = "white", "gray", "black"


@dataclass
class Graph:
    """Граф зависимостей, достижимый из корневого пакета."""

    root: str
    edges: dict
    depths: dict
    cycles: list
    reverse: bool


def visible(children, substring):
    """Отбрасывает пакеты, имя которых содержит подстроку."""
    return [item for item in children
            if not substring or substring not in item]


def traverse(root, neighbors, max_depth, substring):
    """Итеративный DFS с ограничением глубины."""
    depths = {root: ROOT_DEPTH}
    edges = {root: []}
    stack = [root]
    while stack:
        node = stack.pop()
        if depths[node] >= max_depth:
            continue
        children = visible(neighbors(node), substring)
        edges[node] = children
        new_depth = depths[node] + STEP
        for child in children:
            edges.setdefault(child, [])
        for child in reversed(children):
            if child not in depths or depths[child] > new_depth:
                depths[child] = new_depth
                stack.append(child)
    return edges, depths


def record_cycle(path, child, cycles, seen):
    """Запоминает найденный цикл (без повторов)."""
    loop = path[path.index(child):]
    start = loop.index(min(loop))
    key = tuple(loop[start:] + loop[:start])
    if key not in seen:
        seen.add(key)
        cycles.append(list(key) + [key[0]])


def find_cycles(edges, root):
    """Ищет циклы итеративным обходом с раскраской вершин."""
    color = {root: GRAY}
    path = [root]
    cycles, seen = [], set()
    stack = [iter(edges.get(root, []))]
    while stack:
        child = next(stack[-1], None)
        if child is None:
            color[path.pop()] = BLACK
            stack.pop()
            continue
        state = color.get(child, WHITE)
        if state == GRAY:
            record_cycle(path, child, cycles, seen)
        elif state == WHITE:
            color[child] = GRAY
            path.append(child)
            stack.append(iter(edges.get(child, [])))
    return cycles


def build_graph(repository, root, max_depth, substring, reverse):
    """Строит граф прямых (или обратных) зависимостей пакета."""
    if not repository.has_package(root):
        raise GraphError(f"пакет «{root}» не найден в репозитории")
    if substring and substring in root:
        raise GraphError(
            f"имя пакета «{root}» содержит подстроку фильтра «{substring}»")
    neighbors = repository.dependents if reverse else repository.dependencies
    edges, depths = traverse(root, neighbors, max_depth, substring)
    return Graph(root, edges, depths, find_cycles(edges, root), reverse)


def dependency_edges(graph):
    """Список рёбер (зависимый, зависимость) в прямом направлении."""
    pairs = []
    for source, targets in graph.edges.items():
        for target in targets:
            pairs.append((target, source) if graph.reverse
                         else (source, target))
    return pairs
