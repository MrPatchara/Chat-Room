import customtkinter as ctk
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox
import socketio
from PIL import Image, ImageTk, ImageSequence

# --- Socket.IO client ---
sio = socketio.Client()

# --- Global variables ---
server_url = ""
username = ""

users_listbox = None
rooms_listbox = None
chat_window = None
send_button = None
message_entry = None
room_entry = None
code_entry = None
join_button = None

# ----------------- SOCKET.IO EVENT -----------------
@sio.on('room_created')
def on_room_created(data):
    chat_window.insert(tk.END, f"{data['message']}\n")
    room_name = data.get('room')
    if room_name and room_name not in rooms_listbox.get(0, tk.END):
        rooms_listbox.insert(tk.END, room_name)
    join_button.configure(state=ctk.NORMAL)

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

# อัปเดตห้อง
@sio.on('update_rooms')
def on_update_rooms(data):
    rooms = data.get('rooms', [])
    if rooms_listbox:
        rooms_listbox.delete(0, tk.END)
        for r in rooms:
            rooms_listbox.insert(tk.END, r)
        if rooms:
            join_button.configure(state=ctk.NORMAL)

# อัปเดตผู้ใช้ออนไลน์
@sio.on('update_users')
def on_update_users(data):
    users = data.get('users', [])
    if users_listbox:
        users_listbox.delete(0, tk.END)
        for u in users:
            users_listbox.insert(tk.END, u)

# ----------------- FUNCTION -----------------
def ask_admin_code():
    popup = ctk.CTkToplevel()
    popup.title("☠ Admin Verification ☠")
    popup.geometry("350x180")
    popup.configure(fg_color="#121212")
    popup.grab_set()  # focus ที่ popup

    # หัวข้อ
    ctk.CTkLabel(popup, text="Enter Admin Code", 
                 font=("Consolas", 14, "bold"), text_color="#05ff1c").pack(pady=(20, 10))

    # ช่องใส่รหัส
    code_entry = ctk.CTkEntry(popup, width=200, fg_color="#1a1a1a", 
                              text_color="#ff7f00", show="*", font=("Consolas", 12))
    code_entry.pack(pady=5)
    code_entry.focus_set()

    # เก็บผลลัพธ์
    admin_code_result = {"value": None}

    # ปุ่มกด
    def confirm():
        admin_code_result["value"] = code_entry.get().strip()
        popup.destroy()

    def cancel():
        admin_code_result["value"] = None
        popup.destroy()

    button_frame = ctk.CTkFrame(popup, fg_color="#121212")
    button_frame.pack(pady=15)

    ctk.CTkButton(button_frame, text="OK", command=confirm,
                  fg_color="#222244", hover_color="#4444ff",
                  text_color="#aaaaff", width=80).pack(side="left", padx=5)

    ctk.CTkButton(button_frame, text="Cancel", command=cancel,
                  fg_color="#331122", hover_color="#ff2255",
                  text_color="#ff4477", width=80).pack(side="left", padx=5)

    popup.wait_window()
    return admin_code_result["value"]



def ask_room_code(room_name: str):
    """
    Popup สำหรับใส่รหัสเข้าห้อง (DarkWeb Retro)
    return: str | None (None ถ้ากดยกเลิก)
    """
    popup = ctk.CTkToplevel()
    popup.title("☠ Room Code ☠")
    popup.geometry("350x180")
    popup.configure(fg_color="#121212")
    popup.grab_set()  # focus popup

    # หัวข้อ
    ctk.CTkLabel(
        popup,
        text=f"Enter code for room '{room_name}'",
        font=("Consolas", 14, "bold"),
        text_color="#ff00aa"
    ).pack(pady=(20, 10))

    # ช่องใส่รหัส
    code_entry = ctk.CTkEntry(
        popup,
        width=200,
        fg_color="#1a1a1a",
        text_color="#ff00aa",
        show="*",
        font=("Consolas", 12)
    )
    code_entry.pack(pady=5)
    code_entry.focus_set()

    # เก็บผลลัพธ์
    code_result = {"value": None}

    # ปุ่มกด
    def confirm(event=None):
        code_result["value"] = code_entry.get().strip()
        popup.destroy()

    def cancel():
        code_result["value"] = None
        popup.destroy()

    # ปุ่ม OK / Cancel
    button_frame = ctk.CTkFrame(popup, fg_color="#121212")
    button_frame.pack(pady=15)

    ctk.CTkButton(
        button_frame, text="OK", command=confirm,
        fg_color="#222244", hover_color="#4444ff",
        text_color="#aaaaff", width=80
    ).pack(side="left", padx=5)

    ctk.CTkButton(
        button_frame, text="Cancel", command=cancel,
        fg_color="#331122", hover_color="#ff2255",
        text_color="#ff4477", width=80
    ).pack(side="left", padx=5)

    # ✅ Bind Enter key ให้กดแล้วเท่ากับกด OK
    popup.bind("<Return>", confirm)

    popup.wait_window()
    return code_result["value"]

