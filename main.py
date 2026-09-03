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
        self.root.geometry("600x500")
        self.root.minsize(500, 400)

        # Переменная для отслеживания состояния работы
        self.is_running = False

        self.create_widgets()

    def create_widgets(self):
        # Верхняя панель ввода
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="Roblox Username:", font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 5))
        
        self.username_entry = ttk.Entry(top_frame, font=("Arial", 10))
        self.username_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.username_entry.focus()
        # Позволяет запускать проверку по нажатию Enter
        self.username_entry.bind("<Return>", lambda event: self.start_checking())

        self.start_btn = ttk.Button(top_frame, text="Проверить", command=self.start_checking)
        self.start_btn.pack(side=tk.RIGHT)

        # Текстовое поле для вывода логов и результатов
        text_frame = ttk.Frame(self.root, padding="10")
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

    def log(self, text, tag=None):
        """Безопасный вывод текста в поле из любого потока"""
        self.log_text.config(state=tk.NORMAL)
        if tag:
            self.log_text.insert(tk.END, text + "\n", tag)
        else:
            self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)  # Автопрокрутка вниз
        self.log_text.config(state=tk.DISABLED)

    def clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)

    def start_checking(self):
        if self.is_running:
            return
        
        username = self.username_entry.get().strip()
        if not username:
            messagebox.showwarning("Внимание", "Введите имя пользователя Roblox!")
            return

        self.clear_log()
        self.is_running = True
        self.start_btn.config(state=tk.DISABLED)
        self.username_entry.config(state=tk.DISABLED)

        # Запуск проверки в отдельном потоке, чтобы GUI не зависал
        thread = threading.Thread(target=self.check_process, args=(username,), daemon=True)
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

    def finish_checking(self):
        self.is_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.username_entry.config(state=tk.NORMAL)


if __name__ == "__main__":
    root = tk.Tk()
    app = GlovesCheckerApp(root)
    root.mainloop()
