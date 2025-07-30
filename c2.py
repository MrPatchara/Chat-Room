import customtkinter as ctk
import tkinter as tk
from tkinter import scrolledtext
import socketio

# สร้าง client
sio = socketio.Client()

# ฟังก์ชันเชื่อมต่อเซิร์ฟเวอร์
def connect_to_server():
    server_url = server_entry.get()
    try:
        sio.connect(server_url)
        chat_window.insert(tk.END, f"✅ Connected to {server_url}\n")
        connect_button.configure(state=ctk.DISABLED)
    except Exception as e:
        chat_window.insert(tk.END, f"❌ Error connecting to server: {e}\n")

# socket.io event
@sio.on('room_created')
def on_room_created(data):
    chat_window.insert(tk.END, f"{data['message']}\n")

@sio.on('room_joined')
def on_room_joined(data):
    chat_window.insert(tk.END, f"{data['message']}\n")
    send_button.configure(state=ctk.NORMAL)

@sio.on('room_error')
def on_room_error(data):
    chat_window.insert(tk.END, f"Error: {data['message']}\n")

@sio.on('receive_message')
def on_receive_message(data):
    chat_window.insert(tk.END, f"{data['username']}: {data['message']}\n")
    chat_window.yview_moveto(1.0)

# ฟังก์ชันต่างๆ
def create_room():
    username = username_entry.get()
    room = room_entry.get()
    code = code_entry.get()
    if username and room and code:
        sio.emit('create_or_join', {'username': username, 'room': room, 'code': code, 'is_new_room': True})
    else:
        chat_window.insert(tk.END, "⚠️ Enter username, room name, and code to create a room.\n")

def join_room():
    username = username_entry.get()
    room = room_entry.get()
    code = code_entry.get()
    if username and room and code:
        sio.emit('create_or_join', {'username': username, 'room': room, 'code': code, 'is_new_room': False})
    else:
        chat_window.insert(tk.END, "⚠️ Enter username, room name, and code to join a room.\n")

def send_message(event=None):
    username = username_entry.get()
    room = room_entry.get()
    message = message_entry.get()
    if username and room and message:
        sio.emit('send_message', {'username': username, 'room': room, 'message': message})
        message_entry.delete(0, ctk.END)
    else:
        chat_window.insert(tk.END, "⚠️ Enter a message to send.\n")

def paste_clipboard(event=None):
    try:
        server_entry.insert("insert", server_entry.clipboard_get())
    except:
        pass

# ตั้งค่าธีม
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# สร้างหน้าต่างหลัก
root = ctk.CTk()
root.title("☠ DarkNet Chat Room ☠")
root.geometry("650x600")
root.configure(bg="#0f0f0f")
font_mono = ("Consolas", 12)

# Frame 1: Connection
connection_frame = ctk.CTkFrame(root, fg_color="#1a1a1a")
connection_frame.pack(pady=10, padx=10, fill="x")

server_label = ctk.CTkLabel(connection_frame, text="Server URL:", font=font_mono, text_color="#00FF00")
server_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
server_entry = ctk.CTkEntry(connection_frame, width=300, font=font_mono, placeholder_text="http://127.0.0.1:5000")
server_entry.grid(row=0, column=1, padx=5, pady=5)

connect_button = ctk.CTkButton(connection_frame, text="Connect", command=connect_to_server, font=font_mono, text_color="#0f0")
connect_button.grid(row=0, column=2, padx=5, pady=5)

# Frame 2: Room Info
frame = ctk.CTkFrame(root, fg_color="#1a1a1a")
frame.pack(pady=10, padx=10, fill="x")

username_label = ctk.CTkLabel(frame, text="Username:", font=font_mono, text_color="#00FF00")
username_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
username_entry = ctk.CTkEntry(frame, width=200, font=font_mono)
username_entry.grid(row=0, column=1, padx=5, pady=5)

room_label = ctk.CTkLabel(frame, text="Room:", font=font_mono, text_color="#00FF00")
room_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
room_entry = ctk.CTkEntry(frame, width=200, font=font_mono)
room_entry.grid(row=1, column=1, padx=5, pady=5)

code_label = ctk.CTkLabel(frame, text="Room Code:", font=font_mono, text_color="#00FF00")
code_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
code_entry = ctk.CTkEntry(frame, width=200, show="*", font=font_mono)
code_entry.grid(row=2, column=1, padx=5, pady=5)

create_button = ctk.CTkButton(frame, text="☠ Create Room", command=create_room, font=font_mono, text_color="#0f0")
create_button.grid(row=3, column=0, padx=5, pady=10)
join_button = ctk.CTkButton(frame, text="✔ Join Room", command=join_room, font=font_mono, text_color="#0f0")
join_button.grid(row=3, column=1, padx=5, pady=10)

# Chat window
chat_window = scrolledtext.ScrolledText(root, wrap="word", height=15, width=70, bg="#0d0d0d", fg="#00FF00", insertbackground="#00FF00", font=font_mono)
chat_window.pack(padx=10, pady=10, fill="both", expand=True)
chat_window.insert(tk.END, "💀 Waiting for server connection...\n")

# Message input
message_entry = ctk.CTkEntry(root, placeholder_text="> Type your message...", font=font_mono)
message_entry.pack(padx=10, pady=10, fill="x")
message_entry.bind('<Return>', send_message)

# Send button
send_button = ctk.CTkButton(root, text="➤ Send", command=send_message, state=ctk.DISABLED, font=font_mono, text_color="#0f0")
send_button.pack(padx=10, pady=10)

server_entry.bind("<Control-v>", lambda e: server_entry.insert("insert", e.widget.clipboard_get()))


root.mainloop()
