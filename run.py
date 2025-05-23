import uuid

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
import psycopg2
import psycopg2.extras

import pdfkit
import pyzipper
from werkzeug.utils import secure_filename

from datetime import datetime
import os
import io
from dotenv import load_dotenv
import json

import bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf import CSRFProtect
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.jinja_env.filters['loads'] = json.loads


# load Config
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_PORT = os.getenv('DB_PORT')
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER')
ZIP_PASSWORD = os.getenv('ZIP_PASSWORD')
IS_UN = os.getenv('BACK_DOOR_UN')
IS_PW = os.getenv('BACK_DOOR_PW')
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback-dev-key")


# Hardening Login ------------------------------------
# Password Limiter
# Limiter on Local
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)
# Limiter on Server
# limiter = Limiter(
#     key_func=get_remote_address,
#     app=app,
#     storage_uri="redis://localhost:6379",
#     default_limits=["200 per day", "50 per hour"]
# )

# CSRF Protection
csrf = CSRFProtect()
csrf.init_app(app)

# Login manager
login_manager = LoginManager()
login_manager.init_app(app)

# Cookie setting
app.config.update(
    # SESSION_COOKIE_SECURE=True,       # Only True if you're on HTTPS
    SESSION_COOKIE_SECURE=False,       # Only True if you're on Local
    SESSION_sudioCOOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax'
)


class AdminUser(UserMixin):
    def __init__(self, id):  # noqa
        self.id = id


# --- Dataset Type Mapping ---
dataset_structure_tables = {
    "compliance": "compliance_sheet_structure",
    "corporate": "corporate_structure",
    "company_data": "company_data_structure",
    "sub_template": "sub_template_structure"
}

dataset_browse_tables = {
    "compliance": "compliance_sheet_browse",
    "company_data": "company_data_browse"
}

dataset_entries_tables = {
    "compliance": "compliance_sheet_entries",
    "corporate": "corporate_entries",
    "company_data": "company_data_entries"
}

dataset_history_tables = {
    "compliance": "compliance_sheet_entries_history",
    "company_data": "company_data_entries_history"
}


# Helper Functions ====================================================================================================
# Login Manager Loader
@login_manager.user_loader
def load_user(user_id):
    return AdminUser(user_id) if user_id == "admin" else None


# --- Database connection ---
def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )


def backup_old_entries(dataset_type, entity_id, input_codes, conn):
    """
    Function: backup_old_entries
    Purpose: Before updating form data, backup previous entries to history.
    Called from: dataset_data_input_submit_form()
    """
    entry_table = dataset_entries_tables.get(dataset_type)
    history_table = dataset_history_tables.get(dataset_type)

    id_field = (
        "sheet_id" if dataset_type == "compliance"
        else "company_id"
    )

    cursor = conn.cursor()
    for code in input_codes:
        cursor.execute(f"""
            INSERT INTO {history_table} 
            ({id_field}, input_code, value, file_path, is_original, 
            start_date, next_due_date, upload_date, side_note, action_type)
            SELECT {id_field}, input_code, value, file_path, is_original, 
            start_date, next_due_date, upload_date, side_note, 'UPDATE'
            FROM {entry_table}
            WHERE {id_field} = %s AND input_code = %s
        """, (entity_id, code))
    conn.commit()


def update_is_complete_flag(dataset_type, entity_id, conn):
    """
    Function: update_is_complete_flag
    Purpose: Automatically update is_complete = TRUE if all upload-required fields are filled.
    Called from: dataset_data_input_submit_form()
    """
    entry_table = dataset_entries_tables.get(dataset_type)
    structure_table = dataset_structure_tables.get(dataset_type)

    id_field = (
        "sheet_id" if dataset_type == "compliance"
        else "company_id"
    )

    cursor = conn.cursor()

    # Get all upload input_codes from structure
    cursor.execute(f"""
        SELECT input_code FROM {structure_table}
        WHERE {id_field} = %s AND is_upload = TRUE
    """, (entity_id,))
    upload_fields = [row[0] for row in cursor.fetchall()]

    if not upload_fields:
        return  # Nothing to check

    # Check if all upload fields have file_path filled
    incomplete = False
    for code in upload_fields:
        cursor.execute(f"""
            SELECT file_path FROM {entry_table}
            WHERE {id_field} = %s AND input_code = %s
        """, (entity_id, code))
        result = cursor.fetchone()
        if not result or not result[0]:
            incomplete = True
            break

    is_complete = not incomplete

    # Update all rows in entry_table with is_complete
    cursor.execute(f"""
        UPDATE {entry_table}
        SET is_complete = %s
        WHERE {id_field} = %s
    """, (is_complete, entity_id))

    conn.commit()


def renumber_siblings(dataset_type, parent_id, entity_id):
    """
    Function: renumber_siblings
    Purpose: Re-arranges input_code numbering sequentially for siblings after delete.
    Called from: delete_field()
    """
    structure_table = dataset_structure_tables.get(dataset_type)
    if not structure_table:
        return

    id_field = (
        "sheet_id" if dataset_type == "compliance"
        else "corporate_id" if dataset_type == "corporate"
        else "company_data_id"
    )

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute(f"""
        SELECT id, input_code
        FROM {structure_table}
        WHERE parent_id = %s AND {id_field} = %s
        ORDER BY input_code
    """, (parent_id, entity_id))
    siblings = cursor.fetchall()

    if not siblings:
        conn.close()
        return

    for idx, sibling in enumerate(siblings, start=1):
        old_code = sibling['input_code']
        parts = old_code.split('.')
        if parts:
            parts[-1] = str(idx)
            new_code = ".".join(parts)
            cursor.execute(f"""
                UPDATE {structure_table}
                SET input_code = %s
                WHERE id = %s
            """, (new_code, sibling['id']))

    conn.commit()
    conn.close()


@app.route('/upload_file', methods=['POST'])
def upload_file():
    """
    Route: /upload_file
    Purpose: Handle encrypted file upload using pyzipper (ZIP+password) only.
             No database insert/update happens here — handled during full form submit.
    Called from: dataset_data_input.html (JavaScript upload logic).
    """
    uploaded_file = request.files.get('file')
    input_code = request.form.get('input_code')

    if not uploaded_file or uploaded_file.filename == '':
        return jsonify({"error": "No file uploaded."}), 400

    filename = secure_filename(uploaded_file.filename)
    unique_filename = f"{uuid.uuid4()}_{filename}"
    temp_path = os.path.join(UPLOAD_FOLDER, unique_filename)
    uploaded_file.save(temp_path)

    # ZIP + Password Encrypt
    zip_filename = f"{unique_filename}.zip"
    zip_path = os.path.join(UPLOAD_FOLDER, zip_filename)

    try:
        with pyzipper.AESZipFile(zip_path, 'w', compression=pyzipper.ZIP_LZMA) as zf:
            zf.setpassword(ZIP_PASSWORD.encode())
            zf.setencryption(pyzipper.WZ_AES, nbits=256)
            zf.write(temp_path, arcname=filename)
        os.remove(temp_path)  # Remove original file after zipping
    except Exception as e:
        return jsonify({"error": f"Failed to encrypt file: {str(e)}"}), 500

    return jsonify({"file_path": f"/uploaded_files/{zip_filename}"})


