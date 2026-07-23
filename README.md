```markdown
# Online Learning System
This is my thirds project web app on Django cousre 

## Project Overview

Online Learning System is a Django-based web application for creating, managing and delivering online courses. It supports instructors creating courses and lessons, students enrolling in courses, quizzes, assignments, and a simple progress tracking system.

Online_Learning_System/
│
├── online_learning_system/   ← Main settings and configuration for the whole project
├── users/                    ← Handles signup, login, and user roles
├── students/                 ← Student profiles
├── instructors/              ← Instructor profiles
├── employees/                ← Admin/employee profiles
├── courses/                  ← Everything about courses (title, price, category, etc.)
├── category/                 ← Course categories like "Programming" or "Design"
├── lessons/                  ← Individual lessons inside a course (videos, PDFs)
├── assignments/              ← Assignments that instructors create
├── submissions/              ← Files students submit for assignments
├── enrollments/              ← Tracks which student is enrolled in which course
├── reviews/                  ← Student ratings and comments on courses
├── dashboard/                ← The home page each user sees after logging in
├── templates/                ← All the HTML files (what the pages look like)
├── static/                   ← CSS and JavaScript files
├── media/                    ← Uploaded files (course images, videos, PDFs)
└── manage.py                 ← The main Django command-line tool

How to log in
I've already created an admin account you can use to explore:
Username	: S-admin
Password : admin123
Employee : Phon Visal
Pw : admin123
Instructor : Rothana
Pw : admin123
Student : sorya123
Pw : admin123

on my website
# https://ols-system.onrender.com
Username	: S-admin
Password : admin123
Employee : phonvisal1
Pw : admin123
Instructor : Rothana
Pw : admin123
Student : sorya123
Pw : admin123

## Key Features

- User authentication (students, instructors, admin)
- Course creation and management (sections, lessons, resources)
- Enrollment and dashboard for students
- Quizzes and basic assessment tools
- File uploads for course materials and assignments
- Search and category filtering for courses
- Responsive UI (templates using Django templating)

## Tech Stack

- Python (3.8+)
- Django (2.x or 3.x compatible)
- SQLite (default for development; replaceable with PostgreSQL/MySQL)
- HTML/CSS/JavaScript for frontend

## Installation (Development)

1. Clone the repository to your local machine.
2. Create and activate a virtual environment:
	- python -m venv venv
	- Windows: venv\Scripts\activate
	- macOS/Linux: source venv/bin/activate
3. Install dependencies:
	- pip install -r requirements.txt
4. Apply migrations:
	- python manage.py migrate
5. Create a superuser (admin):
	- python manage.py createsuperuser
6. Run the development server:
	- python manage.py runserver

Access the site at http://127.0.0.1:8000/ and the admin at http://127.0.0.1:8000/admin/

## Configuration

- Update DATABASES in settings.py to change the database.
- Configure MEDIA_ROOT and MEDIA_URL for file uploads.
- Set DEBUG = False and configure ALLOWED_HOSTS before production.

## Project Structure (typical)

- manage.py
- OnlineLearningSystem/ (Django project settings)
- courses/ (app for course, lesson, enrollment models)
- users/ (app for custom user profiles and authentication)
- templates/ (HTML templates)
- static/ (CSS, JS, images)
- media/ (uploaded files)

# Future Plan
What I want to add next
Payment integration for paid courses
Email notifications when a review is approved
A search bar to find courses
Certificate generation when a student finishes a course

