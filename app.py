from flask import Flask, render_template, request, redirect, session, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from datetime import datetime

app = Flask(__name__)

# ------------------ ENV VARIABLES ------------------
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey123")
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://aashishjha9844:High%20quality%20123@cluster0.lxhz3yk.mongodb.net/blog_db?retryWrites=true&w=majority")

# ------------------ MONGO CONNECTION ------------------
client = MongoClient(MONGO_URI)
db = client.get_database()  # uses database from URI
users_collection = db.users
posts_collection = db.posts

# ------------------ ROUTES ------------------

@app.route("/")
def index():
    username = session.get("username")
    user_id = session.get("user_id")
    
    all_posts = list(posts_collection.find().sort("timestamp", -1))
    
    # Mark ownership for template
    for post in all_posts:
        post["is_owner"] = str(post.get("user_id")) == str(user_id)
    
    return render_template("dashboard.html", posts=all_posts, username=username)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        if not username:
            return "Enter a valid username"
        
        # Check if user exists
        if users_collection.find_one({"username": username}):
            return "Username already exists"
        
        # Insert new user
        user = {"username": username}
        result = users_collection.insert_one(user)
        
        session["username"] = username
        session["user_id"] = str(result.inserted_id)
        
        return redirect(url_for("index"))
    
    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        user = users_collection.find_one({"username": username})
        
        if user:
            session["username"] = user["username"]
            session["user_id"] = str(user["_id"])
            return redirect(url_for("index"))
        else:
            return "No account with this username. Please sign up."
    
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/create", methods=["GET", "POST"])
def create_post():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        
        if not title or not content:
            return "Title and content required"
        
        post = {
            "user_id": ObjectId(session["user_id"]),
            "title": title,
            "content": content,
            "timestamp": datetime.utcnow()
        }
        posts_collection.insert_one(post)
        return redirect(url_for("index"))
    
    return render_template("create.html")


# ------------------ RUN ------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
