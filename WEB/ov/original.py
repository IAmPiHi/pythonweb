import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import re
import sqlite3
import os
import cgi
from urllib.parse import parse_qs


# 確保 db 資料夾存在

sessions = {}
# 連接到 SQLite，資料庫存放在 db/ 目錄內
db_path = "db/database.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 建立 users 表
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL 
)
""")


conn.commit()

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        
        if self.path == "/":  # 訪問根目錄時，回傳 index.html
           file_path = "html/index.html"
           with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(content.encode("utf-8"))
        elif self.path == "/logins":
            with open("html/login.html", "r", encoding="utf-8") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))

        elif self.path == "/admin":
            session_id = self.get_session()
            if not session_id or sessions.get(session_id) != "admin":
                self.send_response(302)
                self.send_header("Location", "/logins")
                self.end_headers()
                return
            
            with open("html/admin.html", "r", encoding="utf-8") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))
        
        elif self.path == "/users":
            session_id = self.get_session()
            if not session_id or sessions.get(session_id) != "admin":
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b"Forbidden")
                return
            
            cursor.execute("SELECT id, username FROM users")
            users = cursor.fetchall()
            response = "".join(
                f"<tr><td>{user[0]}</td><td>{user[1]}</td>"
                f"<td><button onclick=\"deleteUser({user[0]})\">刪除</button></td></tr>"
                for user in users
            )
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(response.encode("utf-8"))

            
        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"404 Not Found")
    

  
    def do_POST(self):
        
        # 取得 Content-Length，知道要讀多少資料
        content_length = int(self.headers['Content-Length'])
        
        # 讀取 HTTP Body（表單的內容）
        post_data = self.rfile.read(content_length).decode('utf-8')

        # 解析表單數據（application/x-www-form-urlencoded）
        form_data = parse_qs(post_data)
        if self.path == "/login":  # 訪問根目錄時，回傳 index.html
            username = form_data.get('un', [''])[0]
            password = form_data.get('pwd', [''])[0]
            cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            if user and user[0] == password:
              response = 1
            else:
              response = 0

        # 回應客戶端
            file_path = "html/2.html"
            with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            variables = {
                "username": username,
                    
                
            }
        
            # 找到所有 {{變數}}，如果變數在 `variables` 裡就替換，否則用 `?`
            content = re.sub(r"{{\s*(\w+)\s*}}", lambda m: variables.get(m.group(1), "?"), content)
            if response == 1:
                self.wfile.write(content.encode("utf-8"))
            else:
                contents = "<h1>登入失敗!</h1> <br><a href=\"/\">回到主頁</a>" 
                self.wfile.write(contents.encode("utf-8"))
        
        elif self.path == "/logins":
                    username = form_data.get("username", [""])[0]
                    password = form_data.get("password", [""])[0]
                    cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
                    user = cursor.fetchone()

                    if user:
                        session_id = f"session_{user[0]}"
                        sessions[session_id] = username
                        self.send_response(200)  # 成功登入回傳 200 OK
                        self.send_header("Set-Cookie", f"session_id={session_id}; Path=/")
                        self.end_headers()
                        self.wfile.write(b"Login success")  # 確保前端可以識別
                    else:
                        self.send_response(401)
                        self.end_headers()
                        self.wfile.write(b"Invalid credentials")

        elif self.path == "/delete":
            session_id = self.get_session()
            if not session_id or sessions.get(session_id) != "admin":
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b"Forbidden")
                return
            
            user_id = form_data.get('id', [""])[0]
            if not user_id:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Missing user ID")
                return

            cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            if user and user[0] == "admin":
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b"Cannot delete admin user")
            else:
                cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
                conn.commit()
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"User deleted successfully")
        elif self.path == "/register":
            username = form_data.get('un', [''])[0]
            password = form_data.get('pwd', [''])[0]

            # 先檢查 username 是否已存在
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            existing_user = cursor.fetchone()

            if existing_user:
                # 如果 username 已存在，回傳錯誤訊息
                self.send_response(400)  # 400 Bad Request
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write("<h1>註冊失敗，帳號已存在!</h1><br><a href=\"/\">回到主頁</a>".encode("utf-8"))
            else:
                # 帳號不存在，則新增使用者
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                conn.commit()

                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write("<h1>註冊成功!</h1> <br><a href=\"/\">回到主頁</a>".encode("utf-8"))
                

    def get_session(self):
        cookie = self.headers.get("Cookie")
        if cookie:
            for part in cookie.split(";"):
                key, _, value = part.strip().partition("=")
                if key == "session_id":
                    return value
        return None



        
        



        
        

# 啟動伺服器
server_address = ("", 8080)  # 允許本機或區域網路訪問
httpd = HTTPServer(server_address, SimpleHandler)
print("伺服器運行在 http://127.0.0.1:8080")
httpd.serve_forever()