@app.route('/download_file')
def download_file():
    """
    Function: download_file
    Purpose: Handling extract file tobe download from zip protected password, then Download File.
    Called from: dataset_data_input.html
    """
    file_path = request.args.get('path')
    if not file_path or not os.path.exists(file_path):
        return "File not found", 404

    # Decrypt and stream the file content
    with pyzipper.AESZipFile(file_path) as zf:
        zf.setpassword(ZIP_PASSWORD.encode())
        for name in zf.namelist():
            return send_file(io.BytesIO(zf.read(name)), download_name=name)


@app.after_request
def allow_iframe(response):
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    return response


# ROUTES =============================================================================================================
# --- Entry Point ---
@app.route('/')
def login():
    """
    Route: /
    Purpose: Displays login page.
    Called from: Browser default load.
    Calls: login.html
    """
    return render_template('login.html')


@csrf.exempt
@app.route('/login_check', methods=['POST'])
# @limiter.limit("5 per minute")
def login_check():
    """
    Route: /login_check
    Purpose: Validates login against hardcoded credentials.
    """

    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    hashed_pw = IS_PW.encode('utf-8')

    if username == IS_UN and bcrypt.checkpw(password.encode('utf-8'), hashed_pw):
        login_user(AdminUser("admin"))
        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/index')
@login_required
def index():
    """
    Route: /index
    Purpose: Displays landing page with logo and welcome.
    Called from: login.html
    Calls: index.html
    """
    layout = request.args.get("layout", "default")
    if layout == "figma":
        return render_template("index.html", layout_template="base_skin_figma.html")
    return render_template("index.html", layout_template="base.html")


# --- Dataset ---
@app.route('/dataset_data_input/<dataset_type>/<int:entity_id>',
           defaults={'company_id': None, 'corporate_id': None, 'input_code': None})
@app.route('/dataset_data_input/<dataset_type>/<int:entity_id>/<int:company_id>',
           defaults={'corporate_id': None, 'input_code': None})
@app.route('/dataset_data_input/<dataset_type>/<int:entity_id>/<int:company_id>/<int:corporate_id>',
           defaults={'input_code': None})
@app.route('/dataset_data_input/<dataset_type>/<int:entity_id>/<int:company_id>/<int:corporate_id>/<input_code>')
def dataset_data_input(dataset_type, entity_id, company_id, corporate_id, input_code):
    """
    Route: /dataset_data_input/<dataset_type>/<entity_id>
    Purpose: Show dynamic input form to fill data (company data or compliance).
    Called from: dataset_data_input.html
    Calls: dataset_data_input_get_dataset_structure()
    """
    layout_template = request.args.get("layout_template", "base.html")

    return render_template("dataset_data_input.html",
                           dataset_type=dataset_type,
                           company_id=company_id,
                           corporate_id=corporate_id,
                           sheet_id=entity_id if dataset_type == "compliance" else None,
                           company_data_id=entity_id if dataset_type == "company_data" else None,
                           input_code=input_code,
                           layout_template=layout_template)


@app.route('/dataset_data_input_subset.html')
def dataset_data_input_subset():
    """
    Route: /dataset_data_input_subset.html
    Purpose: Renders a partial view of a dataset starting from a specific input_code.
    Called from: dataset_form_browser.html preview buttons.
    """
    dataset_type = request.args.get("dataset_type")
    input_code = request.args.get("input_code")
    layout_template = request.args.get("layout_template", "base_modal.html")
    sheet_id = request.args.get("sheet_id")
    corporate_id = request.args.get("corporate_id")
    company_data_id = request.args.get("company_data_id")

    return render_template("dataset_data_input_subset.html",
                           dataset_type=dataset_type,
                           input_code=input_code,
                           sheet_id=sheet_id if sheet_id != "None" else None,
                           corporate_id=corporate_id if corporate_id != "None" else None,
                           company_data_id=company_data_id if company_data_id != "None" else None,
                           layout_template=layout_template)


@app.route('/dataset_data_input_get_dataset_structure/<dataset_type>/<int:entity_id>', defaults={'input_code': None})
@app.route('/dataset_data_input_get_dataset_structure/<dataset_type>/<int:entity_id>/<input_code>')
def dataset_data_input_get_dataset_structure(dataset_type, entity_id, input_code):
    """
    Route: /dataset_data_input_get_dataset_structure/<dataset_type>/<entity_id>
    Purpose: Fetch structure of dataset form dynamically (header, field type, etc.)
             and join with latest entry values (e.g., file_path, value).
    Called from: dataset_data_input.html (JavaScript form loader).
    """
    structure_table = dataset_structure_tables.get(dataset_type)
    entry_table = dataset_entries_tables.get(dataset_type)
    if not structure_table or not entry_table:
        return jsonify([])

    id_field = (
        "sheet_id" if dataset_type == "compliance"
        else "corporate_id" if dataset_type == "corporate"
        else "company_data_id"
    )

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    if input_code:
        # Recursive version if viewing a subsection
        cursor.execute(f"""
            WITH RECURSIVE tree AS (
                SELECT s.*
                FROM {structure_table} s
                WHERE s.{id_field} = %s AND s.input_code = %s
                UNION ALL
                SELECT s.*
                FROM {structure_table} s
                INNER JOIN tree t ON s.parent_id = t.id
            )
            SELECT t.*, e.value, e.file_path, e.is_original, e.next_due_date, 
                   e.side_note, e.upload_date, e.start_date
            FROM tree t
            LEFT JOIN {entry_table} e 
              ON t.input_code = e.input_code AND e.{id_field} = %s
            ORDER BY t.input_code
        """, (entity_id, input_code, entity_id))
    else:
        # Flat fetch for full structure
        cursor.execute(f"""
            SELECT s.*, e.value, e.file_path, e.is_original, e.next_due_date, 
                          e.side_note, e.upload_date, e.start_date
            FROM {structure_table} s
            LEFT JOIN {entry_table} e 
              ON s.input_code = e.input_code AND e.{id_field} = %s
            WHERE s.{id_field} = %s
            ORDER BY s.input_code
        """, (entity_id, entity_id))

    results = cursor.fetchall()
    for r in results:
        r['is_upload'] = bool(r.get('is_upload'))  # Force it to True/False

    conn.close()
    return jsonify(results)


