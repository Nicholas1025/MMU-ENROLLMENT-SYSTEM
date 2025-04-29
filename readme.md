
# 🎓 MMU Student Enrollment System

A web-based course enrollment system built with **Python + Flask + SQLite**, designed to streamline the student course registration process. This project is part of the TSE6223 Software Engineering coursework at MMU.

---

## 🖼️ Website Homepage

![Homepage Screenshot](screenshot/index.png)

## ✅ Features (Progress: 70% - )

### 👨‍🎓 Student Features
- Student registration & login (with hashed passwords)
- Select department during signup
- View & enroll available courses (filtered by department)
- Real-time **quota checking** and **duplicate prevention**
- **Time conflict detection** (based on day and time fields)
- Enroll in **Lecture + Tutorial/Lab sections** per course
- **Section switching** (change Lecture or Tutorial time)
- View enrolled courses
- 📅 **Weekly Timetable View** with visual blocks
- Drop entire course (with all sections)
- Enforce **prerequisite check** before allowing course enrollment  
- Implement **credit hour limit** (e.g., max 18 credit hours)  

### 🧑‍💼 Admin Features
- Admin login
- Add, edit, delete courses
- Add, edit, delete **sections** (Lecture / Tutorial / Lab)
- View all courses
- View all sections grouped by course
- View **enrolled students per section**
- View course details page with section breakdown

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
│       ├── admin_course_details.html
│       ├── admin_section_students.html
│       ├── course_detail.html
│       ├── course_form.html
│       ├── section_form.html
│       ├── select_tutorial.html
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


Course: TSE6223 Software Engineering @ MMU  
Semester: April 2025  
📜 This project is licensed under CC BY-NC-ND 4.0.
---

## 📌 TODO

### 🛠 Current Features in Progress
- [ ] PDF export for admin course student list  
- [ ] Search bar for student dashboard  
- [ ] Admin analytics dashboard with charts  
- [ ] User profile settings  

### 🧠 Smart Enrollment Logic (Coming Soon)
- [ ] Highlight conflicting sections in Dashboard before selection (conflict prediction system)  

### 🔍 UI / UX Improvements (Planned)
- [ ] Add search bar to student dashboard (filter by course name)  
- [ ] Improve form error feedback (display all validation messages clearly)  
- [ ] Prevent duplicate course code/name during course creation (admin validation)



