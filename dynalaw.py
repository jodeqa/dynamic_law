from flask import Flask, render_template, request, jsonify, send_file
import psycopg2
import psycopg2.extras
from datetime import datetime
import io
import pdfkit

app = Flask(__name__)


# --- Database connection ---
def get_db_connection():
    return psycopg2.connect(
        host='localhost',
        database='dynamic_law',
        user='postgres',
        password='P@ssw0rd',
        port=5432
    )


# --- Dataset Type Mapping ---
dataset_structure_tables = {
    "compliance": "compliance_sheet_structure",
    "corporate": "corporate_structure",
    "company_data": "company_data_structure"
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


@app.route('/')
def entrypoint():
    return render_template('index.html')


#  Corporate and Company Browser ====================================================================================
# --- 1. Browse Corporate Groups ---
@app.route('/corporate_group_browser')
def corporate_group_browser():
    return render_template('corporate_group_browser.html')


@app.route('/corporate_group_data')
def corporate_group_data():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT id, group_name, group_description, created_at FROM corporate_group ORDER BY id")
    data = cursor.fetchall()
    conn.close()
    return jsonify({"data": data})


# --- 2. Add/Edit Corporate Group ---
@app.route('/corporate_group_form', methods=['GET'])
def corporate_group_form():
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
    data = request.form
    conn = get_db_connection()
    cursor = conn.cursor()
    if data.get('id'):
        cursor.execute("UPDATE corporate_group SET group_name = %s, description = %s WHERE id = %s",
                       (data['group_name'], data['description'], data['id']))
    else:
        cursor.execute("INSERT INTO corporate_group (group_name, description) VALUES (%s, %s)",
                       (data['group_name'], data['description']))
    conn.commit()
    conn.close()
    return jsonify({"message": "Corporate Group saved successfully"})


@app.route('/corporate_group_delete/<int:group_id>', methods=['DELETE'])
def corporate_group_delete(group_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM corporate_group WHERE id = %s", (group_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Corporate Group deleted"})


# --- 3. Browse Company Structure (Tree or Table) ---
@app.route('/company_browser/<int:group_id>')
def company_browser(group_id):
    return render_template('company_browser.html', group_id=group_id)


@app.route('/company_tree_data/<int:group_id>')
def company_tree_data(group_id):
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
def company_get(id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM company_structure WHERE id = %s", (id,))
    company = cursor.fetchone()
    conn.close()
    return jsonify(company)


@app.route('/company_save', methods=['POST'])
def company_save():
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
def company_delete(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM company_structure WHERE id = %s", (id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Company deleted"})


#  dataset Data =====================================================================================================
# dataset form ------------------------------------------------------------------------------------------------------
@app.route('/dataset_form_browser/<dataset_type>/<int:entity_id>')
def dataset_form_browser(dataset_type, entity_id):
    return render_template("dataset_form_browser.html",
                           dataset_type=dataset_type,
                           sheet_id=entity_id if dataset_type == "compliance" else None,
                           corporate_id=entity_id if dataset_type == "corporate" else None,
                           company_data_id=entity_id if dataset_type == "company_data" else None)


# --- Dataset Form Tree ---
@app.route('/dataset_form_tree/<dataset_type>/<int:entity_id>')
def dataset_form_tree(dataset_type, entity_id):
    structure_table = dataset_structure_tables.get(dataset_type)
    if not structure_table:
        return jsonify({"error": "Invalid dataset type"}), 400

    id_field = (
        "sheet_id" if dataset_type == "compliance"
        else "corporate_id" if dataset_type == "corporate"
        else "company_data_id"
    )

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(f"SELECT * FROM {structure_table} WHERE {id_field} = %s ORDER BY input_code", (entity_id,))
    results = cursor.fetchall()
    conn.close()
    return jsonify(results)


