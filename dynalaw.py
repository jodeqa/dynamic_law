from flask import Flask, render_template, request, jsonify, redirect, send_file
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

dataset_entries_tables = {
    "compliance": "compliance_sheet_entries",
    "corporate": "corporate_entries",
    "company_data": "company_data_entries"
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
@app.route('/delete_field/<int:field_id>', methods=['DELETE'])
def delete_field(field_id):
    # Generic delete from any structure table based on ID (assuming unique across all)
    conn = get_db_connection()
    cursor = conn.cursor()
    for table in dataset_structure_tables.values():
        cursor.execute(f"DELETE FROM {table} WHERE id = %s", (field_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Field deleted successfully."})


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
        if any(key.endswith(suffix) for suffix in ["_is_original", "_is_copy", "_next_due_date", "_side_note"]):
            continue  # handled below
        input_code = key

        # Related metadata for uploads
        is_original = form_data.get(f"{input_code}_is_original", ["false"])[0] == "on"
        is_copy = form_data.get(f"{input_code}_is_copy", ["false"])[0] == "on"
        next_due_date = form_data.get(f"{input_code}_next_due_date", [None])[0]
        side_note = form_data.get(f"{input_code}_side_note", [""])[0]

        if structure_info.get(input_code):  # only for upload-enabled fields
            cursor.execute(f"""
                INSERT INTO {entry_table} 
                ({id_field}, input_code, value, is_original, is_copy, next_due_date, side_note, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (entity_id, input_code, value, is_original, is_copy, next_due_date, side_note, now))
        else:
            cursor.execute(f"""
                INSERT INTO {entry_table} ({id_field}, input_code, value, created_at)
                VALUES (%s, %s, %s, %s)
            """, (entity_id, input_code, value, now))

    conn.commit()
    conn.close()
    return jsonify({"message": "Data submitted successfully!"})


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

@app.route('/company_compliance_browser/<int:company_id>')
def company_compliance_browser(company_id):
    return render_template("company_compliance_browser.html", company_id=company_id)


# List all compliance assignments for a company
@app.route('/company_compliance_list/<int:company_id>')
def company_compliance_list(company_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("""
        SELECT mapping.id, 
               b.sheet_description, 
               b.sheet_search_tag, 
               mapping.year, 
               mapping.created_at
        FROM company_template_mapping mapping
        JOIN compliance_sheet_browse b ON mapping.compliance_sheet_id = b.id
        WHERE mapping.company_id = %s
        ORDER BY mapping.year DESC, mapping.created_at DESC
    """, (company_id,))
    result = cursor.fetchall()
    conn.close()
    return jsonify({"data": result})  # ⚠️ THIS IS IMPORTANT FOR DATATABLES


@app.route('/company_compliance_assign/<int:company_id>', methods=['POST'])
def company_compliance_assign(company_id):
    year = int(request.form.get("year"))
    sheet_id = int(request.form.get("compliance_sheet_id"))

    conn = get_db_connection()
    cur = conn.cursor()

    # Mark previous assignments as read-only for the same year
    cur.execute("""
        UPDATE company_template_mapping SET is_active = FALSE
        WHERE company_id = %s AND year = %s
    """, (company_id, year))

    # Insert new active assignment
    cur.execute("""
        INSERT INTO company_template_mapping (company_id, compliance_sheet_id, year, is_active, created_at)
        VALUES (%s, %s, %s, TRUE, NOW())
    """, (company_id, sheet_id, year))
    conn.close()
    return redirect(f"/company_compliance_browser/{company_id}")


# Get latest active assignment
@app.route('/company_compliance_latest/<int:company_id>')
def company_compliance_latest(company_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("""
        SELECT mapping.compliance_sheet_id AS sheet_id
        FROM company_template_mapping mapping
        WHERE mapping.company_id = %s
        ORDER BY mapping.year DESC, mapping.created_at DESC
        LIMIT 1
    """, (company_id,))
    result = cursor.fetchone()
    conn.close()
    return jsonify(result or {})  # Return empty object if None


# Export to PDF
@app.route('/company_compliance_pdf/<int:company_id>/<int:mapping_id>')
def export_compliance_pdf(company_id, mapping_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

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

    data = cursor.fetchall()
    conn.close()

    html = render_template("pdf_compliance_export.html", fields=data)
    config = pdfkit.configuration(wkhtmltopdf=r"C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
    pdf = pdfkit.from_string(html, False, configuration=config)

    return send_file(io.BytesIO(pdf), as_attachment=True,
                     download_name="compliance_export.pdf", mimetype='application/pdf')


# @app.route('/company_template_mapping_data/<int:company_id>')
# def company_template_mapping_data(company_id):
#     conn = get_db_connection()
#     cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
#     cursor.execute("""
#         SELECT
#             m.year,
#             m.link_description,
#             m.created_at,
#             cs.sheet_description AS compliance_sheet_description,
#             cd.company_data_description
#         FROM company_template_mapping m
#         LEFT JOIN compliance_sheet_browse cs ON m.compliance_sheet_id = cs.id
#         LEFT JOIN company_data_browse cd ON m.company_data_id = cd.id
#         WHERE m.company_id = %s
#         ORDER BY m.year DESC
#     """, (company_id,))
#     data = cursor.fetchall()
#     conn.close()
#     return jsonify({"data": data})
#
#
@app.route('/company_template_mapping_form', methods=['GET', 'POST'])
def company_template_mapping_form():
    company_id = request.args.get('company_id', type=int)
    if request.method == 'POST':
        compliance_sheet_id = request.form['compliance_sheet_id']
        company_data_id = request.form['company_data_id']
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


@app.route('/company_data_browse_data')
def company_data_browse_data():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT id, company_data_search_tag, company_data_description, created_at "
                   "FROM company_data_browse "
                   "ORDER BY created_at DESC")
    results = cursor.fetchall()
    conn.close()
    return jsonify({"data": results})


@app.route('/compliance_sheet_browse_data')
def compliance_sheet_browse_data():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT id, sheet_search_tag, sheet_description, created_at "
                   "FROM compliance_sheet_browse "
                   "ORDER BY created_at DESC")
    results = cursor.fetchall()
    conn.close()
    return jsonify({"data": results})


@app.route('/add_company_data_template')
def add_company_data_template():
    return render_template("company_data_template_form.html")


@app.route('/add_compliance_sheet_template')
def add_compliance_sheet_template():
    return render_template("compliance_sheet_template_form.html")


if __name__ == '__main__':
    app.run(debug=True)