@app.route('/dataset_data_input_submit_form/<dataset_type>', methods=['POST'])
def dataset_data_input_submit_form(dataset_type):
    """
    Route: /dataset_data_input_submit_form/<dataset_type>
    Purpose: Save or update form data into entries table; Backup old entries before overwrite; Auto update is_complete.
    Called from: dataset_data_input.html (Submit form).
    Calls: backup_old_entries(), update_is_complete_flag()
    """
    company_id = request.args.get('company_id', type=int)

    form_data = request.form.to_dict(flat=False)
    entry_table = dataset_entries_tables.get(dataset_type)
    if not entry_table:
        return jsonify({"error": "Invalid dataset type."}), 400

    entity_id = request.args.get('sheet_id') or request.args.get('corporate_id') or request.args.get('company_data_id')

    id_field = (
        "sheet_id" if dataset_type == "compliance"
        else "corporate_id" if dataset_type == "corporate"
        else "company_data_id"
    )

    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now()

    # Get structure for this entity to know which fields are uploads
    structure_table = dataset_structure_tables.get(dataset_type)
    cursor.execute(f"SELECT input_code, is_upload FROM {structure_table} WHERE {id_field} = %s", (entity_id,))
    structure_info = {row[0]: row[1] for row in cursor.fetchall()}

    # Backup first (before overwriting)
    real_input_codes = [key for key in form_data.keys() if not any(
        key.endswith(suffix) for suffix in ["_is_original", "_start_date", "_next_due_date", "_side_note"])]
    backup_old_entries(dataset_type, entity_id, real_input_codes, conn)

    for key, values in form_data.items():
        if any(key.endswith(suffix) for suffix in ["_is_original", "_start_date", "_next_due_date", "_side_note"]):
            continue  # handled below

        if len(values) > 1:
            value = json.dumps(values)
        else:
            value = values[0]

        input_code = key

        # Related metadata for uploads
        is_original = form_data.get(f"{input_code}_is_original", ["false"])[0] == "on"
        start_date = form_data.get(f"{input_code}_start_date", [None])[0]
        next_due_date = form_data.get(f"{input_code}_next_due_date", [None])[0]
        side_note = form_data.get(f"{input_code}_side_note", [""])[0]

        if structure_info.get(input_code):  # only for upload-enabled fields
            upload_date = now if value else None
            cursor.execute(f"""
                INSERT INTO {entry_table} 
                (company_id, {id_field}, input_code, value, is_original, 
                start_date, next_due_date, upload_date, side_note, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (entity_id, input_code, value, is_original,
                  start_date, next_due_date, upload_date, side_note, now))

        else:
            cursor.execute(f"""
                INSERT INTO {entry_table} (company_id, {id_field}, input_code, value, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (entity_id, input_code, value, now))

    update_is_complete_flag(dataset_type, entity_id, conn)

    conn.commit()
    conn.close()
    return jsonify({"message": "Data submitted successfully!"})


#  Corporate =========================================================================================================
@app.route('/corporate_group_browser')
def corporate_group_browser():
    """
    Route: /corporate_group_data
    Purpose: Returns JSON data of all corporate groups for DataTables.
    Called from: corporate_group_browser.html (AJAX)
    """
    return render_template('corporate_group_browser.html')


@app.route('/corporate_group_data')
def corporate_group_data():
    """
    Route: /corporate_group_data
    Purpose: Returns JSON data of all corporate groups for DataTables.
    Called from: corporate_group_browser.html (AJAX)
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("""
      SELECT g.*, (
        SELECT COUNT(*) FROM company_structure c WHERE c.group_id = g.id
      ) AS company_count
      FROM corporate_group g
      ORDER BY g.id
    """)
    data = cursor.fetchall()
    conn.close()
    return jsonify({"data": data})


@app.route('/corporate_group_form', methods=['GET'])
def corporate_group_form():
    """
    Route: /corporate_group_form
    Purpose: Renders form page to create or edit corporate group.
    Called from: corporate_group_browser.html (via button Add/Edit)
    Calls: corporate_group_form.html
    """
    group_id = request.args.get('edit')
    if group_id:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM corporate_group WHERE id = %s", (group_id,))
        group = cursor.fetchone()
        conn.close()
        return render_template('corporate_group_form.html', group=group)
    return render_template('corporate_group_form.html', group=None)


@app.route('/corporate_group_save', methods=['POST'])
def corporate_group_save():
    """
    Route: /corporate_group_save
    Purpose: Inserts or updates a corporate group record.
    Called from: corporate_group_form.html (Submit form)
    """
    data = request.form
    conn = get_db_connection()
    cursor = conn.cursor()
    if data.get('id'):
        cursor.execute("UPDATE corporate_group SET group_name = %s, group_description = %s WHERE id = %s",
                       (data['group_name'], data['description'], data['id']))
    else:
        cursor.execute("INSERT INTO corporate_group (group_name, group_description) VALUES (%s, %s)",
                       (data['group_name'], data['description']))
    conn.commit()
    conn.close()
    return jsonify({"message": "Corporate Group saved successfully"})


@app.route('/corporate_group_delete/<int:group_id>', methods=['DELETE'])
def corporate_group_delete(group_id):
    """
    Route: /corporate_group_delete/<group_id>
    Purpose: Deletes a corporate group entry by ID.
    Called from: corporate_group_browser.html (Delete button)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM corporate_group WHERE id = %s", (group_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Corporate Group deleted"})


#  Company ===========================================================================================================
@app.route('/company_browser/<int:group_id>')
def company_browser(group_id):
    """
    Route: /company_browser/<group_id>
    Purpose: Displays company hierarchy under a corporate group.
    Called from: corporate_group_browser.html (View button)
    Calls: company_browser.html
    """
    return render_template('company_browser.html', group_id=group_id)


@app.route('/company_tree_data/<int:group_id>')
def company_tree_data(group_id):
    """
    Route: /company_tree_data/<group_id>
    Purpose: Provides JSON data for company hierarchy tree (parent-child).
    Called from: company_browser.html (Tree rendering)
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("""
        SELECT id, parent_id, input_code, company_name, next_inspection_date 
        FROM company_structure WHERE group_id = %s ORDER BY input_code
    """, (group_id,))
    companies = cursor.fetchall()
    conn.close()
    return jsonify(companies)


@app.route('/company_form.html')
def company_form():
    """
    Route: /company_form.html
    Purpose: Renders form to add/edit a company under a corporate group.
    Called from: company_browser.html (Add/Edit)
    Calls: company_form.html
    """
    group_id = request.args.get('group_id', type=int)
    company_id = request.args.get('edit', type=int)
    company = None

    if company_id:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM company_structure WHERE id = %s", (company_id,))
        company = cursor.fetchone()
        conn.close()

    return render_template('company_form.html', company=company, group_id=group_id)


@app.route('/company_get/<int:id>')
def company_get(id):  # noqa
    """
    Route: /company_get/<id>
    Purpose: Fetches single company data by ID (used in edit modal).
    Called from: company_browser.html
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM company_structure WHERE id = %s", (id,))
    company = cursor.fetchone()
    conn.close()
    return jsonify(company)


