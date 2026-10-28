"""Графическое окно эмулятора на tkinter."""

import tkinter as tk

TITLE_PREFIX = "Эмулятор оболочки - VFS: "
START_DELAY_MS = 200
OUTPUT_WIDTH = 90
OUTPUT_HEIGHT = 28
FONT = "TkFixedFont"


class ShellWindow:
    """Окно: область вывода, приглашение и строка ввода."""

    def __init__(self, vfs_name):
        """Создаёт окно с именем VFS в заголовке."""
        self.root = tk.Tk()
        self.root.title(TITLE_PREFIX + vfs_name)
        self.shell = None
        self.prompt_var = tk.StringVar()
        self.text = tk.Text(self.root, width=OUTPUT_WIDTH,
                            height=OUTPUT_HEIGHT, state="disabled",
                            wrap="word", font=FONT)
        self.bottom = tk.Frame(self.root)
        self.entry = tk.Entry(self.bottom, font=FONT)
        self._build_layout()

    def _build_layout(self):
        """Располагает виджеты в окне."""
        scroll = tk.Scrollbar(self.root, command=self.text.yview)
        self.text.configure(yscrollcommand=scroll.set)
        label = tk.Label(self.bottom, textvariable=self.prompt_var,
                         font=FONT)
        label.pack(side="left")
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", self._on_enter)
        self.bottom.pack(side="bottom", fill="x")
        scroll.pack(side="right", fill="y")
        self.text.pack(side="left", fill="both", expand=True)

    def bind_shell(self, shell):
        """Связывает окно с оболочкой и обновляет приглашение."""
        self.shell = shell
        self.prompt_var.set(shell.prompt())
        self.root.focus_force()
        self.entry.focus_force()

    def write(self, text):
        """Добавляет строку в область вывода."""
        self.text.configure(state="normal")
        self.text.insert("end", text + "\n")
        self.text.see("end")
        self.text.configure(state="disabled")
        self.root.update_idletasks()

    def _after_command(self):
        """Закрывает окно после exit или обновляет приглашение."""
        if not self.shell.running:
            self.root.destroy()
            return
        self.prompt_var.set(self.shell.prompt())

    def _on_enter(self, _event):
        """Обрабатывает нажатие Enter в строке ввода."""
        line = self.entry.get()
        self.entry.delete(0, "end")
        self.shell.submit(line)
        self._after_command()

    def schedule(self, action):
        """Выполняет action вскоре после показа окна."""
        def start():
            """Запускает действие и проверяет, не вызван ли exit."""
            action()
            self._after_command()
        self.root.after(START_DELAY_MS, start)

    def run(self):
        """Запускает цикл обработки событий окна."""
        self.root.mainloop()
