from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs
from db import Database
from utils import get_session, render_template
import json
import uuid
import time

class RequestHandler(BaseHTTPRequestHandler):
    sessions = {}  # 格式：{session_id: {"username": username, "expires": timestamp}}
    db = Database()

    def do_GET(self):
        if self.path == "/":
            self._send_html("html/index.html")
        
        elif self.path == "/admin":
            self._handle_admin()
        elif self.path == "/users":
            self._handle_users()
        elif self.path == "/notes":
            self._handle_get_notes()
        else:
            self._send_error(404, "404 Not Found")

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        form_data = parse_qs(post_data)

        if self.path == "/post":
            self._handle_login(form_data)
        elif self.path == "/logins":
            self._handle_logins(form_data)
        elif self.path == "/delete":
            self._handle_delete(form_data)
        elif self.path == "/register":
            self._handle_register(form_data)
        elif self.path == "/add_note":
            self._handle_add_note(form_data)
        elif self.path == "/delete_note":
            self._handle_delete_note(form_data)

    def _send_html(self, file_path):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(render_template(file_path))

    def _send_error(self, code, message):
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(message.encode("utf-8"))

    def _handle_admin(self):
        session_id = get_session(self.headers)
        if not session_id or session_id not in RequestHandler.sessions:
            self.send_response(302)
            self._send_html("html/login.html")
            self.end_headers()
            return
        session = RequestHandler.sessions[session_id]
        if time.time() > session["expires"]:
            del RequestHandler.sessions[session_id]
            self.send_response(302)
            self._send_html("html/login.html")
            self.end_headers()
            return
        if session["username"] != "admin":
            self._send_html("html/login.html")
            return
        self._send_html("html/admin.html")

    def _handle_users(self):
        session_id = get_session(self.headers)
        if not session_id or session_id not in RequestHandler.sessions:
            self._send_html("html/login.html")
            return
        session = RequestHandler.sessions[session_id]
        if time.time() > session["expires"]:
            del RequestHandler.sessions[session_id]
            self._send_error(403, "會話已過期，請重新登入")
            return
        if session["username"] != "admin":
            self._send_html("html/login.html")
            return
        users = self.db.get_all_users()
        response = "".join(
            f"<tr><td>{user[0]}</td><td>{user[1]}</td>"
            f"<td><button onclick=\"deleteUser({user[0]},\'{user[1]}\')\">刪除</button></td></tr>"
            for user in users
        )
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(response.encode("utf-8"))

    def _handle_login(self, form_data):
        username = form_data.get('un', [''])[0]
        password = form_data.get('pwd', [''])[0]
        user = self.db.get_user(username)
        if user and user[2] == password:
            session_id = str(uuid.uuid4())
            RequestHandler.sessions[session_id] = {
                "username": username,
                "expires": time.time() + 1800  # 1 小時
            }
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Set-Cookie", f"session_id={session_id}; Path=/; HttpOnly")
            self.end_headers()
            content = render_template("html/2.html", {"username": username})
            self.wfile.write(content)
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("<h1>登入失敗!</h1><br><a href=\"/\">回到主頁</a>".encode("utf-8"))

    def _handle_logins(self, form_data):
        username = form_data.get("username", [""])[0]
        password = form_data.get("password", [""])[0]
        user = self.db.get_user(username)
        if user and user[2] == password:
            session_id = str(uuid.uuid4())
            RequestHandler.sessions[session_id] = {
                "username": username,
                "expires": time.time() + 3600  # 1 小時
            }
            self.send_response(200)
            self.send_header("Set-Cookie", f"session_id={session_id}; Path=/; HttpOnly")
            self.end_headers()
            self.wfile.write(b"Login success")
        else:
            self._send_error(401, "Invalid credentials")

    def _handle_delete(self, form_data):
        session_id = get_session(self.headers)
        if not session_id or session_id not in RequestHandler.sessions:
            self._send_error(403, "請先登入")
            return
        session = RequestHandler.sessions[session_id]
        if time.time() > session["expires"]:
            del RequestHandler.sessions[session_id]
            self._send_error(403, "會話已過期，請重新登入")
            return
        if session["username"] != "admin":
            self._send_error(403, "Forbidden")
            return
        user_id = form_data.get('id', [""])[0]
        if not user_id:
            self._send_error(400, "Missing user ID")
            return
        user = self.db.get_user_by_id(user_id)
        if user and user[1] == "admin":
            self._send_error(403, "Cannot delete admin user")
        else:
            self.db.delete_user(user_id)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"User deleted successfully")

    def _handle_register(self, form_data):
        username = form_data.get('un', [''])[0]
        password = form_data.get('pwd', [''])[0]
        if self.db.get_user(username):
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("<h1>註冊失敗，帳號已存在!</h1><br><a href=\"/\">回到主頁</a>".encode("utf-8"))
        else:
            self.db.add_user(username, password)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("<h1>註冊成功!</h1><br><a href=\"/\">回到主頁</a>".encode("utf-8"))

    def _handle_get_notes(self):
        notes = self.db.get_all_notes()  # 返回 [(id, content, postby), ...]
        # 將資料轉換為前端期望的格式
        notes_list = [{"id": note[0], "content": note[1], "postby": note[2]} for note in notes]
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(notes_list).encode("utf-8"))

    def _handle_add_note(self, form_data):
        session_id = get_session(self.headers)
        print(f"Session ID: {session_id}, Sessions: {RequestHandler.sessions}")  # 調試用
        if not session_id or session_id not in RequestHandler.sessions:
            self._send_error(403, "請先登入")
            return
        session = RequestHandler.sessions[session_id]
        if time.time() > session["expires"]:
            del RequestHandler.sessions[session_id]
            self._send_error(403, "會話已過期，請重新登入")
            return
        content = form_data.get('content', [''])[0]
        if not content:
            self._send_error(400, "內容不能為空")
            return
        elif len(content) > 100:
            self._send_error(400, "內容長度超過100")
            return
        self.db.add_note(content,session["username"])
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Note added successfully")

    def _handle_delete_note(self, form_data):
        session_id = get_session(self.headers)
        if not session_id or session_id not in RequestHandler.sessions:
            self._send_error(403, "請先登入")
            return
        session = RequestHandler.sessions[session_id]
        if time.time() > session["expires"]:
            del RequestHandler.sessions[session_id]
            self._send_error(403, "會話已過期，請重新登入")
            return
        if session["username"] != "admin":
            self._send_error(403, "Forbidden")
            return
        note_id = form_data.get('id', [""])[0]
        if not note_id:
            self._send_error(400, "Missing note ID")
            return
        self.db.delete_note(note_id)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Note deleted successfully")