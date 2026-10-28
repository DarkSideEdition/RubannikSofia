"""Тесты загрузки VFS из CSV."""

import os
import sys
import tempfile
import unittest

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))

from vfs import VfsError, load  # noqa: E402

HEADER = "path,type,encoding,content\n"


def sample(name):
    """Возвращает путь к примеру VFS из каталога vfs."""
    return os.path.join(ROOT, "vfs", name)


class LoadTemp(unittest.TestCase):
    """Загрузка CSV, созданных во временных файлах."""

    def load_text(self, text):
        """Записывает text во временный CSV и загружает его."""
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "t.csv")
            with open(path, "w", encoding="utf-8", newline="") as out:
                out.write(text)
            return load(path)

    def test_text_and_base64(self):
        """Текстовые и двоичные данные декодируются в байты."""
        vfs = self.load_text(HEADER + "/a,file,text,hi\n/b,file,base64,AAEC\n")
        self.assertEqual(vfs.root.children["a"].data, b"hi")
        self.assertEqual(vfs.root.children["b"].data, b"\x00\x01\x02")

    def test_implicit_parents(self):
        """Недостающие родительские каталоги создаются."""
        vfs = self.load_text(HEADER + "/x/y/z.txt,file,text,1\n")
        self.assertEqual(vfs.stats(), (2, 1, 1))

    def test_duplicate_file(self):
        """Повтор пути файла - ошибка с номером строки."""
        text = HEADER + "/a,file,text,1\n/a,file,text,2\n"
        with self.assertRaisesRegex(VfsError, "строка 3"):
            self.load_text(text)

    def test_file_as_parent(self):
        """Файл нельзя использовать как каталог."""
        with self.assertRaises(VfsError):
            self.load_text(HEADER + "/a,file,text,1\n/a/b,file,text,2\n")

    def test_bad_type_and_base64(self):
        """Неизвестный тип и неверный base64 дают ошибку."""
        with self.assertRaises(VfsError):
            self.load_text(HEADER + "/a,folder,,\n")
        with self.assertRaises(VfsError):
            self.load_text(HEADER + "/a,file,base64,###\n")

    def test_bad_paths(self):
        """Относительные пути и '..' отвергаются."""
        for path in ("a/b", "/a/../b"):
            with self.assertRaises(VfsError):
                self.load_text(HEADER + f"{path},file,text,1\n")

    def test_bad_header_and_empty(self):
        """Нет обязательных столбцов или файл пуст - ошибка."""
        with self.assertRaises(VfsError):
            self.load_text("name,kind\na,file\n")
        with self.assertRaises(VfsError):
            self.load_text("")

    def test_missing_file(self):
        """Несуществующий файл - VfsError, а не OSError."""
        with self.assertRaises(VfsError):
            load(sample("no_such_file.csv"))


class LoadSamples(unittest.TestCase):
    """Загрузка примеров из каталога vfs."""

    def test_minimal(self):
        """Минимальная VFS: один файл."""
        self.assertEqual(load(sample("minimal.csv")).stats()[:2], (0, 1))

    def test_several(self):
        """Несколько файлов, кавычки и многострочный текст."""
        vfs = load(sample("several.csv"))
        self.assertEqual(vfs.stats()[:2], (2, 4))
        notes = vfs.root.children["notes.txt"].data.decode("utf-8")
        self.assertIn('"в кавычках"', notes)
        self.assertEqual(len(notes.splitlines()), 3)

    def test_deep(self):
        """Не менее трёх уровней вложенности."""
        vfs = load(sample("deep.csv"))
        node = vfs.root
        for name in ("home", "user", "projects", "emulator"):
            node = node.children[name]
        self.assertIn("main.py", node.children)

    def test_broken_samples(self):
        """Все битые примеры отвергаются."""
        for name in ("broken_type", "broken_base64", "broken_header",
                     "broken_duplicate"):
            with self.assertRaises(VfsError, msg=name):
                load(sample(name + ".csv"))


if __name__ == "__main__":
    unittest.main()
