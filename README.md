Cafeteria Management System
This is a comprehensive Cafeteria Management System designed to streamline meal planning, track employee attendance, and manage overtime requests. The application features a robust backend built with FastAPI, a user-friendly web interface for employees and administrators, and a standalone desktop application for administrative tasks.

Features
Web Application
User Authentication: Secure login for regular users, managers, and administrators.

Role-Based Access Control:

Users: Can view daily/weekly/monthly menus, mark their attendance for meals, and submit overtime requests to their managers.

Managers: Can view and approve/reject overtime requests from their team members.

Admins: Have full control over the system, including user management, menu planning, viewing all overtime requests, and generating attendance reports.

Menu Management (Admin):

Manually create, update, and delete daily meal plans.

Bulk import menus from an Excel file (.xlsx).

Download an Excel template for easy menu creation.

Attendance Tracking:

Users can indicate whether they will be attending a meal on a given day.

Admins can view and generate reports on who will be attending on any given day.

Overtime Request System:

Employees can submit detailed overtime requests.

Managers receive email notifications and can approve or reject requests.

Admins (HR) have the final say on approving or rejecting manager-approved requests, with email notifications sent to the employee.

Desktop Application
A standalone Qt-based application (built with PySide6) that provides an alternative interface for all administrative and manager functionalities.

Admin Panel:

Dashboard with key statistics (total users, daily attendance).

Full user management (create, edit, delete users).

Menu planning (manual entry and Excel import/export).

Overtime request management.

Attendance report generation.

Manager Panel:

Dashboard with team-specific statistics.

View and manage overtime requests for direct reports.

Generate attendance reports for the team.

Technologies Used
Backend:

FastAPI

SQLAlchemy (with SQLite)

Pydantic

Passlib & python-jose for authentication (JWT)

Frontend (Web):

HTML5

Tailwind CSS (in user-menu.html)

Vanilla JavaScript

Desktop App:

PySide6 (Qt for Python)

Other:

Uvicorn (ASGI server)

Pandas & Openpyxl for Excel operations

python-dotenv for environment variable management

Setup and Installation
Follow these steps to get the project running on your local machine.

Clone the Repository:

Bash

git clone <your-repository-url>
cd Staj_Projesi-29236e5f3a893b4c0ec2f04ff4f42e4b22bdc657
Create a Virtual Environment:
It's recommended to use a virtual environment to manage dependencies.

Bash

python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
Install Dependencies:
Install all the required packages from the requirements.txt file.

Bash

pip install -r requirements.txt
Set Up Environment Variables:
Create a .env file in the root directory of the project. This file is used to store sensitive information like email credentials and a secret key for JWT.

SECRET_KEY=your_very_secret_and_long_random_string
MAIL_PASSWORD=your_gmail_app_password
HR_EMAIL=hr_department_email@example.com
SECRET_KEY: A long, random string. You can generate one easily online.

MAIL_PASSWORD: An "App Password" for your Google account if you are using 2-Factor Authentication.

HR_EMAIL: The email address that will receive notifications for HR approval.

Initialize the Database:
Run the init_db.py script to create the SQLite database (site.db) and populate it with initial admin and test users.

Bash

python init_db.py
Usage
Running the Web Application
Start the FastAPI Server:

Bash

uvicorn app:app --reload
The application will be available at http://127.0.0.1:8000.

Access the Web Interface:

Open index.html in your web browser to access the login page.

Default Login Credentials:

Admin:

Username: admin

Password: admin123

Test User:

Username: test

Password: test123

Running the Desktop Application
Launch the Desktop App:
Ensure your virtual environment is activated and all dependencies are installed. Then, run the desktop_app.py script.

Bash

python desktop_app.py
The desktop application will launch, and you can log in using the same credentials as the web application.
