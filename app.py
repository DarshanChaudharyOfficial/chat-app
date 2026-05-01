from flask import Flask, request, jsonify, session, redirect, render_template_string
import sqlite3
from datetime import datetime
from pathlib import Path

app = Flask(__name__)
app.secret_key = "change_this_to_a_long_random_secret"

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "chat.db"

USERS = {
    "darshan": "1234",
    "divya": "1234",
    "khushi": "1234",
}

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Private Chat Login</title>
    <style>
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #0f172a, #111827);
            color: #e2e8f0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .card {
            width: 100%;
            max-width: 380px;
            background: rgba(17, 24, 39, 0.96);
            border: 1px solid #1f2937;
            border-radius: 20px;
            padding: 28px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.35);
        }
        h1 {
            margin: 0 0 8px;
            font-size: 30px;
        }
        p {
            margin: 0 0 20px;
            color: #94a3b8;
            font-size: 14px;
        }
        input, button {
            width: 100%;
            border: 0;
            outline: none;
            border-radius: 12px;
            font-size: 15px;
        }
        input {
            padding: 14px 16px;
            margin-bottom: 12px;
            background: #0b1220;
            color: #e2e8f0;
            border: 1px solid #334155;
        }
        input:focus {
            border-color: #3b82f6;
        }
        button {
            padding: 14px 16px;
            background: #3b82f6;
            color: white;
            font-weight: 700;
            cursor: pointer;
        }
        button:hover { background: #2563eb; }
        .error {
            margin-top: 12px;
            min-height: 18px;
            color: #f87171;
            font-size: 14px;
        }
        .hint {
            margin-top: 16px;
            font-size: 12px;
            color: #94a3b8;
            line-height: 1.5;
        }
        .tiny {
            display: block;
            margin-top: 8px;
            color: #64748b;
        }
    </style>
</head>
<body>
    <div class="card">
        <h1>Private Chat</h1>
        <p>Members only</p>

        <input id="username" type="text" placeholder="Username" autocomplete="off" />
        <input id="password" type="password" placeholder="Password" />

        <button onclick="login()">Login</button>
        <div id="error" class="error"></div>

        <div class="hint">
            Try: <b>darshan / 1234</b>
            <span class="tiny">If this screen appears, your Flask route is working.</span>
        </div>
    </div>

    <script>
        async function login() {
            const username = document.getElementById("username").value.trim();
            const password = document.getElementById("password").value.trim();
            const error = document.getElementById("error");
            error.textContent = "";

            try {
                const res = await fetch("/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username, password })
                });

                const data = await res.json();
                if (res.ok && data.status === "success") {
                    window.location.href = "/chat";
                } else {
                    error.textContent = data.message || "Login failed";
                }
            } catch (e) {
                error.textContent = "Server error";
            }
        }

        document.addEventListener("keydown", (e) => {
            if (e.key === "Enter") login();
        });
    </script>