@app.route('/company_save', methods=['POST'])
def company_save():
    """
    Route: /company_save
    Purpose: Saves or updates a company record in the database.
    Called from: company_form.html (Submit)
    """
    data = request.form
    conn = get_db_connection()
    cursor = conn.cursor()
    if data.get('id'):
        cursor.execute("""
            UPDATE company_structure SET company_name = %s, input_code = %s, parent_id = %s, next_inspection_date = %s
            WHERE id = %s
        """, (data['company_name'],
              data['input_code'],
              data.get('parent_id'),
              data.get('next_inspection_date'),
              data['id']))
    else:
        cursor.execute("""
            INSERT INTO company_structure (group_id, company_name, input_code, parent_id, next_inspection_date)
            VALUES (%s, %s, %s, %s, %s)
        """, (data['group_id'],
              data['company_name'],
              data['input_code'],
              data.get('parent_id'),
              data.get('next_inspection_date')))
    conn.commit()
    conn.close()
    return jsonify({"message": "Company saved successfully"})


@app.route('/company_delete/<int:id>', methods=['DELETE'])
def company_delete(id):  # noqa
    """
    Route: /company_delete/<id>
    Purpose: Deletes a company from the hierarchy.
    Called from: company_browser.html (Delete button)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM company_structure WHERE id = %s", (id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Company deleted"})


# Company Data =========================================================================================================

# --- Optional API for managing company_structure ---
@app.route('/company_structure_list/<int:group_id>')
def company_structure_list(group_id):
    """
    Route: /company_structure_list/<group_id>
    Purpose: Returns full list of company entries under a corporate group.
    Called from: (optional for table view or batch operations).
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("""
        SELECT id, group_id, company_name, input_code, parent_id, next_inspection_date
        FROM company_structure
        WHERE group_id = %s
        ORDER BY input_code
    """, (group_id,))
    companies = cursor.fetchall()
    conn.close()
    return jsonify(companies)


# Dynamic browser for both compliance and company data ================================================================
# --- Company Template Mapping Pages ---
@app.route('/company_template_browser/<dataset_type>/<int:company_id>')
def company_template_browser(dataset_type, company_id):
    """
    Route: /company_template_browser/<dataset_type>/<company_id>
    Purpose: Browse historical template assignment per company (both company_data and compliance).
    Called from: company_browser.html (Button View Compliance / View Company Data)
    Calls: company_template_browser.html
    """
    if dataset_type not in ["compliance", "company_data"]:
        return "Invalid dataset type", 400
    return render_template("company_template_browser.html",
                           dataset_type=dataset_type,
                           company_id=company_id)


# --- List active mappings dynamically ---
@app.route('/company_template_list/<dataset_type>/<int:company_id>')
def company_template_list(dataset_type, company_id):
    """
    Route: /company_template_list/<dataset_type>/<company_id>
    Purpose: Returns list of templates assigned to a company for given type.
    Used in: company_template_browser.html ➝ DataTables
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    if dataset_type == "compliance":
        cursor.execute("""
            SELECT mapping.id, b.sheet_description, b.sheet_search_tag, mapping.year, mapping.created_at
            FROM company_template_mapping mapping
            JOIN compliance_sheet_browse b ON mapping.compliance_sheet_id = b.id
            WHERE mapping.company_id = %s
            ORDER BY mapping.year DESC, mapping.created_at DESC
        """, (company_id,))
    elif dataset_type == "company_data":
        cursor.execute("""
            SELECT mapping.id, d.company_data_description, d.company_data_search_tag, mapping.year, mapping.created_at
            FROM company_template_mapping mapping
            JOIN company_data_browse d ON mapping.company_data_id = d.id
            WHERE mapping.company_id = %s
            ORDER BY mapping.year DESC, mapping.created_at DESC
        """, (company_id,))
    else:
        return jsonify({"error": "Invalid dataset_type"}), 400

    results = cursor.fetchall()
    conn.close()
    return jsonify({"data": results})


@app.route('/company_template_mapping_all')
def company_template_mapping_all():
    """
    Route: /company_template_mapping_all
    Purpose: Returns all mappings for all companies for quick lookup in browser.
    Used in: company_browser.html to check which company has compliance/data mappings.
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("""
        SELECT
          m.company_id,
          m.company_data_id,
          m.compliance_sheet_id,
        
          -- Company Data % complete
          ROUND(
            COUNT(DISTINCT s_cd.id) FILTER (
              WHERE s_cd.is_header = FALSE
                AND (
                (
                    e_cd.value IS NOT NULL AND TRIM(e_cd.value) <> '') 
                    OR (e_cd.file_path IS NOT NULL AND TRIM(e_cd.file_path) <> '')
                )
            ) * 100.0 /
            NULLIF(COUNT(DISTINCT s_cd.id) FILTER (WHERE s_cd.is_header = FALSE), 0)
          )::int AS company_data_completion,
        
          -- Compliance Sheet % complete
          ROUND(
            COUNT(DISTINCT s_cs.id) FILTER (
              WHERE s_cs.is_header = FALSE
                AND (
                (
                    e_cs.value IS NOT NULL AND TRIM(e_cs.value) <> '') 
                    OR (e_cs.file_path IS NOT NULL AND TRIM(e_cs.file_path) <> '')
                )
            ) * 100.0 /
            NULLIF(COUNT(DISTINCT s_cs.id) FILTER (WHERE s_cs.is_header = FALSE), 0)
          )::int AS compliance_completion
        
        FROM company_template_mapping m
        LEFT JOIN company_data_structure s_cd ON s_cd.company_data_id = m.company_data_id
        LEFT JOIN company_data_entries e_cd
          ON e_cd.company_data_id = s_cd.company_data_id 
          AND e_cd.input_code = s_cd.input_code 
          AND e_cd.company_id = m.company_id
        
        LEFT JOIN compliance_sheet_structure s_cs ON s_cs.sheet_id = m.compliance_sheet_id
        LEFT JOIN compliance_sheet_entries e_cs
          ON e_cs.sheet_id = s_cs.sheet_id 
          AND e_cs.input_code = s_cs.input_code 
          AND e_cs.company_id = m.company_id
        
        GROUP BY m.company_id, m.company_data_id, m.compliance_sheet_id
    """)
    results = cursor.fetchall()
    conn.close()
    return jsonify({"data": results})


