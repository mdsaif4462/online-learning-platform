"""Lumen Learn - Flask backend.

Run (from this folder):
    flask --app app init-db
    flask --app app seed
    flask --app app run --debug
"""
import pandas as pd
from flask import Flask, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import desc, func, or_

from config import Config
from models import Course, Enrollment, Lesson, LessonCompletion, User, db
from recommender import CourseRecommender

csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message = "Please log in to continue."
login_manager.login_message_category = "info"

_rec_cache = {"count": None, "model": None}


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ---------- helpers ----------

def get_recommender():
    """Rebuild the TF-IDF model whenever the number of courses changes."""
    count = Course.query.count()
    if _rec_cache["model"] is None or _rec_cache["count"] != count:
        df = pd.DataFrame(
            [
                {"id": c.id, "title": c.title, "category": c.category,
                 "tags": c.tags or "", "description": c.description or ""}
                for c in Course.query.all()
            ],
            columns=["id", "title", "category", "tags", "description"],
        )
        _rec_cache["model"] = CourseRecommender(df)
        _rec_cache["count"] = count
    return _rec_cache["model"]


def courses_by_ids(ids):
    if not ids:
        return []
    found = {c.id: c for c in Course.query.filter(Course.id.in_(ids)).all()}
    return [found[i] for i in ids if i in found]


def recommendations_for(user, n=6):
    enrolled_ids = [e.course_id for e in Enrollment.query.filter_by(user_id=user.id)]
    if not enrolled_ids:
        return []
    return courses_by_ids(get_recommender().for_user(enrolled_ids, n))


def completed_lesson_ids(user):
    return {c.lesson_id for c in LessonCompletion.query.filter_by(user_id=user.id)}


def user_progress(user):
    completed = completed_lesson_ids(user)
    items = []
    enrollments = (Enrollment.query.filter_by(user_id=user.id)
                   .order_by(Enrollment.enrolled_at.desc()).all())
    for e in enrollments:
        lessons = e.course.lessons
        done = sum(1 for l in lessons if l.id in completed)
        items.append({
            "course": e.course,
            "done": done,
            "total": len(lessons),
            "percent": round(done * 100 / len(lessons)) if lessons else 0,
            "next_lesson": next((l for l in lessons if l.id not in completed), None),
        })
    return items


def is_enrolled(user, course_id):
    return Enrollment.query.filter_by(user_id=user.id, course_id=course_id).first() is not None