</body>
</html>
"""

CHAT_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Private Chat</title>
    <style>
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
        }
        .app {
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .header {
            padding: 16px 18px;
            background: #111827;
            border-bottom: 1px solid #1f2937;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
        }
        .title {
            font-size: 18px;
            font-weight: 700;
        }
        .user {
            font-size: 13px;
            color: #94a3b8;
            margin-top: 2px;
        }
        .logout {
            text-decoration: none;
            color: #e2e8f0;
            background: #1f2937;
            padding: 10px 14px;
            border-radius: 10px;
            white-space: nowrap;
        }
        .box {
            flex: 1;
            overflow-y: auto;
            padding: 18px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .msg {
            max-width: 75%;
            background: #1e293b;
            padding: 12px 14px;
            border-radius: 16px;
            border-top-left-radius: 4px;
            align-self: flex-start;
            word-break: break-word;
        }
        .msg.self {
            background: #2563eb;
            align-self: flex-end;
            border-top-left-radius: 16px;
            border-top-right-radius: 4px;
        }
        .name {
            font-size: 12px;
            font-weight: 700;
            margin-bottom: 6px;
            color: #cbd5e1;
        }
        .self .name {
            color: #eff6ff;
        }
        .text {
            font-size: 15px;
            line-height: 1.4;
            white-space: pre-wrap;
        }
        .time {
            font-size: 11px;
            opacity: 0.75;
            margin-top: 6px;
            text-align: right;
        }
        .input-area {
            display: flex;
            gap: 10px;
            padding: 14px;
            background: #111827;
            border-top: 1px solid #1f2937;
        }
        .input-area input {
            flex: 1;
            padding: 14px 16px;
            border: 1px solid #334155;
            border-radius: 12px;
            background: #0b1220;
            color: #e2e8f0;
            outline: none;
        }
        .input-area input:focus {
            border-color: #3b82f6;
        }
        .input-area button {
            width: 110px;
            border: 0;
            border-radius: 12px;
            background: #3b82f6;
            color: white;
            font-weight: 700;
            cursor: pointer;
        }
        .input-area button:hover {
            background: #2563eb;
        }
        @media (max-width: 600px) {
            .header { padding: 14px; }
            .box { padding: 12px; }
            .msg { max-width: 88%; }
            .input-area { padding: 10px; }
            .input-area button { width: 90px; }
        }
    </style>
</head>
<body>
    <div class="app" data-user="{{ username }}">
        <div class="header">
            <div>
                <div class="title">Private Chat</div>
                <div class="user">Logged in as {{ username }}</div>
            </div>
            <a href="/logout" class="logout">Logout</a>
        </div>

        <div id="chat-box" class="box"></div>

        <div class="input-area">
            <input id="msg" type="text" placeholder="Type a message..." autocomplete="off" />
            <button onclick="sendMessage()">Send</button>
        </div>
    </div>

    <script>
        const currentUser = document.querySelector(".app").dataset.user;

        function escapeHtml(text) {
            const div = document.createElement("div");
            div.textContent = text;
            return div.innerHTML;
        }

        async function fetchMessages() {
            try {
                const res = await fetch("/get");
                const data = await res.json();

                if (!res.ok) {
                    window.location.href = "/";
                    return;
                }

                const box = document.getElementById("chat-box");
                box.innerHTML = "";

                data.forEach(msg => {
                    const div = document.createElement("div");
                    div.className = "msg" + (msg.username === currentUser ? " self" : "");
                    div.innerHTML = `
                        <div class="name">${escapeHtml(msg.username)}</div>
                        <div class="text">${escapeHtml(msg.message)}</div>
                        <div class="time">${escapeHtml(msg.timestamp)}</div>
                    `;
                    box.appendChild(div);
                });

                box.scrollTop = box.scrollHeight;
            } catch (e) {
                console.log(e);
            }
        }

        async function sendMessage() {
            const input = document.getElementById("msg");
            const message = input.value.trim();
            if (!message) return;

            try {
                await fetch("/send", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ message })
                });

                input.value = "";
                fetchMessages();
            } catch (e) {
                console.log(e);
            }
        }

        document.addEventListener("DOMContentLoaded", () => {
            const input = document.getElementById("msg");
            input.addEventListener("keydown", (e) => {
                if (e.key === "Enter") sendMessage();
            });

            fetchMessages();
            setInterval(fetchMessages, 2000);
        });
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    if "user" in session:
        return redirect("/chat")
    return render_template_string(LOGIN_HTML)

@app.route("/chat")
def chat():
    if "user" not in session:
        return redirect("/")
    return render_template_string(CHAT_HTML, username=session["user"])

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()

    if not username or not password:
        return jsonify({"status": "fail", "message": "Username and password required"}), 400

    if USERS.get(username) == password:
        session["user"] = username
        return jsonify({"status": "success"})

    return jsonify({"status": "fail", "message": "Invalid credentials"}), 401

@app.route("/send", methods=["POST"])
def send():
    if "user" not in session:
        return jsonify({"status": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()

    if not message:
        return jsonify({"status": "fail", "message": "Empty message"}), 400

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO messages (username, message, timestamp) VALUES (?, ?, ?)",
        (session["user"], message, timestamp)
    )
    conn.commit()
    conn.close()

    return jsonify({"status": "sent"})

@app.route("/get", methods=["GET"])
def get_messages():
    if "user" not in session:
        return jsonify({"status": "unauthorized"}), 401

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT username, message, timestamp FROM messages ORDER BY id ASC")
    rows = c.fetchall()
    conn.close()

    return jsonify([
        {"username": row[0], "message": row[1], "timestamp": row[2]}
        for row in rows
    ])

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)