# ----------------- FUNCTION -----------------
def create_room():
    room = room_entry.get().strip()
    code = code_entry.get().strip()

    if not username:
        chat_window.insert(tk.END, "⚠️ Please login first.\n")
        return

    if not room:
        chat_window.insert(tk.END, "⚠️ Enter a room name.\n")
        return

    if not code:
        chat_window.insert(tk.END, "⚠️ Enter a room code to create a room.\n")
        return

    # Popup ขอรหัส admin
    admin_code = ask_admin_code()
    if not admin_code:
        chat_window.insert(tk.END, "⚠️ Room creation canceled. Admin code required.\n")
        return


    # ส่งข้อมูลไป server
    sio.emit('create_or_join', {
        'username': username,
        'room': room,
        'code': code,
        'is_new_room': True,
        'admin_code': admin_code
    })


def join_room(room_name=None):
    global username
    if room_name is None:
        selection = rooms_listbox.curselection()
        if selection:
            room_name = rooms_listbox.get(selection[0])
        else:
            chat_window.insert(tk.END, "⚠️ Select a room to join.\n")
            return
    code = ask_room_code(room_name)
    if username and room_name and code:
        sio.emit('create_or_join', {
            'username': username,
            'room': room_name,
            'code': code,
            'is_new_room': False
        })
        room_entry.delete(0, tk.END)
        room_entry.insert(0, room_name)
    else:
        chat_window.insert(tk.END, "⚠️ Enter username, room name, and code to join a room.\n")

def send_message(event=None):
    message = message_entry.get()
    room = room_entry.get()
    if username and room and message:
        sio.emit('send_message', {'username': username, 'room': room, 'message': message})
        message_entry.delete(0, ctk.END)
    else:
        chat_window.insert(tk.END, "⚠️ Enter a message to send.\n")

def on_room_double_click(event):
    selection = rooms_listbox.curselection()
    if selection:
        room_name = rooms_listbox.get(selection[0])
        room_entry.delete(0, tk.END)
        room_entry.insert(0, room_name)
        join_room(room_name)

def delete_room():
    selection = rooms_listbox.curselection()
    if not selection:
        chat_window.insert(tk.END, "⚠️ Please select a room to delete.\n")
        return

    room = rooms_listbox.get(selection[0])

    # Popup ขอรหัส admin
    admin_code = ask_admin_code()
    if not admin_code:
        chat_window.insert(tk.END, "⚠️ Room deletion canceled. Admin code required.\n")
        return
    # ส่งคำสั่งลบห้องไปยัง server
    sio.emit('delete_room', {
        'room': room,
        'admin_code': admin_code
    })
    

# Event รับแจ้งว่าห้องถูกลบ
@sio.on('room_deleted')
def on_room_deleted(data):
    chat_window.insert(tk.END, f"⚠️ {data['message']}\n")

# ----------------- GUI -----------------
ctk.set_appearance_mode("Dark")  # โหมดมืด
ctk.set_default_color_theme("dark-blue")  # สีธีมมืด

root = ctk.CTk()
root.withdraw()  # ซ่อนหน้าหลักก่อน
font_mono = ("Consolas", 12)

# ----- LOGIN WINDOW ----- 
login_window = ctk.CTkToplevel()
login_window.title("☠ THE RIVER - CHAT ☠")
login_window.geometry("300x350")
login_window.grab_set()

# เพิ่มกรอบด้านใน
login_frame = ctk.CTkFrame(login_window, fg_color="#121212", corner_radius=10)
login_frame.pack(padx=20, pady=30, fill="both", expand=True)

# หัวข้อสไตล์ Retro Hacker
ctk.CTkLabel(login_frame, text="💀 THE CIRCLE 💀", 
             font=("Consolas", 18, "bold"), text_color="#05ff1c").pack(pady=15)

