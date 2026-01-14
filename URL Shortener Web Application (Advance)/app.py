from flask import Flask, render_template, request, redirect, session, url_for
from models import db, User, URL
from werkzeug.security import generate_password_hash, check_password_hash
import validators, random, string

app = Flask(__name__)
app.secret_key = "secretkey123"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

def generate_short_code(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            return redirect("/dashboard")
        else:
            error = "Invalid username or password"

    return render_template("login.html", error=error)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if len(username) < 5 or len(username) > 9:
            error = "Username must be between 5 to 9 characters long"
        elif User.query.filter_by(username=username).first():
            error = "This username already exists..."
        else:
            hashed_pw = generate_password_hash(password)
            new_user = User(username=username, password=hashed_pw)
            db.session.add(new_user)
            db.session.commit()
            return redirect("/")

    return render_template("signup.html", error=error)

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user_id" not in session:
        return redirect("/")

    user_id = session["user_id"]
    short_url = None
    error = None

    if request.method == "POST":
        original_url = request.form["url"]

        if not validators.url(original_url):
            error = "Invalid URL"
        else:
            code = generate_short_code()
            new_url = URL(original_url=original_url, short_code=code, user_id=user_id)
            db.session.add(new_url)
            db.session.commit()
            short_url = request.host_url + code

    urls = URL.query.filter_by(user_id=user_id).all()
    return render_template("dashboard.html", short_url=short_url, urls=urls, error=error)

@app.route("/<code>")
def redirect_url(code):
    url = URL.query.filter_by(short_code=code).first_or_404()
    return redirect(url.original_url)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
