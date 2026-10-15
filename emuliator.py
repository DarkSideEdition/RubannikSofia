import sys
import shlex
import tkinter as tk
from tkinter import scrolledtext

class ShellEmulatorStage1:
    def __init__(self):
        # Имя VFS-заглушки для заголовка окна (Этап 1, Требование 2)
        self.vfs_name = "Stage1_Stub_VFS"
        self.current_dir = "/"

        # Создание графического интерфейса (Этап 1, Требование 1)
        self.root = tk.Tk()
        self.root.title(f"Shell Emulator - VFS: {self.vfs_name}")
        self.root.geometry("700x450")

        # Текстовое поле в стиле терминала
        self.txt_display = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, bg="black", fg="white", 
            insertbackground="white", font=("Courier", 11)
        )
        self.txt_display.pack(fill=tk.BOTH, expand=True)

        # Панель ввода
        self.frame_input = tk.Frame(self.root, bg="black")
        self.frame_input.pack(fill=tk.X)

        # Приглашение (Prompt)
        self.lbl_prompt = tk.Label(
            self.frame_input, text=self.get_prompt(), 
            bg="black", fg="#00FF00", font=("Courier", 11)
        )
        self.lbl_prompt.pack(side=tk.LEFT)

        # Поле ввода команд
        self.entry_cmd = tk.Entry(
            self.frame_input, bg="black", fg="white", 
            insertbackground="white", font=("Courier", 11), 
            bd=0, highlightthickness=0
        )
        self.entry_cmd.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry_cmd.bind("<Return>", self.on_enter)

        # Начальный текст с упоминанием test_stage1
        self.insert_output("Welcome to UNIX Shell Emulator Prototype (Stage 1 REPL)!\n")
        self.insert_output("Ready for manual interactive testing (scenario: test_stage1).\n")
        self.insert_output("Try commands: ls, cd, exit. Supports spaces in 'quotes'.\n\n")
        self.entry_cmd.focus_set()

    def get_prompt(self):
        return f"user@emulator:{self.current_dir}$ "

    def insert_output(self, text):
        self.txt_display.insert(tk.END, text)
        self.txt_display.see(tk.END)

    def on_enter(self, event):
        cmd_str = self.entry_cmd.get()
        self.entry_cmd.delete(0, tk.END)
        
        # Вывод команды в окно для истории (Диалог с пользователем)
        self.insert_output(f"{self.get_prompt()}{cmd_str}\n")
        
        self.execute_command(cmd_str)
        self.lbl_prompt.config(text=self.get_prompt())

    def execute_command(self, cmd_str):
        if not cmd_str.strip():
            return

        try:
            # Корректный парсинг аргументов в кавычках (Этап 1, Требование 3)
            args = shlex.split(cmd_str)
        except ValueError as e:
            # Ошибка парсера (например, незакрытая кавычка)
            self.insert_output(f"shell: parser error: {e}\n")
            return

        # Имя команды — первый элемент списка, аргументы — все остальные
        cmd = args.pop(0)
        cmd_args = args

        # Команда exit (Этап 1, Требование 6)
        if cmd == "exit":
            if cmd_args:
                self.insert_output("exit: too many arguments\n")
            else:
                self.root.quit()
                sys.exit(0)

        # Заглушка ls (Этап 1, Требование 5)
        elif cmd == "ls":
            self.insert_output(f"[Stub Command] ls | Arguments: {cmd_args}\n")

        # Заглушка cd (Этап 1, Требование 5)
        elif cmd == "cd":
            if len(cmd_args) > 1:
                # Ошибка: неверные аргументы (Этап 1, Требование 4)
                self.insert_output("cd: too many arguments\n")
            else:
                self.insert_output(f"[Stub Command] cd | Arguments: {cmd_args}\n")
                if cmd_args:
                    # Теперь путь в приглашении (prompt) будет корректно обновляться
                    self.current_dir = cmd_args.pop(0)

        # Ошибка выполнения: неизвестная команда (Этап 1, Требование 4)
        else:
            self.insert_output(f"{cmd}: command not found\n")

if __name__ == "__main__":
    app = ShellEmulatorStage1()
    app.root.mainloop()