# Username
ctk.CTkLabel(login_frame, text="Username:", font=("Consolas", 12), 
             text_color="#05ff1c").pack(pady=(10, 0))
username_entry = ctk.CTkEntry(login_frame, width=220, fg_color="#1a1a1a", 
                              text_color="#05ff1c", font=("Consolas", 12))
username_entry.pack(pady=5)

# Server URL
ctk.CTkLabel(login_frame, text="Server URL:", font=("Consolas", 12), 
             text_color="#ff7f00").pack(pady=(10, 0))
server_entry = ctk.CTkEntry(login_frame, width=220, fg_color="#1a1a1a", 
                            text_color="#ff7f00", font=("Consolas", 12))
server_entry.pack(pady=5)

# ปุ่ม Connect สไตล์ Hacker
def connect_and_open_main():
    global server_url, username
    server_url = server_entry.get().strip()
    username = username_entry.get().strip()
    if not server_url or not username:
        messagebox.showwarning("Warning", "Please enter Server URL and Username")
        return
    try:
        sio.connect(server_url)
        sio.emit('login', {'username': username})  # ส่ง username ให้ server
        login_window.destroy()
        show_main_window()
    except Exception as e:
        messagebox.showerror("Connection Error", str(e))

ctk.CTkButton(login_frame, text="☠ Connect", command=connect_and_open_main,
              fg_color="#222244", hover_color="#4444ff",
              text_color="#aaaaff", font=("Consolas", 12, "bold"), 
              corner_radius=10, width=200).pack(pady=20)

# เอฟเฟกต์ไฟกระพริบ (Retro)
def blink_title():
    current = login_window.title()
    if "☠" in current:
        login_window.title("the river<3>")
    else:
        login_window.title("☠ Login ☠")
    login_window.after(800, blink_title)

blink_title()


