import time
import os
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

# Константы
HEADLESS_MODE = False  # Режим без отображения браузера
TIMEOUT_SHORT = 5    # Короткое ожидание для всплывающих окон
TIMEOUT_MEDIUM = 15  # Основное ожидание элементов
TIMEOUT_LONG = 30    # Долгое ожидание (например, для загрузки страницы)

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

        # Фрейм для выбора файла
        file_frame = ttk.Frame(self.root, padding=10)
        file_frame.pack(fill="x")
        ttk.Label(file_frame, text="Выберите изображение:").pack(anchor="w")
        file_selector = ttk.Frame(file_frame)
        file_selector.pack(fill="x", pady=5)
        self.entry_file = ttk.Entry(file_selector, textvariable=self.image_path, width=40)
        self.entry_file.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(file_selector, text="Обзор...", command=self.select_file).pack(side="left")

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
                                 command=self.run_automation, state="normal")
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
        self.console.insert("end", "> Выберите изображение и нажмите 'Запустить обработку'\n")

    def select_file(self):
        file_types = (
            ("Изображения", "*.jpg *.jpeg *.png"),
            ("Все файлы", "*.*")
        )
        file_path = filedialog.askopenfilename(
            title="Выберите изображение",
            initialdir=os.path.expanduser("~"),
            filetypes=file_types
        )
        if file_path:
            self.image_path.set(file_path)
            self.log(f"> Выбран файл: {os.path.basename(file_path)}")

    def select_save_directory(self):
        save_dir = filedialog.askdirectory(
            title="Выберите папку для сохранения",
            initialdir=os.path.expanduser("~")
        )
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
            self.log("> Инициализация браузера...")
            print (user_agent)
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            wait = WebDriverWait(driver, TIMEOUT_SHORT)
            
            self.update_progress(20)

            try:
                self.log("> Открываем сайт palette.fm...")
                driver.get("https://palette.fm/color/filters") 
                self.update_progress(30)
                
                self.close_popups(driver)

                self.log("> Начинаем процесс загрузки...")
                upload_button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'UPLOAD NEW IMAGE')]"))
                )
              
                self.log("> Загружаем изображение...")

                file_input = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
                )

                driver.execute_script("arguments[0].removeAttribute('hidden')", file_input)
                driver.execute_script("arguments[0].style.display = 'block'", file_input)
                driver.execute_script("arguments[0].style.visibility = 'visible'", file_input)

                file_path = os.path.abspath(self.image_path.get())
                file_input.send_keys(file_path)
                self.log(f"> Файл '{os.path.basename(file_path)}' отправлен")
                self.update_progress(40)

                self.log("> Ожидаем результата...")
                wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.image-container")),
                    message="Результат не найден!"
                )
                self.log("> Изображение успешно обработано!")
                self.update_progress(80)

                result_image = self.get_result_image(driver)
                if result_image:
                    timestamp = int(time.time())
                    filename = f"palette_{timestamp}.png"
                    save_path = os.path.join(self.save_dir_path.get(), filename)
                    with open(save_path, "wb") as f:
                        f.write(result_image)
                    self.log(f"> Успешно! Файл сохранен: {save_path}")
                    self.status.set(f"Готово! Файл сохранен в {self.save_dir_path.get()}")
                    self.update_progress(100)
                else:
                    raise Exception("Не удалось получить изображение")

            except TimeoutException as e:
                self.log(f"> Ошибка: Результат не загружен за отведенное время — {str(e)}")
                driver.save_screenshot("timeout_error.png")
                self.status.set("Ошибка: результат не загружен")
                self.update_progress(100)

            except WebDriverException as e:
                self.log(f"> Ошибка подключения к браузеру — {str(e)}")
                driver.save_screenshot("browser_error.png")
                self.status.set("Ошибка браузера")
                self.update_progress(100)

            except Exception as e:
                self.log(f"> Ошибка: {str(e)}")
                self.status.set("Ошибка при выполнении")
                driver.save_screenshot("error_screenshot.png")

            finally:
                time.sleep(2)
                driver.quit()
                self.log("> Браузер закрыт")

        except Exception as e:
            self.log(f"> Критическая ошибка: {str(e)}")
            self.status.set("Ошибка инициализации")

        finally:
            self.btn_run["state"] = "normal"

    def close_popups(self, driver):
        try:
            time.sleep(1)
            self.log("> Автоматическое вводим путь к файлу...")
            pyautogui.write(r"c:/1.jpg")  # Вводим путь к файлу
            pyautogui.press('enter')  # Нажимаем Enter
            self.update_progress(40)
            time.sleep(1)
        except:
            pass
    
     
    def get_result_image(self, driver):
        try:
            self.log("> Ожидание появления первого изображения...")
            # Захват первого изображения
            first_image_element = WebDriverWait(driver, TIMEOUT_MEDIUM).until(
                EC.visibility_of_element_located((By.XPATH, "//img[contains(@src, 'base64')]"))
            )
            first_image_src = first_image_element.get_attribute("src")
            self.log(f"> Первое изображение найдено: {first_image_src[:50]}...")

            # Ожидание исчезновения первого изображения
            self.log("> Ожидание исчезновения первого изображения...")
            WebDriverWait(driver, TIMEOUT_MEDIUM).until(
                EC.invisibility_of_element_located((By.XPATH, f"//img[@src='{first_image_src}']"))
            )
            self.log("> Первое изображение исчезло.")

            # Захват второго изображения
            self.log("> Ожидание появления второго изображения...")
            second_image_element = WebDriverWait(driver, TIMEOUT_MEDIUM).until(
                EC.visibility_of_element_located((By.XPATH, "//img[contains(@src, 'base64')]"))
            )
            second_image_src = second_image_element.get_attribute("src")
            self.log(f"> Второе изображение найдено: {second_image_src[:50]}...")

            # Сравнение первого и второго изображений
            if first_image_src != second_image_src:
                self.log("> Изображения различаются. Сохранение второго изображения...")
                if second_image_src and second_image_src.startswith('data:image'):
                    # Извлекаем base64-часть после запятой
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
            self.log("> Ошибка: Изображение не найдено за отведённое время.")
            return None
        except Exception as e:
            self.log(f"> Ошибка получения изображения: {str(e)}")
            return None
                
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = PaletteFMAutomator()
    app.run()