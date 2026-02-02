from flask import Flask, render_template, request, redirect, session, url_for, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")  # session secret

# MongoDB Atlas connection
MONGO_URI = os.environ.get("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["blog_db"]
users_col = db["users"]
posts_col = db["posts"]

# -------------------- ROUTES -------------------- #

@app.route("/")
def home():
    if "username" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

# --------------- SIGNUP ---------------- #
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username").strip()
        if not username:
            flash("Username cannot be empty!")
            return redirect(url_for("signup"))
        user = users_col.find_one({"username": username})
        if user:
            flash("Username already exists! Try logging in.")
            return redirect(url_for("login"))
        user_id = users_col.insert_one({"username": username}).inserted_id
        session["username"] = username
        session["user_id"] = str(user_id)
        return redirect(url_for("dashboard"))
    return render_template("signup.html")

# --------------- LOGIN ---------------- #
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username").strip()
        user = users_col.find_one({"username": username})
        if not user:
            flash("No account found. Please sign up.")
            return redirect(url_for("signup"))
        session["username"] = user["username"]
        session["user_id"] = str(user["_id"])
        return redirect(url_for("dashboard"))
    return render_template("login.html")

# --------------- LOGOUT ---------------- #
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# --------------- DASHBOARD ---------------- #
@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))
    all_posts = list(posts_col.find().sort("timestamp", -1))
    return render_template("dashboard.html", posts=all_posts, user_id=session["user_id"], name=session["username"])

# --------------- ADD POST ---------------- #
@app.route("/add_post", methods=["POST"])
def add_post():
    if "username" not in session:
        return redirect(url_for("login"))
    title = request.form.get("title").strip()
    content = request.form.get("content").strip()
    if title and content:
        posts_col.insert_one({
            "title": title,
            "content": content,
            "user_id": ObjectId(session["user_id"]),
            "timestamp": datetime.utcnow()
        })
    return redirect(url_for("dashboard"))

# --------------- DELETE POST ---------------- #
@app.route("/delete_post/<post_id>")
def delete_post(post_id):
    if "username" not in session:
        return redirect(url_for("login"))
    post = posts_col.find_one({"_id": ObjectId(post_id)})
    if post and str(post["user_id"]) == session["user_id"]:
        posts_col.delete_one({"_id": ObjectId(post_id)})
    return redirect(url_for("dashboard"))

# --------------- EDIT POST ---------------- #
@app.route("/edit_post/<post_id>", methods=["GET", "POST"])
def edit_post(post_id):
    if "username" not in session:
        return redirect(url_for("login"))
    post = posts_col.find_one({"_id": ObjectId(post_id)})
    if not post or str(post["user_id"]) != session["user_id"]:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        title = request.form.get("title").strip()
        content = request.form.get("content").strip()
        if title and content:
            posts_col.update_one({"_id": ObjectId(post_id)}, {"$set": {"title": title, "content": content}})
        return redirect(url_for("dashboard"))
    return render_template("edit_post.html", post=post)

# -------------------- RUN -------------------- #
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