# ----- MAIN CHAT WINDOW -----
def show_main_window():
    global chat_window, send_button, message_entry, room_entry, code_entry
    global rooms_listbox, users_listbox, join_button, right_frame

    root.deiconify()
    root.title("☠ the river<3>")
    root.geometry("1000x650")
    root.configure(bg="#0b0b0b")  # ฉากหลังมืด

    # ----- LEFT PANEL -----
    left_frame = ctk.CTkFrame(root, fg_color="#0b0b0b", width=260, corner_radius=10)
    left_frame.pack(side="left", fill="y", padx=8, pady=8)

    # --- Online Users ---
    top_frame = ctk.CTkFrame(left_frame, fg_color="#121212", corner_radius=10)
    top_frame.pack(side="top", fill="both", expand=True, padx=4, pady=4)

    ctk.CTkLabel(top_frame, text="🟢 Online Users", font=("Consolas", 13, "bold"), text_color="#05ff1c").pack(pady=5)
    users_listbox = tk.Listbox(top_frame,
                               bg="#050505", fg="#05ff1c",
                               font=("Consolas", 12),
                               selectbackground="#1f1f1f", selectforeground="#00ff99",
                               highlightthickness=0, bd=0)
    users_listbox.pack(fill="both", expand=True, padx=6, pady=6)

    # --- Available Rooms ---
    bottom_frame = ctk.CTkFrame(left_frame, fg_color="#121212", corner_radius=10)
    bottom_frame.pack(side="bottom", fill="both", expand=True, padx=4, pady=4)

    ctk.CTkLabel(bottom_frame, text="💀 Rooms", font=("Consolas", 13, "bold"), text_color="#ff00aa").pack(pady=5)
    rooms_listbox = tk.Listbox(bottom_frame,
                               bg="#050505", fg="#ff00aa",
                               font=("Consolas", 12),
                               selectbackground="#1f1f1f", selectforeground="#ff66cc",
                               highlightthickness=0, bd=0)
    rooms_listbox.pack(fill="both", expand=True, padx=6, pady=6)
    rooms_listbox.bind("<Double-1>", on_room_double_click)

    join_button = ctk.CTkButton(bottom_frame, text="Join Room", command=join_room,
                                fg_color="#333333", hover_color="#00ff99", text_color="#05ff1c",
                                corner_radius=10)
    join_button.pack(pady=5)
    join_button.configure(state=ctk.DISABLED)

    delete_button = ctk.CTkButton(bottom_frame, text="Delete Room", command=delete_room,
                                  fg_color="#331122", hover_color="#ff2255", text_color="#ff4477",
                                  corner_radius=10)
    delete_button.pack(pady=5)

    # ----- RIGHT PANEL -----
    right_frame = ctk.CTkFrame(root, fg_color="#0b0b0b")
    right_frame.pack(side="right", fill="both", expand=True, padx=8, pady=8)

    # --- Room Creation + GIF ---
    room_frame = ctk.CTkFrame(right_frame, fg_color="#121212", corner_radius=10)
    room_frame.pack(pady=10, fill="x")

    # เฟรมภายในสำหรับจัดซ้าย-ขวา
    room_inner_frame = tk.Frame(room_frame, bg="#121212")
    room_inner_frame.pack(fill="x", padx=5, pady=5)

    # ฟอร์มสร้างห้อง (ซ้าย)
    room_form = tk.Frame(room_inner_frame, bg="#121212")
    room_form.pack(side="left", anchor="w")

    ctk.CTkLabel(room_form, text="Room:", font=("Consolas", 12), text_color="#05ff1c").grid(row=0, column=0, padx=5, pady=5)
    room_entry = ctk.CTkEntry(room_form, width=160, font=("Consolas", 12),
                            fg_color="#1a1a1a", text_color="#05ff1c")
    room_entry.grid(row=0, column=1, padx=5, pady=5)

    ctk.CTkLabel(room_form, text="Room Code:", font=("Consolas", 12), text_color="#ff00aa").grid(row=1, column=0, padx=5, pady=5)
    code_entry = ctk.CTkEntry(room_form, width=160, show="*", font=("Consolas", 12),
                            fg_color="#1a1a1a", text_color="#ff00aa")
    code_entry.grid(row=1, column=1, padx=5, pady=5)

    ctk.CTkButton(room_form, text="☠ Create Room", command=create_room,
                fg_color="#222244", hover_color="#4444ff", text_color="#aaaaff",
                font=("Consolas", 12, "bold"), corner_radius=10).grid(row=2, column=0, padx=5, pady=10)

    # --- GIF ด้านขวา ---
    from PIL import Image, ImageTk, ImageSequence

    gif_path = "your_animation.gif"  # เปลี่ยนเป็นชื่อไฟล์จริง
    gif_img = Image.open(gif_path)

    # ขนาดใหม่ของ gif
    new_size = (550, 200)  # ปรับตามต้องการ เช่น (กว้าง, สูง)

    frames = [
        ImageTk.PhotoImage(frame.copy().convert("RGBA").resize(new_size, Image.LANCZOS))
        for frame in ImageSequence.Iterator(gif_img)
    ]

    gif_label = tk.Label(room_inner_frame, bg="#121212")
    gif_label.pack(side="right", padx=10, pady=5)

    def update_gif(frame_index=0):
        frame = frames[frame_index]  # เลือกเฟรมปัจจุบัน
        gif_label.configure(image=frame)  # อัปเดตภาพใน Label
        gif_label.image = frame          # เก็บอ้างอิงเพื่อไม่ให้ถูกเก็บขยะ
        root.after(100, update_gif, (frame_index + 1) % len(frames))

    update_gif()

    # --- Chat Window ---
    chat_window = scrolledtext.ScrolledText(right_frame, wrap="word", height=18, width=75,
                                           bg="#1d1d1d",  # พื้นหลังเข้ม
                                           fg="#ff7f00",  # ข้อความสีส้ม
                                           insertbackground="#a51300",  # เคอร์เซอร์ส้มแดง
                                           font=("Consolas", 12), borderwidth=0)
    chat_window.pack(padx=12, pady=12, fill="both", expand=True)
    chat_window.insert(tk.END, f"💀 Connected as {username} to {server_url}\n")

    # --- Message Input ---
    message_entry = ctk.CTkEntry(right_frame, placeholder_text="> Type your message...",
                                 font=("Consolas", 12), fg_color="#1a1a1a", text_color="#ff7f00")
    message_entry.pack(padx=12, pady=8, fill="x")
    message_entry.bind('<Return>', send_message)

    send_button = ctk.CTkButton(right_frame, text="➤ Send", command=send_message,
                                state=ctk.DISABLED, fg_color="#333333", hover_color="#ff7f00",
                                text_color="#ff7f00", corner_radius=10)
    send_button.pack(padx=12, pady=8)


root.mainloop()
