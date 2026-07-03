# -*- coding: utf-8 -*-
"""
CRM Web Application - Flask + MySQL
Đồ án môn Cơ sở Ứng dụng HTTT - Nhóm 07 - NLU 2024
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
import mysql.connector
from mysql.connector import Error
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'crm_nlu_nhom07_2024_secret_key_fixed'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE']   = False

# ─── Decorator kiểm tra đăng nhập ──────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            flash('Vui lòng đăng nhập!', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('Bạn không có quyền thực hiện thao tác này!', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated

def employee_required(f):
    """Cho phép admin và employee, chặn guest."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        if session.get('role') == 'guest':
            flash('Khách không có quyền thực hiện thao tác này!', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated

# ─── Cấu hình kết nối MySQL ────────────────────────────────
DB_CONFIG = {
    'host':     'localhost',
    'user':     'root',
    'password': '',          # Đổi thành mật khẩu MySQL của bạn
    'database': 'crm_db',
    'charset':  'utf8mb4'
}

def get_db():
    """Tạo kết nối database."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Lỗi kết nối DB: {e}")
        return None

def query(sql, params=None, fetch='all'):
    """Hàm tiện ích thực thi SQL."""
    conn = get_db()
    if not conn:
        return [] if fetch == 'all' else None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params or ())
        if fetch == 'all':
            return cur.fetchall()
        elif fetch == 'one':
            return cur.fetchone()
        else:
            conn.commit()
            return cur.lastrowid
    except Error as e:
        print(f"Lỗi SQL: {e}")
        conn.rollback()
        return [] if fetch == 'all' else None
    finally:
        conn.close()

def log_activity(action, module, description):
    """Ghi log hoạt động người dùng."""
    if 'user' not in session:
        return
    try:
        ip = request.remote_addr or 'unknown'
        query("""
            INSERT INTO ActivityLog (Username, FullName, Action, Module, Description, IPAddress)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            session.get('user'), session.get('name'),
            action, module, description, ip
        ), fetch='commit')
    except:
        pass  # Log lỗi không được làm crash app

def is_admin():
    return session.get('role') == 'admin'

def is_employee():
    return session.get('role') in ('admin', 'employee')

def my_employee_id():
    """Trả về EmployeeID của user đang đăng nhập (nếu có)."""
    return session.get('employee_id')