def create_app():
    app = Flask(
        __name__,
        template_folder="../frontend/templates",
        static_folder="../frontend/static",
    )
    app.config.from_object(Config)
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    # ---------- public pages ----------

    @app.route("/")
    def index():
        popular_rows = (
            db.session.query(Course, func.count(Enrollment.id).label("n"))
            .outerjoin(Enrollment, Enrollment.course_id == Course.id)
            .group_by(Course.id)
            .order_by(desc("n"), Course.id)
            .limit(6)
            .all()
        )
        popular = [row[0] for row in popular_rows]
        recommended = recommendations_for(current_user, 3) if current_user.is_authenticated else []
        categories = [c[0] for c in db.session.query(Course.category).distinct().order_by(Course.category)]
        return render_template("index.html", popular=popular, recommended=recommended,
                               categories=categories)

    @app.route("/courses")
    def courses():
        q = request.args.get("q", "").strip()
        category = request.args.get("category", "").strip()
        level = request.args.get("level", "").strip()

        query = Course.query
        if q:
            like = f"%{q}%"
            query = query.filter(or_(Course.title.ilike(like),
                                     Course.description.ilike(like),
                                     Course.tags.ilike(like)))
        if category:
            query = query.filter(Course.category == category)
        if level:
            query = query.filter(Course.level == level)

        categories = [c[0] for c in db.session.query(Course.category).distinct().order_by(Course.category)]
        return render_template("courses.html", courses=query.order_by(Course.title).all(),
                               categories=categories, q=q, category=category, level=level)

    @app.route("/courses/<int:course_id>")
    def course_detail(course_id):
        course = db.get_or_404(Course, course_id)
        enrolled, completed = False, set()
        if current_user.is_authenticated:
            enrolled = is_enrolled(current_user, course.id)
            if enrolled:
                completed = completed_lesson_ids(current_user)
        similar = courses_by_ids(get_recommender().similar_to(course.id, 3))
        return render_template("course_detail.html", course=course, enrolled=enrolled,
                               completed=completed, similar=similar)

    # ---------- learning ----------

    @app.route("/courses/<int:course_id>/enroll", methods=["POST"])
    @login_required
    def enroll(course_id):
        course = db.get_or_404(Course, course_id)
        if not is_enrolled(current_user, course.id):
            db.session.add(Enrollment(user_id=current_user.id, course_id=course.id))
            db.session.commit()
            flash(f"You are enrolled in {course.title}.", "success")
        if course.lessons:
            return redirect(url_for("lesson_view", course_id=course.id, lesson_id=course.lessons[0].id))
        return redirect(url_for("course_detail", course_id=course.id))

    @app.route("/learn/<int:course_id>/<int:lesson_id>")
    @login_required
    def lesson_view(course_id, lesson_id):
        course = db.get_or_404(Course, course_id)
        lesson = db.get_or_404(Lesson, lesson_id)
        if lesson.course_id != course.id:
            abort(404)
        if not is_enrolled(current_user, course.id):
            flash("Enroll in this course to open its lessons.", "info")
            return redirect(url_for("course_detail", course_id=course.id))

        lessons = course.lessons
        idx = lessons.index(lesson)
        return render_template(
            "lesson.html", course=course, lesson=lesson, lessons=lessons,
            prev_lesson=lessons[idx - 1] if idx > 0 else None,
            next_lesson=lessons[idx + 1] if idx < len(lessons) - 1 else None,
            completed=completed_lesson_ids(current_user),
        )

    @app.route("/learn/<int:course_id>/<int:lesson_id>/complete", methods=["POST"])
    @login_required
    def complete_lesson(course_id, lesson_id):
        lesson = db.get_or_404(Lesson, lesson_id)
        if lesson.course_id != course_id or not is_enrolled(current_user, course_id):
            abort(403)
        exists = LessonCompletion.query.filter_by(user_id=current_user.id, lesson_id=lesson.id).first()
        if not exists:
            db.session.add(LessonCompletion(user_id=current_user.id, lesson_id=lesson.id))
            db.session.commit()

        lessons = lesson.course.lessons
        idx = lessons.index(lesson)
        if idx < len(lessons) - 1:
            return redirect(url_for("lesson_view", course_id=course_id, lesson_id=lessons[idx + 1].id))
        flash("Course finished. Nice work!", "success")
        return redirect(url_for("dashboard"))

    @app.route("/dashboard")
    @login_required
    def dashboard():
        return render_template("dashboard.html", progress=user_progress(current_user),
                               recommended=recommendations_for(current_user, 6))

    @app.route("/api/recommendations")
    @login_required
    def api_recommendations():
        recs = recommendations_for(current_user, 6)
        return jsonify([{"id": c.id, "title": c.title, "category": c.category, "level": c.level}
                        for c in recs])

    # ---------- auth ----------

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")

            error = None
            if not name or not email or not password:
                error = "Fill in every field."
            elif "@" not in email:
                error = "Enter a valid email address."
            elif len(password) < 8:
                error = "Use a password of at least 8 characters."
            elif User.query.filter_by(email=email).first():
                error = "An account with this email already exists. Try logging in."

            if error:
                flash(error, "danger")
                return render_template("register.html", name=name, email=email), 400

            user = User(name=name, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Welcome! Pick a course to get started.", "success")
            return redirect(url_for("courses"))
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            user = User.query.filter_by(email=email).first()
            if user and user.check_password(request.form.get("password", "")):
                login_user(user)
                nxt = request.args.get("next", "")
                if nxt.startswith("/") and not nxt.startswith("//"):
                    return redirect(nxt)
                return redirect(url_for("dashboard"))
            flash("Email or password is incorrect.", "danger")
            return render_template("login.html", email=email), 401
        return render_template("login.html")

    @app.route("/logout", methods=["POST"])
    @login_required
    def logout():
        logout_user()
        flash("You have been logged out.", "info")
        return redirect(url_for("index"))

    # ---------- CLI ----------

    @app.cli.command("init-db")
    def init_db():
        """Create all tables."""
        db.create_all()
        print("Tables created.")

    @app.cli.command("seed")
    def seed():
        """Insert sample courses and a demo user."""
        from seed import run
        run()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
