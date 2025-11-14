import threading
from socket import socket, AF_INET, SOCK_STREAM
from customtkinter import *
from tkinter import filedialog, messagebox
import pygame
import os

# Налаштування зовнішнього вигляду CustomTkinter
set_appearance_mode("dark")
set_default_color_theme("blue")


class MainWindow(CTk):
    def __init__(self, host="localhost", port=8080):
        super().__init__()
        self.title("Telescam — Combined")
        self.geometry("700x460")
        self.minsize(1200, 600)

        # ---------- NETWORK ----------
        self.host = host
        self.port = port
        self.username = "Artem"
        self.sock = None
        self.connect_to_server()

        # ---------- PYGAME (MUSIC) ----------
        pygame.mixer.init()
        self.is_music_playing = False
        self.music_file = None
        self.volume = 0.5

        # ---------- MENU (анімоване) ----------
        self.menu_frame = CTkFrame(self, width=0, height=self.winfo_height(), fg_color=("gray20", "gray90"))
        self.menu_frame.place(x=0, y=0)
        self.menu_frame.pack_propagate(False)
        self.menu_width = 0
        self.menu_speed = 12  # швидкість анімації (пікселів за крок)
        self.menu_open = False
        self.target_width = 240

        # --- меню: вміст (будемо оновлювати при відкритті/закритті) ---
        # Створимо базові виджети, але не всі одразу pack — щоб уникнути дублювання при повторному відкритті
        self._build_menu_widgets()

        # ---------- Кнопка відкриття меню ----------
        self.toggle_btn = CTkButton(self, text="≡", width=36, height=36, command=self.toggle_menu)
        self.toggle_btn.place(x=10, y=10)

        # ---------- CHAT AREA ----------
        self.chat_text = CTkTextbox(self, state="disabled", width=420, height=300)
        self.chat_text.place(x=40, y=60)

        # ---------- MESSAGE INPUT & BUTTONS ----------
        self.message_input = CTkEntry(self, placeholder_text="Введіть повідомлення...", width=330)
        self.message_input.place(x=40, y=380)

        self.send_btn = CTkButton(self, text="➤", width=40, height=36, command=self.send_message)
        self.send_btn.place(x=385, y=376)

        self.sticker_btn = CTkButton(self, text="😀", width=40, height=36, command=self.open_stickers)
        self.sticker_btn.place(x=435, y=376)

        # ---------- STATUS BAR ----------
        self.status_label = CTkLabel(self, text=f"User: {self.username} — {self.host}:{self.port}")
        self.status_label.place(x=40, y=28)

        # ---------- адаптивний інтерфейс і loop ----------
        # (ВИПРАВЛЕНО) Запускаємо цикл швидше для плавної анімації
        self.after(15, self.adaptive_ui)

        # ---------- NETWORK ----------

    def connect_to_server(self):
        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.settimeout(5)
            self.sock.connect((self.host, self.port))
            self.sock.settimeout(None)
            hello = f"TEXT@{self.username}@[SYSTEM] {self.username} приєднався(лась) до чату!\n"
            self.sock.sendall(hello.encode('utf-8'))
            threading.Thread(target=self.recv_message, daemon=True).start()
        except Exception as e:
            self.sock = None
            # якщо не вдається підключитися — повідомимо в інтерфейсі
            # не викликаємо messagebox тут, щоб не фокусуватися при запуску
            print(f"Не вдалося підключитися: {e}")

    def recv_message(self):
        if not self.sock:
            return
        buffer = ""
        while True:
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                buffer += chunk.decode(errors="ignore")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self.handle_line(line.strip())
            except Exception:
                break
        try:
            self.sock.close()
        except Exception:
            pass
        self.sock = None
        self.add_message("[SYSTEM] Відключено від сервера.")

    def handle_line(self, line):
        if not line:
            return
        parts = line.split("@", 3)
        msg_type = parts[0]
        if msg_type == "TEXT":
            if len(parts) >= 3:
                author = parts[1]
                message = parts[2]
                # показуємо всі повідомлення (включно з власними — сервер може реверснути)
                self.add_message(f"{author}: {message}")
        elif msg_type == "IMAGE":
            if len(parts) >= 4:
                author = parts[1]
                filename = parts[2]
                self.add_message(f"{author} надіслав(ла) зображення: {filename}")
        else:
            # інші повідомлення — показуємо як є
            self.add_message(line)

    # ---------- UI: меню ----------
    def _build_menu_widgets(self):
        # Очистимо фрейм
        for w in self.menu_frame.winfo_children():
            w.destroy()

        # Заголовок меню
        self.menu_title = CTkLabel(self.menu_frame, text="Меню", font=("Arial", 16, "bold"))
        self.menu_title.pack(pady=(12, 6))

        # Ім'я / підписка
        self.name_label = CTkLabel(self.menu_frame, text="Ім'я:")
        self.name_label.pack(pady=(6, 2))
        self.entry_name = CTkEntry(self.menu_frame, placeholder_text=self.username)
        self.entry_name.pack(pady=2, padx=10, fill="x")
        self.subscribe_btn = CTkButton(self.menu_frame, text="Підписатись ✅", command=self.subscribe)
        self.subscribe_btn.pack(pady=8, padx=10, fill="x")

        # Роздільник
        self.sep1 = CTkLabel(self.menu_frame, text="──────────")
        self.sep1.pack(pady=6)

        # Музика: вибір файлу, play/stop, гучність
        self.music_label = CTkLabel(self.menu_frame, text="Музика")
        self.music_label.pack(pady=(6, 2))

        self.select_button = CTkButton(self.menu_frame, text="📂 Обрати муз. файл", command=self.choose_music)
        self.select_button.pack(pady=4, padx=10, fill="x")

        self.music_button = CTkButton(self.menu_frame, text="▶/■ Вкл/Викл музику", command=self.toggle_music)
        self.music_button.pack(pady=4, padx=10, fill="x")

        self.volume_label = CTkLabel(self.menu_frame, text=f"🔊 Гучність: {int(self.volume * 100)}%")
        self.volume_label.pack(pady=(8, 2))
        self.volume_slider = CTkSlider(self.menu_frame, from_=0, to=1, number_of_steps=100, command=self.set_volume)
        self.volume_slider.set(self.volume)
        self.volume_slider.pack(padx=10, pady=(0, 8), fill="x")

        # Роздільник
        self.sep2 = CTkLabel(self.menu_frame, text="──────────")
        self.sep2.pack(pady=6)

        # Тема
        self.theme_label = CTkLabel(self.menu_frame, text="Тема")
        self.theme_label.pack(pady=(6, 2))
        self.theme_option = CTkOptionMenu(self.menu_frame, values=["Dark", "Light"], command=self.change_theme)
        self.theme_option.set("Dark" if get_appearance_mode() == "dark" or get_appearance_mode() == "Dark" else "Light")
        self.theme_option.pack(padx=10, pady=6, fill="x")

        # Невеликий пояснювальний текст
        self.info_label = CTkLabel(self.menu_frame, text="Стікер: 😀  |  Відправлення: кнопка ➤", wraplength=200,
                                   justify="left")
        self.info_label.pack(side="bottom", pady=8, padx=8)

    def toggle_menu(self):
        self.menu_open = not self.menu_open

        if self.menu_open:
            # 1. Створюємо наново віджети
            self._build_menu_widgets()

            # 2. (ВИПРАВЛЕННЯ Z-INDEX)
            # Піднімаємо фрейм меню НАД чатом
            self.menu_frame.lift()

            # 3. (ВИПРАВЛЕННЯ Z-INDEX)
            # Піднімаємо кнопку "≡" НАД фреймом меню
            self.toggle_btn.lift()

            # Запускаємо анімацію
        self.animate_menu()

    # (ВИПРАВЛЕНО) Ця функція ТІЛЬКИ змінює змінну 'self.menu_width'
    def animate_menu(self):
        step = self.menu_speed if self.menu_open else -self.menu_speed
        new_width = self.menu_width + step

        if 0 <= new_width <= self.target_width:
            self.menu_width = new_width
            # Ми прибрали звідси .configure() та _move_main_ui()
            self.after(10, self.animate_menu)  # Швидкий цикл для зміни змінної
        else:
            # кінець анімації
            self.menu_width = self.target_width if self.menu_open else 0
            # Ми прибрали звідси .configure() та _move_main_ui()

    def _move_main_ui(self, shift):
        # зрушуємо чат і інпут праворуч при відкритті меню
        base_x = 40 + shift
        self.chat_text.place(x=base_x, y=60)
        self.message_input.place(x=base_x, y=380)
        self.send_btn.place(x=base_x + 345, y=376)
        self.sticker_btn.place(x=base_x + 395, y=376)
        self.status_label.place(x=base_x, y=28)

    # ---------- MUSIC ----------
    def choose_music(self):
        file_path = filedialog.askopenfilename(
            title="Виберіть музичний файл",
            filetypes=[("Audio Files", "*.mp3 *.wav *.ogg"), ("All Files", "*.*")]
        )
        if file_path:
            self.music_file = file_path
            fname = os.path.basename(file_path)
            self.add_message(f"🎵 Обрано музику: {fname}")
            # оновимо status
            self.status_label.configure(text=f"User: {self.username} — {self.host}:{self.port}  |  Музыка: {fname}")

    def toggle_music(self):
        if not self.music_file:
            self.add_message("⚠️ Спочатку оберіть файл музики!")
            return

        if not self.is_music_playing:
            try:
                pygame.mixer.music.load(self.music_file)
                pygame.mixer.music.set_volume(self.volume)
                pygame.mixer.music.play(-1)  # повторюється
                self.is_music_playing = True
                self.add_message(f"▶️ Відтворення: {os.path.basename(self.music_file)}")
            except Exception as e:
                self.add_message(f"Помилка запуску музики: {e}")
        else:
            pygame.mixer.music.stop()
            self.is_music_playing = False
            self.add_message("⏹️ Музику вимкнено")

    def set_volume(self, value):
        try:
            self.volume = float(value)
            pygame.mixer.music.set_volume(self.volume)
            if hasattr(self, 'volume_label'):
                self.volume_label.configure(text=f"🔊 Гучність: {int(self.volume * 100)}%")
        except Exception:
            pass

    # ---------- CHAT ----------
    def add_message(self, text):
        # Додаємо повідомлення у Chat textbox
        self.chat_text.configure(state="normal")
        self.chat_text.insert("end", text + "\n")
        self.chat_text.configure(state="disabled")
        self.chat_text.see("end")

    def send_message(self):
        msg = self.message_input.get().strip()
        if not msg:
            return
        # Локально показуємо
        self.add_message(f"{self.username}: {msg}")
        data = f"TEXT@{self.username}@{msg}\n"
        if self.sock:
            try:
                self.sock.sendall(data.encode())
            except Exception:
                self.add_message("⚠️ Не вдалося відправити повідомлення.")
        else:
            self.add_message("⚠️ Не підключено до сервера.")
        self.message_input.delete(0, "end")

    # ---------- STICKERS ----------
    def open_stickers(self):
        stickers = [
            "😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣", "😊", "😇",
            "🙂", "🙃", "😉", "😌", "😍", "🥰", "😘", "😗", "😙", "😚",
            "😋", "😛", "😜", "🤪", "😝", "🤑", "🤗", "🤭", "🤫", "🤔",
            "😏", "😶", "😐", "😑", "😬", "🙄", "😯", "😮", "😲", "😳",
            "🥺", "😢", "😭", "😤", "😠", "😡", "🤬", "🤯", "😱", "😰"
        ]
        sticker_win = CTkToplevel(self)
        sticker_win.title("Стікери")
        sticker_win.geometry("420x200")
        sticker_win.resizable(False, False)

        for i, s in enumerate(stickers):
            btn = CTkButton(sticker_win, text=s, width=36, height=36,
                            command=lambda x=s: self.add_sticker(x))
            btn.grid(row=i // 10, column=i % 10, padx=6, pady=6)

    def add_sticker(self, s):
        self.chat_text.configure(state="normal")
        self.chat_text.insert("end", f"{self.username} sent a sticker: {s}\n")
        self.chat_text.configure(state="disabled")
        self.chat_text.see("end")
        try:
            if self.sock:
                data = f"TEXT@{self.username}@[Sticker] {s}\n"
                self.sock.sendall(data.encode())
        except Exception:
            pass

    # ---------- SUBSCRIBE / CHANGE NAME ----------
    def subscribe(self):
        name = self.entry_name.get().strip()
        if name:
            old = self.username
            self.username = name
            messagebox.showinfo("Subscribed!", f"{name}, ви підписані 🎉")
            self.status_label.configure(text=f"User: {self.username} — {self.host}:{self.port}")
            # повідомляємо сервер про зміну імені
            if self.sock:
                try:
                    self.sock.sendall(
                        f"TEXT@{self.username}@[SYSTEM] {self.username} змінив(ла) ім'я з {old}.\n".encode())
                except Exception:
                    self.add_message("⚠️ Не вдалося повідомити сервер про зміну імені.")
        else:
            messagebox.showwarning("Error", "Спочатку введіть ім'я!")

    # ---------- THEME ----------
    def change_theme(self, value):
        # value приходить як "Dark" або "Light"
        set_appearance_mode("dark" if value == "Dark" else "light")
        # (ВИПРАВЛЕНО) Нам більше не потрібно оновлювати колір меню тут,
        # оскільки 'adaptive_ui' зробить це на наступному кадрі.
        # self.menu_frame.configure(fg_color=("gray20" if value == "Dark" else "gray90"))

    # ---------- ADAPTIVE UI (оновлення позицій під час resize) ----------
    # (ВИПРАВЛЕНО) Ця функція тепер єдиний "художник"
    def adaptive_ui(self):
        try:
            # 1. Оновлюємо висоту меню
            self.menu_frame.configure(height=self.winfo_height())

            # 2. Оновлюємо ширину меню (на основі self.menu_width)
            self.menu_frame.configure(width=self.menu_width)

            # 3. Оновлюємо колір (щоб він відповідав темі)
            self.menu_frame.configure(fg_color=("gray20" if get_appearance_mode().lower() == "dark" else "gray90"))

            # 4. Переміщуємо основні елементи
            self._move_main_ui(self.menu_width)
        except Exception:
            pass

        # 5. Повторюємо цикл (на тій самій швидкості, що і в __init__)
        self.after(15, self.adaptive_ui)


if __name__ == "__main__":
    # Запускаємо головний вікно
    win = MainWindow()
    win.mainloop()