# ─── ĐĂNG NHẬP / ĐĂNG XUẤT ────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        # Kiểm tra tài khoản tồn tại nhưng chưa duyệt
        pending = query(
            "SELECT * FROM Users WHERE Username=%s AND Password=%s AND Status='Inactive'",
            (username, password), fetch='one'
        )
        if pending:
            flash('Tài khoản của bạn đang chờ admin duyệt!', 'warning')
            return render_template('login.html')
        user = query(
            "SELECT * FROM Users WHERE Username=%s AND Password=%s AND Status='Active'",
            (username, password), fetch='one'
        )
        if user:
            session['user']        = user['Username']
            session['role']        = user['Role']
            session['name']        = user['FullName']
            session['employee_id'] = user['EmployeeID']
            log_activity('LOGIN', 'Auth', f'Đăng nhập thành công')
            flash(f'Xin chào, {user["FullName"]}!', 'success')
            return redirect(url_for('index'))
        flash('Tên đăng nhập hoặc mật khẩu không đúng!', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm  = request.form.get('confirm', '').strip()
        fullname = request.form.get('fullname', '').strip()

        # Validate
        if not username or not password or not fullname:
            flash('Vui lòng điền đầy đủ thông tin!', 'danger')
        elif len(username) < 4:
            flash('Tên đăng nhập phải có ít nhất 4 ký tự!', 'danger')
        elif len(password) < 6:
            flash('Mật khẩu phải có ít nhất 6 ký tự!', 'danger')
        elif password != confirm:
            flash('Mật khẩu xác nhận không khớp!', 'danger')
        else:
            # Kiểm tra username đã tồn tại chưa
            existing = query("SELECT UserID FROM Users WHERE Username=%s",
                           (username,), fetch='one')
            if existing:
                flash('Tên đăng nhập đã tồn tại, vui lòng chọn tên khác!', 'danger')
            else:
                query("""
                    INSERT INTO Users (Username, Password, Role, FullName, Status)
                    VALUES (%s, %s, 'guest', %s, 'Inactive')
                """, (username, password, fullname), fetch='commit')
                flash('Đăng ký thành công! Vui lòng chờ admin duyệt tài khoản.', 'success')
                return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    log_activity('LOGOUT', 'Auth', 'Đăng xuất')
    session.clear()
    flash('Đã đăng xuất.', 'info')
    return redirect(url_for('login'))

# ─── QUẢN LÝ TÀI KHOẢN ─────────────────────────────────────
@app.route('/users')
@admin_required
def users():
    all_users = query("""
        SELECT u.*, e.FullName AS emp_name, e.Department
        FROM Users u
        LEFT JOIN Employees e ON u.EmployeeID = e.EmployeeID
        ORDER BY u.Status DESC, u.Role, u.Username
    """)
    pending_count = sum(1 for u in all_users if u['Status'] == 'Inactive')
    return render_template('users.html', users=all_users, pending_count=pending_count)

@app.route('/users/add', methods=['GET', 'POST'])
@admin_required
def add_user():
    employees = query("""
        SELECT e.EmployeeID, e.FullName, e.Department
        FROM Employees e
        WHERE e.Status='Active'
        AND e.EmployeeID NOT IN (SELECT EmployeeID FROM Users WHERE EmployeeID IS NOT NULL)
        ORDER BY e.FullName
    """)
    if request.method == 'POST':
        # Kiểm tra username đã tồn tại chưa
        existing = query("SELECT UserID FROM Users WHERE Username=%s",
                        (request.form['username'],), fetch='one')
        if existing:
            flash('Tên đăng nhập đã tồn tại!', 'danger')
        else:
            query("""
                INSERT INTO Users (Username, Password, Role, EmployeeID, FullName)
                VALUES (%s,%s,%s,%s,%s)
            """, (
                request.form['username'],
                request.form['password'],
                request.form['role'],
                request.form['employee_id'] or None,
                request.form['fullname'],
            ), fetch='commit')
            flash('Đã tạo tài khoản!', 'success')
            return redirect(url_for('users'))
    return render_template('user_form.html', user=None, employees=employees)

@app.route('/users/edit/<int:uid>', methods=['GET', 'POST'])
@admin_required
def edit_user(uid):
    user      = query("SELECT * FROM Users WHERE UserID=%s", (uid,), fetch='one')
    employees = query("SELECT EmployeeID, FullName, Department FROM Employees WHERE Status='Active' ORDER BY FullName")
    if request.method == 'POST':
        new_pass = request.form['password'].strip()
        if new_pass:
            query("""
                UPDATE Users SET Username=%s, Password=%s, Role=%s,
                EmployeeID=%s, FullName=%s, Status=%s WHERE UserID=%s
            """, (
                request.form['username'], new_pass,
                request.form['role'],
                request.form['employee_id'] or None,
                request.form['fullname'],
                request.form['status'], uid
            ), fetch='commit')
        else:
            query("""
                UPDATE Users SET Username=%s, Role=%s,
                EmployeeID=%s, FullName=%s, Status=%s WHERE UserID=%s
            """, (
                request.form['username'],
                request.form['role'],
                request.form['employee_id'] or None,
                request.form['fullname'],
                request.form['status'], uid
            ), fetch='commit')
        flash('Đã cập nhật tài khoản!', 'success')
        return redirect(url_for('users'))
    return render_template('user_form.html', user=user, employees=employees)

@app.route('/users/approve/<int:uid>', methods=['POST'])
@admin_required
def approve_user(uid):
    role = request.form.get('role', 'guest')
    query("UPDATE Users SET Status='Active', Role=%s WHERE UserID=%s",
          (role, uid), fetch='commit')
    user = query("SELECT FullName FROM Users WHERE UserID=%s", (uid,), fetch='one')
    log_activity('UPDATE','User',f'Duyệt tài khoản: {user["FullName"]} với role {role}')
    flash(f'Đã duyệt tài khoản {user["FullName"]}!', 'success')
    return redirect(url_for('users'))

@app.route('/users/delete/<int:uid>', methods=['POST'])
@admin_required
def delete_user(uid):
    # Không cho xóa tài khoản admin duy nhất
    admin_count = query("SELECT COUNT(*) AS c FROM Users WHERE Role='admin' AND Status='Active'", fetch='one')['c']
    current_user = query("SELECT Role FROM Users WHERE UserID=%s", (uid,), fetch='one')
    if current_user and current_user['Role'] == 'admin' and admin_count <= 1:
        flash('Không thể xóa tài khoản admin duy nhất!', 'danger')
        return redirect(url_for('users'))
    query("DELETE FROM Users WHERE UserID=%s", (uid,), fetch='commit')
    flash('Đã xóa tài khoản.', 'warning')
    return redirect(url_for('users'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Trang đổi mật khẩu cho người dùng hiện tại."""
    if request.method == 'POST':
        old_pass = request.form['old_password'].strip()
        new_pass = request.form['new_password'].strip()
        confirm  = request.form['confirm_password'].strip()
        user = query(
            "SELECT * FROM Users WHERE Username=%s AND Password=%s",
            (session['user'], old_pass), fetch='one'
        )
        if not user:
            flash('Mật khẩu cũ không đúng!', 'danger')
        elif new_pass != confirm:
            flash('Mật khẩu mới không khớp!', 'danger')
        elif len(new_pass) < 6:
            flash('Mật khẩu mới phải có ít nhất 6 ký tự!', 'danger')
        else:
            query("UPDATE Users SET Password=%s WHERE Username=%s",
                  (new_pass, session['user']), fetch='commit')
            flash('Đã đổi mật khẩu thành công!', 'success')
    return render_template('profile.html')

# ─── TRANG CHỦ ─────────────────────────────────────────────
@app.route('/')
@login_required
def index():
    # Thống kê tổng quan
    stats = {
        'customers':    query("SELECT COUNT(*) AS c FROM Customers",    fetch='one')['c'],
        'employees':    query("SELECT COUNT(*) AS c FROM Employees",    fetch='one')['c'],
        'open_opps':    query("SELECT COUNT(*) AS c FROM Opportunities WHERE Stage NOT IN ('Closed Won','Closed Lost')", fetch='one')['c'],
        'won_value':    query("SELECT IFNULL(SUM(Value),0) AS v FROM Opportunities WHERE Stage='Closed Won'", fetch='one')['v'],
        'open_tickets': query("SELECT COUNT(*) AS c FROM SupportTickets WHERE Status IN ('Open','In Progress')", fetch='one')['c'],
        'interactions': query("SELECT COUNT(*) AS c FROM Interactions", fetch='one')['c'],
    }
    # Pipeline theo giai đoạn
    pipeline = query("""
        SELECT Stage, COUNT(*) AS count, IFNULL(SUM(Value),0) AS total_value
        FROM Opportunities
        GROUP BY Stage
        ORDER BY FIELD(Stage,'Lead','Qualified','Proposal','Negotiation','Closed Won','Closed Lost')
    """)
    # Tương tác gần đây
    recent_interactions = query("""
        SELECT i.Subject, i.Type, i.InteractedAt,
               c.FullName AS customer, e.FullName AS employee
        FROM Interactions i
        JOIN Customers c ON i.CustomerID = c.CustomerID
        JOIN Employees e ON i.EmployeeID = e.EmployeeID
        ORDER BY i.InteractedAt DESC LIMIT 5
    """)
    return render_template('index.html', stats=stats,
                           pipeline=pipeline, recent=recent_interactions)

# ─── HÀM HỖ TRỢ PHÂN TRANG ───────────────────────────────
def paginate(data, page, per_page=10):
    """Phân trang danh sách."""
    total   = len(data)
    pages   = max(1, (total + per_page - 1) // per_page)
    page    = max(1, min(page, pages))
    start   = (page - 1) * per_page
    items   = data[start:start + per_page]
    return {
        'items':    items,
        'page':     page,
        'pages':    pages,
        'total':    total,
        'per_page': per_page,
        'has_prev': page > 1,
        'has_next': page < pages,
    }

# ─── TÌM KIẾM TOÀN CỤC ────────────────────────────────────
@app.route('/search')
@login_required
def search():
    q = request.args.get('q', '').strip()
    results = {'customers': [], 'opportunities': [], 'interactions': [], 'tickets': []}
    if q:
        like = f'%{q}%'
        results['customers'] = query("""
            SELECT CustomerID, FullName, Company, Email, Segment
            FROM Customers WHERE FullName LIKE %s OR Company LIKE %s OR Email LIKE %s
            LIMIT 5
        """, (like, like, like))
        results['opportunities'] = query("""
            SELECT o.OpportunityID, o.Title, o.Stage, c.FullName AS customer
            FROM Opportunities o JOIN Customers c ON o.CustomerID=c.CustomerID
            WHERE o.Title LIKE %s OR c.FullName LIKE %s LIMIT 5
        """, (like, like))
        results['interactions'] = query("""
            SELECT i.InteractionID, i.Subject, i.Type, c.FullName AS customer
            FROM Interactions i JOIN Customers c ON i.CustomerID=c.CustomerID
            WHERE i.Subject LIKE %s OR c.FullName LIKE %s LIMIT 5
        """, (like, like))
        results['tickets'] = query("""
            SELECT t.TicketID, t.Subject, t.Status, c.FullName AS customer
            FROM SupportTickets t JOIN Customers c ON t.CustomerID=c.CustomerID
            WHERE t.Subject LIKE %s OR c.FullName LIKE %s LIMIT 5
        """, (like, like))
    return render_template('search.html', results=results, q=q)

# ─── KHÁCH HÀNG ────────────────────────────────────────────
@app.route('/customers')
@login_required
def customers():
    # Lấy tham số lọc + tìm kiếm + phân trang
    q        = request.args.get('q', '').strip()
    segment  = request.args.get('segment', '')
    assigned = request.args.get('assigned', '')
    page     = int(request.args.get('page', 1))

    sql = """
        SELECT c.*, e.FullName AS employee_name,
               COUNT(DISTINCT o.OpportunityID) AS opp_count,
               COUNT(DISTINCT t.TicketID)      AS ticket_count
        FROM Customers c
        LEFT JOIN Employees e   ON c.AssignedTo = e.EmployeeID
        LEFT JOIN Opportunities o ON c.CustomerID = o.CustomerID
        LEFT JOIN SupportTickets t ON c.CustomerID = t.CustomerID
        WHERE 1=1
    """
    params = []
    if q:
        sql += " AND (c.FullName LIKE %s OR c.Company LIKE %s OR c.Email LIKE %s OR c.Phone LIKE %s)"
        like = f'%{q}%'
        params += [like, like, like, like]
    if segment:
        sql += " AND c.Segment = %s"
        params.append(segment)
    if assigned:
        sql += " AND c.AssignedTo = %s"
        params.append(assigned)
    sql += " GROUP BY c.CustomerID ORDER BY c.CreatedAt DESC"

    all_customers = query(sql, params)
    paged         = paginate(all_customers, page)
    employees_list = query("SELECT EmployeeID, FullName FROM Employees WHERE Status='Active' ORDER BY FullName")

    return render_template('customers.html',
                           customers=paged['items'], paged=paged,
                           segment=segment, assigned=assigned, q=q,
                           employees_list=employees_list)

@app.route('/customers/add', methods=['GET', 'POST'])
@admin_required
@admin_required
def add_customer():
    employees = query("SELECT EmployeeID, FullName FROM Employees WHERE Status='Active' ORDER BY FullName")
    if request.method == 'POST':
        query("""
            INSERT INTO Customers (FullName, Email, Phone, Company, Segment, Source, AssignedTo)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (
            request.form['fullname'], request.form['email'],
            request.form['phone'],    request.form['company'],
            request.form['segment'],  request.form['source'],
            request.form['assigned_to'] or None
        ), fetch='commit')
        log_activity('CREATE','Customer',f'Thêm khách hàng: {request.form["fullname"]}')
        flash('Đã thêm khách hàng thành công!', 'success')
        return redirect(url_for('customers'))
    return render_template('customer_form.html', employees=employees, customer=None)

@app.route('/customers/<int:cid>')
@login_required
def customer_detail(cid):
    customer = query("SELECT * FROM Customers WHERE CustomerID=%s", (cid,), fetch='one')
    if not customer:
        flash('Không tìm thấy khách hàng.', 'danger')
        return redirect(url_for('customers'))
    opps    = query("SELECT o.*, p.ProductName, e.FullName AS emp FROM Opportunities o LEFT JOIN Products p ON o.ProductID=p.ProductID LEFT JOIN Employees e ON o.EmployeeID=e.EmployeeID WHERE o.CustomerID=%s ORDER BY o.CreatedAt DESC", (cid,))
    inters  = query("SELECT i.*, e.FullName AS emp FROM Interactions i JOIN Employees e ON i.EmployeeID=e.EmployeeID WHERE i.CustomerID=%s ORDER BY i.InteractedAt DESC", (cid,))
    tickets = query("SELECT t.*, e.FullName AS emp FROM SupportTickets t LEFT JOIN Employees e ON t.EmployeeID=e.EmployeeID WHERE t.CustomerID=%s ORDER BY t.CreatedAt DESC", (cid,))
    return render_template('customer_detail.html', customer=customer,
                           opportunities=opps, interactions=inters, tickets=tickets)

@app.route('/customers/edit/<int:cid>', methods=['GET', 'POST'])
@admin_required
def edit_customer(cid):
    customer  = query("SELECT * FROM Customers WHERE CustomerID=%s", (cid,), fetch='one')
    employees = query("SELECT EmployeeID, FullName FROM Employees WHERE Status='Active' ORDER BY FullName")
    if request.method == 'POST':
        query("""
            UPDATE Customers SET FullName=%s, Email=%s, Phone=%s,
            Company=%s, Segment=%s, Source=%s, AssignedTo=%s
            WHERE CustomerID=%s
        """, (
            request.form['fullname'], request.form['email'],
            request.form['phone'],    request.form['company'],
            request.form['segment'],  request.form['source'],
            request.form['assigned_to'] or None, cid
        ), fetch='commit')
        log_activity('UPDATE','Customer',f'Cập nhật khách hàng ID {cid}')
        flash('Đã cập nhật khách hàng!', 'success')
        return redirect(url_for('customer_detail', cid=cid))
    return render_template('customer_form.html', customer=customer, employees=employees)

@app.route('/customers/delete/<int:cid>', methods=['POST'])
@admin_required
def delete_customer(cid):
    query("DELETE FROM SupportTickets  WHERE CustomerID=%s", (cid,), fetch='commit')
    query("DELETE FROM Interactions    WHERE CustomerID=%s", (cid,), fetch='commit')
    query("DELETE FROM Opportunities   WHERE CustomerID=%s", (cid,), fetch='commit')
    query("DELETE FROM Customers       WHERE CustomerID=%s", (cid,), fetch='commit')
    log_activity('DELETE','Customer',f'Xóa khách hàng ID {cid}')
    flash('Đã xóa khách hàng.', 'warning')
    return redirect(url_for('customers'))

# ─── CƠ HỘI BÁN HÀNG (PIPELINE) ───────────────────────────
@app.route('/opportunities')
@login_required
def opportunities():
    q        = request.args.get('q', '').strip()
    stage    = request.args.get('stage', '')
    employee = request.args.get('employee', '')
    page     = int(request.args.get('page', 1))

    sql = """
        SELECT o.*, c.FullName AS customer, c.Company,
               e.FullName AS employee, p.ProductName
        FROM Opportunities o
        JOIN Customers c ON o.CustomerID = c.CustomerID
        JOIN Employees e ON o.EmployeeID = e.EmployeeID
        LEFT JOIN Products p ON o.ProductID = p.ProductID
        WHERE 1=1
    """
    params = []
    if q:
        sql += " AND (o.Title LIKE %s OR c.FullName LIKE %s OR c.Company LIKE %s)"
        like = f'%{q}%'
        params += [like, like, like]
    if stage:
        sql += " AND o.Stage = %s"
        params.append(stage)
    if employee:
        sql += " AND o.EmployeeID = %s"
        params.append(employee)
    sql += " ORDER BY o.CreatedAt DESC"

    all_opps       = query(sql, params)
    paged          = paginate(all_opps, page)
    stages         = ['Lead','Qualified','Proposal','Negotiation','Closed Won','Closed Lost']
    employees_list = query("SELECT EmployeeID, FullName FROM Employees WHERE Status='Active' ORDER BY FullName")

    return render_template('opportunities.html',
                           opportunities=paged['items'], paged=paged,
                           stages=stages, current_stage=stage,
                           q=q, employee=employee,
                           employees_list=employees_list)

@app.route('/opportunities/add', methods=['GET', 'POST'])
@admin_required
def add_opportunity():
    customers = query("SELECT CustomerID, FullName, Company FROM Customers ORDER BY FullName")
    employees = query("SELECT EmployeeID, FullName FROM Employees WHERE Status='Active' ORDER BY FullName")
    products  = query("SELECT ProductID, ProductName, Price FROM Products WHERE Status='Active' ORDER BY ProductName")
    if request.method == 'POST':
        query("""
            INSERT INTO Opportunities
            (CustomerID, EmployeeID, ProductID, Title, Stage, Value, Probability, ExpectedClose, Notes)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            request.form['customer_id'],   request.form['employee_id'],
            request.form['product_id'] or None, request.form['title'],
            request.form['stage'],         request.form['value'],
            request.form['probability'],   request.form['expected_close'] or None,
            request.form['notes']
        ), fetch='commit')
        log_activity('CREATE','Opportunity',f'Thêm cơ hội: {request.form["title"]}')
        flash('Đã thêm cơ hội bán hàng!', 'success')
        return redirect(url_for('opportunities'))
    return render_template('opportunity_form.html',
                           customers=customers, employees=employees,
                           products=products, opp=None)

@app.route('/opportunities/edit/<int:oid>', methods=['GET', 'POST'])
@admin_required
def edit_opportunity(oid):
    opp       = query("SELECT * FROM Opportunities WHERE OpportunityID=%s", (oid,), fetch='one')
    customers = query("SELECT CustomerID, FullName, Company FROM Customers ORDER BY FullName")
    employees = query("SELECT EmployeeID, FullName FROM Employees WHERE Status='Active' ORDER BY FullName")
    products  = query("SELECT ProductID, ProductName, Price FROM Products WHERE Status='Active' ORDER BY ProductName")
    if request.method == 'POST':
        closed_at = None
        if request.form['stage'] in ('Closed Won', 'Closed Lost'):
            closed_at = datetime.now()
        query("""
            UPDATE Opportunities SET CustomerID=%s, EmployeeID=%s, ProductID=%s,
            Title=%s, Stage=%s, Value=%s, Probability=%s, ExpectedClose=%s,
            Notes=%s, ClosedAt=%s WHERE OpportunityID=%s
        """, (
            request.form['customer_id'],   request.form['employee_id'],
            request.form['product_id'] or None, request.form['title'],
            request.form['stage'],         request.form['value'],
            request.form['probability'],   request.form['expected_close'] or None,
            request.form['notes'],         closed_at, oid
        ), fetch='commit')
        log_activity('UPDATE','Opportunity',f'Cập nhật cơ hội ID {oid}')
        flash('Đã cập nhật cơ hội!', 'success')
        return redirect(url_for('opportunities'))
    return render_template('opportunity_form.html',
                           customers=customers, employees=employees,
                           products=products, opp=opp)

# ─── TƯƠNG TÁC ─────────────────────────────────────────────
@app.route('/interactions')
@login_required
def interactions():
    q        = request.args.get('q', '').strip()
    itype    = request.args.get('type', '')
    page     = int(request.args.get('page', 1))

    sql = """
        SELECT i.*, c.FullName AS customer, c.Company,
               e.FullName AS employee
        FROM Interactions i
        JOIN Customers c ON i.CustomerID = c.CustomerID
        JOIN Employees e ON i.EmployeeID = e.EmployeeID
        WHERE 1=1
    """
    params = []
    if q:
        sql += " AND (i.Subject LIKE %s OR c.FullName LIKE %s OR c.Company LIKE %s)"
        like = f'%{q}%'
        params += [like, like, like]
    if itype:
        sql += " AND i.Type = %s"
        params.append(itype)
    sql += " ORDER BY i.InteractedAt DESC"

    all_inters = query(sql, params)
    paged      = paginate(all_inters, page)

    return render_template('interactions.html',
                           interactions=paged['items'], paged=paged,
                           q=q, itype=itype)

@app.route('/interactions/add', methods=['GET', 'POST'])
@admin_required
def add_interaction():
    customers = query("SELECT CustomerID, FullName, Company FROM Customers ORDER BY FullName")
    employees = query("SELECT EmployeeID, FullName FROM Employees WHERE Status='Active' ORDER BY FullName")
    if request.method == 'POST':
        query("""
            INSERT INTO Interactions (CustomerID, EmployeeID, Type, Subject, Notes)
            VALUES (%s,%s,%s,%s,%s)
        """, (
            request.form['customer_id'], request.form['employee_id'],
            request.form['type'],        request.form['subject'],
            request.form['notes']
        ), fetch='commit')
        log_activity('CREATE','Interaction',f'Ghi nhận tương tác: {request.form["subject"]}')
        flash('Đã ghi nhận tương tác!', 'success')
        return redirect(url_for('interactions'))
    return render_template('interaction_form.html', customers=customers, employees=employees)

# ─── TICKET HỖ TRỢ ─────────────────────────────────────────
@app.route('/tickets')
@login_required
def tickets():
    q        = request.args.get('q', '').strip()
    status   = request.args.get('status', '')
    priority = request.args.get('priority', '')
    page     = int(request.args.get('page', 1))

    sql = """
        SELECT t.*, c.FullName AS customer, c.Company,
               e.FullName AS employee
        FROM SupportTickets t
        JOIN Customers c ON t.CustomerID = c.CustomerID
        LEFT JOIN Employees e ON t.EmployeeID = e.EmployeeID
        WHERE 1=1
    """
    params = []
    if q:
        sql += " AND (t.Subject LIKE %s OR c.FullName LIKE %s OR c.Company LIKE %s)"
        like = f'%{q}%'
        params += [like, like, like]
    if status:
        sql += " AND t.Status = %s"
        params.append(status)
    if priority:
        sql += " AND t.Priority = %s"
        params.append(priority)
    sql += " ORDER BY t.CreatedAt DESC"

    all_tickets = query(sql, params)
    paged       = paginate(all_tickets, page)
    statuses    = ['Open', 'In Progress', 'Resolved', 'Closed']
    priorities  = ['Low', 'Medium', 'High', 'Critical']

    return render_template('tickets.html',
                           tickets=paged['items'], paged=paged,
                           statuses=statuses, priorities=priorities,
                           current_status=status, current_priority=priority, q=q)

@app.route('/tickets/add', methods=['GET', 'POST'])
@admin_required
def add_ticket():
    customers = query("SELECT CustomerID, FullName, Company FROM Customers ORDER BY FullName")
    employees = query("SELECT EmployeeID, FullName FROM Employees WHERE Department='Support' ORDER BY FullName")
    if request.method == 'POST':
        query("""
            INSERT INTO SupportTickets (CustomerID, EmployeeID, Subject, Description, Priority)
            VALUES (%s,%s,%s,%s,%s)
        """, (
            request.form['customer_id'],
            request.form['employee_id'] or None,
            request.form['subject'],
            request.form['description'],
            request.form['priority']
        ), fetch='commit')
        log_activity('CREATE','Ticket',f'Tạo ticket: {request.form["subject"]}')
        flash('Đã tạo ticket hỗ trợ!', 'success')
        return redirect(url_for('tickets'))
    return render_template('ticket_form.html', customers=customers, employees=employees)

@app.route('/tickets/resolve/<int:tid>', methods=['POST'])
@admin_required
def resolve_ticket(tid):
    query("""
        UPDATE SupportTickets SET Status='Resolved', ResolvedAt=%s WHERE TicketID=%s
    """, (datetime.now(), tid), fetch='commit')
    log_activity('UPDATE','Ticket',f'Giải quyết ticket ID {tid}')
    flash('Ticket đã được giải quyết!', 'success')
    return redirect(url_for('tickets'))

# ─── NHÂN VIÊN ─────────────────────────────────────────────
@app.route('/employees')
@login_required
def employees():
    emps = query("""
        SELECT e.*,
               COUNT(DISTINCT c.CustomerID)     AS customer_count,
               COUNT(DISTINCT o.OpportunityID)  AS opp_count
        FROM Employees e
        LEFT JOIN Customers     c ON e.EmployeeID = c.AssignedTo
        LEFT JOIN Opportunities o ON e.EmployeeID = o.EmployeeID
        GROUP BY e.EmployeeID ORDER BY e.FullName
    """)
    return render_template('employees.html', employees=emps)

# ─── NHÂN VIÊN CRUD ────────────────────────────────────────
@app.route('/employees/add', methods=['GET', 'POST'])
@admin_required
def add_employee():
    if request.method == 'POST':
        query("""
            INSERT INTO Employees (FullName, Email, Phone, Department, Role, HireDate, Status)
            VALUES (%s,%s,%s,%s,%s,%s,'Active')
        """, (
            request.form['fullname'],   request.form['email'],
            request.form['phone'],      request.form['department'],
            request.form['role'],       request.form['hiredate'] or None,
        ), fetch='commit')
        flash('Đã thêm nhân viên!', 'success')
        return redirect(url_for('employees'))
    return render_template('employee_form.html', emp=None)

@app.route('/employees/edit/<int:eid>', methods=['GET', 'POST'])
@admin_required
def edit_employee(eid):
    emp = query("SELECT * FROM Employees WHERE EmployeeID=%s", (eid,), fetch='one')
    if request.method == 'POST':
        query("""
            UPDATE Employees SET FullName=%s, Email=%s, Phone=%s,
            Department=%s, Role=%s, HireDate=%s, Status=%s
            WHERE EmployeeID=%s
        """, (
            request.form['fullname'],   request.form['email'],
            request.form['phone'],      request.form['department'],
            request.form['role'],       request.form['hiredate'] or None,
            request.form['status'],     eid
        ), fetch='commit')
        flash('Đã cập nhật nhân viên!', 'success')
        return redirect(url_for('employees'))
    return render_template('employee_form.html', emp=emp)

@app.route('/employees/delete/<int:eid>', methods=['POST'])
@admin_required
def delete_employee(eid):
    # Bỏ liên kết trước khi xóa
    query("UPDATE Customers SET AssignedTo=NULL WHERE AssignedTo=%s", (eid,), fetch='commit')
    query("DELETE FROM Interactions    WHERE EmployeeID=%s", (eid,), fetch='commit')
    query("DELETE FROM SupportTickets  WHERE EmployeeID=%s", (eid,), fetch='commit')
    query("DELETE FROM Employees       WHERE EmployeeID=%s", (eid,), fetch='commit')
    flash('Đã xóa nhân viên.', 'warning')
    return redirect(url_for('employees'))

# ─── CƠ HỘI — XÓA ──────────────────────────────────────────
@app.route('/opportunities/delete/<int:oid>', methods=['POST'])
@admin_required
def delete_opportunity(oid):
    query("DELETE FROM Opportunities WHERE OpportunityID=%s", (oid,), fetch='commit')
    flash('Đã xóa cơ hội.', 'warning')
    return redirect(url_for('opportunities'))

# ─── TƯƠNG TÁC — SỬA / XÓA ────────────────────────────────
@app.route('/interactions/edit/<int:iid>', methods=['GET', 'POST'])
@admin_required
def edit_interaction(iid):
    inter     = query("SELECT * FROM Interactions WHERE InteractionID=%s", (iid,), fetch='one')
    customers = query("SELECT CustomerID, FullName, Company FROM Customers ORDER BY FullName")
    employees = query("SELECT EmployeeID, FullName FROM Employees WHERE Status='Active' ORDER BY FullName")
    if request.method == 'POST':
        query("""
            UPDATE Interactions SET CustomerID=%s, EmployeeID=%s,
            Type=%s, Subject=%s, Notes=%s WHERE InteractionID=%s
        """, (
            request.form['customer_id'], request.form['employee_id'],
            request.form['type'],        request.form['subject'],
            request.form['notes'],       iid
        ), fetch='commit')
        flash('Đã cập nhật tương tác!', 'success')
        return redirect(url_for('interactions'))
    return render_template('interaction_form.html',
                           customers=customers, employees=employees, inter=inter)

@app.route('/interactions/delete/<int:iid>', methods=['POST'])
@admin_required
def delete_interaction(iid):
    query("DELETE FROM Interactions WHERE InteractionID=%s", (iid,), fetch='commit')
    flash('Đã xóa tương tác.', 'warning')
    return redirect(url_for('interactions'))

# ─── TICKET — SỬA / XÓA ───────────────────────────────────
@app.route('/tickets/edit/<int:tid>', methods=['GET', 'POST'])
@admin_required
def edit_ticket(tid):
    ticket    = query("SELECT * FROM SupportTickets WHERE TicketID=%s", (tid,), fetch='one')
    customers = query("SELECT CustomerID, FullName, Company FROM Customers ORDER BY FullName")
    employees = query("SELECT EmployeeID, FullName FROM Employees WHERE Department='Support' ORDER BY FullName")
    if request.method == 'POST':
        resolved_at = None
        if request.form['status'] == 'Resolved':
            resolved_at = datetime.now()
        query("""
            UPDATE SupportTickets SET CustomerID=%s, EmployeeID=%s, Subject=%s,
            Description=%s, Priority=%s, Status=%s, ResolvedAt=%s
            WHERE TicketID=%s
        """, (
            request.form['customer_id'],
            request.form['employee_id'] or None,
            request.form['subject'],
            request.form['description'],
            request.form['priority'],
            request.form['status'],
            resolved_at, tid
        ), fetch='commit')
        flash('Đã cập nhật ticket!', 'success')
        return redirect(url_for('tickets'))
    return render_template('ticket_form.html',
                           customers=customers, employees=employees, ticket=ticket)

@app.route('/tickets/delete/<int:tid>', methods=['POST'])
@admin_required
def delete_ticket(tid):
    query("DELETE FROM SupportTickets WHERE TicketID=%s", (tid,), fetch='commit')
    flash('Đã xóa ticket.', 'warning')
    return redirect(url_for('tickets'))

# ─── SẢN PHẨM (module mới) ─────────────────────────────────
@app.route('/products')
@login_required
def products():
    prods = query("SELECT * FROM Products ORDER BY Category, ProductName")
    return render_template('products.html', products=prods)

@app.route('/products/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    if request.method == 'POST':
        query("""
            INSERT INTO Products (ProductName, Category, Price, Description, Status)
            VALUES (%s,%s,%s,%s,'Active')
        """, (
            request.form['name'],     request.form['category'],
            request.form['price'],    request.form['description'],
        ), fetch='commit')
        flash('Đã thêm sản phẩm!', 'success')
        return redirect(url_for('products'))
    return render_template('product_form.html', product=None)

@app.route('/products/edit/<int:pid>', methods=['GET', 'POST'])
@admin_required
def edit_product(pid):
    product = query("SELECT * FROM Products WHERE ProductID=%s", (pid,), fetch='one')
    if request.method == 'POST':
        query("""
            UPDATE Products SET ProductName=%s, Category=%s,
            Price=%s, Description=%s, Status=%s WHERE ProductID=%s
        """, (
            request.form['name'],     request.form['category'],
            request.form['price'],    request.form['description'],
            request.form['status'],   pid
        ), fetch='commit')
        flash('Đã cập nhật sản phẩm!', 'success')
        return redirect(url_for('products'))
    return render_template('product_form.html', product=product)

@app.route('/products/delete/<int:pid>', methods=['POST'])
@admin_required
def delete_product(pid):
    query("UPDATE Opportunities SET ProductID=NULL WHERE ProductID=%s", (pid,), fetch='commit')
    query("DELETE FROM Products WHERE ProductID=%s", (pid,), fetch='commit')
    flash('Đã xóa sản phẩm.', 'warning')
    return redirect(url_for('products'))

# ─── HÀM DÙNG CHUNG CHO MODULE GIÁO DỤC ──────────────────
def edu_query(sql, params=None, fetch='all'):
    """Query database crm_edu."""
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host='localhost', user='root', password='',
            database='crm_edu', charset='utf8mb4'
        )
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params or ())
        if fetch == 'all':
            result = cur.fetchall()
        elif fetch == 'one':
            result = cur.fetchone()
        else:
            conn.commit()
            result = cur.lastrowid
        conn.close()
        return result
    except Exception as e:
        print(f"EDU DB Error: {e}")
        return [] if fetch == 'all' else None

# ─── MODULE GIÁO DỤC — HỌC VIÊN ──────────────────────────
@app.route('/edu/students')
@login_required
def edu_students():
    q      = request.args.get('q', '').strip()
    status = request.args.get('status', '')
    source = request.args.get('source', '')
    page   = int(request.args.get('page', 1))

    sql = """SELECT s.*, st.FullName AS staff_name,
                    COUNT(DISTINCT e.EnrollmentID) AS enroll_count
             FROM Students s
             LEFT JOIN Staff st ON s.AssignedTo=st.StaffID
             LEFT JOIN Enrollments e ON s.StudentID=e.StudentID
             WHERE 1=1"""
    params = []
    if q:
        sql += " AND (s.FullName LIKE %s OR s.Email LIKE %s OR s.Phone LIKE %s)"
        like = f'%{q}%'; params += [like, like, like]
    if status: sql += " AND s.Status=%s"; params.append(status)
    if source: sql += " AND s.Source=%s"; params.append(source)
    sql += " GROUP BY s.StudentID ORDER BY s.CreatedAt DESC"

    paged      = paginate(edu_query(sql, params), page)
    staff_list = edu_query("SELECT StaffID, FullName FROM Staff WHERE Status='Active' ORDER BY FullName")
    statuses   = ['Prospect', 'Enrolled', 'Studying', 'Graduated', 'Dropped']
    sources    = ['Website', 'Facebook', 'Referral', 'Walk-in', 'Zalo']
    return render_template('edu/students.html',
                           students=paged['items'], paged=paged,
                           q=q, status=status, source=source,
                           statuses=statuses, sources=sources,
                           staff_list=staff_list)

@app.route('/edu/students/add', methods=['GET', 'POST'])
@employee_required
def edu_add_student():
    staff_list = edu_query("SELECT StaffID, FullName FROM Staff WHERE Status='Active' ORDER BY FullName")
    if request.method == 'POST':
        edu_query("""INSERT INTO Students (FullName,Email,Phone,DOB,Gender,Address,Source,AssignedTo,Notes)
                     VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                  (request.form['fullname'], request.form['email'],
                   request.form['phone'], request.form['dob'] or None,
                   request.form['gender'], request.form['address'],
                   request.form['source'], request.form['assigned_to'] or None,
                   request.form['notes']), fetch='commit')
        log_activity('CREATE', 'EduStudent', f'Thêm học viên: {request.form["fullname"]}')
        flash('Đã thêm học viên!', 'success')
        return redirect(url_for('edu_students'))
    return render_template('edu/student_form.html', student=None, staff_list=staff_list)

@app.route('/edu/students/<int:sid>')
@login_required
def edu_student_detail(sid):
    student  = edu_query("""SELECT s.*, st.FullName AS staff_name
                             FROM Students s LEFT JOIN Staff st ON s.AssignedTo=st.StaffID
                             WHERE s.StudentID=%s""", (sid,), fetch='one')
    enrolls  = edu_query("""SELECT e.*, cl.ClassName, c.CourseName,
                                    IFNULL(SUM(p.Amount),0) AS paid,
                                    e.FinalFee - IFNULL(SUM(p.Amount),0) AS remaining
                             FROM Enrollments e
                             JOIN Classes cl ON e.ClassID=cl.ClassID
                             JOIN Courses c ON cl.CourseID=c.CourseID
                             LEFT JOIN Payments p ON e.EnrollmentID=p.EnrollmentID
                             WHERE e.StudentID=%s GROUP BY e.EnrollmentID
                             ORDER BY e.CreatedAt DESC""", (sid,))
    consults = edu_query("""SELECT co.*, st.FullName AS staff
                             FROM Consultations co
                             JOIN Staff st ON co.StaffID=st.StaffID
                             WHERE co.StudentID=%s ORDER BY co.ConsultedAt DESC""", (sid,))
    feedbacks= edu_query("SELECT * FROM Feedbacks WHERE StudentID=%s ORDER BY CreatedAt DESC", (sid,))
    payments = edu_query("""SELECT p.*, st.FullName AS staff
                             FROM Payments p LEFT JOIN Staff st ON p.CreatedBy=st.StaffID
                             WHERE p.StudentID=%s ORDER BY p.PaymentDate DESC""", (sid,))
    return render_template('edu/student_detail.html',
                           student=student, enrolls=enrolls,
                           consults=consults, feedbacks=feedbacks, payments=payments)

@app.route('/edu/students/edit/<int:sid>', methods=['GET', 'POST'])
@employee_required
def edu_edit_student(sid):
    student    = edu_query("SELECT * FROM Students WHERE StudentID=%s", (sid,), fetch='one')
    staff_list = edu_query("SELECT StaffID, FullName FROM Staff WHERE Status='Active' ORDER BY FullName")
    if request.method == 'POST':
        edu_query("""UPDATE Students SET FullName=%s,Email=%s,Phone=%s,DOB=%s,Gender=%s,
                     Address=%s,Source=%s,AssignedTo=%s,Status=%s,Notes=%s
                     WHERE StudentID=%s""",
                  (request.form['fullname'], request.form['email'],
                   request.form['phone'], request.form['dob'] or None,
                   request.form['gender'], request.form['address'],
                   request.form['source'], request.form['assigned_to'] or None,
                   request.form['status'], request.form['notes'], sid), fetch='commit')
        log_activity('UPDATE', 'EduStudent', f'Cập nhật học viên ID {sid}')
        flash('Đã cập nhật học viên!', 'success')
        return redirect(url_for('edu_student_detail', sid=sid))
    return render_template('edu/student_form.html', student=student, staff_list=staff_list)

@app.route('/edu/students/delete/<int:sid>', methods=['POST'])
@admin_required
def edu_delete_student(sid):
    edu_query("DELETE FROM Payments      WHERE StudentID=%s", (sid,), fetch='commit')
    edu_query("DELETE FROM Feedbacks     WHERE StudentID=%s", (sid,), fetch='commit')
    edu_query("DELETE FROM Consultations WHERE StudentID=%s", (sid,), fetch='commit')
    edu_query("DELETE FROM Enrollments   WHERE StudentID=%s", (sid,), fetch='commit')
    edu_query("DELETE FROM Students      WHERE StudentID=%s", (sid,), fetch='commit')
    log_activity('DELETE', 'EduStudent', f'Xóa học viên ID {sid}')
    flash('Đã xóa học viên.', 'warning')
    return redirect(url_for('edu_students'))

# ─── MODULE GIÁO DỤC ─── edu_home ────────────────────────
@app.route('/edu')
@login_required
def edu_home():
    try:
        import mysql.connector
        conn = mysql.connector.connect(host='localhost', user='root', password='', database='crm_edu', charset='utf8mb4')
        conn.close()
    except:
        return render_template('edu_not_ready.html')

    stats = {
        'students':    (edu_query("SELECT COUNT(*) AS c FROM Students WHERE Status NOT IN ('Dropped')", fetch='one') or {}).get('c', 0),
        'enrollments': (edu_query("SELECT COUNT(*) AS c FROM Enrollments WHERE Status IN ('Studying','Confirmed')", fetch='one') or {}).get('c', 0),
        'classes':     (edu_query("SELECT COUNT(*) AS c FROM Classes WHERE Status IN ('Ongoing','Upcoming')", fetch='one') or {}).get('c', 0),
        'revenue':     (edu_query("SELECT IFNULL(SUM(Amount),0) AS v FROM Payments WHERE MONTH(PaymentDate)=MONTH(NOW()) AND YEAR(PaymentDate)=YEAR(NOW())", fetch='one') or {}).get('v', 0),
        'pending_fee': (edu_query("""SELECT IFNULL(SUM(e.FinalFee - IFNULL(p.paid,0)),0) AS v
                                     FROM Enrollments e
                                     LEFT JOIN (SELECT EnrollmentID, SUM(Amount) AS paid FROM Payments GROUP BY EnrollmentID) p
                                     ON e.EnrollmentID=p.EnrollmentID
                                     WHERE e.Status IN ('Studying','Confirmed')""", fetch='one') or {}).get('v', 0),
        'open_feedback':(edu_query("SELECT COUNT(*) AS c FROM Feedbacks WHERE Status IN ('Open','Processing')", fetch='one') or {}).get('c', 0),
    }
    recent_students = edu_query("SELECT s.*, st.FullName AS staff_name FROM Students s LEFT JOIN Staff st ON s.AssignedTo=st.StaffID ORDER BY s.CreatedAt DESC LIMIT 5")
    ongoing_classes = edu_query("SELECT cl.*, c.CourseName, c.Category, s.FullName AS teacher FROM Classes cl JOIN Courses c ON cl.CourseID=c.CourseID LEFT JOIN Staff s ON cl.TeacherID=s.StaffID WHERE cl.Status IN ('Ongoing','Upcoming') ORDER BY cl.StartDate LIMIT 6")
    recent_consults = edu_query("SELECT co.*, s.FullName AS student, st.FullName AS staff FROM Consultations co JOIN Students s ON co.StudentID=s.StudentID JOIN Staff st ON co.StaffID=st.StaffID ORDER BY co.ConsultedAt DESC LIMIT 5")
    return render_template('edu/index.html', stats=stats,
                           recent_students=recent_students,
                           ongoing_classes=ongoing_classes,
                           recent_consults=recent_consults)

# ─── EDU: LỚP HỌC ─────────────────────────────────────────
@app.route('/edu/classes')
@login_required
def edu_classes():
    q      = request.args.get('q','').strip()
    status = request.args.get('status','')
    page   = int(request.args.get('page',1))
    def eq(sql,p=None,f='all'): return edu_query(sql,p,f)
    all_cls = eq("""
        SELECT cl.*,c.CourseName,c.Category,c.Fee,s.FullName AS teacher
        FROM Classes cl
        JOIN Courses c ON cl.CourseID=c.CourseID
        LEFT JOIN Staff s ON cl.TeacherID=s.StaffID
        WHERE (cl.ClassName LIKE %s OR c.CourseName LIKE %s)
        """ + (" AND cl.Status=%s" if status else ""),
        ([f'%{q}%',f'%{q}%']+([status] if status else [])) if q else
        (([status] if status else None))
    )
    paged    = paginate(all_cls or [], page)
    statuses = ['Upcoming','Ongoing','Completed','Cancelled']
    return render_template('edu/classes.html', classes=paged['items'], paged=paged,
                           q=q, status=status, statuses=statuses)

@app.route('/edu/classes/add', methods=['GET','POST'])
@admin_required
def edu_add_class():
    courses_list = edu_query("SELECT CourseID,CourseName,Fee FROM Courses WHERE Status='Active' ORDER BY CourseName")
    staff_list   = edu_query("SELECT StaffID,FullName FROM Staff WHERE Department='Teaching' AND Status='Active'")
    if request.method=='POST':
        edu_query("""INSERT INTO Classes (CourseID,ClassName,TeacherID,StartDate,EndDate,Schedule,Room,MaxStudents,Status)
                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'Upcoming')""",
              (request.form['course_id'],request.form['classname'],
               request.form['teacher_id'] or None,
               request.form['start_date'] or None, request.form['end_date'] or None,
               request.form['schedule'],request.form['room'],
               request.form['max_students']), fetch='commit')
        flash('Đã thêm lớp học!','success')
        return redirect(url_for('edu_classes'))
    return render_template('edu/class_form.html', cls=None,
                           courses_list=courses_list, staff_list=staff_list)

@app.route('/edu/classes/edit/<int:cid>', methods=['GET','POST'])
@admin_required
def edu_edit_class(cid):
    cls          = edu_query("SELECT * FROM Classes WHERE ClassID=%s",(cid,),fetch='one')
    courses_list = edu_query("SELECT CourseID,CourseName FROM Courses WHERE Status='Active' ORDER BY CourseName")
    staff_list   = edu_query("SELECT StaffID,FullName FROM Staff WHERE Department='Teaching' AND Status='Active'")
    if request.method=='POST':
        edu_query("""UPDATE Classes SET CourseID=%s,ClassName=%s,TeacherID=%s,StartDate=%s,
                 EndDate=%s,Schedule=%s,Room=%s,MaxStudents=%s,Status=%s WHERE ClassID=%s""",
              (request.form['course_id'],request.form['classname'],
               request.form['teacher_id'] or None,
               request.form['start_date'] or None, request.form['end_date'] or None,
               request.form['schedule'],request.form['room'],
               request.form['max_students'],request.form['status'],cid), fetch='commit')
        flash('Đã cập nhật lớp học!','success')
        return redirect(url_for('edu_classes'))
    return render_template('edu/class_form.html', cls=cls,
                           courses_list=courses_list, staff_list=staff_list)

@app.route('/edu/classes/delete/<int:cid>', methods=['POST'])
@admin_required
def edu_delete_class(cid):
    edu_query("DELETE FROM Classes WHERE ClassID=%s",(cid,),fetch='commit')
    flash('Đã xóa lớp học.','warning')
    return redirect(url_for('edu_classes'))

# ─── EDU: KHÓA HỌC ────────────────────────────────────────
@app.route('/edu/courses')
@login_required
def edu_courses():
    q        = request.args.get('q','').strip()
    category = request.args.get('category','')
    page     = int(request.args.get('page',1))
    sql = "SELECT * FROM Courses WHERE (CourseName LIKE %s OR Description LIKE %s)"
    params = [f'%{q}%',f'%{q}%']
    if category: sql += " AND Category=%s"; params.append(category)
    sql += " ORDER BY Category,CourseName"
    paged      = paginate(edu_query(sql,params) or [], page)
    categories = ['Lập trình','Ngoại ngữ','Kỹ năng','Thiết kế','Tin học']
    return render_template('edu/courses.html', courses=paged['items'], paged=paged,
                           q=q, category=category, categories=categories)

@app.route('/edu/courses/add', methods=['GET','POST'])
@admin_required
def edu_add_course():
    if request.method=='POST':
        edu_query("INSERT INTO Courses (CourseName,Category,Level,Duration,Fee,Description) VALUES (%s,%s,%s,%s,%s,%s)",
              (request.form['name'],request.form['category'],request.form['level'],
               request.form['duration'],request.form['fee'],request.form['description']),fetch='commit')
        flash('Đã thêm khóa học!','success')
        return redirect(url_for('edu_courses'))
    return render_template('edu/course_form.html', course=None)

@app.route('/edu/courses/edit/<int:cid>', methods=['GET','POST'])
@admin_required
def edu_edit_course(cid):
    course = edu_query("SELECT * FROM Courses WHERE CourseID=%s",(cid,),fetch='one')
    if request.method=='POST':
        edu_query("UPDATE Courses SET CourseName=%s,Category=%s,Level=%s,Duration=%s,Fee=%s,Description=%s,Status=%s WHERE CourseID=%s",
              (request.form['name'],request.form['category'],request.form['level'],
               request.form['duration'],request.form['fee'],request.form['description'],
               request.form['status'],cid),fetch='commit')
        flash('Đã cập nhật!','success')
        return redirect(url_for('edu_courses'))
    return render_template('edu/course_form.html', course=course)

# ─── EDU: ĐĂNG KÝ HỌC ─────────────────────────────────────
@app.route('/edu/enrollments')
@login_required
def edu_enrollments():
    q      = request.args.get('q','').strip()
    status = request.args.get('status','')
    page   = int(request.args.get('page',1))
    sql = """SELECT e.*,s.FullName AS student,cl.ClassName,c.CourseName,
                    st.FullName AS staff,
                    IFNULL(SUM(p.Amount),0) AS paid,
                    e.FinalFee - IFNULL(SUM(p.Amount),0) AS remaining
             FROM Enrollments e
             JOIN Students s ON e.StudentID=s.StudentID
             JOIN Classes cl ON e.ClassID=cl.ClassID
             JOIN Courses c ON cl.CourseID=c.CourseID
             LEFT JOIN Staff st ON e.StaffID=st.StaffID
             LEFT JOIN Payments p ON e.EnrollmentID=p.EnrollmentID
             WHERE (s.FullName LIKE %s OR cl.ClassName LIKE %s)"""
    params = [f'%{q}%',f'%{q}%']
    if status: sql += " AND e.Status=%s"; params.append(status)
    sql += " GROUP BY e.EnrollmentID ORDER BY e.CreatedAt DESC"
    paged    = paginate(edu_query(sql,params) or [], page)
    statuses = ['Pending','Confirmed','Studying','Completed','Dropped','Refunded']
    return render_template('edu/enrollments.html', enrollments=paged['items'],
                           paged=paged, q=q, status=status, statuses=statuses)

@app.route('/edu/enrollments/add', methods=['GET','POST'])
@employee_required
def edu_add_enrollment():
    students_list = edu_query("SELECT StudentID,FullName,Phone FROM Students WHERE Status NOT IN ('Dropped') ORDER BY FullName")
    classes_list  = edu_query("""SELECT cl.ClassID,cl.ClassName,c.CourseName,c.Fee,
                                     cl.MaxStudents-cl.CurrentStudents AS seats
                              FROM Classes cl JOIN Courses c ON cl.CourseID=c.CourseID
                              WHERE cl.Status IN ('Upcoming','Ongoing') ORDER BY cl.StartDate""")
    staff_list    = edu_query("SELECT StaffID,FullName FROM Staff WHERE Status='Active' ORDER BY FullName")
    if request.method=='POST':
        fee=float(request.form.get('total_fee',0) or 0)
        discount=float(request.form.get('discount',0) or 0)
        final=fee-discount
        edu_query("""INSERT INTO Enrollments (StudentID,ClassID,StaffID,EnrollDate,Status,TotalFee,Discount,FinalFee,Notes)
                 VALUES (%s,%s,%s,%s,'Confirmed',%s,%s,%s,%s)""",
              (request.form['student_id'],request.form['class_id'],
               request.form['staff_id'] or None,
               datetime.now().strftime('%Y-%m-%d'),fee,discount,final,
               request.form['notes']),fetch='commit')
        edu_query("UPDATE Classes SET CurrentStudents=CurrentStudents+1 WHERE ClassID=%s",
              (request.form['class_id'],),fetch='commit')
        edu_query("UPDATE Students SET Status='Enrolled' WHERE StudentID=%s",
              (request.form['student_id'],),fetch='commit')
        log_activity('CREATE','Enrollment',f'Đăng ký học viên ID {request.form["student_id"]}')
        flash('Đã tạo đăng ký học!','success')
        return redirect(url_for('edu_enrollments'))
    return render_template('edu/enrollment_form.html',
                           students_list=students_list, classes_list=classes_list,
                           staff_list=staff_list, enroll=None)

@app.route('/edu/enrollments/edit/<int:eid>', methods=['GET','POST'])
@employee_required
def edu_edit_enrollment(eid):
    enroll        = edu_query("SELECT * FROM Enrollments WHERE EnrollmentID=%s",(eid,),fetch='one')
    students_list = edu_query("SELECT StudentID,FullName FROM Students ORDER BY FullName")
    classes_list  = edu_query("""SELECT cl.ClassID,cl.ClassName,c.CourseName
                              FROM Classes cl JOIN Courses c ON cl.CourseID=c.CourseID ORDER BY cl.StartDate""")
    staff_list    = edu_query("SELECT StaffID,FullName FROM Staff WHERE Status='Active' ORDER BY FullName")
    if request.method=='POST':
        edu_query("""UPDATE Enrollments SET StudentID=%s,ClassID=%s,StaffID=%s,
                 Status=%s,Discount=%s,FinalFee=%s,Notes=%s WHERE EnrollmentID=%s""",
              (request.form['student_id'],request.form['class_id'],
               request.form['staff_id'] or None,request.form['status'],
               request.form['discount'],request.form['final_fee'],
               request.form['notes'],eid),fetch='commit')
        flash('Đã cập nhật đăng ký!','success')
        return redirect(url_for('edu_enrollments'))
    return render_template('edu/enrollment_form.html', enroll=enroll,
                           students_list=students_list, classes_list=classes_list,
                           staff_list=staff_list)

# ─── EDU: HỌC PHÍ ─────────────────────────────────────────
@app.route('/edu/payments')
@login_required
def edu_payments():
    q    = request.args.get('q','').strip()
    page = int(request.args.get('page',1))
    sql  = """SELECT p.*,s.FullName AS student,cl.ClassName,c.CourseName,st.FullName AS staff
              FROM Payments p
              JOIN Students s ON p.StudentID=s.StudentID
              JOIN Enrollments e ON p.EnrollmentID=e.EnrollmentID
              JOIN Classes cl ON e.ClassID=cl.ClassID
              JOIN Courses c ON cl.CourseID=c.CourseID
              LEFT JOIN Staff st ON p.CreatedBy=st.StaffID
              WHERE (s.FullName LIKE %s OR cl.ClassName LIKE %s)
              ORDER BY p.PaymentDate DESC"""
    paged = paginate(edu_query(sql,[f'%{q}%',f'%{q}%']) or [], page)
    total = (edu_query("SELECT IFNULL(SUM(Amount),0) AS v FROM Payments",fetch='one') or {}).get('v',0)
    return render_template('edu/payments.html', payments=paged['items'],
                           paged=paged, q=q, total=total)

@app.route('/edu/payments/add', methods=['GET','POST'])
@employee_required
def edu_add_payment():
    enroll_list = edu_query("""SELECT e.EnrollmentID,s.FullName AS student,cl.ClassName,
                                   e.FinalFee,IFNULL(SUM(p.Amount),0) AS paid,
                                   e.FinalFee-IFNULL(SUM(p.Amount),0) AS remaining,e.StudentID
                            FROM Enrollments e
                            JOIN Students s ON e.StudentID=s.StudentID
                            JOIN Classes cl ON e.ClassID=cl.ClassID
                            LEFT JOIN Payments p ON e.EnrollmentID=p.EnrollmentID
                            WHERE e.Status IN ('Confirmed','Studying')
                            GROUP BY e.EnrollmentID HAVING remaining>0 ORDER BY s.FullName""")
    staff_list = edu_query("SELECT StaffID,FullName FROM Staff WHERE Status='Active' ORDER BY FullName")
    if request.method=='POST':
        enroll = edu_query("SELECT StudentID FROM Enrollments WHERE EnrollmentID=%s",
                       (request.form['enrollment_id'],),fetch='one')
        edu_query("""INSERT INTO Payments (EnrollmentID,StudentID,Amount,PaymentDate,Method,Note,CreatedBy)
                 VALUES (%s,%s,%s,%s,%s,%s,%s)""",
              (request.form['enrollment_id'], enroll['StudentID'],
               request.form['amount'],
               request.form['payment_date'] or datetime.now().strftime('%Y-%m-%d'),
               request.form['method'],request.form['note'],
               request.form['staff_id'] or None),fetch='commit')
        log_activity('CREATE','Payment',f'Thu học phí đăng ký ID {request.form["enrollment_id"]}')
        flash('Đã ghi nhận thanh toán!','success')
        return redirect(url_for('edu_payments'))
    return render_template('edu/payment_form.html',
                           enroll_list=enroll_list, staff_list=staff_list)

# ─── EDU: TƯ VẤN ──────────────────────────────────────────
@app.route('/edu/consultations')
@login_required
def edu_consultations():
    q    = request.args.get('q','').strip()
    ctype= request.args.get('type','')
    page = int(request.args.get('page',1))
    sql  = """SELECT co.*,s.FullName AS student,s.Phone,st.FullName AS staff
              FROM Consultations co
              JOIN Students s ON co.StudentID=s.StudentID
              JOIN Staff st ON co.StaffID=st.StaffID
              WHERE (s.FullName LIKE %s OR co.Subject LIKE %s)"""
    params=[f'%{q}%',f'%{q}%']
    if ctype: sql+=" AND co.Type=%s"; params.append(ctype)
    sql+=" ORDER BY co.ConsultedAt DESC"
    paged = paginate(edu_query(sql,params) or [], page)
    types = ['Gọi điện','Gặp mặt','Zalo','Email','Demo']
    return render_template('edu/consultations.html', consultations=paged['items'],
                           paged=paged, q=q, ctype=ctype, types=types)

@app.route('/edu/consultations/add', methods=['GET','POST'])
@employee_required
def edu_add_consultation():
    students_list = edu_query("SELECT StudentID,FullName,Phone FROM Students ORDER BY FullName")
    staff_list    = edu_query("SELECT StaffID,FullName FROM Staff WHERE Status='Active' ORDER BY FullName")
    if request.method=='POST':
        edu_query("""INSERT INTO Consultations (StudentID,StaffID,Type,Subject,Notes,Result,NextAction)
                 VALUES (%s,%s,%s,%s,%s,%s,%s)""",
              (request.form['student_id'],request.form['staff_id'],
               request.form['type'],request.form['subject'],request.form['notes'],
               request.form['result'],request.form['next_action']),fetch='commit')
        flash('Đã ghi nhận tư vấn!','success')
        return redirect(url_for('edu_consultations'))
    return render_template('edu/consultation_form.html',
                           students_list=students_list, staff_list=staff_list, consult=None)

# ─── EDU: PHẢN HỒI ────────────────────────────────────────
@app.route('/edu/feedbacks')
@login_required
def edu_feedbacks():
    q      = request.args.get('q','').strip()
    status = request.args.get('status','')
    page   = int(request.args.get('page',1))
    sql    = """SELECT f.*,s.FullName AS student,cl.ClassName,st.FullName AS staff
                FROM Feedbacks f
                JOIN Students s ON f.StudentID=s.StudentID
                LEFT JOIN Classes cl ON f.ClassID=cl.ClassID
                LEFT JOIN Staff st ON f.StaffID=st.StaffID
                WHERE (s.FullName LIKE %s OR f.Subject LIKE %s)"""
    params=[f'%{q}%',f'%{q}%']
    if status: sql+=" AND f.Status=%s"; params.append(status)
    sql+=" ORDER BY f.CreatedAt DESC"
    paged    = paginate(edu_query(sql,params) or [], page)
    statuses = ['Open','Processing','Resolved','Closed']
    return render_template('edu/feedbacks.html', feedbacks=paged['items'],
                           paged=paged, q=q, status=status, statuses=statuses)

@app.route('/edu/feedbacks/add', methods=['GET','POST'])
@employee_required
def edu_add_feedback():
    students_list = edu_query("SELECT StudentID,FullName FROM Students ORDER BY FullName")
    staff_list    = edu_query("SELECT StaffID,FullName FROM Staff WHERE Status='Active' ORDER BY FullName")
    classes_list  = edu_query("SELECT ClassID,ClassName FROM Classes ORDER BY ClassName")
    if request.method=='POST':
        edu_query("""INSERT INTO Feedbacks (StudentID,StaffID,ClassID,Type,Subject,Content,Priority)
                 VALUES (%s,%s,%s,%s,%s,%s,%s)""",
              (request.form['student_id'],
               request.form['staff_id'] or None,
               request.form['class_id'] or None,
               request.form['type'],request.form['subject'],
               request.form['content'],request.form['priority']),fetch='commit')
        flash('Đã ghi nhận phản hồi!','success')
        return redirect(url_for('edu_feedbacks'))
    return render_template('edu/feedback_form.html',
                           students_list=students_list, staff_list=staff_list,
                           classes_list=classes_list, feedback=None)

@app.route('/edu/feedbacks/resolve/<int:fid>', methods=['POST'])
@employee_required
def edu_resolve_feedback(fid):
    edu_query("UPDATE Feedbacks SET Status='Resolved',Response=%s,ResolvedAt=%s WHERE FeedbackID=%s",
          (request.form.get('response',''), datetime.now(), fid),fetch='commit')
    flash('Đã giải quyết phản hồi!','success')
    return redirect(url_for('edu_feedbacks'))

# ─── EDU: NHÂN VIÊN ───────────────────────────────────────
@app.route('/edu/staff')
@login_required
def edu_staff():
    emps = edu_query("""SELECT s.*,COUNT(DISTINCT st.StudentID) AS students,
                           COUNT(DISTINCT e.EnrollmentID) AS enrollments
                    FROM Staff s
                    LEFT JOIN Students st ON s.StaffID=st.AssignedTo
                    LEFT JOIN Enrollments e ON s.StaffID=e.StaffID
                    GROUP BY s.StaffID ORDER BY s.FullName""")
    return render_template('edu/staff.html', staff=emps or [])

@app.route('/edu/staff/add', methods=['GET','POST'])
@admin_required
def edu_add_staff():
    if request.method=='POST':
        edu_query("INSERT INTO Staff (FullName,Email,Phone,Department,Role,HireDate) VALUES (%s,%s,%s,%s,%s,%s)",
              (request.form['fullname'],request.form['email'],request.form['phone'],
               request.form['department'],request.form['role'],
               request.form['hiredate'] or None),fetch='commit')
        flash('Đã thêm nhân viên!','success')
        return redirect(url_for('edu_staff'))
    return render_template('edu/staff_form.html', emp=None)

@app.route('/edu/staff/edit/<int:sid>', methods=['GET','POST'])
@admin_required
def edu_edit_staff(sid):
    emp = edu_query("SELECT * FROM Staff WHERE StaffID=%s",(sid,),fetch='one')
    if request.method=='POST':
        edu_query("UPDATE Staff SET FullName=%s,Email=%s,Phone=%s,Department=%s,Role=%s,Status=%s WHERE StaffID=%s",
              (request.form['fullname'],request.form['email'],request.form['phone'],
               request.form['department'],request.form['role'],
               request.form['status'],sid),fetch='commit')
        flash('Đã cập nhật!','success')
        return redirect(url_for('edu_staff'))
    return render_template('edu/staff_form.html', emp=emp)

# ─── BÁO CÁO THỐNG KÊ ─────────────────────────────────────
@app.route('/reports')
@login_required
def reports():
    # 1. Doanh thu theo giai đoạn
    pipeline = query("""
        SELECT Stage,
               COUNT(*) AS count,
               IFNULL(SUM(Value),0) AS total_value,
               IFNULL(AVG(Probability),0) AS avg_prob
        FROM Opportunities
        GROUP BY Stage
        ORDER BY FIELD(Stage,'Lead','Qualified','Proposal','Negotiation','Closed Won','Closed Lost')
    """)

    # 2. Doanh thu theo tháng (6 tháng gần nhất - Closed Won)
    revenue_monthly = query("""
        SELECT DATE_FORMAT(ClosedAt, '%m/%Y') AS month,
               COUNT(*) AS deals,
               IFNULL(SUM(Value),0) AS revenue
        FROM Opportunities
        WHERE Stage='Closed Won' AND ClosedAt IS NOT NULL
              AND ClosedAt >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
        GROUP BY DATE_FORMAT(ClosedAt, '%Y-%m')
        ORDER BY DATE_FORMAT(ClosedAt, '%Y-%m')
    """)

    # 3. Hiệu suất nhân viên
    emp_perf = query("""
        SELECT e.FullName, e.Department,
               COUNT(DISTINCT c.CustomerID)  AS customers,
               COUNT(DISTINCT o.OpportunityID) AS total_opps,
               SUM(CASE WHEN o.Stage='Closed Won' THEN 1 ELSE 0 END) AS won,
               IFNULL(SUM(CASE WHEN o.Stage='Closed Won' THEN o.Value ELSE 0 END),0) AS revenue,
               COUNT(DISTINCT i.InteractionID) AS interactions
        FROM Employees e
        LEFT JOIN Customers     c ON e.EmployeeID = c.AssignedTo
        LEFT JOIN Opportunities o ON e.EmployeeID = o.EmployeeID
        LEFT JOIN Interactions  i ON e.EmployeeID = i.EmployeeID
        GROUP BY e.EmployeeID
        ORDER BY revenue DESC
    """)

    # 4. Phân khúc khách hàng
    segments = query("""
        SELECT Segment, COUNT(*) AS count
        FROM Customers GROUP BY Segment ORDER BY count DESC
    """)

    # 5. Nguồn khách hàng
    sources = query("""
        SELECT Source, COUNT(*) AS count
        FROM Customers GROUP BY Source ORDER BY count DESC
    """)

    # 6. Ticket theo trạng thái
    ticket_stats = query("""
        SELECT Status, COUNT(*) AS count,
               Priority
        FROM SupportTickets
        GROUP BY Status, Priority
        ORDER BY FIELD(Status,'Open','In Progress','Resolved','Closed')
    """)

    ticket_by_status = query("""
        SELECT Status, COUNT(*) AS count
        FROM SupportTickets GROUP BY Status
    """)

    ticket_by_priority = query("""
        SELECT Priority, COUNT(*) AS count
        FROM SupportTickets GROUP BY Priority
        ORDER BY FIELD(Priority,'Critical','High','Medium','Low')
    """)

    # 7. Tương tác theo loại
    interaction_types = query("""
        SELECT Type, COUNT(*) AS count
        FROM Interactions GROUP BY Type ORDER BY count DESC
    """)

    # 8. KPI tổng quan
    kpi = {
        'total_customers':   query("SELECT COUNT(*) AS c FROM Customers", fetch='one')['c'],
        'total_revenue':     query("SELECT IFNULL(SUM(Value),0) AS v FROM Opportunities WHERE Stage='Closed Won'", fetch='one')['v'],
        'win_rate':          0,
        'avg_deal_value':    query("SELECT IFNULL(AVG(Value),0) AS v FROM Opportunities WHERE Stage='Closed Won'", fetch='one')['v'],
        'open_tickets':      query("SELECT COUNT(*) AS c FROM SupportTickets WHERE Status IN ('Open','In Progress')", fetch='one')['c'],
        'total_interactions':query("SELECT COUNT(*) AS c FROM Interactions", fetch='one')['c'],
    }
    won  = query("SELECT COUNT(*) AS c FROM Opportunities WHERE Stage='Closed Won'",  fetch='one')['c']
    lost = query("SELECT COUNT(*) AS c FROM Opportunities WHERE Stage='Closed Lost'", fetch='one')['c']
    if (won + lost) > 0:
        kpi['win_rate'] = round(won / (won + lost) * 100, 1)

    return render_template('reports.html',
                           pipeline=pipeline,
                           revenue_monthly=revenue_monthly,
                           emp_perf=emp_perf,
                           segments=segments,
                           sources=sources,
                           ticket_by_status=ticket_by_status,
                           ticket_by_priority=ticket_by_priority,
                           interaction_types=interaction_types,
                           kpi=kpi)

# ─── NHẬT KÝ HOẠT ĐỘNG ────────────────────────────────────
@app.route('/activity-log')
@admin_required
def activity_log():
    q       = request.args.get('q', '').strip()
    action  = request.args.get('action', '')
    module  = request.args.get('module', '')
    page    = int(request.args.get('page', 1))

    sql = "SELECT * FROM ActivityLog WHERE 1=1"
    params = []
    if q:
        sql += " AND (Username LIKE %s OR FullName LIKE %s OR Description LIKE %s)"
        like = f'%{q}%'
        params += [like, like, like]
    if action:
        sql += " AND Action = %s"
        params.append(action)
    if module:
        sql += " AND Module = %s"
        params.append(module)
    sql += " ORDER BY CreatedAt DESC"

    all_logs = query(sql, params)
    paged    = paginate(all_logs, page, per_page=20)
    actions  = ['LOGIN','LOGOUT','CREATE','UPDATE','DELETE']
    modules  = ['Auth','Customer','Opportunity','Interaction','Ticket','User']

    return render_template('activity_log.html',
                           logs=paged['items'], paged=paged,
                           q=q, action=action, module=module,
                           actions=actions, modules=modules)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)