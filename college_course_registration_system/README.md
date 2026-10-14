# College Course Registration System

A presentation-ready mini project built with:

- HTML5 — page structure
- CSS3 — responsive UI
- JavaScript — search, filtering and confirmations
- Python Flask — backend and routing
- SQLite — database

## 1. Install Flask

Open PowerShell inside this folder:

```powershell
python -m pip install flask
```

## 2. Run the project

```powershell
python app.py
```

Then open:

http://127.0.0.1:5000

## 3. Demo accounts

### Student
Email: `student@college.com`
Password: `123456`

### Admin
Username: `admin`
Password: `admin123`

## Main features

Student:
- Login
- New student registration
- Dashboard
- Course catalog
- Search/filter courses
- Register course
- Drop course
- View total credits
- Profile

Admin:
- Admin login
- Dashboard statistics
- Add/delete courses
- View students
- View registration records

## Project structure

college_course_registration_system/
├── app.py
├── college.db              # automatically created after first run
├── README.md
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── dashboard.html
│   ├── courses.html
│   ├── my_courses.html
│   ├── profile.html
│   ├── admin_login.html
│   ├── admin_dashboard.html
│   ├── admin_courses.html
│   ├── students.html
│   └── registrations.html
└── static/
    ├── style.css
    └── script.js
