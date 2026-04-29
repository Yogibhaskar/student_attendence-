"""
Attendance Management System
Flask + SQLite + Bootstrap 5
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime, date, timedelta
from functools import wraps
import csv
import io
import json

app = Flask(__name__)
app.secret_key = 'attendance_secret_key_2024_secure'

DATABASE = 'attendance.db'

# ─────────────────────────────────────────────
# DATABASE HELPERS
# ─────────────────────────────────────────────

def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Initialize database with tables and seed data."""
    conn = get_db()
    c = conn.cursor()

    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'admin',
        name TEXT,
        email TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Students table
    c.execute('''CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        roll_no TEXT NOT NULL,
        department TEXT NOT NULL,
        year INTEGER NOT NULL,
        email TEXT,
        phone TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Attendance table
    c.execute('''CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'absent',
        marked_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
        UNIQUE(student_id, date)
    )''')

    # Create default admin
    existing = c.execute("SELECT id FROM users WHERE username='admin'").fetchone()
    if not existing:
        c.execute("INSERT INTO users (username, password, role, name, email) VALUES (?, ?, ?, ?, ?)",
                  ('admin', generate_password_hash('admin123'), 'admin', 'Administrator', 'admin@school.edu'))

    # Seed sample students
    sample_students = [
        ('STU001', 'Aarav Sharma',     'R001', 'Computer Science', 2, 'aarav@school.edu',   '9876543210'),
        ('STU002', 'Priya Patel',      'R002', 'Electronics',      3, 'priya@school.edu',   '9876543211'),
        ('STU003', 'Rohan Mehta',      'R003', 'Mechanical',       1, 'rohan@school.edu',   '9876543212'),
        ('STU004', 'Sneha Reddy',      'R004', 'Computer Science', 2, 'sneha@school.edu',   '9876543213'),
        ('STU005', 'Vikram Singh',     'R005', 'Civil',            4, 'vikram@school.edu',  '9876543214'),
        ('STU006', 'Ananya Gupta',     'R006', 'Electronics',      2, 'ananya@school.edu',  '9876543215'),
        ('STU007', 'Karthik Nair',     'R007', 'Mechanical',       3, 'karthik@school.edu', '9876543216'),
        ('STU008', 'Divya Iyer',       'R008', 'Computer Science', 1, 'divya@school.edu',   '9876543217'),
        ('STU009', 'Arjun Verma',      'R009', 'Civil',            2, 'arjun@school.edu',   '9876543218'),
        ('STU010', 'Meera Krishnan',   'R010', 'Electronics',      4, 'meera@school.edu',   '9876543219'),
    ]

    existing_count = c.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    if existing_count == 0:
        c.executemany(
            "INSERT OR IGNORE INTO students (student_id, name, roll_no, department, year, email, phone) VALUES (?,?,?,?,?,?,?)",
            sample_students
        )

        # Seed 30 days of attendance
        students = c.execute("SELECT id FROM students").fetchall()
        today = date.today()
        import random
        random.seed(42)
        for i in range(30, 0, -1):
            d = (today - timedelta(days=i)).strftime('%Y-%m-%d')
            for s in students:
                status = 'present' if random.random() > 0.25 else 'absent'
                c.execute("INSERT OR IGNORE INTO attendance (student_id, date, status) VALUES (?,?,?)",
                          (s['id'], d, status))

    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
# AUTH DECORATORS
# ─────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated


# ─────────────────────────────────────────────
# AUTH ROUTES
# ─────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Username and password are required.', 'danger')
            return render_template('login.html')

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['name'] = user['name'] or user['username']
            flash(f'Welcome back, {session["name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# ─────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db()
    today_str = date.today().strftime('%Y-%m-%d')

    total_students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    present_today  = conn.execute("SELECT COUNT(*) FROM attendance WHERE date=? AND status='present'", (today_str,)).fetchone()[0]
    absent_today   = conn.execute("SELECT COUNT(*) FROM attendance WHERE date=? AND status='absent'",  (today_str,)).fetchone()[0]
    attendance_pct = round((present_today / total_students * 100) if total_students else 0, 1)

    # Last 7 days trend
    trend_labels, trend_present, trend_absent = [], [], []
    for i in range(6, -1, -1):
        d = (date.today() - timedelta(days=i))
        d_str = d.strftime('%Y-%m-%d')
        p = conn.execute("SELECT COUNT(*) FROM attendance WHERE date=? AND status='present'", (d_str,)).fetchone()[0]
        a = conn.execute("SELECT COUNT(*) FROM attendance WHERE date=? AND status='absent'",  (d_str,)).fetchone()[0]
        trend_labels.append(d.strftime('%b %d'))
        trend_present.append(p)
        trend_absent.append(a)

    # Dept-wise stats
    dept_rows = conn.execute("""
        SELECT s.department,
               COUNT(DISTINCT s.id) as total,
               SUM(CASE WHEN a.status='present' THEN 1 ELSE 0 END) as present_count,
               COUNT(a.id) as total_records
        FROM students s
        LEFT JOIN attendance a ON s.id = a.student_id
        GROUP BY s.department
    """).fetchall()

    dept_data = []
    for r in dept_rows:
        pct = round((r['present_count'] / r['total_records'] * 100) if r['total_records'] else 0, 1)
        dept_data.append({'dept': r['department'], 'total': r['total'], 'pct': pct})

    # Recent attendance (last 5 records)
    recent = conn.execute("""
        SELECT s.name, s.department, a.date, a.status
        FROM attendance a JOIN students s ON a.student_id = s.id
        ORDER BY a.created_at DESC LIMIT 10
    """).fetchall()

    # Top absent students
    low_attendance = conn.execute("""
        SELECT s.name, s.student_id, s.department,
               SUM(CASE WHEN a.status='present' THEN 1 ELSE 0 END) as p,
               COUNT(a.id) as total
        FROM students s
        LEFT JOIN attendance a ON s.id = a.student_id
        GROUP BY s.id
        HAVING total > 0
        ORDER BY (p*1.0/total) ASC LIMIT 5
    """).fetchall()

    conn.close()

    return render_template('dashboard.html',
        total_students=total_students,
        present_today=present_today,
        absent_today=absent_today,
        attendance_pct=attendance_pct,
        trend_labels=json.dumps(trend_labels),
        trend_present=json.dumps(trend_present),
        trend_absent=json.dumps(trend_absent),
        dept_data=dept_data,
        recent=recent,
        low_attendance=low_attendance,
        today=date.today().strftime('%B %d, %Y')
    )


# ─────────────────────────────────────────────
# STUDENTS
# ─────────────────────────────────────────────

@app.route('/students')
@login_required
def students():
    conn = get_db()
    q = request.args.get('q', '').strip()
    dept_filter = request.args.get('dept', '').strip()

    query = "SELECT * FROM students WHERE 1=1"
    params = []
    if q:
        query += " AND (name LIKE ? OR student_id LIKE ? OR roll_no LIKE ? OR email LIKE ?)"
        like = f'%{q}%'
        params.extend([like, like, like, like])
    if dept_filter:
        query += " AND department=?"
        params.append(dept_filter)
    query += " ORDER BY name"

    student_list = conn.execute(query, params).fetchall()
    departments = conn.execute("SELECT DISTINCT department FROM students ORDER BY department").fetchall()
    conn.close()

    return render_template('students.html',
        students=student_list,
        departments=departments,
        q=q,
        dept_filter=dept_filter
    )


@app.route('/students/add', methods=['GET', 'POST'])
@login_required
def add_student():
    if request.method == 'POST':
        data = {
            'student_id': request.form.get('student_id', '').strip(),
            'name':       request.form.get('name', '').strip(),
            'roll_no':    request.form.get('roll_no', '').strip(),
            'department': request.form.get('department', '').strip(),
            'year':       request.form.get('year', '').strip(),
            'email':      request.form.get('email', '').strip(),
            'phone':      request.form.get('phone', '').strip(),
        }

        if not all([data['student_id'], data['name'], data['roll_no'], data['department'], data['year']]):
            flash('All required fields must be filled.', 'danger')
            return render_template('add_student.html', data=data, edit=False)

        conn = get_db()
        try:
            conn.execute("""
                INSERT INTO students (student_id, name, roll_no, department, year, email, phone)
                VALUES (:student_id, :name, :roll_no, :department, :year, :email, :phone)
            """, data)
            conn.commit()
            flash(f'Student "{data["name"]}" added successfully!', 'success')
            return redirect(url_for('students'))
        except sqlite3.IntegrityError:
            flash('Student ID already exists.', 'danger')
        finally:
            conn.close()

    return render_template('add_student.html', data={}, edit=False)


@app.route('/students/edit/<int:sid>', methods=['GET', 'POST'])
@login_required
def edit_student(sid):
    conn = get_db()
    student = conn.execute("SELECT * FROM students WHERE id=?", (sid,)).fetchone()
    if not student:
        conn.close()
        flash('Student not found.', 'danger')
        return redirect(url_for('students'))

    if request.method == 'POST':
        data = {
            'id':         sid,
            'student_id': request.form.get('student_id', '').strip(),
            'name':       request.form.get('name', '').strip(),
            'roll_no':    request.form.get('roll_no', '').strip(),
            'department': request.form.get('department', '').strip(),
            'year':       request.form.get('year', '').strip(),
            'email':      request.form.get('email', '').strip(),
            'phone':      request.form.get('phone', '').strip(),
        }
        try:
            conn.execute("""
                UPDATE students SET student_id=:student_id, name=:name, roll_no=:roll_no,
                department=:department, year=:year, email=:email, phone=:phone
                WHERE id=:id
            """, data)
            conn.commit()
            flash(f'Student updated successfully!', 'success')
            return redirect(url_for('students'))
        except sqlite3.IntegrityError:
            flash('Student ID already exists.', 'danger')
        finally:
            conn.close()

    conn.close()
    return render_template('add_student.html', data=dict(student), edit=True)


@app.route('/students/delete/<int:sid>', methods=['POST'])
@login_required
def delete_student(sid):
    conn = get_db()
    student = conn.execute("SELECT name FROM students WHERE id=?", (sid,)).fetchone()
    if student:
        conn.execute("DELETE FROM students WHERE id=?", (sid,))
        conn.commit()
        flash(f'Student "{student["name"]}" deleted.', 'success')
    else:
        flash('Student not found.', 'danger')
    conn.close()
    return redirect(url_for('students'))


# ─────────────────────────────────────────────
# ATTENDANCE
# ─────────────────────────────────────────────

@app.route('/attendance', methods=['GET', 'POST'])
@login_required
def attendance():
    conn = get_db()
    selected_date = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    dept_filter   = request.args.get('dept', '')

    if request.method == 'POST':
        att_date = request.form.get('att_date', date.today().strftime('%Y-%m-%d'))
        student_ids = request.form.getlist('student_ids')
        present_ids = set(request.form.getlist('present'))

        saved = 0
        for sid in student_ids:
            status = 'present' if sid in present_ids else 'absent'
            conn.execute("""
                INSERT INTO attendance (student_id, date, status, marked_by)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(student_id, date) DO UPDATE SET status=excluded.status
            """, (int(sid), att_date, status, session['user_id']))
            saved += 1

        conn.commit()
        flash(f'Attendance saved for {saved} students on {att_date}.', 'success')
        return redirect(url_for('attendance', date=att_date, dept=dept_filter))

    # Load students with their attendance for selected date
    query = """
        SELECT s.id, s.student_id, s.name, s.roll_no, s.department, s.year,
               COALESCE(a.status, '') as status
        FROM students s
        LEFT JOIN attendance a ON s.id = a.student_id AND a.date = ?
        WHERE 1=1
    """
    params = [selected_date]
    if dept_filter:
        query += " AND s.department=?"
        params.append(dept_filter)
    query += " ORDER BY s.roll_no"

    student_list = conn.execute(query, params).fetchall()
    departments  = conn.execute("SELECT DISTINCT department FROM students ORDER BY department").fetchall()

    # Stats for selected date
    total   = len(student_list)
    present = sum(1 for s in student_list if s['status'] == 'present')
    absent  = sum(1 for s in student_list if s['status'] == 'absent')
    unmarked = sum(1 for s in student_list if s['status'] == '')

    conn.close()

    return render_template('attendance.html',
        students=student_list,
        departments=departments,
        selected_date=selected_date,
        dept_filter=dept_filter,
        total=total, present=present, absent=absent, unmarked=unmarked,
        today_iso=date.today().strftime('%Y-%m-%d')
    )


# ─────────────────────────────────────────────
# REPORTS
# ─────────────────────────────────────────────

@app.route('/reports')
@login_required
def reports():
    conn = get_db()
    report_type = request.args.get('type', 'daily')
    selected_date = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    selected_month = request.args.get('month', date.today().strftime('%Y-%m'))
    student_filter = request.args.get('student_id', '')

    rows = []
    title = ''

    if report_type == 'daily':
        title = f'Daily Report — {selected_date}'
        rows = conn.execute("""
            SELECT s.student_id, s.name, s.roll_no, s.department, s.year,
                   COALESCE(a.status, 'unmarked') as status
            FROM students s
            LEFT JOIN attendance a ON s.id = a.student_id AND a.date = ?
            ORDER BY s.department, s.roll_no
        """, (selected_date,)).fetchall()

    elif report_type == 'monthly':
        title = f'Monthly Report — {selected_month}'
        year, month = selected_month.split('-')
        rows = conn.execute("""
            SELECT s.student_id, s.name, s.roll_no, s.department,
                   SUM(CASE WHEN a.status='present' THEN 1 ELSE 0 END) as present_days,
                   COUNT(a.id) as total_days,
                   ROUND(SUM(CASE WHEN a.status='present' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(a.id),0), 1) as pct
            FROM students s
            LEFT JOIN attendance a ON s.id = a.student_id
                AND strftime('%Y', a.date) = ? AND strftime('%m', a.date) = ?
            GROUP BY s.id ORDER BY s.department, s.roll_no
        """, (year, month)).fetchall()

    elif report_type == 'student':
        title = 'Student-wise Attendance Report'
        rows = conn.execute("""
            SELECT s.student_id, s.name, s.roll_no, s.department, s.year,
                   SUM(CASE WHEN a.status='present' THEN 1 ELSE 0 END) as present_days,
                   SUM(CASE WHEN a.status='absent'  THEN 1 ELSE 0 END) as absent_days,
                   COUNT(a.id) as total_days,
                   ROUND(SUM(CASE WHEN a.status='present' THEN 1 ELSE 0 END)*100.0/NULLIF(COUNT(a.id),0),1) as pct
            FROM students s
            LEFT JOIN attendance a ON s.id = a.student_id
            GROUP BY s.id ORDER BY pct ASC
        """).fetchall()

    students_list = conn.execute("SELECT id, student_id, name FROM students ORDER BY name").fetchall()
    conn.close()

    return render_template('reports.html',
        rows=rows, title=title,
        report_type=report_type,
        selected_date=selected_date,
        selected_month=selected_month,
        student_filter=student_filter,
        students_list=students_list
    )


@app.route('/reports/export/csv')
@login_required
def export_csv():
    conn = get_db()
    report_type = request.args.get('type', 'daily')
    selected_date = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    selected_month = request.args.get('month', date.today().strftime('%Y-%m'))

    output = io.StringIO()
    writer = csv.writer(output)

    if report_type == 'daily':
        writer.writerow(['Student ID', 'Name', 'Roll No', 'Department', 'Year', 'Status'])
        rows = conn.execute("""
            SELECT s.student_id, s.name, s.roll_no, s.department, s.year,
                   COALESCE(a.status,'unmarked') as status
            FROM students s LEFT JOIN attendance a ON s.id=a.student_id AND a.date=?
            ORDER BY s.department, s.roll_no
        """, (selected_date,)).fetchall()
        for r in rows:
            writer.writerow([r['student_id'], r['name'], r['roll_no'], r['department'], r['year'], r['status']])
        filename = f'attendance_{selected_date}.csv'

    elif report_type == 'monthly':
        writer.writerow(['Student ID', 'Name', 'Roll No', 'Department', 'Present Days', 'Total Days', 'Percentage'])
        year, month = selected_month.split('-')
        rows = conn.execute("""
            SELECT s.student_id, s.name, s.roll_no, s.department,
                   SUM(CASE WHEN a.status='present' THEN 1 ELSE 0 END) as p,
                   COUNT(a.id) as t,
                   ROUND(SUM(CASE WHEN a.status='present' THEN 1 ELSE 0 END)*100.0/NULLIF(COUNT(a.id),0),1) as pct
            FROM students s LEFT JOIN attendance a ON s.id=a.student_id
                AND strftime('%Y',a.date)=? AND strftime('%m',a.date)=?
            GROUP BY s.id ORDER BY s.department, s.roll_no
        """, (year, month)).fetchall()
        for r in rows:
            writer.writerow([r['student_id'], r['name'], r['roll_no'], r['department'], r['p'], r['t'], f"{r['pct']}%"])
        filename = f'attendance_{selected_month}.csv'
    else:
        writer.writerow(['Student ID', 'Name', 'Department', 'Present', 'Absent', 'Total', 'Percentage'])
        rows = conn.execute("""
            SELECT s.student_id, s.name, s.department,
                   SUM(CASE WHEN a.status='present' THEN 1 ELSE 0 END) as p,
                   SUM(CASE WHEN a.status='absent'  THEN 1 ELSE 0 END) as ab,
                   COUNT(a.id) as t,
                   ROUND(SUM(CASE WHEN a.status='present' THEN 1 ELSE 0 END)*100.0/NULLIF(COUNT(a.id),0),1) as pct
            FROM students s LEFT JOIN attendance a ON s.id=a.student_id
            GROUP BY s.id ORDER BY pct
        """).fetchall()
        for r in rows:
            writer.writerow([r['student_id'], r['name'], r['department'], r['p'], r['ab'], r['t'], f"{r['pct']}%"])
        filename = 'attendance_student_report.csv'

    conn.close()
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    response.headers['Content-type'] = 'text/csv'
    return response


# ─────────────────────────────────────────────
# API ENDPOINTS (JSON)
# ─────────────────────────────────────────────

@app.route('/api/attendance/stats')
@login_required
def api_stats():
    """Return last 30 days attendance data for charts."""
    conn = get_db()
    labels, present_data, absent_data = [], [], []
    for i in range(29, -1, -1):
        d = (date.today() - timedelta(days=i))
        d_str = d.strftime('%Y-%m-%d')
        p = conn.execute("SELECT COUNT(*) FROM attendance WHERE date=? AND status='present'", (d_str,)).fetchone()[0]
        a = conn.execute("SELECT COUNT(*) FROM attendance WHERE date=? AND status='absent'",  (d_str,)).fetchone()[0]
        labels.append(d.strftime('%b %d'))
        present_data.append(p)
        absent_data.append(a)
    conn.close()
    return jsonify({'labels': labels, 'present': present_data, 'absent': absent_data})


@app.route('/api/student/<int:sid>/attendance')
@login_required
def api_student_attendance(sid):
    conn = get_db()
    records = conn.execute("""
        SELECT date, status FROM attendance
        WHERE student_id=? ORDER BY date DESC LIMIT 30
    """, (sid,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in records])


# ─────────────────────────────────────────────
# STUDENT PORTAL
# ─────────────────────────────────────────────

@app.route('/portal', methods=['GET', 'POST'])
def student_portal():
    if request.method == 'POST':
        student_id = request.form.get('student_id', '').strip().upper()
        conn = get_db()
        student = conn.execute("SELECT * FROM students WHERE student_id=?", (student_id,)).fetchone()

        if not student:
            conn.close()
            flash('Student ID not found.', 'danger')
            return render_template('portal.html', student=None)

        records = conn.execute("""
            SELECT date, status FROM attendance
            WHERE student_id=? ORDER BY date DESC
        """, (student['id'],)).fetchall()

        total   = len(records)
        present = sum(1 for r in records if r['status'] == 'present')
        absent  = total - present
        pct     = round((present / total * 100) if total else 0, 1)

        # Monthly breakdown
        monthly = conn.execute("""
            SELECT strftime('%Y-%m', date) as month,
                   SUM(CASE WHEN status='present' THEN 1 ELSE 0 END) as p,
                   COUNT(*) as t
            FROM attendance WHERE student_id=?
            GROUP BY month ORDER BY month DESC LIMIT 6
        """, (student['id'],)).fetchall()

        conn.close()
        return render_template('portal.html',
            student=dict(student), records=records,
            total=total, present=present, absent=absent, pct=pct,
            monthly=monthly
        )

    return render_template('portal.html', student=None)


# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    else:
        # Ensure schema is up to date
        init_db()
    print("=" * 50)
    print("  Attendance Management System")
    print("  http://127.0.0.1:5000")
    print("  Admin: admin / admin123")
    print("=" * 50)
    app.run(debug=True, port=5000)
