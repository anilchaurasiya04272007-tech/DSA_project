from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
from pathlib import Path
from functools import wraps

app = Flask(__name__)
app.secret_key = "college-course-registration-demo-secret"

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "college.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        roll_no TEXT UNIQUE NOT NULL,
        course TEXT NOT NULL,
        semester INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        instructor TEXT NOT NULL,
        credits INTEGER NOT NULL,
        semester INTEGER NOT NULL,
        seats INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS registrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        course_id INTEGER NOT NULL,
        registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(student_id, course_id),
        FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
        FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
    );
    """)

    if conn.execute("SELECT COUNT(*) FROM students").fetchone()[0] == 0:
        conn.execute(
            "INSERT INTO students (name,email,password,roll_no,course,semester) VALUES (?,?,?,?,?,?)",
            ("Demo Student", "student@college.com", "123456", "BCA2026-001", "BCA", 2)
        )

    if conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0] == 0:
        courses = [
            ("BCA201", "Data Structures", "Dr. Akash", 4, 2, 60),
            ("BCA202", "Database Management System", "Ms. Neha", 4, 2, 60),
            ("BCA203", "Python Programming", "Mr. Rahul", 3, 2, 50),
            ("BCA204", "Information Security", "Ms. Priya", 3, 2, 50),
            ("BCA205", "Computer Organization", "Dr. Amit", 3, 2, 55),
            ("BCA206", "Web Technology", "Mr. Kunal", 3, 2, 50),
            ("BCA301", "Operating Systems", "Ms. Ritu", 4, 3, 60),
            ("BCA302", "Computer Networks", "Dr. Vivek", 4, 3, 60)
        ]
        conn.executemany(
            "INSERT INTO courses (code,name,instructor,credits,semester,seats) VALUES (?,?,?,?,?,?)",
            courses
        )
    conn.commit()
    conn.close()

def student_login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "student_id" not in session:
            flash("Please login as a student first.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

def admin_login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin"):
            flash("Please login as admin first.", "warning")
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)
    return wrapped

@app.route("/")
def index():
    conn = get_db()
    course_count = conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
    student_count = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    registration_count = conn.execute("SELECT COUNT(*) FROM registrations").fetchone()[0]
    conn.close()
    return render_template("index.html", course_count=course_count,
                           student_count=student_count,
                           registration_count=registration_count)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"]
        conn = get_db()
        student = conn.execute(
            "SELECT * FROM students WHERE email=? AND password=?", (email, password)
        ).fetchone()
        conn.close()
        if student:
            session["student_id"] = student["id"]
            session["student_name"] = student["name"]
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")

@app.route("/register-student", methods=["POST"])
def register_student():
    name = request.form["name"].strip()
    email = request.form["email"].strip()
    password = request.form["password"]
    roll_no = request.form["roll_no"].strip()
    course = request.form["course"].strip()
    semester = int(request.form["semester"])
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO students (name,email,password,roll_no,course,semester) VALUES (?,?,?,?,?,?)",
            (name, email, password, roll_no, course, semester)
        )
        conn.commit()
        flash("Account created successfully. Please login.", "success")
    except sqlite3.IntegrityError:
        flash("Email or roll number already exists.", "danger")
    finally:
        conn.close()
    return redirect(url_for("login"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/dashboard")
@student_login_required
def dashboard():
    conn = get_db()
    student_id = session["student_id"]
    student = conn.execute("SELECT * FROM students WHERE id=?", (student_id,)).fetchone()
    registered = conn.execute("""
        SELECT c.* FROM courses c
        JOIN registrations r ON c.id=r.course_id
        WHERE r.student_id=?
        ORDER BY c.code
    """, (student_id,)).fetchall()
    total_credits = sum(c["credits"] for c in registered)
    conn.close()
    return render_template("dashboard.html", student=student, registered=registered,
                           total_credits=total_credits)

@app.route("/courses")
@student_login_required
def courses():
    conn = get_db()
    student_id = session["student_id"]
    rows = conn.execute("""
        SELECT c.*,
               CASE WHEN r.id IS NULL THEN 0 ELSE 1 END AS is_registered,
               (SELECT COUNT(*) FROM registrations rr WHERE rr.course_id=c.id) AS enrolled
        FROM courses c
        LEFT JOIN registrations r ON c.id=r.course_id AND r.student_id=?
        ORDER BY c.semester, c.code
    """, (student_id,)).fetchall()
    conn.close()
    return render_template("courses.html", courses=rows)

@app.route("/register-course/<int:course_id>", methods=["POST"])
@student_login_required
def register_course(course_id):
    student_id = session["student_id"]
    conn = get_db()
    course = conn.execute("SELECT * FROM courses WHERE id=?", (course_id,)).fetchone()
    if not course:
        flash("Course not found.", "danger")
    else:
        enrolled = conn.execute(
            "SELECT COUNT(*) FROM registrations WHERE course_id=?", (course_id,)
        ).fetchone()[0]
        existing = conn.execute(
            "SELECT id FROM registrations WHERE student_id=? AND course_id=?",
            (student_id, course_id)
        ).fetchone()
        if existing:
            flash("You are already registered for this course.", "info")
        elif enrolled >= course["seats"]:
            flash("No seats available for this course.", "danger")
        else:
            conn.execute(
                "INSERT INTO registrations (student_id,course_id) VALUES (?,?)",
                (student_id, course_id)
            )
            conn.commit()
            flash(f"{course['name']} registered successfully.", "success")
    conn.close()
    return redirect(url_for("courses"))

@app.route("/drop-course/<int:course_id>", methods=["POST"])
@student_login_required
def drop_course(course_id):
    conn = get_db()
    conn.execute(
        "DELETE FROM registrations WHERE student_id=? AND course_id=?",
        (session["student_id"], course_id)
    )
    conn.commit()
    conn.close()
    flash("Course dropped successfully.", "success")
    return redirect(url_for("my_courses"))

@app.route("/my-courses")
@student_login_required
def my_courses():
    conn = get_db()
    rows = conn.execute("""
        SELECT c.*, r.registered_at
        FROM courses c
        JOIN registrations r ON c.id=r.course_id
        WHERE r.student_id=?
        ORDER BY r.registered_at DESC
    """, (session["student_id"],)).fetchall()
    conn.close()
    return render_template("my_courses.html", courses=rows,
                           total_credits=sum(r["credits"] for r in rows))

@app.route("/profile")
@student_login_required
def profile():
    conn = get_db()
    student = conn.execute("SELECT * FROM students WHERE id=?", (session["student_id"],)).fetchone()
    conn.close()
    return render_template("profile.html", student=student)

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "admin123":
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Invalid admin credentials.", "danger")
    return render_template("admin_login.html")

@app.route("/admin")
@admin_login_required
def admin_dashboard():
    conn = get_db()
    stats = {
        "students": conn.execute("SELECT COUNT(*) FROM students").fetchone()[0],
        "courses": conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0],
        "registrations": conn.execute("SELECT COUNT(*) FROM registrations").fetchone()[0],
        "credits": conn.execute("""
            SELECT COALESCE(SUM(c.credits),0)
            FROM registrations r JOIN courses c ON c.id=r.course_id
        """).fetchone()[0]
    }
    popular = conn.execute("""
        SELECT c.code, c.name, COUNT(r.id) AS total
        FROM courses c LEFT JOIN registrations r ON c.id=r.course_id
        GROUP BY c.id ORDER BY total DESC, c.code LIMIT 5
    """).fetchall()
    conn.close()
    return render_template("admin_dashboard.html", stats=stats, popular=popular)

@app.route("/admin/courses", methods=["GET", "POST"])
@admin_login_required
def admin_courses():
    conn = get_db()
    if request.method == "POST":
        try:
            conn.execute(
                "INSERT INTO courses (code,name,instructor,credits,semester,seats) VALUES (?,?,?,?,?,?)",
                (request.form["code"].strip(), request.form["name"].strip(),
                 request.form["instructor"].strip(), int(request.form["credits"]),
                 int(request.form["semester"]), int(request.form["seats"]))
            )
            conn.commit()
            flash("Course added successfully.", "success")
        except sqlite3.IntegrityError:
            flash("Course code already exists.", "danger")
        return redirect(url_for("admin_courses"))
    rows = conn.execute("SELECT * FROM courses ORDER BY semester, code").fetchall()
    conn.close()
    return render_template("admin_courses.html", courses=rows)

@app.route("/admin/delete-course/<int:course_id>", methods=["POST"])
@admin_login_required
def delete_course(course_id):
    conn = get_db()
    conn.execute("DELETE FROM courses WHERE id=?", (course_id,))
    conn.commit()
    conn.close()
    flash("Course deleted.", "success")
    return redirect(url_for("admin_courses"))

@app.route("/admin/students")
@admin_login_required
def students():
    conn = get_db()
    rows = conn.execute("SELECT * FROM students ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("students.html", students=rows)

@app.route("/admin/registrations")
@admin_login_required
def registrations():
    conn = get_db()
    rows = conn.execute("""
        SELECT r.id, r.registered_at, s.name, s.roll_no, s.email,
               c.code, c.name AS course_name, c.credits
        FROM registrations r
        JOIN students s ON s.id=r.student_id
        JOIN courses c ON c.id=r.course_id
        ORDER BY r.registered_at DESC
    """).fetchall()
    conn.close()
    return render_template("registrations.html", registrations=rows)

@app.route("/api/course-count")
def api_course_count():
    conn = get_db()
    data = conn.execute("""
        SELECT semester, COUNT(*) AS count
        FROM courses GROUP BY semester ORDER BY semester
    """).fetchall()
    conn.close()
    return jsonify([dict(x) for x in data])

init_db()

if __name__ == "__main__":
    app.run(debug=True)