# --- Get latest mapping dynamically ---
@app.route('/company_template_latest/<dataset_type>/<int:company_id>')
def company_template_latest(dataset_type, company_id):
    """
    Route: /company_template_latest/<dataset_type>/<company_id>
    Purpose: Returns the most recent template assigned to a company.
    Used in: company_template_browser.html ➝ Edit Latest button
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    if dataset_type == "compliance":
        cursor.execute("""
            SELECT mapping.compliance_sheet_id AS sheet_id
            FROM company_template_mapping mapping
            WHERE mapping.company_id = %s
            ORDER BY mapping.year DESC, mapping.created_at DESC
            LIMIT 1
        """, (company_id,))
    elif dataset_type == "company_data":
        cursor.execute("""
            SELECT mapping.company_data_id AS data_id
            FROM company_template_mapping mapping
            WHERE mapping.company_id = %s
            ORDER BY mapping.year DESC, mapping.created_at DESC
            LIMIT 1
        """, (company_id,))
    else:
        return jsonify({"error": "Invalid dataset_type"}), 400

    result = cursor.fetchone()
    conn.close()
    return jsonify(result or {})


# Dynamic Export PDF -------------------
@app.route('/company_template_export_pdf/<dataset_type>/<int:company_id>/<int:mapping_id>')
def export_company_template_pdf(dataset_type, company_id, mapping_id):
    """
    Route: /company_template_export_pdf/<dataset_type>/<company_id>/<mapping_id>
    Purpose: Export the current (or historical) compliance/company data entries into downloadable PDF.
    Called from: company_template_browser.html ➝ Export PDF button
    Calls: pdf_compliance_export.html (rendered as string)
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    if dataset_type == "compliance":
        cursor.execute("""
            SELECT s.input_code, s.input_display, s.input_type, s.is_header, s.is_upload,
                   e.value, e.file_path
            FROM company_template_mapping m
            JOIN compliance_sheet_structure s ON s.sheet_id = m.compliance_sheet_id
            LEFT JOIN compliance_sheet_entries e 
                ON e.sheet_id = s.sheet_id AND e.input_code = s.input_code AND e.user_id = m.company_id
            WHERE m.id = %s AND m.company_id = %s
            ORDER BY s.input_code
        """, (mapping_id, company_id))
    elif dataset_type == "company_data":
        cursor.execute("""
            SELECT s.input_code, s.input_display, s.input_type, s.is_header, s.is_upload,
                   e.value, e.file_path
            FROM company_template_mapping m
            JOIN company_data_structure s ON s.company_data_id = m.company_data_id
            LEFT JOIN company_data_entries e 
                ON e.company_data_id = s.company_data_id AND e.input_code = s.input_code AND e.user_id = m.company_id
            WHERE m.id = %s AND m.company_id = %s
            ORDER BY s.input_code
        """, (mapping_id, company_id))
    else:
        return jsonify({"error": "Invalid dataset_type"}), 400

    data = cursor.fetchall()
    conn.close()

    html = render_template("pdf_compliance_export.html", fields=data)
    config = pdfkit.configuration(wkhtmltopdf=r"C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
    pdf = pdfkit.from_string(html, False, configuration=config)

    return send_file(io.BytesIO(pdf), as_attachment=True,
                     download_name=f"{dataset_type}_export.pdf", mimetype='application/pdf')


# Dynamic Template Mapping (Company - Template) ======================================================================
# --- Company Template Mapping Browser (both company_data + compliance view) ---
@app.route('/company_template_mapping_browser/<int:company_id>')
def company_template_mapping_browser(company_id):
    """
    Route: /company_template_mapping_browser/<company_id>
    Purpose: Opens modal or popup to manage company-to-template mappings.
    Calls: company_template_mapping_browser.html
    """
    return render_template("company_template_mapping_browser.html", company_id=company_id)


# --- List all active template mappings for a company ---
@app.route('/company_template_mapping_list/<int:company_id>')
def company_template_mapping_list(company_id):
    """
    Route: /company_template_mapping_list/<company_id>
    Purpose: Lists all mappings (template + year) assigned to a company.
    Used in: company_template_mapping_browser.html ➝ DataTables
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("""
        SELECT m.id, m.year, m.link_description,
               cd.company_data_description, cs.sheet_description
        FROM company_template_mapping m
        LEFT JOIN company_data_browse cd ON m.company_data_id = cd.id
        LEFT JOIN compliance_sheet_browse cs ON m.compliance_sheet_id = cs.id
        WHERE m.company_id = %s
        ORDER BY m.year DESC, m.created_at DESC
    """, (company_id,))
    result = cursor.fetchall()
    conn.close()
    return jsonify({"data": result})


# --- Assign new mapping (and auto-backup previous into history) ---
@app.route('/company_template_mapping_form', methods=['GET', 'POST'])
def company_template_mapping_form():
    """
    Route: /company_template_mapping_form
    Purpose: Renders form to assign a company to a data + compliance template.
    Used in: company_template_mapping_browser.html ➝ Assign Template
    """
    company_id = request.args.get('company_id', type=int)

    if request.method == 'POST':
        compliance_sheet_id = request.form.get('compliance_sheet_id') or None
        company_data_id = request.form.get('company_data_id') or None
        year = request.form['year']
        link_description = request.form.get('link_description', '')

        conn = get_db_connection()
        cursor = conn.cursor()

        # --- Backup previous into company_template_mapping_history ---
        cursor.execute("""
            INSERT INTO company_template_mapping_history 
            (company_id, company_data_id, compliance_sheet_id, year, link_description, action_type, action_time)
            SELECT company_id, company_data_id, compliance_sheet_id, year, link_description, 'UPDATE', NOW()
            FROM company_template_mapping
            WHERE company_id = %s
        """, (company_id,))

        # --- Optional: delete old mapping if you want only 1 active mapping ---
        cursor.execute("""
            DELETE FROM company_template_mapping
            WHERE company_id = %s
        """, (company_id,))

        # --- Insert new mapping ---
        cursor.execute("""
            INSERT INTO company_template_mapping 
            (company_id, compliance_sheet_id, company_data_id, year, link_description)
            VALUES (%s, %s, %s, %s, %s)
        """, (company_id, compliance_sheet_id, company_data_id, year, link_description))

        conn.commit()
        conn.close()
        return jsonify({"message": "Mapping saved successfully!"}), 200

    # -- GET form mode (fetch dropdown options) --
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT id, sheet_description FROM compliance_sheet_browse")
    sheets = cursor.fetchall()
    cursor.execute("SELECT id, company_data_description FROM company_data_browse")
    templates = cursor.fetchall()
    conn.close()

    return render_template("company_template_mapping_form.html",
                           company_id=company_id,
                           sheets=sheets,
                           templates=templates,
                           layout_template="base_modal.html")


# --- Company Template Mapping History ---
@app.route('/company_template_mapping_history/<int:company_id>')
def company_template_mapping_history(company_id):
    """
    Route: /company_template_mapping_history/<company_id>
    Purpose: Fetches all previous mapping history for audit purposes.
    Used in: company_template_mapping_browser.html
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("""
        SELECT h.id, h.year, h.link_description, 
               cd.company_data_description, cs.sheet_description,
               h.action_type, h.action_time
        FROM company_template_mapping_history h
        LEFT JOIN company_data_browse cd ON h.company_data_id = cd.id
        LEFT JOIN compliance_sheet_browse cs ON h.compliance_sheet_id = cs.id
        WHERE h.company_id = %s
        ORDER BY h.action_time DESC
    """, (company_id,))
    results = cursor.fetchall()
    conn.close()
    return jsonify({"data": results})


# ====================================================================================================================
@app.route('/dataset_template_browser.html')
def template_browser():
    """
    Route: /dataset_template_browser.html
    Purpose: Browse templates (company data or compliance) with option to Add New Template.
    Called from: Navbar -> Manage Template -> Template Browser
    Calls: dataset_template_browser.html
    """
    dataset_type = request.args.get('dataset_type')
    if dataset_type not in ['compliance', 'company_data']:
        return "Invalid dataset type", 400
    return render_template("dataset_template_browser.html", dataset_type=dataset_type)


@app.route('/dataset_template_browse_data/<dataset_type>')
def dataset_template_browse_data(dataset_type):
    """
    Route: /dataset_template_browse_data/<dataset_type>
    Purpose: Return JSON-formatted list of available templates of a given type (compliance/company data).
    Called from: dataset_template_browser.html ➝ DataTables AJAX
    """
    if dataset_type == "company_data":
        table = "company_data_browse"
        columns = "id, company_data_search_tag AS search_tag, company_data_description AS description, created_at"
    elif dataset_type == "compliance":
        table = "compliance_sheet_browse"
        columns = "id, sheet_search_tag AS search_tag, sheet_description AS description, created_at"
    else:
        return jsonify({"data": []})

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(f"SELECT {columns} FROM {table} ORDER BY created_at DESC")
    results = cursor.fetchall()
    conn.close()
    return jsonify({"data": results})


# Unified form renderer
@app.route('/dataset_template_form/<dataset_type>', defaults={'template_id': None})
@app.route('/dataset_template_form/<dataset_type>/<int:template_id>')
def dataset_template_form(dataset_type, template_id):
    """
    Route: /dataset_template_form/<dataset_type> or /dataset_template_form/<dataset_type>/<id>
    Purpose: Displays the form to Add or Edit Template.
    Called from: dataset_template_browser.html
    Calls: dataset_template_form.html
    """
    if dataset_type not in ['company_data', 'compliance']:
        return "Invalid dataset type", 400

    template_data = None
    if template_id is not None:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(f"SELECT * FROM {dataset_browse_tables[dataset_type]} WHERE id = %s", (template_id,))
        template_data = cur.fetchone()
        conn.close()

    return render_template(
        'dataset_template_form.html',
        dataset_type=dataset_type,
        template_data=template_data
    )


# Unified save
@app.route('/dataset_template_save/<dataset_type>', methods=['POST'])
def dataset_template_save(dataset_type):
    """
    Route: /dataset_template_save/<dataset_type> [POST]
    Purpose: Insert or update a template record into compliance or company_data browse table.
    Called from: dataset_template_form.html ➝ Submit
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    search_tag = request.form['search_tag']
    description = request.form['description']
    template_id = request.form.get('template_id')
    try:
        if dataset_type == 'company_data':
            if template_id:
                cursor.execute("""
                    UPDATE company_data_browse
                    SET company_data_search_tag = %s,
                        company_data_description = %s
                    WHERE id = %s
                """, (search_tag, description, template_id))
                new_id = template_id
            else:
                cursor.execute("""
                    INSERT INTO company_data_browse (company_data_search_tag, company_data_description)
                    VALUES (%s, %s) RETURNING id
                """, (search_tag, description))
                new_id = cursor.fetchone()[0]

        elif dataset_type == 'compliance':
            if template_id:
                cursor.execute("""
                    UPDATE compliance_sheet_browse
                    SET sheet_search_tag = %s,
                        sheet_description = %s
                    WHERE id = %s
                """, (search_tag, description, template_id))
                new_id = template_id
            else:
                cursor.execute("""
                    INSERT INTO compliance_sheet_browse (sheet_search_tag, sheet_description)
                    VALUES (%s, %s) RETURNING id
                """, (search_tag, description))
                new_id = cursor.fetchone()[0]
        else:
            return jsonify({"error": "Invalid dataset type."}), 400

        conn.commit()
        return jsonify({"id": new_id})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)})
    finally:
        conn.close()


# dataset Data ========================================================================================================

@app.route('/dataset_form_browser/<dataset_type>/<int:entity_id>/<string:template_name>')
def dataset_form_browser(dataset_type, entity_id, template_name):
    """
    Route: /dataset_form_browser/<dataset_type>/<entity_id>/<template_name>
    Purpose: Displays template field structure in Tree/Collapse/Expand style for a dataset.
    Used in: dataset_template_browser.html ➝ Edit Structure
    Called from: dataset_form_browser.html
    Calls: dataset_data_input_get_dataset_structure()
    """
    return render_template("dataset_form_browser.html",
                           dataset_type=dataset_type,
                           template_name=template_name,
                           sheet_id=entity_id if dataset_type == "compliance" else None,
                           corporate_id=entity_id if dataset_type == "corporate" else None,
                           company_data_id=entity_id if dataset_type == "company_data" else None)


# --- Dataset Form Tree ---
@app.route('/dataset_form_tree/<dataset_type>/<int:entity_id>')
def dataset_form_tree(dataset_type, entity_id):
    """
    Route: /dataset_form_tree/<dataset_type>/<int:entity_id>
    Purpose: Fetches dataset structure in a flat list (supports nesting).
    Used in: dataset_form_browser.html to display structure as a tree.
    """
    structure_table = dataset_structure_tables.get(dataset_type)
    if not structure_table:
        return jsonify({"error": "Invalid dataset type"}), 400

    id_field = (
        "sheet_id" if dataset_type == "compliance"
        else "corporate_id" if dataset_type == "corporate"
        else "company_data_id" if dataset_type == "company"
        else "sub_template_id"
    )

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(f"SELECT * FROM {structure_table} WHERE {id_field} = %s ORDER BY input_code", (entity_id,))
    results = cursor.fetchall()
    conn.close()
    return jsonify(results)


@app.route('/dataset_form_add_and_edit.html')
def dataset_form_add_and_edit():
    """
    Route: /dataset_form_add_and_edit.html
    Purpose: Renders a unified HTML form to add or edit dataset structure fields.
    Called from: dataset_form_browser.html ➝ Add/Edit buttons.
    Calls: dataset_form_add_and_edit.html
    """
    dataset_type = request.args.get('dataset_type')
    sheet_id = request.args.get('sheet_id')
    corporate_id = request.args.get('corporate_id')
    company_data_id = request.args.get('company_data_id')
    return render_template("dataset_form_add_and_edit.html",
                           dataset_type=dataset_type,
                           sheet_id=sheet_id,
                           corporate_id=corporate_id,
                           company_data_id=company_data_id)


# --- Get Parent & Sibling Info ---
@app.route('/dataset_form_get_parent_sibling_info/<dataset_type>/<int:parent_id>/<int:entity_id>', methods=['GET'])
def dataset_form_get_parent_sibling_info(dataset_type, parent_id, entity_id):
    """
    Route: /dataset_form_get_parent_sibling_info/<dataset_type>/<int:target_id>/<int:entity_id>
    Purpose: Retrieves parent ID and sibling list for a given field to assist in adding new fields.
    Used in: dataset_form_browser.html ➝ Add Sibling or Child field
    """
    table_name = dataset_structure_tables.get(dataset_type)
    if not table_name:
        return jsonify({"error": "Invalid dataset type."}), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    id_field = (
        "sheet_id" if dataset_type == "compliance"
        else "corporate_id" if dataset_type == "corporate"
        else "company_data_id" if dataset_type == "company"
        else "sub_template_id"
    )

    # Get parent info
    cursor.execute(f"SELECT input_display FROM {table_name} WHERE id = %s", (parent_id,))
    parent_row = cursor.fetchone()
    parent_display = parent_row['input_display'] if parent_row else "Root"

    # Get last sibling code
    cursor.execute(f"""
        SELECT input_code FROM {table_name}
        WHERE parent_id = %s AND {id_field} = %s
        ORDER BY input_code DESC LIMIT 1
    """, (parent_id, entity_id))
    sibling = cursor.fetchone()

    def get_next_code(last_code):   # noqa
        if not last_code:
            return "1"
        parts = last_code.split('.')
        parts[-1] = str(int(parts[-1]) + 1)
        return '.'.join(parts)

    last_code = sibling['input_code'] if sibling else None
    next_code = get_next_code(last_code)

    conn.close()
    return jsonify({
        f"{id_field}": entity_id,
        "parent_id": parent_id,
        "parent_display": parent_display,
        "last_sibling_code": last_code,
        "next_input_code": next_code
    })


@app.route('/dataset_form_get_field/<dataset_type>/<int:field_id>', methods=['GET'])
def get_field(dataset_type, field_id):
    """
    Route: /dataset_form_get_field/<dataset_type>/<int:field_id>
    Purpose: Fetches a single dataset field for editing.
    Used in: dataset_form_browser.html ➝ Edit button
    """
    table_name = dataset_structure_tables.get(dataset_type)
    if not table_name:
        return jsonify({"error": "Invalid dataset type."}), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(f"SELECT * FROM {table_name} WHERE id = %s", (field_id,))
    field = cursor.fetchone()
    conn.close()
    return jsonify(field)


@app.route('/dataset_form_add_field/<dataset_type>', methods=['POST'])
def add_field(dataset_type):
    """
    Route: /dataset_form_add_field/<dataset_type> [POST]
    Purpose: Adds a new field to the dataset structure.
    Used in: dataset_form_add_and_edit.html (Add form)
    """
    table_name = dataset_structure_tables.get(dataset_type)
    if not table_name:
        return jsonify({"error": "Invalid dataset type."}), 400

    data = request.json
    id_field = (
        "sheet_id" if dataset_type == "compliance"
        else "corporate_id" if dataset_type == "corporate"
        else "company_data_id"
    )

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        INSERT INTO {table_name}
        ({id_field}, input_code, parent_id, is_header, input_display, input_type, is_mandatory, select_value, is_upload)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        data.get(id_field), data['input_code'], data.get('parent_id'), data['is_header'],
        data['input_display'], data['input_type'], data['is_mandatory'], data['select_value'], data['is_upload']
    ))
    conn.commit()
    conn.close()
    return jsonify({"message": "Field added successfully."})


@app.route('/dataset_form_edit_field/<dataset_type>/<int:field_id>', methods=['PUT'])
def edit_field(dataset_type, field_id):
    """
    Route: /dataset_form_edit_field/<dataset_type>/<int:field_id> [PUT]
    Purpose: Updates an existing field in the dataset structure.
    Used in: dataset_form_add_and_edit.html (Edit form)
    """
    table_name = dataset_structure_tables.get(dataset_type)
    if not table_name:
        return jsonify({"error": "Invalid dataset type."}), 400

    data = request.json

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        UPDATE {table_name} SET
            input_code = %s,
            input_display = %s,
            input_type = %s,
            is_mandatory = %s,
            select_value = %s,
            is_upload = %s,
            is_header = %s
        WHERE id = %s
    """, (
        data['input_code'], data['input_display'], data['input_type'], data['is_mandatory'],
        data['select_value'], data['is_upload'], data['is_header'], field_id
    ))
    conn.commit()
    conn.close()
    return jsonify({"message": "Field updated successfully."})


