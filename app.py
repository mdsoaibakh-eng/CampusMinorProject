import os
from flask import Flask, render_template, redirect, url_for, flash, request, session
from dotenv import load_dotenv
from models import db, Item, Admin, Student, Application
from markupsafe import Markup, escape
from werkzeug.utils import secure_filename
from datetime import datetime

load_dotenv()

# ===========================
# Admin Login Required
# ===========================
def admin_login_required(f):
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin_id"):
            flash("Please log in as admin.", "error")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return wrapper

# ===========================
# Student Login Required
# ===========================
def student_login_required(f):
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("student_id"):
            flash("Please log in as a student.", "error")
            return redirect(url_for("student_login"))
        return f(*args, **kwargs)
    return wrapper


# ===========================
# Create App
# ===========================
def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    UPLOAD_FOLDER = "static/uploads"
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    ALLOWED_EXTENSIONS = {"pdf", "doc", "docx"}

    db.init_app(app)

    # Create tables
    with app.app_context():
        db.create_all()

    # ================
    # Template filter
    # ================
    @app.template_filter('nl2br')
    def nl2br_filter(s):
        if s is None:
            return ""
        return Markup("<br>".join(escape(s).splitlines()))

    # ===========================
    # ADMIN AUTH
    # ===========================

    @app.route("/admin/register", methods=["GET", "POST"])
    def admin_register():
        if request.method == "POST":
            username = request.form.get("username").strip()
            password = request.form.get("password").strip()

            if not username or not password:
                flash("Username and password required.", "error")
                return render_template("admin_register.html")

            if Admin.query.filter_by(username=username).first():
                flash("Username already taken.", "error")
                return render_template("admin_register.html")

            admin = Admin(username=username)
            admin.set_password(password)

            db.session.add(admin)
            db.session.commit()

            flash("Admin registered successfully.", "success")
            return redirect(url_for("admin_login"))

        return render_template("admin_register.html")

    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        if request.method == "POST":
            username = request.form.get("username").strip()
            password = request.form.get("password").strip()

            admin = Admin.query.filter_by(username=username).first()

            if not admin or not admin.check_password(password):
                flash("Invalid username or password.", "error")
                return render_template("admin_login.html")

            session.clear()
            session["admin_id"] = admin.id

            flash("Logged in successfully.", "success")
            return redirect(url_for("index"))

        return render_template("admin_login.html")

    @app.route("/admin/logout")
    def logout():
        session.pop("admin_id", None)
        flash("Logged out.", "info")
        return redirect(url_for("index"))

    # STUDENT AUTH
    # ===========================

    @app.route("/student/register", methods=["GET", "POST"])
    def student_register():
        if request.method == "POST":
            username = request.form.get("username").strip()
            email = request.form.get("email").strip()
            password = request.form.get("password").strip()

            if not username or not email or not password:
                flash("All fields are required.", "error")
                return render_template("student_register.html")

            if Student.query.filter_by(username=username).first() or Student.query.filter_by(email=email).first():
                flash("Username or email already taken.", "error")
                return render_template("student_register.html")

            student = Student(username=username, email=email)
            student.set_password(password)
            db.session.add(student)
            db.session.commit()

            flash("Registered successfully. Please login.", "success")
            return redirect(url_for("student_login"))

        return render_template("student_register.html")

    @app.route("/student/login", methods=["GET", "POST"])
    def student_login():
        if request.method == "POST":
            username = request.form.get("username").strip()
            password = request.form.get("password").strip()

            student = Student.query.filter_by(username=username).first()

            if not student or not student.check_password(password):
                flash("Invalid username or password.", "error")
                return render_template("student_login.html")

            session.clear()
            session["student_id"] = student.id

            flash("Logged in successfully.", "success")
            return redirect(url_for("student_dashboard"))

        return render_template("student_login.html")

    @app.route("/student/logout")
    def student_logout():
        session.pop("student_id", None)
        flash("Logged out.", "info")
        return redirect(url_for("index"))


    # ===========================
    # FILE UPLOAD (RESUME)
    # ===========================

    def allowed_file(filename):
        return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

    @app.route("/student/upload", methods=["GET", "POST"])
    @student_login_required
    def upload_resume():
        student = Student.query.get(session["student_id"])

        if request.method == "POST":
            if "resume" not in request.files:
                flash("No file part.", "error")
                return redirect(request.url)

            file = request.files["resume"]

            if file.filename == "":
                flash("No selected file.", "error")
                return redirect(request.url)

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                path = os.path.join(UPLOAD_FOLDER, filename)
                
                file.save(path)

                app_record = Application(student_id=student.id, resume_filename=filename)
                db.session.add(app_record)
                db.session.commit()

                flash("Resume uploaded successfully.", "success")
                return redirect(url_for("student_dashboard"))

        return render_template("upload_resume.html", student=student)


    # ===========================
    # STUDENT DASHBOARD
    # ===========================

    @app.route("/student/dashboard")
    @student_login_required
    def student_dashboard():
        student = Student.query.get(session["student_id"])
        applications = student.applications
        return render_template("student_dashboard.html", student=student, applications=applications)


    # ===========================
    # Admin: View & Approve Applications
    # ===========================

    @app.route("/admin/applications")
    @admin_login_required
    def admin_view_applications():
        applications = Application.query.order_by(Application.created_at.desc()).all()
        return render_template("admin_applications.html", applications=applications)

    @app.route("/admin/applications/approve/<int:app_id>", methods=["POST"])
    @admin_login_required
    def approve_application(app_id):
        app_record = Application.query.get_or_404(app_id)
        app_record.status = "Approved"
        app_record.approved_at = datetime.utcnow()
        db.session.commit()

        flash("Application approved.", "success")
        return redirect(url_for("admin_view_applications"))


    # ===========================
    # PUBLIC ITEM VIEWS
    # ===========================

    @app.route("/")
    def index():
        page = request.args.get("page", 1, type=int)
        per_page = 6
        items = Item.query.order_by(Item.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
        return render_template("list.html", items=items)

    @app.route("/item/<int:item_id>")
    def detail(item_id):
        item = Item.query.get_or_404(item_id)
        return render_template("detail.html", item=item)


    # ===========================
    # ADMIN CRUD
    # ===========================

    @app.route("/create", methods=["GET", "POST"])
    @admin_login_required
    def create():
        if request.method == "POST":
            title = (request.form.get("title") or "").strip()
            description = (request.form.get("description") or "").strip() or None

            if not title:
                flash("Title is required.", "error")
                return render_template("create.html", title=title, description=description)

            item = Item(title=title, description=description)
            db.session.add(item)
            db.session.commit()

            flash("Item created successfully.", "success")
            return redirect(url_for("index"))

        return render_template("create.html", title="", description="")

    @app.route("/edit/<int:item_id>", methods=["GET", "POST"])
    @admin_login_required
    def edit(item_id):
        item = Item.query.get_or_404(item_id)

        if request.method == "POST":
            title = (request.form.get("title") or "").strip()
            description = (request.form.get("description") or "").strip() or None

            if not title:
                flash("Title is required.", "error")
                return render_template("edit.html", item=item, title=title, description=description)

            item.title = title
            item.description = description

            db.session.commit()

            flash("Item updated.", "success")
            return redirect(url_for("detail", item_id=item.id))

        return render_template("edit.html", item=item, title=item.title, description=item.description or "")

    @app.route("/delete/<int:item_id>", methods=["POST"])
    @admin_login_required
    def delete(item_id):
        item = Item.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()
        flash("Item deleted.", "info")
        return redirect(url_for("index"))

    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    return app

if __name__ == "__main__":
    create_app().run(debug=True)
