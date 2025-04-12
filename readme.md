
# 🎓 MMU Student Enrollment System

A web-based course enrollment system built with **Python + Flask + SQLite**, designed to streamline the student course registration process. This project is part of the TSE6223 Software Engineering coursework at MMU.

---

## ✅ Features (Progress: 50% - Ongoing)

### 👨‍🎓 Student Features
- Student registration & login (with hashed passwords)
- Select department during signup
- View & enroll available courses (filtered by department)
- Real-time **quota checking** and **duplicate prevention**
- **Time conflict detection** (based on day and time fields)
- View enrolled courses
- 📅 **Weekly Timetable View**

### 🧑‍💼 Admin Features
- Admin login
- Add, edit, delete courses
- View all courses
- View **enrolled students per course**

---

## 🗃️ Technologies Used

- **Backend**: Python + Flask
- **Frontend**: HTML + Bootstrap + Jinja2
- **Database**: SQLite + SQLAlchemy ORM
- **Forms**: Flask-WTF + WTForms
- **Session Management**: Flask Session + Flash messages

---

## 📦 Folder Structure

```
MMU-ENROLLMENT-SYSTEM/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   ├── forms.py
│   └── templates/
│       ├── base.html
│       ├── register.html
│       ├── dashboard.html
│       ├── timetable.html
│       └── admin_*.html
├── app.db
├── run.py
└── README.md
```

---

## 🚀 How to Run

1. **Clone the repo**
   ```bash
   git clone https://github.com/your-username/MMU-ENROLLMENT-SYSTEM.git
   cd MMU-ENROLLMENT-SYSTEM
   ```

2. **Create virtual environment and install dependencies**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Run the app**
   ```bash
   python run.py
   ```

4. **(Optional)**: Populate demo data (students, courses)
   ```
   Visit: http://127.0.0.1:5000/init-demo
   ```

---

## ✍️ Credits

Developed by **Nicholas Tay Jun Yang**  
Course: TSE6223 Software Engineering @ MMU  
Semester: April 2025  
Progress: 50% (still actively expanding and polishing features)

---

## 📌 TODO

- [ ] PDF export for admin course student list
- [ ] Search bar for student dashboard
- [ ] Admin analytics dashboard (charts)
- [ ] User profile settings

http://127.0.0.1:5000/admin/dashboard admin login page
 admin = Admin(username="admin")
            admin.set_password("admin123")

