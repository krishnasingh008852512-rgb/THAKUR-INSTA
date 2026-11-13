
from flask import Flask, request, redirect, session, render_template_string, url_for
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "local-dev-key")

def connect_db():
    return sqlite3.connect("thakur_insta.db")

def init_db():
    db = connect_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            receiver TEXT NOT NULL,
            message TEXT NOT NULL
        )
    """)
    db.commit()
    db.close()

STYLE = """
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
* { box-sizing: border-box; }
body {
    margin: 0; background: #100d15; color: white;
    font-family: Arial; padding: 20px;
}
h1 { color: gold; text-align: center; }
.box {
    background: #281f30; padding: 22px;
    border-radius: 15px; max-width: 420px;
    margin: 25px auto;
}
input {
    width: 100%; padding: 13px; margin: 8px 0;
    border: 0; border-radius: 8px;
}
button {
    background: gold; color: black; padding: 12px;
    border: 0; border-radius: 8px; cursor: pointer;
    font-weight: bold; width: 100%;
}
a { color: gold; text-decoration: none; }
.user {
    display: block; background: #392c44;
    padding: 14px; margin: 10px 0; border-radius: 8px;
}
.msg { background: #392c44; padding: 10px;
       margin: 8px 0; border-radius: 10px; }
.mine { background: #604b18; text-align: right; }
</style>
"""

@app.route("/")
def home():
    if "username" not in session:
        return redirect("/login")

    db = connect_db()
    users = db.execute(
        "SELECT username FROM users WHERE username != ?",
        (session["username"],)
    ).fetchall()
    db.close()

    return render_template_string("""
    """ + STYLE + """
    <h1>👑 THAKUR INSTA</h1>
    <div class="box">
        <h2>Welcome, {{ username }}!</h2>
        <p>Your Royal Social World</p>
        <h3>💬 Chat with people</h3>
        {% for user in users %}
          <a class="user" href="/chat/{{ user[0] }}">
            👤 {{ user[0] }} — Message
          </a>
        {% else %}
          <p>Abhi koi doosra account nahi hai.</p>
        {% endfor %}
        <br><a href="/logout">Logout</a>
    </div>
    """, username=session["username"], users=users)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = ""
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        if not username or not password:
            error = "Sabhi details bharo!"
        elif len(password) < 6:
            error = "Password kam se kam 6 characters ka rakho!"
        else:
            db = connect_db()
            try:
                db.execute(
                    "INSERT INTO users (username, password) VALUES (?, ?)",
                    (username, generate_password_hash(password))
                )
                db.commit()
                session["username"] = username
                return redirect("/")
            except sqlite3.IntegrityError:
                error = "Ye username pehle se hai!"
            finally:
                db.close()

    return render_template_string("""
    """ + STYLE + """
    <div class="box">
      <h1>👑 THAKUR INSTA</h1>
      <h2>Create Account</h2>
      <p style="color:red">{{ error }}</p>
      <form method="POST">
        <input name="username" placeholder="Username" required>
        <input name="password" type="password"
               placeholder="Create Password" required>
        <button>Create Account</button>
      </form>
      <p>Already account hai? <a href="/login">Login</a></p>
    </div>
    """, error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        db = connect_db()
        user = db.execute(
            "SELECT password FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        db.close()

        if user and check_password_hash(user[0], password):
            session["username"] = username
            return redirect("/")
        error = "Username ya password galat hai!"

    return render_template_string("""
    """ + STYLE + """
    <div class="box">
      <h1>👑 THAKUR INSTA</h1>
      <h2>Login Account</h2>
      <p style="color:red">{{ error }}</p>
      <form method="POST">
        <input name="username" placeholder="Username" required>
        <input name="password" type="password"
               placeholder="Password" required>
        <button>LOGIN</button>
      </form>
      <p>New user? <a href="/signup">Create Account</a></p>
    </div>
    """, error=error)


@app.route("/chat/<username>", methods=["GET", "POST"])
def chat(username):
    if "username" not in session:
        return redirect("/login")

    me = session["username"]
    db = connect_db()

    other = db.execute(
        "SELECT id FROM users WHERE username = ?", (username,)
    ).fetchone()

    if not other or username == me:
        db.close()
        return redirect("/")

    if request.method == "POST":
        message = request.form.get("message", "").strip()
        if message and len(message) <= 1000:
            db.execute(
                "INSERT INTO messages (sender, receiver, message) VALUES (?, ?, ?)",
                (me, username, message)
            )
            db.commit()

    messages = db.execute("""
        SELECT sender, message FROM messages
        WHERE (sender=? AND receiver=?)
        OR (sender=? AND receiver=?)
        ORDER BY id
    """, (me, username, username, me)).fetchall()

    db.close()

    return render_template_string("""
    """ + STYLE + """
    <div class="box">
      <h1>💬 Chat</h1>
      <h3>{{ username }}</h3>
      <div>
        {% for sender, message in messages %}
          <div class="msg {% if sender == me %}mine{% endif %}">
            <b>{{ sender }}</b><br>{{ message }}
          </div>
        {% endfor %}
      </div>
      <form method="POST">
        <input name="message" placeholder="Message likho..." required>
        <button>Send Message</button>
      </form>
      <p><a href="/">← Back to Home</a></p>
    </div>
    """, username=username, messages=messages, me=me)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