@app.route('/delete_field/<dataset_type>/<int:field_id>', methods=['DELETE'])
def delete_field(dataset_type, field_id):
    """
    Route: /delete_field/<dataset_type>/<field_id>
    Purpose: Deletes a field safely if not already used; then renumber sibling fields.
    Called from: dataset_form_browser.html (Delete button).
    Calls: renumber_siblings()
    """
    structure_table = dataset_structure_tables.get(dataset_type)
    entry_table = dataset_entries_tables.get(dataset_type)
    history_table = dataset_history_tables.get(dataset_type)

    if not structure_table or not entry_table or not history_table:
        return jsonify({"error": "Invalid dataset type."}), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Get field info
    cursor.execute(
        f"SELECT id, input_code, parent_id, "
        f"{'sheet_id' if dataset_type == 'compliance' else 'company_data_id'} as entity_id "
        f"FROM {structure_table} WHERE id = %s",
        (field_id,))

    field = cursor.fetchone()
    if not field:
        conn.close()
        return jsonify({"error": "Field not found."}), 404

    input_code = field['input_code']
    parent_id = field['parent_id']
    entity_id = field['entity_id']

    # Check if this field has entries
    cursor.execute(f"SELECT COUNT(*) FROM {entry_table} WHERE input_code = %s", (input_code,))
    count = cursor.fetchone()['count']
    if count > 0:
        conn.close()
        return jsonify({"error": "Cannot delete: field already used by company or user."}), 400

    # Safe to delete: archive and delete
    cursor.execute(f"INSERT INTO {history_table} "
                   f"({'sheet_id' if dataset_type == 'compliance' else 'company_data_id'}, "
                   f"input_code, value, action_type, action_time) "
                   f"SELECT {'sheet_id' if dataset_type == 'compliance' else 'company_data_id'}, "
                   f"input_code, value, 'DELETE', NOW() FROM {entry_table} WHERE input_code = %s", (input_code,))
    cursor.execute(f"DELETE FROM {structure_table} WHERE id = %s", (field_id,))

    conn.commit()

    # Renumber siblings
    renumber_siblings(dataset_type, parent_id, entity_id)
    conn.close()
    return jsonify({"message": "Deleted and Renumbered Successfully."})


