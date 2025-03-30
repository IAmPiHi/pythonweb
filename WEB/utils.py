def get_session(headers):
    cookie = headers.get("Cookie")
    if cookie:
        for part in cookie.split(";"):
            key, _, value = part.strip().partition("=")
            if key == "session_id":
                return value
    return None

def render_template(file_path, variables=None):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    if variables:
        import re
        content = re.sub(r"{{\s*(\w+)\s*}}", lambda m: variables.get(m.group(1), "?"), content)
    return content.encode("utf-8")