@app.route('/dataset_form_add_and_edit.html')
def dataset_form_add_and_edit():
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
    table_name = dataset_structure_tables.get(dataset_type)
    if not table_name:
        return jsonify({"error": "Invalid dataset type."}), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    id_field = (
        "sheet_id" if dataset_type == "compliance"
        else "corporate_id" if dataset_type == "corporate"
        else "company_data_id"
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

    def get_next_code(last_code):
        if not last_code:
            return "1"
        parts = last_code.split('.')
        parts[-1] = str(int(parts[-1]) + 1)
        return '.'.join(parts)

    last_code = sibling['input_code'] if sibling else None
    next_code = get_next_code(last_code)

    conn.close()
    return jsonify({
        "parent_display": parent_display,
        "last_sibling_code": last_code,
        "next_input_code": next_code
    })


# --- Get Single Field ---
@app.route('/dataset_form_get_field/<dataset_type>/<int:field_id>', methods=['GET'])
def get_field(dataset_type, field_id):
    table_name = dataset_structure_tables.get(dataset_type)
    if not table_name:
        return jsonify({"error": "Invalid dataset type."}), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(f"SELECT * FROM {table_name} WHERE id = %s", (field_id,))
    field = cursor.fetchone()
    conn.close()
    return jsonify(field)


# --- Add New Field ---
@app.route('/dataset_form_add_field/<dataset_type>', methods=['POST'])
def add_field(dataset_type):
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


# --- Edit Existing Field ---
@app.route('/dataset_form_edit_field/<dataset_type>/<int:field_id>', methods=['PUT'])
def edit_field(dataset_type, field_id):
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


# --- Delete Field ---
@app.route('/delete_field/<dataset_type>/<int:field_id>', methods=['DELETE'])
def delete_field(dataset_type, field_id):
    structure_table = dataset_structure_tables.get(dataset_type)
    entry_table = dataset_entries_tables.get(dataset_type)
    history_table = dataset_history_tables.get(dataset_type)

    if not structure_table or not entry_table or not history_table:
        return jsonify({"error": "Invalid dataset type."}), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Get field info
    cursor.execute(f"SELECT id, input_code, parent_id FROM {structure_table} WHERE id = %s", (field_id,))
    field = cursor.fetchone()
    if not field:
        conn.close()
        return jsonify({"error": "Field not found."}), 404

    input_code = field['input_code']
    parent_id = field['parent_id']

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
    renumber_siblings(dataset_type, parent_id)

    conn.close()
    return jsonify({"message": "Deleted and Renumbered Successfully."})


# --- COPY TEMPLATE ---
@app.route('/copy_template/<dataset_type>/<int:template_id>', methods=['POST'])
def copy_template(dataset_type, template_id):
    structure_table = dataset_structure_tables.get(dataset_type)
    template_table = dataset_browse_tables.get(dataset_type)
    new_template_id = None

    if not structure_table or not template_table:
        return jsonify({"error": "Invalid dataset type."}), 400

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Fetch original template
    if dataset_type == "company_data":
        cursor.execute("SELECT company_data_search_tag, company_data_description "
                       "FROM company_data_browse WHERE id = %s", (template_id,))
        template = cursor.fetchone()
        if not template:
            conn.close()
            return jsonify({"error": "Original template not found."}), 404

        # Insert new template
        cursor.execute("""
            INSERT INTO company_data_browse (company_data_search_tag, company_data_description, created_at)
            VALUES (%s, %s, NOW()) RETURNING id
        """, (template['company_data_search_tag'] + " Copy", template['company_data_description'] + " (Copy)"))
        new_template_id = cursor.fetchone()['id']

        # Copy structure
        cursor.execute("""
            INSERT INTO company_data_structure 
            (company_data_id, input_code, parent_id, is_header, input_display, 
            input_type, is_mandatory, select_value, is_upload, created_at)
            SELECT 
            %s, input_code, parent_id, is_header, input_display, 
            input_type, is_mandatory, select_value, is_upload, NOW()
            FROM company_data_structure WHERE company_data_id = %s
        """, (new_template_id, template_id))

    elif dataset_type == "compliance":
        cursor.execute("SELECT sheet_search_tag, sheet_description "
                       "FROM compliance_sheet_browse WHERE id = %s", (template_id,))
        template = cursor.fetchone()
        if not template:
            conn.close()
            return jsonify({"error": "Original template not found."}), 404

        cursor.execute("""
            INSERT INTO compliance_sheet_browse (sheet_search_tag, sheet_description, created_at)
            VALUES (%s, %s, NOW()) RETURNING id
        """, (template['sheet_search_tag'] + " Copy", template['sheet_description'] + " (Copy)"))
        new_template_id = cursor.fetchone()['id']

        cursor.execute("""
            INSERT INTO compliance_sheet_structure 
            (sheet_id, input_code, parent_id, is_header, input_display, 
            input_type, is_mandatory, select_value, is_upload, created_at)
            SELECT %s, input_code, parent_id, is_header, input_display, 
            input_type, is_mandatory, select_value, is_upload, NOW()
            FROM compliance_sheet_structure WHERE sheet_id = %s
        """, (new_template_id, template_id))

    conn.commit()
    conn.close()

    return jsonify({"message": "Template copied successfully!", "new_id": new_template_id})


def renumber_siblings(dataset_type, parent_id, entity_id):
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


# --- Dataset Input Data Retrieval ---
@app.route('/dataset_data_input/<dataset_type>/<int:entity_id>', defaults={'input_code': None})
@app.route('/dataset_data_input/<dataset_type>/<int:entity_id>/<input_code>')
def dataset_data_input(dataset_type, entity_id, input_code):
    return render_template("dataset_data_input.html",
                           dataset_type=dataset_type,
                           sheet_id=entity_id if dataset_type == "compliance" else None,
                           corporate_id=entity_id if dataset_type == "corporate" else None,
                           company_data_id=entity_id if dataset_type == "company_data" else None,
                           input_code=input_code)


@app.route('/dataset_data_input_get_dataset_structure/<dataset_type>/<int:entity_id>', defaults={'input_code': None})
@app.route('/dataset_data_input_get_dataset_structure/<dataset_type>/<int:entity_id>/<input_code>')
def dataset_data_input_get_dataset_structure(dataset_type, entity_id, input_code):
    structure_table = dataset_structure_tables.get(dataset_type)
    if not structure_table:
        return jsonify([])

    id_field = (
        "sheet_id" if dataset_type == "compliance"
        else "corporate_id" if dataset_type == "corporate"
        else "company_data_id"
    )

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    if input_code:
        cursor.execute(f"""
            WITH RECURSIVE tree AS (
                SELECT * FROM {structure_table} WHERE {id_field} = %s AND input_code = %s
                UNION ALL
                SELECT s.* FROM {structure_table} s
                INNER JOIN tree t ON s.parent_id = t.id
            )
            SELECT * FROM tree ORDER BY input_code
        """, (entity_id, input_code))
    else:
        cursor.execute(f"SELECT * FROM {structure_table} WHERE {id_field} = %s ORDER BY input_code", (entity_id,))

    results = cursor.fetchall()
    conn.close()
    return jsonify(results)


# --- Dataset Input Form Submission ---
@app.route('/dataset_data_input_submit_form/<dataset_type>', methods=['POST'])
def dataset_data_input_submit_form(dataset_type):
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

    for key, values in form_data.items():
        value = values[0]
        if any(key.endswith(suffix) for suffix in ["_is_original", "_start_date", "_next_due_date", "_side_note"]):
            continue  # handled below
        input_code = key

        # Related metadata for uploads
        is_original = form_data.get(f"{input_code}_is_original", ["false"])[0] == "on"
        start_date = form_data.get(f"{input_code}_start_date", [None])[0]
        next_due_date = form_data.get(f"{input_code}_next_due_date", [None])[0]
        side_note = form_data.get(f"{input_code}_side_note", [""])[0]

        if structure_info.get(input_code):  # only for upload-enabled fields
            cursor.execute(f"""
                INSERT INTO {entry_table} 
                ({id_field}, input_code, value, is_original, start_date, next_due_date, side_note, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (entity_id, input_code, value, is_original, start_date, next_due_date, side_note, now))
        else:
            cursor.execute(f"""
                INSERT INTO {entry_table} ({id_field}, input_code, value, created_at)
                VALUES (%s, %s, %s, %s)
            """, (entity_id, input_code, value, now))

    conn.commit()
    conn.close()
    return jsonify({"message": "Data submitted successfully!"})


def backup_old_entries(dataset_type, entity_id, input_codes, conn):
    """Backup existing data into *_history table before overwriting."""
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
    """Automatically update is_complete if all uploads are filled."""
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


# --- Optional API for managing company_structure ---
@app.route('/company_structure_list/<int:group_id>')
def company_structure_list(group_id):
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


# -------------------------
# Compliance Sheet Assignments (Per Company)
# -------------------------

# Dynamic browser for both compliance and company data
@app.route('/company_template_browser/<dataset_type>/<int:company_id>')
def company_template_browser(dataset_type, company_id):
    if dataset_type not in ["compliance", "company_data"]:
        return "Invalid dataset type", 400
    return render_template("company_template_browser.html",
                           dataset_type=dataset_type,
                           company_id=company_id)


# Dynamic List
@app.route('/company_template_list/<dataset_type>/<int:company_id>')
def company_template_list(dataset_type, company_id):
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


# Dynamic Latest
@app.route('/company_template_latest/<dataset_type>/<int:company_id>')
def company_template_latest(dataset_type, company_id):
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


# Dynamic Export PDF
@app.route('/company_template_export_pdf/<dataset_type>/<int:company_id>/<int:mapping_id>')
def export_company_template_pdf(dataset_type, company_id, mapping_id):
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


# Dynamic Template Mapping (Company - Template)

@app.route('/company_template_mapping_browser/<int:company_id>')
def company_template_mapping_browser(company_id):
    return render_template("company_template_mapping_browser.html", company_id=company_id)


# List all template mappings (dynamic)
@app.route('/company_template_mapping_list/<int:company_id>')
def company_template_mapping_list(company_id):
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


# Assign new template mapping (company to data + compliance)
@app.route('/company_template_mapping_form', methods=['GET', 'POST'])
def company_template_mapping_form():
    company_id = request.args.get('company_id', type=int)
    if request.method == 'POST':
        compliance_sheet_id = request.form.get('compliance_sheet_id') or None
        company_data_id = request.form.get('company_data_id') or None
        year = request.form['year']
        link_description = request.form.get('link_description', '')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO 
            company_template_mapping (company_id, compliance_sheet_id, company_data_id, year, link_description)
            VALUES (%s, %s, %s, %s, %s)
        """, (company_id, compliance_sheet_id, company_data_id, year, link_description))
        conn.commit()
        conn.close()
        return jsonify({"message": "Mapping saved"}), 200

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
                           templates=templates)


