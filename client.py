import customtkinter as ctk
import os

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

FILES = {"Основний": "main.txt", "Збережені": "saved.txt"}

class ChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Чат")
        self.geometry("500x400")
        self.current_chat = "Основний"

        # Кнопки переключения чатов
        self.btn_frame = ctk.CTkFrame(self, height=50)
        self.btn_frame.pack(fill="x")
        for chat in FILES:
            ctk.CTkButton(self.btn_frame, text=chat, command=lambda c=chat: self.switch_chat(c)).pack(side="left", padx=5, pady=5)

        # Область сообщений
        self.chat_box = ctk.CTkTextbox(self, state="disabled")
        self.chat_box.pack(fill="both", expand=True, padx=10, pady=5)

        # Поле ввода и кнопка отправки
        self.entry = ctk.CTkEntry(self)
        self.entry.pack(fill="x", padx=10, pady=(0,5))
        self.entry.bind("<Return>", lambda e: self.send_message())
        ctk.CTkButton(self, text="Відправити", command=self.send_message).pack(pady=(0,5))

        self.load_messages()

    def switch_chat(self, chat_name):
        self.current_chat = chat_name
        self.load_messages()

    def load_messages(self):
        self.chat_box.configure(state="normal")
        self.chat_box.delete("1.0", "end")
        if os.path.exists(FILES[self.current_chat]):
            with open(FILES[self.current_chat], "r", encoding="utf-8") as f:
                self.chat_box.insert("end", f.read())
        self.chat_box.configure(state="disabled")

    def send_message(self):
        text = self.entry.get().strip()
        if text:
            with open(FILES[self.current_chat], "a", encoding="utf-8") as f:
                f.write(text + "\n")
            self.entry.delete(0, "end")
            self.load_messages()

if __name__ == "__main__":
    app = ChatApp()
    app.mainloop()