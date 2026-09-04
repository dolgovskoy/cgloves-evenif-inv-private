import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import threading
import requests
import time

# API и URL-адреса
GLOVES_URL = "https://ariflan159.github.io/cgloves-web/gloves.json"
USERS_URL = "https://users.roproxy.com/v1/usernames/users"
INVENTORY_URL = "https://inventory.roproxy.com/v1/users/{}/items/2/{}/is-owned"

class GlovesCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Roblox Gloves Checker")
        self.root.geometry("700x600")
        self.root.minsize(600, 500)

        # Переменная для отслеживания состояния работы
        self.is_running = False
        self.mode = tk.StringVar(value="single")  # "single" или "compare"

        self.create_widgets()

    def create_widgets(self):
        # Основной контейнер
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Панель выбора режима
        mode_frame = ttk.LabelFrame(main_frame, text="Режим проверки", padding="10")
        mode_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Radiobutton(mode_frame, text="Проверить одного игрока", 
                       variable=self.mode, value="single", 
                       command=self.toggle_mode).pack(side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(mode_frame, text="Сравнить двух игроков", 
                       variable=self.mode, value="compare",
                       command=self.toggle_mode).pack(side=tk.LEFT)

        # Панель ввода для одного игрока
        self.single_frame = ttk.Frame(main_frame)
        self.single_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(self.single_frame, text="Roblox Username:", font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 5))
        self.username_entry = ttk.Entry(self.single_frame, font=("Arial", 10))
        self.username_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.username_entry.focus()
        self.username_entry.bind("<Return>", lambda event: self.start_checking())

        # Панель ввода для двух игроков (скрыта по умолчанию)
        self.compare_frame = ttk.Frame(main_frame)
        # Не пакуем сразу, покажем при переключении режима

        ttk.Label(self.compare_frame, text="Игрок 1:", font=("Arial", 10)).grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.player1_entry = ttk.Entry(self.compare_frame, font=("Arial", 10))
        self.player1_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        self.player1_entry.bind("<Return>", lambda event: self.start_checking())

        ttk.Label(self.compare_frame, text="Игрок 2:", font=("Arial", 10)).grid(row=1, column=0, sticky="w", padx=(0, 5))
        self.player2_entry = ttk.Entry(self.compare_frame, font=("Arial", 10))
        self.player2_entry.grid(row=1, column=1, sticky="ew", padx=(0, 10))
        self.player2_entry.bind("<Return>", lambda event: self.start_checking())

        self.compare_frame.columnconfigure(1, weight=1)

        # Кнопка проверки
        self.start_btn = ttk.Button(main_frame, text="Проверить", command=self.start_checking)
        self.start_btn.pack(pady=(0, 10))

        # Текстовое поле для вывода логов и результатов
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(text_frame, wrap=tk.WORD, font=("Consolas", 10), state=tk.DISABLED)
        scrollbar = ttk.Scrollbar(text_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Цветовые теги для красивого вывода
        self.log_text.tag_config("success", foreground="green")
        self.log_text.tag_config("fail", foreground="red")
        self.log_text.tag_config("error", foreground="orange")
        self.log_text.tag_config("bold", font=("Consolas", 10, "bold"))
        self.log_text.tag_config("both", foreground="blue")
        self.log_text.tag_config("only_first", foreground="green")
        self.log_text.tag_config("only_second", foreground="orange")
        self.log_text.tag_config("none", foreground="gray")

    def toggle_mode(self):
        """Переключение между режимами"""
        if self.mode.get() == "single":
            self.compare_frame.pack_forget()
            self.single_frame.pack(fill=tk.X, pady=(0, 10))
            self.username_entry.focus()
        else:
            self.single_frame.pack_forget()
            self.compare_frame.pack(fill=tk.X, pady=(0, 10))
            self.player1_entry.focus()

    def log(self, text, tag=None):
        """Безопасный вывод текста в поле из любого потока"""
        self.log_text.config(state=tk.NORMAL)
        if tag:
            self.log_text.insert(tk.END, text + "\n", tag)
        else:
            self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)

    def start_checking(self):
        if self.is_running:
            return

        if self.mode.get() == "single":
            username = self.username_entry.get().strip()
            if not username:
                messagebox.showwarning("Внимание", "Введите имя пользователя Roblox!")
                return
            self.clear_log()
            self.is_running = True
            self.start_btn.config(state=tk.DISABLED)
            self.username_entry.config(state=tk.DISABLED)
            thread = threading.Thread(target=self.check_process, args=(username,), daemon=True)
            thread.start()
        else:
            player1 = self.player1_entry.get().strip()
            player2 = self.player2_entry.get().strip()
            if not player1 or not player2:
                messagebox.showwarning("Внимание", "Введите имена обоих пользователей!")
                return
            if player1 == player2:
                messagebox.showwarning("Внимание", "Имена пользователей должны различаться!")
                return
            self.clear_log()
            self.is_running = True
            self.start_btn.config(state=tk.DISABLED)
            self.player1_entry.config(state=tk.DISABLED)
            self.player2_entry.config(state=tk.DISABLED)
            thread = threading.Thread(target=self.compare_process, args=(player1, player2), daemon=True)
            thread.start()

    def get_gloves(self):
        response = requests.get(GLOVES_URL)
        response.raise_for_status()
        return response.json()

    def get_user_id(self, username):
        data = {"usernames": [username], "excludeBannedUsers": True}
        response = requests.post(USERS_URL, json=data)
        response.raise_for_status()
        result = response.json()
        if not result.get("data"):
            return None
        return result["data"][0]["id"]

    def check_glove(self, user_id, glove_id):
        url = INVENTORY_URL.format(user_id, glove_id)
        try:
            response = requests.get(url, timeout=5)
            if response.status_code != 200:
                return None
            return response.json()
        except Exception:
            return None

    def check_process(self, username):
        """Проверка одного игрока"""
        try:
            self.log("Получаю список перчаток...")
            gloves = self.get_gloves()
            self.log(f"Всего перчаток найдено: {len(gloves)}\n")

            self.log("Ищу пользователя...")
            user_id = self.get_user_id(username)

            if user_id is None:
                self.log("Пользователь не найден.", "fail")
                self.finish_checking()
                return

            self.log(f"User ID: {user_id}\n")
            self.log("Проверяю перчатки...\n", "bold")

            obtained = []
            unobtained = []
            errors = []

            for number, (glove_id, glove_name) in enumerate(gloves.items(), start=1):
                status = self.check_glove(user_id, glove_id)

                if status is True:
                    obtained.append(glove_name)
                    self.log(f"[{number}/{len(gloves)}] ✓ {glove_name}", "success")
                elif status is False:
                    unobtained.append(glove_name)
                    self.log(f"[{number}/{len(gloves)}] ✗ {glove_name}", "fail")
                else:
                    errors.append(glove_name)
                    self.log(f"[{number}/{len(gloves)}] ? {glove_name} — ERROR", "error")

                time.sleep(0.5)

            # Вывод финального отчета
            self.log("\n" + "="*40, "bold")
            self.log("РЕЗУЛЬТАТ", "bold")
            self.log("="*40 + "\n", "bold")

            self.log(f"Получено: {len(obtained)}", "success")
            for glove in obtained:
                self.log(f"  ✓ {glove}", "success")

            self.log(f"\nНе получено: {len(unobtained)}", "fail")
            for glove in unobtained:
                self.log(f"  ✗ {glove}", "fail")

            if errors:
                self.log(f"\nОшибок: {len(errors)}", "error")
                for glove in errors:
                    self.log(f"  ? {glove}", "error")

        except Exception as e:
            self.log(f"\nПроизошла критическая ошибка: {e}", "fail")
        finally:
            self.finish_checking()

    def compare_process(self, username1, username2):
        """Сравнение двух игроков"""
        try:
            self.log("Получаю список перчаток...")
            gloves = self.get_gloves()
            self.log(f"Всего перчаток найдено: {len(gloves)}\n")

            self.log(f"Ищу пользователя 1: {username1}...")
            user_id1 = self.get_user_id(username1)
            if user_id1 is None:
                self.log(f"Пользователь {username1} не найден.", "fail")
                self.finish_checking()
                return
            self.log(f"✓ {username1} найден (ID: {user_id1})", "success")

            self.log(f"Ищу пользователя 2: {username2}...")
            user_id2 = self.get_user_id(username2)
            if user_id2 is None:
                self.log(f"Пользователь {username2} не найден.", "fail")
                self.finish_checking()
                return
            self.log(f"✓ {username2} найден (ID: {user_id2})\n", "success")

            self.log("Сравниваю перчатки...\n", "bold")

            both = []          # есть у обоих
            only_first = []    # только у первого
            only_second = []   # только у второго
            none = []          # нет ни у кого
            errors = []

            total = len(gloves)
            for number, (glove_id, glove_name) in enumerate(gloves.items(), start=1):
                status1 = self.check_glove(user_id1, glove_id)
                status2 = self.check_glove(user_id2, glove_id)

                if status1 is True and status2 is True:
                    both.append(glove_name)
                    self.log(f"[{number}/{total}] ✓✓ {glove_name} - Есть у обоих", "both")
                elif status1 is True and status2 is False:
                    only_first.append(glove_name)
                    self.log(f"[{number}/{total}] ✓✗ {glove_name} - Только у {username1}", "only_first")
                elif status1 is False and status2 is True:
                    only_second.append(glove_name)
                    self.log(f"[{number}/{total}] ✗✓ {glove_name} - Только у {username2}", "only_second")
                elif status1 is False and status2 is False:
                    none.append(glove_name)
                    self.log(f"[{number}/{total}] ✗✗ {glove_name} - Нет ни у кого", "none")
                else:
                    errors.append(glove_name)
                    self.log(f"[{number}/{total}] ?? {glove_name} - Ошибка проверки", "error")

                time.sleep(0.5)

            # Вывод финального отчета
            self.log("\n" + "="*50, "bold")
            self.log("РЕЗУЛЬТАТ СРАВНЕНИЯ", "bold")
            self.log("="*50 + "\n", "bold")

            self.log(f"Есть у обоих: {len(both)}", "both")
            for glove in both:
                self.log(f"  ✓✓ {glove}", "both")

            self.log(f"\nТолько у {username1}: {len(only_first)}", "only_first")
            for glove in only_first:
                self.log(f"  ✓✗ {glove}", "only_first")

            self.log(f"\nТолько у {username2}: {len(only_second)}", "only_second")
            for glove in only_second:
                self.log(f"  ✗✓ {glove}", "only_second")

            self.log(f"\nНет ни у кого: {len(none)}", "none")
            for glove in none:
                self.log(f"  ✗✗ {glove}", "none")

            if errors:
                self.log(f"\nОшибок: {len(errors)}", "error")
                for glove in errors:
                    self.log(f"  ?? {glove}", "error")

        except Exception as e:
            self.log(f"\nПроизошла критическая ошибка: {e}", "fail")
        finally:
            self.finish_checking()

    def finish_checking(self):
        self.is_running = False
        self.start_btn.config(state=tk.NORMAL)
        if self.mode.get() == "single":
            self.username_entry.config(state=tk.NORMAL)
        else:
            self.player1_entry.config(state=tk.NORMAL)
            self.player2_entry.config(state=tk.NORMAL)


if __name__ == "__main__":
    root = tk.Tk()
    app = GlovesCheckerApp(root)
    root.mainloop()
