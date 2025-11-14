import threading
from socket import socket, AF_INET, SOCK_STREAM
from customtkinter import *
from tkinter import filedialog, messagebox
import pygame
import os

set_appearance_mode("dark")
set_default_color_theme("blue")


class MainWindow(CTk):
    def __init__(self, host="localhost", port=8080):
        super().__init__()
        self.title("Telescam — Combined")
        self.geometry("700x460")
        self.minsize(1200, 600)

        # ---------- ЛОГІКА ЧАТІВ ----------
        self.current_chat = "Основний"
        self.CHAT_FILES = {"Основний": "main.txt", "Збережені": "saved.txt"}

        # ---------- NETWORK ----------
        self.host = host
        self.port = port
        self.username = "Artem"
        self.sock = None
        self.connected = False

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
        self.menu_speed = 12  # швидкість анімації
        self.menu_open = False
        self.target_width = 240

        # --- меню ---
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
        self.status_label = CTkLabel(self,
                                     text=f"Чат: {self.current_chat} | User: {self.username} — {self.host}:{self.port}")
        self.status_label.place(x=40, y=28)

        self.after(15, self.adaptive_ui)

        self.load_chat_messages()

    # ---------- NETWORK ----------
    def connect_to_server(self):
        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.settimeout(5)
            self.sock.connect((self.host, self.port))
            self.sock.settimeout(None)
            hello = f"TEXT@{self.username}@[SYSTEM] {self.username} приєднався(лась) до чату!\n"
            self.sock.sendall(hello.encode('utf-8'))

            self.connected = True
            self.connect_status_label.configure(text="Підключено", text_color="green")
            self.connect_subscribe_btn.configure(text="Оновити ім'я ✅")

            threading.Thread(target=self.recv_message, daemon=True).start()
        except Exception as e:
            self.sock = None
            self.connected = False
            self.connect_status_label.configure(text="Помилка підключення", text_color="red")
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
                pass
        self.sock = None
        self.connected = False  # (НОВЕ)
        self.add_message("[SYSTEM] Відключено від сервера.")

        self.connect_status_label.configure(text="Відключено", text_color="red")
        self.connect_subscribe_btn.configure(text="Підключитися")

    def handle_line(self, line):
        if not line:
            return

        message_text = line

        parts = line.split("@", 3)
        msg_type = parts[0]

        if msg_type == "TEXT":
            if len(parts) >= 3:
                author = parts[1]
                message = parts[2]
                message_text = f"{author}: {message}"
        elif msg_type == "IMAGE":
            if len(parts) >= 4:
                author = parts[1]
                filename = parts[2]
                message_text = f"{author} надіслав(ла) зображення: {filename}"

        self.add_message_to_file(message_text, chat_name="Основний")

        if self.current_chat == "Основний":
            self.add_message(message_text)

    # ---------- UI: меню ----------
    def _build_menu_widgets(self):
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

        self.connect_subscribe_btn = CTkButton(self.menu_frame, text="Підключитися", command=self.connect_or_subscribe)
        self.connect_subscribe_btn.pack(pady=8, padx=10, fill="x")

        self.connect_status_label = CTkLabel(self.menu_frame, text="Не підключено", text_color="red")
        self.connect_status_label.pack(pady=(0, 8), padx=10)

        self.chat_switch_label = CTkLabel(self.menu_frame, text="Чати")
        self.chat_switch_label.pack(pady=(6, 2))
        self.chat_switch_frame = CTkFrame(self.menu_frame, fg_color="transparent")
        self.chat_switch_frame.pack(pady=4, padx=10, fill="x")

        self.btn_main_chat = CTkButton(self.chat_switch_frame, text="Основний",
                                       command=lambda: self.switch_chat("Основний"))
        self.btn_main_chat.pack(side="left", expand=True, padx=2)

        self.btn_saved_chat = CTkButton(self.chat_switch_frame, text="Збережені",
                                        command=lambda: self.switch_chat("Збережені"))
        self.btn_saved_chat.pack(side="right", expand=True, padx=2)

        # Роздільник
        self.sep1 = CTkLabel(self.menu_frame, text="──────────")
        self.sep1.pack(pady=6)

        # Музика
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

        self.info_label = CTkLabel(self.menu_frame, text="Стікер: 😀  |  Відправлення: кнопка ➤", wraplength=200,
                                   justify="left")
        self.info_label.pack(side="bottom", pady=8, padx=8)

    def toggle_menu(self):
        self.menu_open = not self.menu_open
        if self.menu_open:
            self._build_menu_widgets()
            self.menu_frame.lift()
            self.toggle_btn.lift()
        self.animate_menu()

    def animate_menu(self):
        step = self.menu_speed if self.menu_open else -self.menu_speed
        new_width = self.menu_width + step

        if 0 <= new_width <= self.target_width:
            self.menu_width = new_width
            self.after(10, self.animate_menu)
        else:
            self.menu_width = self.target_width if self.menu_open else 0

    def _move_main_ui(self, shift):
        base_x = 40 + shift
        self.chat_text.place(x=base_x, y=60)
        self.message_input.place(x=base_x, y=380)
        self.send_btn.place(x=base_x + 345, y=376)
        self.sticker_btn.place(x=base_x + 395, y=376)

        self.status_label.place(x=base_x, y=28)
        self.status_label.configure(text=f"Чат: {self.current_chat} | User: {self.username} — {self.host}:{self.port}")

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
            self.status_label.configure(
                text=f"Чат: {self.current_chat} | User: {self.username} — {self.host}:{self.port}  |  Музика: {fname}")

    def toggle_music(self):
        if not self.music_file:
            self.add_message("⚠️ Спочатку оберіть файл музики!")
            return
        if not self.is_music_playing:
            try:
                pygame.mixer.music.load(self.music_file)
                pygame.mixer.music.set_volume(self.volume)
                pygame.mixer.music.play(-1)
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

    # ---------- CHAT (НОВІ ФУНКЦІЇ) ----------

    def switch_chat(self, chat_name):
        if chat_name == self.current_chat:
            return

        self.current_chat = chat_name
        self.load_chat_messages()

        self.status_label.configure(text=f"Чат: {self.current_chat} | User: {self.username} — {self.host}:{self.port}")

        if self.menu_open:
            self.toggle_menu()

    def load_chat_messages(self):
        self.chat_text.configure(state="normal")
        self.chat_text.delete("1.0", "end")

        filepath = self.CHAT_FILES[self.current_chat]

        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    self.chat_text.insert("end", f.read())
            except Exception as e:
                print(f"Помилка читання файлу {filepath}: {e}")

        self.chat_text.configure(state="disabled")
        self.chat_text.see("end")

    def add_message_to_file(self, message, chat_name=None):
        if chat_name:
            filepath = self.CHAT_FILES.get(chat_name)
        else:
            filepath = self.CHAT_FILES.get(self.current_chat)

        if not filepath:
            return

        try:
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(message + "\n")
        except Exception as e:
            print(f"Помилка запису у файл {filepath}: {e}")

    def add_message(self, text):
        self.chat_text.configure(state="normal")
        self.chat_text.insert("end", text + "\n")
        self.chat_text.configure(state="disabled")
        self.chat_text.see("end")

    def send_message(self):
        msg = self.message_input.get().strip()
        if not msg:
            return

        if self.current_chat == "Основний" and not self.connected:
            self.add_message("⚠️ Спочатку підключіться до сервера!")
            return

        full_message = f"{self.username}: {msg}"

        self.add_message_to_file(full_message)

        self.add_message(full_message)

        if self.current_chat == "Основний":
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
        message_text = f"{self.username} sent a sticker: {s}"
        self.add_message_to_file(message_text)

        self.add_message(message_text)

        if self.current_chat == "Основний":
            if not self.connected:
                self.add_message("⚠️ Спочатку підключіться до сервера!")
                return
            try:
                if self.sock:
                    data = f"TEXT@{self.username}@[Sticker] {s}\n"
                    self.sock.sendall(data.encode())
            except Exception:
                pass

    def connect_or_subscribe(self):
        name = self.entry_name.get().strip()
        if not name:
            messagebox.showwarning("Error", "Спочатку введіть ім'я!")
            return

        if not self.connected:
            self.username = name
            self.status_label.configure(
                text=f"Чат: {self.current_chat} | User: {self.username} — {self.host}:{self.port}")
            self.connect_status_label.configure(text="Підключення...", text_color="orange")
            threading.Thread(target=self.connect_to_server, daemon=True).start()

        else:
            if name == self.username:
                messagebox.showinfo("Info", "Це ім'я вже використовується.")
                return

            old = self.username
            self.username = name
            messagebox.showinfo("Subscribed!", f"{name}, ви оновили ім'я 🎉")
            self.status_label.configure(
                text=f"Чат: {self.current_chat} | User: {self.username} — {self.host}:{self.port}")

            if self.sock:
                try:
                    message_text = f"[SYSTEM] {self.username} змінив(ла) ім'я з {old}."

                    self.add_message_to_file(message_text, chat_name="Основний")

                    if self.current_chat == "Основний":
                        self.add_message(message_text)

                    self.sock.sendall(
                        f"TEXT@{self.username}@[SYSTEM] {self.username} змінив(ла) ім'я з {old}.\n".encode())
                except Exception:
                    self.add_message("⚠️ Не вдалося повідомити сервер про зміну імені.")

    # ---------- THEME ----------
    def change_theme(self, value):
        set_appearance_mode("dark" if value == "Dark" else "light")

    # ---------- ADAPTIVE UI ----------
    # (ДОПИСАНО)
    def adaptive_ui(self):
        try:
            self.menu_frame.configure(height=self.winfo_height())

            self.menu_frame.configure(width=self.menu_width)

            self.menu_frame.configure(fg_color=("gray20" if get_appearance_mode().lower() == "dark" else "gray90"))

            self._move_main_ui(self.menu_width)
        except Exception:
            pass
        self.after(15, self.adaptive_ui)


if __name__ == "__main__":
    win = MainWindow()
    win.mainloop()