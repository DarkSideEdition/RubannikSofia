"""Тесты разбора индекса Alpine."""

import unittest

from depviz.apk import index_url, parse_index, strip_token

INDEX = """C:Q1abc
P:busybox
V:1.36.1-r0
p:cmd:busybox=1.36.1-r0
D:so:libc.musl-x86_64.so.1

P:musl
V:1.2.4-r0
p:so:libc.musl-x86_64.so.1=1

P:app
V:1.0-r0
D:busybox>=1.36 !conflicting musl~1.2 cmd:busybox app so:libmissing.so.1
"""


class ApkTest(unittest.TestCase):
    """Проверка преобразования APKINDEX в граф зависимостей."""

    def test_strip_token(self):
        """Ограничения версий убираются, конфликты отбрасываются."""
        self.assertEqual(strip_token("busybox>=1.36"), "busybox")
        self.assertEqual(strip_token("musl~1.2"), "musl")
        self.assertIsNone(strip_token("!foo"))

    def test_parse_index(self):
        """Зависимости приводятся к именам пакетов через provides."""
        adjacency = parse_index(INDEX)
        self.assertEqual(adjacency["busybox"], ["musl"])
        self.assertEqual(adjacency["musl"], [])
        self.assertEqual(
            adjacency["app"], ["busybox", "musl", "so:libmissing.so.1"])

    def test_index_url(self):
        """К адресу репозитория добавляется имя архива."""
        base = "https://example.org/alpine/main/x86_64"
        self.assertTrue(index_url(base + "/").endswith("/APKINDEX.tar.gz"))
        full = base + "/APKINDEX.tar.gz"
        self.assertEqual(index_url(full), full)


if __name__ == "__main__":
    unittest.main()
