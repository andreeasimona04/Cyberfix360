import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, g

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")
DATABASE = "app.db"


# ---------- Database helpers ----------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row      # access columns by name
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            body TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.commit()

with app.app_context():
    init_db()


# ---------- Routes ----------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        body = request.form.get("body", "").strip()

        # Server-side validation (never rely on front-end validation alone)
        if not name or "@" not in email or len(body) < 10:
            flash("Please fill in all fields correctly.")
            return render_template("contact.html"), 400

        db = get_db()
        # Parameterised query: prevents SQL injection
        db.execute(
            "INSERT INTO messages (name, email, body) VALUES (?, ?, ?)",
            (name, email, body),
        )
        db.commit()
        flash("Thanks, your message was sent.")
        return redirect(url_for("contact"))   # Post/Redirect/Get pattern

    return render_template("contact.html")

@app.route("/api/messages")
def api_messages():
    rows = get_db().execute(
        "SELECT id, name, created_at FROM messages ORDER BY created_at DESC LIMIT 10"
    ).fetchall()
    return jsonify([dict(r) for r in rows])


if __name__ == "__main__":
    app.run(debug=True)    # development only