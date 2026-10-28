"""Представления графа: Mermaid, ASCII-дерево и SVG-изображение."""

from dataclasses import dataclass
from xml.sax.saxutils import escape

from depviz.graph import dependency_edges

BRANCH_MID = "|-- "
BRANCH_LAST = "`-- "
PIPE = "|   "
SPACE = "    "
NOTE_CYCLE = " (цикл)"
NOTE_REPEAT = " (повтор)"

MIN_WIDTH = 90
CHAR_WIDTH = 8
PADDING = 24
BOX_HEIGHT = 34
COL_GAP = 90
ROW_GAP = 22
MARGIN = 30
BULGE = 40
LOOP_RISE = 18
FILL, STROKE = "#eef3fb", "#3b5b92"
ROOT_FILL, ROOT_STROKE = "#ffe9b0", "#b8860b"
EDGE_COLOR = "#555555"


@dataclass
class Box:
    """Прямоугольник вершины на изображении."""

    x: float
    y: float
    w: float
    h: float


def escape_label(text):
    """Экранирует подпись вершины для Mermaid."""
    return text.replace('"', "#quot;")


def to_mermaid(graph):
    """Формирует описание графа на языке Mermaid."""
    ids = {name: f"n{index}" for index, name in enumerate(graph.edges)}
    lines = ["graph TD"]
    for name, node_id in ids.items():
        lines.append(f'    {node_id}["{escape_label(name)}"]')
    for source, target in dependency_edges(graph):
        lines.append(f"    {ids[source]} --> {ids[target]}")
    return "\n".join(lines) + "\n"


def tree_entries(children, prefix, ancestors):
    """Готовит записи дерева для помещения в стек (в обратном порядке)."""
    last = len(children) - 1
    entries = [(child, prefix, index == last, ancestors)
               for index, child in enumerate(children)]
    entries.reverse()
    return entries


def tree_note(graph, node, ancestors, expanded):
    """Возвращает пометку для цикла или повторно встреченной вершины."""
    if node in ancestors:
        return NOTE_CYCLE
    if node in expanded and graph.edges[node]:
        return NOTE_REPEAT
    return ""


def ascii_tree(graph):
    """Строит ASCII-дерево зависимостей от корня графа."""
    lines = [graph.root]
    expanded = {graph.root}
    stack = tree_entries(graph.edges[graph.root], "", (graph.root,))
    while stack:
        node, prefix, is_last, ancestors = stack.pop()
        branch = BRANCH_LAST if is_last else BRANCH_MID
        note = tree_note(graph, node, ancestors, expanded)
        lines.append(prefix + branch + node + note)
        if note:
            continue
        expanded.add(node)
        shift = SPACE if is_last else PIPE
        stack.extend(tree_entries(
            graph.edges[node], prefix + shift, ancestors + (node,)))
    return "\n".join(lines) + "\n"


def box_width(name):
    """Ширина прямоугольника вершины по длине имени."""
    return max(MIN_WIDTH, len(name) * CHAR_WIDTH + PADDING)


def group_layers(graph):
    """Группирует вершины по глубине."""
    layers = {}
    for name in graph.edges:
        layers.setdefault(graph.depths[name], []).append(name)
    return [layers[depth] for depth in sorted(layers)]


def layout(graph):
    """Раскладывает вершины по слоям слева направо."""
    layers = group_layers(graph)
    tallest = max(len(layer) for layer in layers)
    boxes = {}
    x_pos = MARGIN
    for layer in layers:
        width = max(box_width(name) for name in layer)
        shift = (tallest - len(layer)) * (BOX_HEIGHT + ROW_GAP) / 2
        for row, name in enumerate(layer):
            y_pos = MARGIN + shift + row * (BOX_HEIGHT + ROW_GAP)
            boxes[name] = Box(x_pos, y_pos, width, BOX_HEIGHT)
        x_pos += width + COL_GAP
    return boxes


def self_loop_path(box):
    """Путь петли для пакета, зависящего от самого себя."""
    x_pos = box.x + box.w
    top = box.y + box.h / 4
    bottom = box.y + box.h * 3 / 4
    return (f"M {x_pos},{top} C {x_pos + BULGE},{top - LOOP_RISE} "
            f"{x_pos + BULGE},{bottom + LOOP_RISE} {x_pos},{bottom}")


def edge_path(source, target):
    """Строит кривую Безье от одной вершины к другой."""
    s_y, e_y = source.y + source.h / 2, target.y + target.h / 2
    if source is target:
        return self_loop_path(source)
    if target.x > source.x:
        s_x, e_x = source.x + source.w, target.x
        shift = (e_x - s_x) / 2
    elif target.x < source.x:
        s_x, e_x = source.x, target.x + target.w
        shift = (e_x - s_x) / 2
    else:
        s_x = e_x = source.x + source.w
        shift = BULGE
    return (f"M {s_x},{s_y} C {s_x + shift},{s_y} "
            f"{e_x - shift},{e_y} {e_x},{e_y}")


def svg_node(name, box, is_root):
    """SVG-элемент вершины."""
    fill, stroke = (ROOT_FILL, ROOT_STROKE) if is_root else (FILL, STROKE)
    return (
        f'<rect x="{box.x}" y="{box.y}" width="{box.w}" height="{box.h}" '
        f'rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
        f'<text x="{box.x + box.w / 2}" y="{box.y + box.h / 2 + 5}" '
        f'text-anchor="middle" font-family="Arial, sans-serif" '
        f'font-size="14">{escape(name)}</text>')


def svg_edge(path):
    """SVG-элемент ребра со стрелкой."""
    return (f'<path d="{path}" fill="none" stroke="{EDGE_COLOR}" '
            'stroke-width="1.3" marker-end="url(#arrow)"/>')


def svg_header(width, height):
    """Заголовок SVG с определением стрелки и фоном."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}">'
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{EDGE_COLOR}"/>'
        '</marker></defs>'
        f'<rect width="{width}" height="{height}" fill="white"/>')


def to_svg(graph):
    """Формирует изображение графа в формате SVG."""
    boxes = layout(graph)
    width = max(box.x + box.w for box in boxes.values()) + MARGIN
    height = max(box.y + box.h for box in boxes.values()) + MARGIN
    parts = [svg_header(width, height)]
    for source, target in dependency_edges(graph):
        parts.append(svg_edge(edge_path(boxes[source], boxes[target])))
    for name, box in boxes.items():
        parts.append(svg_node(name, box, name == graph.root))
    parts.append("</svg>")
    return "\n".join(parts) + "\n"
