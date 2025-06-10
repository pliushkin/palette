import time
import os
import base64
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from playwright.sync_api import sync_playwright

class PaletteFMAutomator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Palette.fm Automator")
        self.root.geometry("500x400")
        self.root.resizable(False, False)

        # Переменные
        self.image_path = tk.StringVar()
        self.status = tk.StringVar(value="Готов к работе")
        self.save_dir_path = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Downloads"))

        # Создаем элементы интерфейса
        self.create_widgets()

    def create_widgets(self):
        style = ttk.Style()
        style.configure("TButton", padding=6, font=("Arial", 10))
        style.configure("TLabel", font=("Arial", 10))
        style.configure("Status.TLabel", font=("Arial", 9), foreground="gray")

        # Выбор изображения
        file_frame = ttk.Frame(self.root, padding=10)
        file_frame.pack(fill="x")
        ttk.Label(file_frame, text="Выберите изображение:").pack(anchor="w")
        file_selector = ttk.Frame(file_frame)
        file_selector.pack(fill="x", pady=5)
        self.entry_file = ttk.Entry(file_selector, textvariable=self.image_path, width=40)
        self.entry_file.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(file_selector, text="Обзор...", command=self.select_file).pack(side="left")

        # Выбор директории
        save_dir_frame = ttk.Frame(self.root, padding=10)
        save_dir_frame.pack(fill="x")
        ttk.Label(save_dir_frame, text="Директория для сохранения:").pack(anchor="w")
        dir_selector = ttk.Frame(save_dir_frame)
        dir_selector.pack(fill="x", pady=5)
        self.entry_save_dir = ttk.Entry(dir_selector, textvariable=self.save_dir_path, width=40)
        self.entry_save_dir.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(dir_selector, text="Выбрать папку...", command=self.select_save_directory).pack(side="left")

        # Кнопка запуска
        btn_frame = ttk.Frame(self.root, padding=10)
        btn_frame.pack(fill="x")
        self.btn_run = ttk.Button(btn_frame, text="Запустить обработку",
                                 command=self.run_automation, state="normal")
        self.btn_run.pack(pady=10)

        # Статус
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill="x", padx=10, pady=5)
        self.status_label = ttk.Label(status_frame, textvariable=self.status, style="Status.TLabel")
        self.status_label.pack(anchor="w")

        # Прогресс
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=480, mode="determinate")
        self.progress.pack(pady=10, padx=10)

        # Консоль
        console_frame = ttk.Frame(self.root, padding=10)
        console_frame.pack(fill="both", expand=True)
        self.console = tk.Text(console_frame, height=8, bg="#f0f0f0", font=("Consolas", 9))
        self.console.pack(fill="both")
        self.console.insert("end", "> Выберите изображение и нажмите 'Запустить обработку'\n")

    def select_file(self):
        file_types = (
            ("Изображения", "*.jpg *.jpeg *.png"),
            ("Все файлы", "*.*")
        )
        file_path = filedialog.askopenfilename(title="Выберите изображение", initialdir=os.path.expanduser("~"), filetypes=file_types)
        if file_path:
            self.image_path.set(file_path)
            self.log(f"> Выбран файл: {os.path.basename(file_path)}")

    def select_save_directory(self):
        save_dir = filedialog.askdirectory(title="Выберите папку для сохранения", initialdir=os.path.expanduser("~"))
        if save_dir:
            self.save_dir_path.set(save_dir)
            self.log(f"> Выбрана директория для сохранения: {save_dir}")

    def log(self, message):
        self.console.insert("end", message + "\n")
        self.console.see("end")
        self.root.update_idletasks()

    def update_progress(self, value):
        self.progress["value"] = value
        self.root.update_idletasks()

    def run_automation(self):
        if not self.image_path.get():
            messagebox.showerror("Ошибка", "Пожалуйста, выберите изображение")
            return

        self.btn_run["state"] = "disabled"
        self.status.set("Запуск обработки...")
        self.update_progress(10)

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                context = browser.new_context()
                page = context.new_page()

                self.log("> Открываем сайт palette.fm...")
                page.goto("https://palette.fm/color/filters") 
                self.update_progress(20)

                self.log("> Закрываем всплывающие окна...")
                page.click("button:has-text('Accept')", timeout=5000)
                page.click("button[aria-label='Close']", timeout=5000)
                self.update_progress(30)

                self.log("> Нажимаем 'Upload image'...")
                page.click("button:has-text('UPLOAD NEW IMAGE')")
                self.update_progress(40)

                self.log("> Загружаем изображение...")
                page.set_input_files("input[type='file']", self.image_path.get())
                self.update_progress(60)

                self.log("> Ожидаем результата...")
                page.wait_for_selector("div.result-image", timeout=30000)
                self.update_progress(80)

                self.log("> Получаем изображение...")
                result_style = page.eval_on_selector("div.result-image", "el => el.style.backgroundImage")
                if result_style.startswith('url("data:image'):
                    start = result_style.find("base64,") + 7
                    end = result_style.find('")', start)
                    base64_data = result_style[start:end]
                    image_data = base64.b64decode(base64_data)

                    timestamp = int(time.time())
                    filename = f"palette_{timestamp}.png"
                    save_path = os.path.join(self.save_dir_path.get(), filename)
                    with open(save_path, "wb") as f:
                        f.write(image_data)
                    self.log(f"> Успешно! Файл сохранен: {save_path}")
                    self.status.set(f"Готово! Файл сохранен в {self.save_dir_path.get()}")
                    self.update_progress(100)
                else:
                    raise Exception("Не удалось получить изображение")

                context.close()
        except Exception as e:
            self.log(f"> Ошибка: {str(e)}")
            self.status.set("Ошибка выполнения")
        finally:
            self.btn_run["state"] = "normal"


    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = PaletteFMAutomator()
    app.run()