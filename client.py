import threading
from socket import *
from customtkinter import *
from tkinter import filedialog  # <-- для вибору файлів
import pygame  # <-- для музики


class MainWindow(CTk):
    def __init__(self):
        super().__init__()
        self.geometry('500x350')
        self.label = None

        # --- Ініціалізація pygame ---
        pygame.mixer.init()
        self.is_music_playing = False
        self.music_file = None  # файл буде вибирати користувач
        self.volume = 0.5

        # --- menu frame ---
        self.menu_frame = CTkFrame(self, width=30, height=350)
        self.menu_frame.pack_propagate(False)
        self.menu_frame.place(x=0, y=0)
        self.is_show_menu = False
        self.speed_animate_menu = -5
        self.btn = CTkButton(self, text='▶️', command=self.toggle_show_menu, width=30)
        self.btn.place(x=0, y=0)

        # --- chat UI ---
        self.chat_field = CTkTextbox(self, font=('Arial', 14, 'bold'), state='disable')
        self.chat_field.place(x=0, y=0)
        self.message_entry = CTkEntry(self, placeholder_text='Введіть повідомлення:', height=40)
        self.message_entry.place(x=0, y=0)
        self.send_button = CTkButton(self, text='>', width=50, height=40, command=self.send_message)
        self.send_button.place(x=0, y=0)

        self.username = 'Artem'
        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect(('localhost', 8080))
            hello = f"TEXT@{self.username}@[SYSTEM] {self.username} приєднався(лась) до чату!\n"
            self.sock.send(hello.encode('utf-8'))
            threading.Thread(target=self.recv_message, daemon=True).start()
        except Exception as e:
            self.add_message(f"Не вдалося підключитися до сервера: {e}")

        self.adaptive_ui()

    # ------------------ MENU ------------------ #
    def toggle_show_menu(self):
        if self.is_show_menu:
            self.is_show_menu = False
            self.speed_animate_menu *= -1
            self.btn.configure(text='▶️')
            self.show_menu()
        else:
            self.is_show_menu = True
            self.speed_animate_menu *= -1
            self.btn.configure(text='◀️')
            self.show_menu()

            # --- елементи меню ---
            self.label = CTkLabel(self.menu_frame, text='Імʼя')
            self.label.pack(pady=10)
            self.entry = CTkEntry(self.menu_frame)
            self.entry.pack(pady=5)

            # --- вибір музики ---
            self.select_button = CTkButton(self.menu_frame, text='📂 Вибрати музику', command=self.choose_music)
            self.select_button.pack(pady=10)

            # --- кнопка музики ---
            self.music_button = CTkButton(self.menu_frame, text='🎵 Вкл/Викл музику', command=self.toggle_music)
            self.music_button.pack(pady=10)

            # --- повзунок гучності ---
            self.volume_label = CTkLabel(self.menu_frame, text=f"🔊 Гучність: {int(self.volume*100)}%")
            self.volume_label.pack(pady=5)
            self.volume_slider = CTkSlider(self.menu_frame, from_=0, to=1, number_of_steps=100,
                                           command=self.set_volume)
            self.volume_slider.set(self.volume)
            self.volume_slider.pack(pady=5)

    def show_menu(self):
        self.menu_frame.configure(width=self.menu_frame.winfo_width() + self.speed_animate_menu)
        if not self.menu_frame.winfo_width() >= 200 and self.is_show_menu:
            self.after(10, self.show_menu)
        elif self.menu_frame.winfo_width() >= 40 and not self.is_show_menu:
            self.after(10, self.show_menu)
            # знищуємо елементи при закритті меню
            for w in [getattr(self, x, None) for x in
                      ("label", "entry", "select_button", "music_button", "volume_label", "volume_slider")]:
                if w:
                    w.destroy()

    # ------------------ MUSIC ------------------ #
    def choose_music(self):
        """Відкрити діалог вибору музики"""
        file_path = filedialog.askopenfilename(
            title="Виберіть музичний файл",
            filetypes=[("Audio Files", "*.mp3 *.wav *.ogg"), ("All Files", "*.*")]
        )
        if file_path:
            self.music_file = file_path
            self.add_message(f"🎵 Обрано музику: {file_path.split('/')[-1]}")

    def toggle_music(self):
        """Увімкнути або вимкнути музику"""
        if not self.music_file:
            self.add_message("⚠️ Спочатку оберіть файл музики!")
            return

        if not self.is_music_playing:
            try:
                pygame.mixer.music.load(self.music_file)
                pygame.mixer.music.set_volume(self.volume)
                pygame.mixer.music.play(-1)  # безкінечне повторення
                self.is_music_playing = True
                self.add_message(f"🎶 Відтворення: {self.music_file.split('/')[-1]}")
            except Exception as e:
                self.add_message(f"Помилка запуску музики: {e}")
        else:
            pygame.mixer.music.stop()
            self.is_music_playing = False
            self.add_message("🔇 Музику вимкнено")

    def set_volume(self, value):
        """Функція змінює гучність музики"""
        self.volume = float(value)
        pygame.mixer.music.set_volume(self.volume)
        if hasattr(self, 'volume_label'):
            self.volume_label.configure(text=f"🔊 Гучність: {int(self.volume*100)}%")

    # ------------------ CHAT ------------------ #
    def adaptive_ui(self):
        self.menu_frame.configure(height=self.winfo_height())
        self.chat_field.place(x=self.menu_frame.winfo_width())
        self.chat_field.configure(width=self.winfo_width() - self.menu_frame.winfo_width(),
                                  height=self.winfo_height() - 40)
        self.send_button.place(x=self.winfo_width() - 50, y=self.winfo_height() - 40)
        self.message_entry.place(x=self.menu_frame.winfo_width(), y=self.send_button.winfo_y())
        self.message_entry.configure(
            width=self.winfo_width() - self.menu_frame.winfo_width() - self.send_button.winfo_width())
        self.after(50, self.adaptive_ui)

    def add_message(self, text):
        self.chat_field.configure(state='normal')
        self.chat_field.insert(END, text + '\n')
        self.chat_field.configure(state='disable')

    def send_message(self):
        message = self.message_entry.get()
        if message:
            self.add_message(f"{self.username}: {message}")
            data = f"TEXT@{self.username}@{message}\n"
            try:
                self.sock.sendall(data.encode())
            except:
                pass
        self.message_entry.delete(0, END)

    def recv_message(self):
        buffer = ""
        while True:
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                buffer += chunk.decode()
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self.handle_line(line.strip())
            except:
                break
        self.sock.close()

    def handle_line(self, line):
        if not line:
            return
        parts = line.split("@", 3)
        msg_type = parts[0]

        if msg_type == "TEXT":
            if len(parts) >= 3:
                author = parts[1]
                message = parts[2]
                self.add_message(f"{author}: {message}")
        elif msg_type == "IMAGE":
            if len(parts) >= 4:
                author = parts[1]
                filename = parts[2]
                self.add_message(f"{author} надіслав(ла) зображення: {filename}")
        else:
            self.add_message(line)


win = MainWindow()
win.mainloop()
