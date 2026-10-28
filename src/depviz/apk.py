"""Чтение индекса репозитория Alpine Linux (APKINDEX)."""

import io
import re
import tarfile
import urllib.error
import urllib.request

from depviz.errors import RepositoryError
from depviz.repository import Repository

INDEX_ARCHIVE = "APKINDEX.tar.gz"
INDEX_MEMBER = "APKINDEX"
TIMEOUT_SECONDS = 30
CONFLICT_MARK = "!"
OPERATORS = re.compile(r"[<>=~]")
USER_AGENT = "depviz/1.0"


def index_url(url):
    """Возвращает полный адрес архива APKINDEX.tar.gz."""
    if url.endswith(INDEX_ARCHIVE):
        return url
    return url.rstrip("/") + "/" + INDEX_ARCHIVE


def fetch_index_text(url):
    """Скачивает индекс репозитория и возвращает его текст."""
    request = urllib.request.Request(
        index_url(url), headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as resp:
            payload = resp.read()
        with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as arch:
            member = arch.extractfile(INDEX_MEMBER)
            return member.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, OSError, ValueError) as error:
        raise RepositoryError(
            f"не удалось получить индекс {url}: {error}") from error
    except (tarfile.TarError, KeyError, AttributeError) as error:
        raise RepositoryError(
            f"некорректный архив индекса по адресу {url}") from error


def parse_block(block):
    """Разбирает одну запись индекса, возвращает (имя, D, p) или None."""
    fields = {}
    for line in block.splitlines():
        key, separator, value = line.partition(":")
        if separator:
            fields[key] = value
    if "P" not in fields:
        return None
    depends = fields.get("D", "").split()
    provides = fields.get("p", "").split()
    return fields["P"], depends, provides


def strip_token(token):
    """Убирает ограничения версии; для конфликтов возвращает None."""
    if token.startswith(CONFLICT_MARK):
        return None
    return OPERATORS.split(token, maxsplit=1)[0]


def build_providers(records):
    """Строит отображение «предоставляемое имя -> пакет»."""
    providers = {}
    for name, _, _ in records:
        providers.setdefault(name, name)
    for name, _, provides in records:
        for token in provides:
            providers.setdefault(strip_token(token), name)
    return providers


def resolve_dependencies(name, depends, providers):
    """Приводит зависимости пакета к именам пакетов репозитория."""
    result = []
    for token in depends:
        dependency = strip_token(token)
        if not dependency:
            continue
        target = providers.get(dependency, dependency)
        if target != name and target not in result:
            result.append(target)
    return result


def parse_index(text):
    """Разбирает текст APKINDEX в словарь «пакет -> зависимости»."""
    blocks = text.replace("\r\n", "\n").split("\n\n")
    records = [rec for rec in map(parse_block, blocks) if rec]
    providers = build_providers(records)
    adjacency = {}
    for name, depends, _ in records:
        if name not in adjacency:
            adjacency[name] = resolve_dependencies(name, depends, providers)
    return adjacency


def load_apk_repository(url):
    """Загружает репозиторий Alpine по URL."""
    return Repository(parse_index(fetch_index_text(url)))