@app.route('/dataset_template_browser.html')
def template_browser():
    dataset_type = request.args.get('dataset_type')
    if dataset_type not in ['compliance', 'company_data']:
        return "Invalid dataset type", 400
    return render_template("dataset_template_browser.html", dataset_type=dataset_type)


@app.route('/dataset_template_browse_data/<dataset_type>')
def dataset_template_browse_data(dataset_type):
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
@app.route('/dataset_template_form/<dataset_type>')
def dataset_template_form(dataset_type):
    if dataset_type not in ['company_data', 'compliance']:
        return "Invalid dataset type", 400
    return render_template('dataset_template_form.html', dataset_type=dataset_type)


# Unified save
@app.route('/dataset_template_save/<dataset_type>', methods=['POST'])
def dataset_template_save(dataset_type):
    conn = get_db_connection()
    cursor = conn.cursor()

    search_tag = request.form['search_tag']
    description = request.form['description']

    if dataset_type == 'company_data':
        cursor.execute("""
            INSERT INTO company_data_browse (company_data_search_tag, company_data_description)
            VALUES (%s, %s) RETURNING id
        """, (search_tag, description))
    elif dataset_type == 'compliance':
        cursor.execute("""
            INSERT INTO compliance_sheet_browse (sheet_search_tag, sheet_description)
            VALUES (%s, %s) RETURNING id
        """, (search_tag, description))
    else:
        conn.close()
        return jsonify({"error": "Invalid dataset type."}), 400

    new_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return jsonify({"id": new_id})


if __name__ == '__main__':
    app.run(debug=True)