@app.route('/copy_template/<dataset_type>/<int:template_id>', methods=['POST'])
def copy_template(dataset_type, template_id):
    """
    Route: /copy_template/<dataset_type>/<template_id>
    Purpose: Copies existing template structure into a new template (including nested fields).
    Called from: dataset_template_browser.html (Button Copy)
    """
    structure_table = dataset_structure_tables.get(dataset_type)
    template_table = dataset_browse_tables.get(dataset_type)
    id_field = "company_data_id" if dataset_type == "company_data" else "sheet_id"
    new_template_id = None

    if not structure_table or not template_table:
        return jsonify({"error": "Invalid dataset type."}), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Step 1: Duplicate template metadata
    if dataset_type == "company_data":
        cursor.execute("SELECT company_data_search_tag, company_data_description "
                       "FROM company_data_browse WHERE id = %s", (template_id,))
        template = cursor.fetchone()
        if not template:
            conn.close()
            return jsonify({"error": "Original template not found."}), 404

        cursor.execute("""INSERT INTO company_data_browse 
                          (company_data_search_tag, company_data_description, created_at)
                          VALUES (%s, %s, NOW()) RETURNING id""",
                       (template['company_data_search_tag'] + " Copy",
                        template['company_data_description'] + " (Copy)"))
    else:  # compliance
        cursor.execute("SELECT sheet_search_tag, sheet_description "
                       "FROM compliance_sheet_browse WHERE id = %s", (template_id,))
        template = cursor.fetchone()
        if not template:
            conn.close()
            return jsonify({"error": "Original template not found."}), 404

        cursor.execute("""INSERT INTO compliance_sheet_browse (sheet_search_tag, sheet_description, created_at)
                          VALUES (%s, %s, NOW()) RETURNING id""",
                       (template['sheet_search_tag'] + " Copy", template['sheet_description'] + " (Copy)"))

    new_template_id = cursor.fetchone()['id']

    # Step 2: Copy structure rows with temporary NULL parent_id
    cursor.execute(f"""INSERT INTO {structure_table}
                      ({id_field}, input_code, parent_id, is_header, input_display, input_type, 
                      is_mandatory, select_value, is_upload, created_at)
                      SELECT %s, input_code, NULL, is_header, input_display, input_type, 
                      is_mandatory, select_value, is_upload, NOW()
                      FROM {structure_table} WHERE {id_field} = %s
                      RETURNING id, input_code""", (new_template_id, template_id))
    new_rows = cursor.fetchall()
    code_to_new_id = {row['input_code']: row['id'] for row in new_rows}

    # Step 3: Fetch old input_code → parent_id
    cursor.execute(f"""SELECT id, input_code, parent_id 
                            FROM {structure_table} WHERE {id_field} = %s""", (template_id,))
    old_rows = cursor.fetchall()
    old_id_to_code = {r['id']: r['input_code'] for r in old_rows}
    child_code_to_parent_code = \
        {r['input_code']: old_id_to_code.get(r['parent_id']) for r in old_rows if r['parent_id']}

    # Step 4: Update parent_id in new structure
    for child_code, parent_code in child_code_to_parent_code.items():
        new_child_id = code_to_new_id.get(child_code)
        new_parent_id = code_to_new_id.get(parent_code)
        if new_child_id and new_parent_id:
            cursor.execute(f"""UPDATE {structure_table} SET parent_id = %s WHERE id = %s""",
                           (new_parent_id, new_child_id))

    conn.commit()
    conn.close()
    return jsonify({"message": "Template copied successfully!", "new_id": new_template_id})


