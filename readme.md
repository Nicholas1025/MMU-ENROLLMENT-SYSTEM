# 🎓 MMU Student Enrollment System

A comprehensive web-based course enrollment system built with **Python Flask** for Multimedia University (MMU), designed to streamline the entire course registration process for students, instructors, and administrators.

**Course Project**: TSE6223 Software Engineering Fundamentals  
**Institution**: Multimedia University (MMU)  
**Semester**: March/April 2025

---

## 🖼️ System Overview

![Homepage Screenshot](screenshot/index.png)

---

## ✨ Key Features  

### 👨‍🎓 **Student Portal**
- **Secure Registration & Authentication** with university email validation
- **Smart Course Dashboard** with intelligent course categorization:
  - ✅ Eligible Courses (available for enrollment)
  - ❌ Locked Courses (with specific blocking reasons)
  - ✔️ Completed Courses (from previous semesters)
- **Advanced Enrollment System**:
  - Real-time **quota checking** and **duplicate prevention**
  - **Time conflict detection** during enrollment
  - **Credit limit enforcement** (20 credits per semester)
  - **Prerequisite validation** before enrollment
  - **FYP eligibility check** (requires ≥ 60 completed credits)
- **Section Management**: Enroll in Lecture + Tutorial/Lab combinations
- **Flexible Section Switching**: Change between different lecture/tutorial sections
- **Interactive Timetable**: Visual weekly schedule with course details
- **Course Management**: View enrolled courses and drop functionality
- **Academic Profile**: Track completed courses and total credit hours
- **Financial Summary**: Real-time fee calculation with scholarship discounts
- **Credit Transfer Integration**: View transferred credits from other institutions
- **Password Recovery**: Forgot password functionality

### 🧑‍💼 **Admin Dashboard**
- **Comprehensive Course Management**:
  - Create, edit, and delete courses with prerequisite relationships
  - Set course credits, departments, and semester offerings
  - Bulk course operations and semester management
- **Advanced Section Management**:
  - Create and assign multiple sections per course (Lecture, Tutorial, Lab)
  - Instructor assignment and scheduling
  - Quota management and capacity planning
- **Student Administration**:
  - Complete student database management
  - Edit student profiles and scholarship percentages
  - View individual student academic records
- **Credit Transfer System**: Add and manage external credit transfers
- **System Configuration**:
  - Set active semester for enrollment
  - Global system settings management
- **Analytics & Reporting**:
  - 📊 **Comprehensive Reports Dashboard**
  - Real-time enrollment statistics and trends
  - Department-wise performance analytics
  - Popular courses and underenrolled course identification
  - Instructor workload analysis
  - Time slot usage optimization
  - Student credit load distribution
  - Interactive charts and data visualizations
- **Instructor Management**: Manage instructor profiles and assignments
- **Data Import/Export**: Sample data management for testing

### 👨‍🏫 **Instructor Portal**
- **Teaching Dashboard**: Overview of assigned courses and sections
- **Student Management**: View enrolled students in each section
- **Teaching Schedule**: Weekly timetable of all teaching commitments
- **Profile Management**: Update personal information and biography
- **Profile Picture Upload**: Professional photo management
- **Class Rosters**: Access student contact information for communication
- **Multi-Section Support**: Handle multiple course assignments efficiently

---

## 🛠️ **Technology Stack**

### **Backend**
- **Framework**: Python Flask 2.2.5
- **Database**: SQLite (Development) / PostgreSQL (Production-ready)
- **ORM**: SQLAlchemy 3.1.1 with Flask-SQLAlchemy integration
- **Authentication**: Flask-Login with secure session management
- **Forms**: Flask-WTF with WTForms validation
- **Security**: CSRF protection, password hashing with Werkzeug

### **Frontend**
- **Styling**: Bootstrap 5.3.0 with responsive design
- **Templating**: Jinja2 with template inheritance
- **Typography**: Inter font family for modern aesthetics
- **Icons**: Bootstrap Icons for consistent UI elements
- **JavaScript**: Vanilla JS for interactive elements

### **Development Tools**
- **Version Control**: Git with comprehensive commit history
- **Environment**: Virtual environment with pip dependency management
- **File Handling**: Secure file uploads with Pillow for image processing
- **Email Validation**: Advanced email format validation

---

## 🚀 **Installation & Setup**

### **Prerequisites**
- Python 3.8 or higher
- pip package manager
- Git (for cloning)

### **Step-by-Step Installation**

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-username/MMU-ENROLLMENT-SYSTEM.git
   cd MMU-ENROLLMENT-SYSTEM
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize Database**
   ```bash
   # The database will be created automatically on first run
   python run.py
   ```

5. **Access the Application**
   - Open your browser and navigate to: `http://localhost:5000`
   - Default admin credentials: `admin` / `admin123`

---

## 🔐 **User Accounts & Access**

### **Default Admin Account**
- **Username**: `admin`
- **Password**: `admin123`
- **Access**: Full system administration

### **Sample Student Account** (after data import)
- **Email**: `alice.tan@student.mmu.edu.my`
- **Password**: `password123`
- **Department**: FIST

### **Sample Instructor Account** (after data import)
- **Email**: `john.tan@mmu.edu.my`
- **Password**: `instructor123`
- **Department**: FIST

---

## 📊 **System Capabilities**

### **Business Logic Enforcement**
- ✅ **Credit Limit Validation**: Maximum 20 credits per semester
- ✅ **Prerequisite Checking**: Automatic validation of course dependencies
- ✅ **Time Conflict Prevention**: No overlapping class schedules
- ✅ **Quota Management**: Real-time seat availability tracking
- ✅ **FYP Restrictions**: Final Year Project requires 60+ completed credits
- ✅ **Department Filtering**: Students see only relevant department courses

### **Data Integrity Features**
- 🔒 **Secure Authentication**: Role-based access control
- 🔒 **Input Validation**: Comprehensive form validation and sanitization
- 🔒 **CSRF Protection**: Secure form submissions
- 🔒 **Email Validation**: University domain enforcement (@student.mmu.edu.my)
- 🔒 **File Upload Security**: Safe image upload with type validation

### **Advanced Functionality**
- 📈 **Real-time Analytics**: Live enrollment statistics and reporting
- 📱 **Responsive Design**: Mobile-friendly interface
- 🔄 **Dynamic Updates**: Real-time course availability updates
- 💰 **Financial Integration**: Automatic fee calculation with scholarships
- 📋 **Comprehensive Reporting**: Multi-dimensional analytics dashboard

---

## 🧪 **Testing & Quality Assurance**

The system has undergone comprehensive testing including:

- **Unit Testing**: Individual component validation
- **Module Testing**: Student, Admin, and Instructor functionality
- **Integration Testing**: Cross-module data consistency
- **User Acceptance Testing**: Real-world scenario validation
- **Security Testing**: Authentication and authorization verification

**Test Coverage**: 65 test cases with 100% pass rate across all modules.

---


## 📄 **License**

This project is licensed under the **Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International License**.

---

## 🙏 **Acknowledgments**

- **Institution**: Multimedia University (MMU)
- **Course**: TSE6223 Software Engineering Fundamentals
- **Semester**: March/April 2025
- **Development Framework**: Flask ecosystem and community
- **UI Framework**: Bootstrap team for responsive design components

---


## 🔗 **Quick Links**

- [🏠 Live Demo](http://localhost:5000) (when running locally)
- [📚 Flask Documentation](https://flask.palletsprojects.com/)
- [🎨 Bootstrap Documentation](https://getbootstrap.com/docs/5.3/)
- [🏛️ MMU Official Website](https://www.mmu.edu.my/)

---
