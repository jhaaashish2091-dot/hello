from flask import Flask, render_template, request, redirect, session, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecret123"

# MongoDB Atlas connection
MONGO_URI = "mongodb+srv://aashishjha9844:High%20quality%20123@cluster0.lxhz3yk.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["blog_db"]
users = db["users"]
posts = db["posts"]

from bson import ObjectId  # make sure this is imported

@app.route("/")
def index():
    if "user_id" not in session:
        return redirect("/login")

    current_user_id = session["user_id"]  # this is a string
    all_posts = list(posts.find().sort("timestamp", -1))

    # mark ownership correctly
    for post in all_posts:
        post["is_owner"] = str(post["user_id"]) == current_user_id  # convert ObjectId to string

    return render_template("dashboard.html", posts=all_posts, name=session["username"])

# Sign Up
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"].strip()
        if users.find_one({"name": name}):
            return "User exists! Go login."
        user = users.insert_one({"name": name})
        session["user_id"] = str(user.inserted_id)
        session["username"] = name
        return redirect("/")
    return render_template("signup.html")

# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form["name"].strip()
        user = users.find_one({"name": name})
        if user:
            session["user_id"] = str(user["_id"])
            session["username"] = user["name"]
            return redirect("/")
        else:
            return "No account found. Please sign up."
    return render_template("login.html")

# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# Add blog post
@app.route("/add_post", methods=["POST"])
def add_post():
    if "user_id" not in session:
        return redirect("/login")
    title = request.form["title"]
    content = request.form["content"]
    posts.insert_one({
        "user_id": ObjectId(session["user_id"]),
        "title": title,
        "content": content,
        "timestamp": datetime.utcnow()
    })
    return redirect("/")

# Delete post
@app.route("/delete_post/<post_id>")
def delete_post(post_id):
    if "user_id" not in session:
        return redirect("/login")
    post = posts.find_one({"_id": ObjectId(post_id)})
    if post and str(post["user_id"]) == session["user_id"]:
        posts.delete_one({"_id": ObjectId(post_id)})
    return redirect("/")

# Edit post
@app.route("/edit_post/<post_id>", methods=["GET", "POST"])
def edit_post(post_id):
    if "user_id" not in session:
        return redirect("/login")
    post = posts.find_one({"_id": ObjectId(post_id)})
    if not post or str(post["user_id"]) != session["user_id"]:
        return redirect("/")
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        posts.update_one({"_id": ObjectId(post_id)}, {"$set": {"title": title, "content": content}})
        return redirect("/")
    return render_template("edit_post.html", post=post)

if __name__ == "__main__":
    app.run(debug=True)