#  Sub Template ========================================================================================================

@app.route('/sub_template_browser.html')
def sub_template_browser_html():
    return render_template("sub_template_browser.html")


@app.route('/sub_template_browse_data')
def sub_template_browse_data():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT id, name, description, created_at FROM sub_template_browse ORDER BY created_at DESC")
    data = cursor.fetchall()
    conn.close()
    return jsonify({"data": data})


@app.route('/sub_template_form', methods=['GET', 'POST'])
def sub_template_form():
    if request.method == 'POST':
        template_id = request.form.get("template_id", type=int)
        name = request.form['name']
        description = request.form['description']
        conn = get_db_connection()
        cursor = conn.cursor()
        if template_id:
            cursor.execute(
                "UPDATE sub_template_browse SET name=%s, description=%s WHERE id=%s",
                (name, description, template_id)
            )
        else:
            cursor.execute(
                "INSERT INTO sub_template_browse (name, description) VALUES (%s, %s) RETURNING id",
                (name, description)
            )
            template_id = cursor.fetchone()[0]  # ✅ this was missing

        conn.commit()
        conn.close()
        return jsonify({"message": "Saved", "id": template_id})

    # --- GET request ---
    template_id = request.args.get("template_id", type=int)
    template = None
    if template_id:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM sub_template_browse WHERE id = %s", (template_id,))
        template = cursor.fetchone()
        conn.close()

    return render_template("sub_template_form.html", template_data=template)


@app.route('/sub_template_form_browser/<int:sub_template_id>')
def sub_template_form_browser(sub_template_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sub_template_browse WHERE id = %s", (sub_template_id,))
    row = cursor.fetchone()
    conn.close()
    return render_template("sub_template_form_browser.html",
                           sub_template_id=sub_template_id,
                           template_name=row[0] if row else "Unknown")


@app.route('/copy_sub_template_to_template/<dataset_type>/<int:target_id>/<int:sub_template_id>/<int:parent_id>',
           methods=["POST"])
def copy_sub_template_to_template(dataset_type, target_id, sub_template_id, parent_id):
    """
    dataset_type: 'company_data' or 'compliance'
    target_id: company_data_id or sheet_id
    parent_id: parent node in the destination template
    """
    structure_table = dataset_structure_tables.get(dataset_type)
    if not structure_table:
        return jsonify({"error": "Invalid dataset type"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Load sub_template_structure tree (ordered)
    cursor.execute("""
        WITH RECURSIVE tree AS (
            SELECT *, 0 AS level FROM sub_template_structure WHERE sub_template_id = %s AND parent_id IS NULL
            UNION ALL
            SELECT s.*, t.level + 1
            FROM sub_template_structure s
            JOIN tree t ON s.parent_id = t.id
        )
        SELECT * FROM tree ORDER BY level, input_code
    """, (sub_template_id,))
    source_fields = cursor.fetchall()

    # 2. Generate new entries into the target structure table
    old_to_new_ids = {}
    for field in source_fields:
        parent_new_id = old_to_new_ids.get(field['parent_id'], parent_id)
        cursor.execute(f"""
            INSERT INTO {structure_table}
              (input_code, parent_id, is_header, input_display, input_type, is_mandatory,
               select_value, is_upload, {'sheet_id' if dataset_type == 'compliance' else 'company_data_id'})
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            field['input_code'],
            parent_new_id,
            field['is_header'],
            field['input_display'],
            field['input_type'],
            field['is_mandatory'],
            field['select_value'],
            field['is_upload'],
            target_id
        ))
        new_id = cursor.fetchone()[0]
        old_to_new_ids[field['id']] = new_id

    conn.commit()
    conn.close()
    return jsonify({"message": "Sub template copied successfully!"})


@app.route('/sub_template_add_and_edit.html')
def sub_template_add_and_edit():
    sub_template_id = request.args.get('sub_template_id', type=int)
    return render_template('sub_template_add_and_edit.html', sub_template_id=sub_template_id)


@app.route('/sub_template_compare.html')
def sub_template_compare():
    return render_template("sub_template_compare.html")


# Error Handler for Uniform JSON ======================================================================================

@app.errorhandler(404)
def page_not_found(e):  # noqa
    return jsonify({"error": "Not Found"}), 404


@app.errorhandler(405)
def method_not_allowed(e):  # noqa
    return jsonify({"error": "Method Not Allowed"}), 405


@app.errorhandler(500)
def internal_error(e):  # noqa
    return jsonify({"error": "Internal Server Error"}), 500


# RUN ================================================================================================================
if __name__ == '__main__':
    app.run(debug=True)
