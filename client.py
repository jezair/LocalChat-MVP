import threading
import os
import pygame
import random
from socket import socket, AF_INET, SOCK_STREAM
from tkinter import filedialog, messagebox
from customtkinter import *


# ---------------------------------------------------------
#   Глобальні налаштування
# ---------------------------------------------------------
set_appearance_mode("dark")
set_default_color_theme("blue")


# ---------------------------------------------------------
#   Клас бульбашки для анімації
# ---------------------------------------------------------
class Bubble:
    def __init__(self, canvas, x, y, radius, speed):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.radius = radius
        self.speed = speed

        colors = ["#5599cc", "#6ba3d4", "#7aaddc", "#89b7e4", "#98c1ec"]
        color = random.choice(colors)

        self.id = canvas.create_oval(
            x - radius, y - radius,
            x + radius, y + radius,
            fill=color, outline="", width=0
        )

    def move(self, height):
        self.y -= self.speed

        if self.y + self.radius < 0:
            self.y = height + self.radius
            self.x = random.randint(20, 220)

        self.canvas.coords(
            self.id,
            self.x - self.radius, self.y - self.radius,
            self.x + self.radius, self.y + self.radius
        )


# ---------------------------------------------------------
#   Головне вікно програми
# ---------------------------------------------------------
class MainWindow(CTk):
    def __init__(self, host="localhost", port=8080):
        super().__init__()

        # ---------- Вікно ----------
        self.title("Telescam — Чат")
        self.geometry("1200x700")
        self.minsize(1100, 620)

        # ---------- Чати ----------
        self.current_chat = "Основний"
        self.CHAT_FILES = {
            "Основний": "main.txt",
            "Збережені": "saved.txt"
        }

        # ---------- Мережа ----------
        self.host = host
        self.port = port
        self.username = "Artem"
        self.sock = None
        self.connected = False

        # ---------- Музика ----------
        pygame.mixer.init()
        self.music_file = None
        self.volume = 0.5
        self.is_music_playing = False

        # ---------- Анімаційне меню ----------
        self.menu_width = 0
        self.menu_open = False
        self.target_width = 240
        self.menu_speed = 12

        self.menu_frame = CTkFrame(self, width=0, height=self.winfo_height())
        self.menu_frame.place(x=0, y=0)
        self.menu_frame.pack_propagate(False)

        # ---------- Полотно з бульбашками ----------
        self.bubble_canvas = CTkCanvas(
            self.menu_frame,
            width=0,
            height=self.winfo_height(),
            bg="#2b2b2b",
            highlightthickness=0
        )
        self.bubble_canvas.place(x=0, y=0)

        self.bubbles = []
        for _ in range(14):
            x = random.randint(20, 220)
            y = random.randint(0, 700)
            radius = random.randint(6, 18)
            speed = random.uniform(0.4, 1.2)
            self.bubbles.append(Bubble(self.bubble_canvas, x, y, radius, speed))

        self.animate_bubbles()

        # ---------- Побудова меню ----------
        self._build_menu()

        # ---------- Кнопка відкриття меню ----------
        self.toggle_btn = CTkButton(self, text="≡", width=40, height=40, command=self.toggle_menu)
        self.toggle_btn.place(x=10, y=10)

        # ---------- Поле чату ----------
        self.chat_text = CTkTextbox(self, state="disabled", width=700, height=500)
        self.chat_text.place(x=60, y=80)

        self.message_input = CTkEntry(self, placeholder_text="Введіть повідомлення...", width=620)
        self.message_input.place(x=60, y=600)

        self.send_btn = CTkButton(self, text="➤", width=40, height=36, command=self.send_message)
        self.send_btn.place(x=690, y=596)

        self.sticker_btn = CTkButton(self, text="😀", width=40, height=36, command=self.open_stickers)
        self.sticker_btn.place(x=740, y=596)

        # ---------- Статус ----------
        self.status_label = CTkLabel(
            self,
            text=f"Чат: {self.current_chat} | Користувач: {self.username} — {self.host}:{self.port}"
        )
        self.status_label.place(x=60, y=50)

        # ---------- Завантаження історії ----------
        self.load_chat_messages()

        # Постійне оновлення інтерфейсу
        self.after(15, self.adaptive_ui)

    # ---------------------------------------------------------
    #   Анімація бульбашок
    # ---------------------------------------------------------
    def animate_bubbles(self):
        h = self.menu_frame.winfo_height()
        for b in self.bubbles:
            b.move(h)
        self.after(45, self.animate_bubbles)

    # ---------------------------------------------------------
    #   Побудова лівого меню
    # ---------------------------------------------------------
    def _build_menu(self):
        for w in self.menu_frame.winfo_children():
            if w != self.bubble_canvas:
                w.destroy()

        CTkLabel(self.menu_frame, text="Меню", font=("Arial", 17, "bold")).pack(pady=12)

        # Ім’я
        CTkLabel(self.menu_frame, text="Ім'я:").pack()
        self.entry_name = CTkEntry(self.menu_frame, placeholder_text=self.username)
        self.entry_name.pack(padx=10, pady=5, fill="x")

        self.connect_btn = CTkButton(self.menu_frame, text="Підключитися", command=self.connect_or_set_name)
        self.connect_btn.pack(padx=10, pady=6, fill="x")

        self.connect_status = CTkLabel(self.menu_frame, text="Не підключено", text_color="red")
        self.connect_status.pack()

        # Чати
        CTkLabel(self.menu_frame, text="Чати").pack(pady=6)

        panel = CTkFrame(self.menu_frame)
        panel.pack(padx=10, pady=4, fill="x")

        CTkButton(panel, text="Основний", command=lambda: self.switch_chat("Основний")).pack(side="left", expand=True)
        CTkButton(panel, text="Збережені", command=lambda: self.switch_chat("Збережені")).pack(side="right", expand=True)

        CTkLabel(self.menu_frame, text="──────────").pack(pady=10)

        # Музика
        CTkLabel(self.menu_frame, text="Музика").pack()

        CTkButton(self.menu_frame, text="📂 Обрати файл", command=self.choose_music).pack(padx=10, pady=4, fill="x")
        CTkButton(self.menu_frame, text="▶ / ■ Вкл/Викл", command=self.toggle_music).pack(padx=10, pady=4, fill="x")

        self.volume_label = CTkLabel(self.menu_frame, text=f"🔊 Гучність: {int(self.volume*100)}%")
        self.volume_label.pack()

        self.volume_slider = CTkSlider(self.menu_frame, from_=0, to=1, command=self.set_volume)
        self.volume_slider.set(self.volume)
        self.volume_slider.pack(padx=10, pady=6, fill="x")

        CTkLabel(self.menu_frame, text="──────────").pack(pady=10)

        # Тема
        CTkLabel(self.menu_frame, text="Тема").pack()

        theme = CTkOptionMenu(self.menu_frame, values=["Темна", "Світла"], command=self.change_theme)
        theme.set("Темна")
        theme.pack(padx=10, pady=6, fill="x")

    # ---------------------------------------------------------
    #   Анімація відкриття меню
    # ---------------------------------------------------------
    def toggle_menu(self):
        self.menu_open = not self.menu_open
        self._build_menu()
        self.animate_menu()

    def animate_menu(self):
        step = self.menu_speed if self.menu_open else -self.menu_speed
        new_w = self.menu_width + step

        if 0 <= new_w <= self.target_width:
            self.menu_width = new_w
            self.after(10, self.animate_menu)
        else:
            self.menu_width = self.target_width if self.menu_open else 0

    # ---------------------------------------------------------
    #   Підключення
    # ---------------------------------------------------------
    def connect_or_set_name(self):
        name = self.entry_name.get().strip()
        if not name:
            messagebox.showwarning("Помилка", "Введіть ім'я!")
            return

        if not self.connected:
            self.username = name
            threading.Thread(target=self.connect_to_server, daemon=True).start()
        else:
            old = self.username
            self.username = name
            self.add_message(f"[SYSTEM] {old} змінив ім'я на {name}")

    def connect_to_server(self):
        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect((self.host, self.port))

            msg = f"TEXT@{self.username}@[SYSTEM] {self.username} приєднався!\n"
            self.sock.sendall(msg.encode())

            self.connected = True
            self.connect_status.configure(text="Підключено", text_color="green")
            self.connect_btn.configure(text="Оновити ім'я")

            threading.Thread(target=self.receive_messages, daemon=True).start()

        except:
            self.connect_status.configure(text="Помилка", text_color="red")

    def receive_messages(self):
        buf = ""
        while True:
            try:
                data = self.sock.recv(4096)
                if not data:
                    break

                buf += data.decode()

                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    self.process_message(line.strip())

            except:
                break

        self.connected = False
        self.connect_status.configure(text="Відключено", text_color="red")
        self.add_message("[SYSTEM] З'єднання розірвано")

    def process_message(self, line):
        if not line:
            return

        parts = line.split("@")

        if len(parts) >= 3 and parts[0] == "TEXT":
            user = parts[1]
            text = parts[2]
            msg = f"{user}: {text}"
        else:
            msg = line

        self.save_message(msg, "Основний")

        if self.current_chat == "Основний":
            self.add_message(msg)

    # ---------------------------------------------------------
    #   Робота з чатом
    # ---------------------------------------------------------
    def send_message(self):
        text = self.message_input.get().strip()
        if not text:
            return

        final = f"{self.username}: {text}"

        self.add_message(final)
        self.save_message(final)

        if self.connected and self.current_chat == "Основний":
            msg = f"TEXT@{self.username}@{text}\n"
            self.sock.sendall(msg.encode())

        self.message_input.delete(0, "end")

    def add_message(self, msg):
        self.chat_text.configure(state="normal")
        self.chat_text.insert("end", msg + "\n")
        self.chat_text.configure(state="disabled")
        self.chat_text.see("end")

    def save_message(self, msg, chat=None):
        fname = self.CHAT_FILES.get(chat or self.current_chat)
        try:
            with open(fname, "a", encoding="utf-8") as f:
                f.write(msg + "\n")
        except:
            pass

    def load_chat_messages(self):
        fname = self.CHAT_FILES[self.current_chat]

        self.chat_text.configure(state="normal")
        self.chat_text.delete("1.0", "end")

        if os.path.exists(fname):
            with open(fname, "r", encoding="utf-8") as f:
                self.chat_text.insert("end", f.read())

        self.chat_text.configure(state="disabled")

    def switch_chat(self, chat_name):
        self.current_chat = chat_name
        self.load_chat_messages()
        self.status_label.configure(
            text=f"Чат: {chat_name} | Користувач: {self.username} — {self.host}:{self.port}"
        )
        if self.menu_open:
            self.toggle_menu()

    # ---------------------------------------------------------
    #   Стікери
    # ---------------------------------------------------------
    def open_stickers(self):
        win = CTkToplevel(self)
        win.title("Стікери")
        win.geometry("420x200")

        stickers = [
            "😀", "😃", "😄", "😁", "😆", "😂", "🤣", "😊",
            "😇", "🙂", "🙃", "😉", "😍", "🥰", "😘",
            "😋", "😛", "😜", "🤪", "🤩"
        ]

        for i, s in enumerate(stickers):
            CTkButton(win, text=s, width=40, height=40,
                      command=lambda x=s: self.send_sticker(x)).grid(
                row=i // 10, column=i % 10, padx=5, pady=5
            )

    def send_sticker(self, s):
        msg = f"{self.username} відправив стікер: {s}"
        self.add_message(msg)
        self.save_message(msg)

        if self.connected and self.current_chat == "Основний":
            self.sock.sendall(f"TEXT@{self.username}@[Стікер] {s}\n".encode())

    # ---------------------------------------------------------
    #   Музика
    # ---------------------------------------------------------
    def choose_music(self):
        path = filedialog.askopenfilename(
            filetypes=[("Аудіо файли", "*.mp3 *.wav *.ogg")]
        )
        if path:
            self.music_file = path
            self.add_message(f"🎵 Обрано файл: {os.path.basename(path)}")

    def toggle_music(self):
        if not self.music_file:
            self.add_message("⚠ Спочатку оберіть файл музики!")
            return

        if not self.is_music_playing:
            pygame.mixer.music.load(self.music_file)
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play(-1)
            self.is_music_playing = True
            self.add_message("▶ Музику увімкнено")
        else:
            pygame.mixer.music.stop()
            self.is_music_playing = False
            self.add_message("■ Музику вимкнено")

    def set_volume(self, v):
        self.volume = float(v)
        pygame.mixer.music.set_volume(self.volume)
        self.volume_label.configure(text=f"🔊 Гучність: {int(self.volume*100)}%")

    # ---------------------------------------------------------
    #   Тема
    # ---------------------------------------------------------
    def change_theme(self, mode):
        set_appearance_mode("dark" if mode == "Темна" else "light")

    # ---------------------------------------------------------
    #   Адаптація інтерфейсу
    # ---------------------------------------------------------
    def adaptive_ui(self):
        try:
            self.menu_frame.configure(width=self.menu_width, height=self.winfo_height())
            self.bubble_canvas.configure(width=self.menu_width, height=self.winfo_height())

            shift = self.menu_width + 60

            self.chat_text.place(x=shift, y=80)
            self.message_input.place(x=shift, y=600)
            self.send_btn.place(x=shift + 630, y=596)
            self.sticker_btn.place(x=shift + 680, y=596)
            self.status_label.place(x=shift, y=50)

        except:
            pass

        self.after(15, self.adaptive_ui)


# ---------------------------------------------------------
#   Запуск програми
# ---------------------------------------------------------
if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
