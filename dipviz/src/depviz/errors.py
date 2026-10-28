"""Исключения инструмента depviz."""


class DepVizError(Exception):
    """Базовая ошибка инструмента."""


class ConfigError(DepVizError):
    """Ошибка в конфигурационном файле."""


class RepositoryError(DepVizError):
    """Ошибка получения или разбора данных репозитория."""


class GraphError(DepVizError):
    """Ошибка построения графа."""
