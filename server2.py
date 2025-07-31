import time
from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# เก็บห้องและรหัส
rooms_with_codes = {}
# เก็บผู้ใช้ออนไลน์ {sid: username}
online_users = {}

# ----------------- Helper Functions -----------------
def broadcast_rooms():
    """ส่งรายชื่อห้องไปให้ทุกคน"""
    socketio.emit('update_rooms', {'rooms': list(rooms_with_codes.keys())})

def broadcast_users():
    """ส่งรายชื่อผู้ใช้ออนไลน์ไปให้ทุกคน"""
    socketio.emit('update_users', {'users': list(online_users.values())})

def send_periodic_user_updates():
    """ส่งข้อมูลผู้ใช้ออนไลน์ทุกๆ 5 วินาที"""
    while True:
        broadcast_users()  # ส่งข้อมูลผู้ใช้ออนไลน์
        time.sleep(5)  # 5 วินาที

def send_periodic_room_updates():
    """ส่งข้อมูลห้องทุกๆ 5 วินาที"""
    while True:
        broadcast_rooms()  # ส่งข้อมูลห้อง
        time.sleep(5)  # 5 วินาที

# ----------------- Events -----------------
@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")
    # เริ่มส่งข้อมูลผู้ใช้ออนไลน์อัตโนมัติ
    socketio.start_background_task(send_periodic_user_updates)
    socketio.start_background_task(send_periodic_room_updates)  # เริ่มส่งข้อมูลห้องทุกๆ 30 วินาที

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in online_users:
        username = online_users[request.sid]
        del online_users[request.sid]
        print(f"User {username} disconnected.")

        # ส่งข้อมูลผู้ใช้ออนไลน์หลังจากมีคนออกจากระบบ
        broadcast_users()

@socketio.on('login')
def handle_login(data):
    """Client ส่ง username เข้ามาเมื่อกด Connect"""
    username = data.get('username')
    if username:
        online_users[request.sid] = username
        print(f"User {username} logged in with SID {request.sid}")

        # ส่งรายชื่อ users และ rooms ให้ทุกคนทันที
        broadcast_users()
        broadcast_rooms()

SECRET_ADMIN_CODE = "admin"  # รหัสลับสำหรับสร้างห้อง

@socketio.on('create_or_join')
def create_or_join(data):
    username = data['username']
    room = data['room']
    code = data.get('code')
    is_new_room = data.get('is_new_room', False)

    # ถ้าเป็นการสร้างห้องใหม่
    if is_new_room:
        admin_code = data.get('admin_code')  # รับรหัสลับจาก client
        if admin_code != SECRET_ADMIN_CODE:
            emit('room_error', {'message': 'Unauthorized: Admin code required to create a room.'}, to=request.sid)
            return

        if room in rooms_with_codes:
            emit('room_error', {'message': 'Room already exists. Choose a different name.'}, to=request.sid)
        else:
            rooms_with_codes[room] = code
            join_room(room)
            emit('room_created', {'message': f"Room '{room}' created successfully!", 'room': room}, to=request.sid)
            broadcast_rooms()
    else:
        # join room ปกติ
        if room not in rooms_with_codes:
            emit('room_error', {'message': 'Room does not exist.'}, to=request.sid)
        elif rooms_with_codes[room] != code:
            emit('room_error', {'message': 'Incorrect room code.'}, to=request.sid)
        else:
            join_room(room)
            emit('room_joined', {'message': f"{username} joined room: {room}"}, to=request.sid)
            emit('room_joined', {'message': f"{username} joined the room!"}, to=room)

@socketio.on('delete_room')
def delete_room(data):
    room = data.get('room')
    admin_code = data.get('admin_code')

    if admin_code != SECRET_ADMIN_CODE:
        emit('room_error', {'message': 'Unauthorized: Admin code required to delete room.'}, to=request.sid)
        return

    if room not in rooms_with_codes:
        emit('room_error', {'message': f"Room '{room}' does not exist."}, to=request.sid)
        return

    # ลบห้องออก
    del rooms_with_codes[room]

    # แจ้งผู้ใช้ทุกคนว่าห้องถูกลบ
    socketio.emit('room_deleted', {'message': f"Room '{room}' was deleted by admin.", 'room': room})
    broadcast_rooms()

    
@socketio.on('send_message')
def handle_message(data):
    username = data['username']
    message = data['message']
    room = data['room']
    emit('receive_message', {'username': username, 'message': message}, to=room)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
