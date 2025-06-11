import os
import time
import base64
import random
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
import threading

# Константы
HEADLESS_MODE = False  # Режим без отображения браузера
TIMEOUT_SHORT = 5      # Короткое ожидание для всплывающих окон
TIMEOUT_MEDIUM = 15    # Основное ожидание элементов
TIMEOUT_LONG = 30      # Долгое ожидание (например, для загрузки страницы)

class PaletteFMAutomator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Palette.fm Automator")
        self.root.geometry("800x800")
        self.root.resizable(False, False)
        # Переменные
        self.image_path = tk.StringVar()
        self.status = tk.StringVar(value="Готов к работе")
        self.save_dir_path = tk.StringVar(
            value=os.path.join(os.path.expanduser("~"), "Downloads")
        )
        # Создаем элементы интерфейса
        self.create_widgets()

    def create_widgets(self):
        style = ttk.Style()
        style.configure("TButton", padding=6, font=("Arial", 10))
        style.configure("TLabel", font=("Arial", 10))
        style.configure("Status.TLabel", font=("Arial", 9), foreground="gray")
        # Фрейм для выбора папки
        folder_frame = ttk.Frame(self.root, padding=10)
        folder_frame.pack(fill="x")
        ttk.Label(folder_frame, text="Выберите папку с изображениями:").pack(anchor="w")
        folder_selector = ttk.Frame(folder_frame)
        folder_selector.pack(fill="x", pady=5)
        self.entry_folder = ttk.Entry(folder_selector, textvariable=self.image_path, width=40)
        self.entry_folder.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(folder_selector, text="Выбрать папку...", command=self.select_folder).pack(side="left")
        # Фрейм для выбора директории
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
                                  command=self.start_automation_thread, state="normal")
        self.btn_run.pack(pady=10)
        # Статус
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill="x", padx=10, pady=5)
        self.status_label = ttk.Label(status_frame, textvariable=self.status, style="Status.TLabel")
        self.status_label.pack(anchor="w")
        # Прогресс-бар
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=480, mode="determinate")
        self.progress.pack(pady=10, padx=10)
        # Консоль
        console_frame = ttk.Frame(self.root, padding=10)
        console_frame.pack(fill="both", expand=True)
        self.console = tk.Text(console_frame, height=40, bg="#ffffff", font=("Consolas", 9))
        self.console.pack(fill="both")
        self.console.insert("end", "> Выберите папку с изображениями и нажмите 'Запустить обработку'\n")

    def select_folder(self):
        folder_path = filedialog.askdirectory(
            title="Выберите папку с изображениями",
            initialdir=os.path.expanduser("~")
        )
        if folder_path:
            self.image_path.set(folder_path)
            self.log(f"> Выбрана папка: {folder_path}")

    def select_save_directory(self):
        save_dir = filedialog.askdirectory(
            title="Выберите папку для сохранения",
            initialdir=os.path.expanduser("~")
        )
        if save_dir:
            self.save_dir_path.set(save_dir)
            self.log(f"> Выбрана директория для сохранения: {save_dir}")

    def log(self, message):
        """Добавляет сообщение в консоль."""
        def update_console():
            self.console.insert("end", message + "\n")
            self.console.see("end")
        self.root.after(0, update_console)

    def update_progress(self, value):
        """Обновляет прогресс-бар."""
        def update_progressbar():
            self.progress["value"] = value
        self.root.after(0, update_progressbar)

    def process_image(self, image_file, folder_path, save_dir):
        """Обработка одного изображения."""
        try:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--ignore-ssl-errors')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            if HEADLESS_MODE:
                chrome_options.add_argument('--headless=new')
            prefs = {
                "profile.default_content_setting_values.automatic_downloads": 1,
                "download_restrictions": 3,
                "download.prompt_for_download": False,
                "media_stream": 1,
                "media_stream_mic": 1,
                "media_stream_camera": 1,
            }
            chrome_options.add_experimental_option("prefs", prefs)
            user_agent = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(90, 120)}.0.0.0 Safari/537.36"
            chrome_options.add_argument(f'user-agent={user_agent}')
            self.log(f"> Запуск браузера для файла: {image_file}")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            wait = WebDriverWait(driver, TIMEOUT_SHORT)
            try:
                self.log(f"> Открываем сайт palette.fm для файла: {image_file}")
                driver.get("https://palette.fm/color/filters")  
                self.log(f"> Начинаем процесс загрузки для файла: {image_file}")
                upload_button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'UPLOAD NEW IMAGE')]"))
                )
                file_input = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
                )
                driver.execute_script("arguments[0].removeAttribute('hidden')", file_input)
                driver.execute_script("arguments[0].style.display = 'block'", file_input)
                driver.execute_script("arguments[0].style.visibility = 'visible'", file_input)
                file_path = os.path.abspath(os.path.join(folder_path, image_file))
                file_input.send_keys(file_path)
                self.log(f"> Файл '{image_file}' отправлен")
                self.log(f"> Ожидаем результата для файла: {image_file}")
                wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.image-container")),
                    message="Результат не найден!"
                )
                self.log(f"> Изображение успешно обработано: {image_file}")
                result_image = self.get_result_image(driver)
                if result_image:
                    save_path = os.path.join(save_dir, image_file)
                    with open(save_path, "wb") as f:
                        f.write(result_image)
                    self.log(f"> Успешно! Файл сохранен: {save_path}")
                else:
                    self.log(f"> Не удалось получить результат для файла: {image_file}")
            except Exception as e:
                self.log(f"> Ошибка при обработке файла {image_file}: {str(e)}")
            finally:
                driver.quit()
                self.log(f"> Браузер закрыт для файла: {image_file}")
        except Exception as e:
            self.log(f"> Критическая ошибка при обработке файла {image_file}: {str(e)}")

    def run_automation(self):
        folder_path = self.image_path.get()
        if not folder_path or not os.path.isdir(folder_path):
            messagebox.showerror("Ошибка", "Пожалуйста, выберите папку с изображениями")
            return
        # Получаем список поддерживаемых изображений
        supported_extensions = (".jpg", ".jpeg", ".png")
        image_files = [
            f for f in os.listdir(folder_path)
            if os.path.isfile(os.path.join(folder_path, f)) and f.lower().endswith(supported_extensions)
        ]
        if not image_files:
            messagebox.showerror("Ошибка", "В выбранной папке нет поддерживаемых изображений")
            return
        self.btn_run["state"] = "disabled"
        self.status.set("Запуск обработки...")
        self.update_progress(0)
        try:
            total_files = len(image_files)
            save_dir = self.save_dir_path.get()
            for i, image_file in enumerate(image_files, start=1):
                self.log(f"> Обработка файла {i}/{total_files}: {image_file}")
                self.update_progress(int((i / total_files) * 100))
                self.process_image(image_file, folder_path, save_dir)
        except Exception as e:
            self.log(f"> Критическая ошибка: {str(e)}")
            self.status.set("Ошибка инициализации")
        finally:
            self.btn_run["state"] = "normal"
            self.log("> Обработка завершена")

    def get_result_image(self, driver):
        try:
            self.log("> Поиск изображения с base64 в src...")
            first_image_element = WebDriverWait(driver, TIMEOUT_MEDIUM).until(
                EC.visibility_of_element_located((By.XPATH, "//img[contains(@src, 'base64')]"))
            )
            first_image_src = first_image_element.get_attribute("src")
            self.log(f"> Первое изображение найдено: {first_image_src[:50]}...")
            self.log("> Ожидание исчезновения первого изображения...")
            WebDriverWait(driver, TIMEOUT_MEDIUM).until(
                EC.invisibility_of_element_located((By.XPATH, f"//img[@src='{first_image_src}']"))
            )
            self.log("> Первое изображение исчезло.")
            self.log("> Ожидание появления второго изображения...")
            second_image_element = WebDriverWait(driver, TIMEOUT_MEDIUM).until(
                EC.visibility_of_element_located((By.XPATH, "//img[contains(@src, 'base64')]"))
            )
            second_image_src = second_image_element.get_attribute("src")
            self.log(f"> Второе изображение найдено: {second_image_src[:50]}...")
            if first_image_src != second_image_src:
                self.log("> Изображения различаются. Сохранение второго изображения...")
                if second_image_src and second_image_src.startswith('data:image'):
                    base64_data = second_image_src.split(',', 1)[1]
                    image_data = base64.b64decode(base64_data)
                    return image_data
                else:
                    self.log("> Атрибут 'src' второго изображения не содержит base64-данных.")
                    return None
            else:
                self.log("> Изображения одинаковые. Сохранение не требуется.")
                return None
        except TimeoutException:
            self.log("> Ошибка: Изображение с base64 не найдено за отведённое время.")
            return None
        except Exception as e:
            self.log(f"> Ошибка получения изображения: {str(e)}")
            return None

    def start_automation_thread(self):
        """Запускает обработку в отдельном потоке."""
        self.btn_run["state"] = "disabled"
        self.status.set("Запуск обработки...")
        self.update_progress(0)
        # Запускаем run_automation в отдельном потоке
        thread = threading.Thread(target=self.run_automation)
        thread.start()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = PaletteFMAutomator()
    app.run()