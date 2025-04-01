from http.server import HTTPServer
from handler import RequestHandler

sessions = {}  # 全局變數

def run_server(port=8080):
    server_address = ("0.0.0.0", port)
    httpd = HTTPServer(server_address, RequestHandler)
    RequestHandler.sessions = sessions  # 將全局 sessions 傳給 RequestHandler
    print(f"伺服器運行在 http://localhost:{port}")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()