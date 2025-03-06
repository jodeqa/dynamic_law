from flask import Flask, request, jsonify, render_template
import psycopg2
from psycopg2.extras import RealDictCursor
import psycopg2.errors

app = Flask(__name__)

DATABASE = "dynamic_law"
USER = "postgres"
PASSWORD = "P@ssw0rd"
HOST = "localhost"

VALID_INPUT_TYPES = {
    "text/free", "text/number", "text/email", "text/date",
    "select/radio", "select/check", "select/drop"
}


#  Generic Function ===================================================================================================

def get_db_connection():
    return psycopg2.connect(
        database=DATABASE,
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=5432,
        cursor_factory=RealDictCursor)


def increment_last_segment(input_code):
    parts = input_code.split(".")  # Split by "."
    parts[-1] = str(int(parts[-1]) + 1)  # Increment the last segment
    return ".".join(parts)  # Join back into a string


#  Compliance Sheet ===================================================================================================

# Compliance Sheet Form -----------------------------------------------------------------------------------------------
@app.route('/compliance_sheet_form_browser/')
@app.route('/compliance_sheet_form_browser/<int:sheet_id>')
def compliance_sheet_form_browser(sheet_id=1001):  # Default to 1001 if no sheet_id is provided
    return render_template("compliance_sheet_form_browser.html", sheet_id=sheet_id)


@app.route('/compliance_sheet_form_tree/<int:sheet_id>', methods=['GET'])
def compliance_sheet_form_tree(sheet_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Recursive Common Table Expression (CTE) to fetch hierarchy
    query = """
    WITH RECURSIVE dataset_tree AS (
        SELECT id, sheet_id, input_code, parent_id, is_header, input_display, input_type, 
        is_mandatory, select_value, is_upload
        FROM compliance_sheet_structure
        WHERE sheet_id = %s AND parent_id IS NULL  -- Fetch only top-level parents

        UNION ALL

        SELECT d.id, d.sheet_id, d.input_code, d.parent_id, d.is_header, d.input_display, d.input_type, 
        d.is_mandatory, d.select_value, d.is_upload
        FROM compliance_sheet_structure d
        INNER JOIN dataset_tree dt ON d.parent_id = dt.id  -- Recursive relation
    )
    SELECT * FROM dataset_tree ORDER BY input_code;
    """

    cursor.execute(query, (sheet_id,))
    dataset = cursor.fetchall()
    conn.close()

    return jsonify(dataset)


# @app.route('/dataset/<int:sheet_id>', methods=['GET'])
# def get_dataset(sheet_id):
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute("SELECT * FROM compliance_sheet_structure WHERE sheet_id = %s ORDER BY input_code", (sheet_id,))
#     dataset = cursor.fetchall()
#     conn.close()
#
#     dataset_json = [{"input_code": row[2], "input_display": row[3], "input_type": row[4], "is_mandatory": row[5],
#                      "select_value": row[6], "is_upload": row[7]} for row in dataset]
#
#     return jsonify(dataset_json)


@app.route('/compliance_sheet_form_add_and_edit.html')
def compliance_sheet_form_add_and_edit():
    return render_template('compliance_sheet_form_add_and_edit.html')  # Ensure file is in 'templates/' folder


@app.route('/compliance_sheet_form_get_parent_sibling_info/<int:parent_id>/<int:sheet_id>', methods=['GET'])
def compliance_sheet_form_get_parent_sibling_info(parent_id, sheet_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if parent_id is NULL (Level 1)
    if parent_id == 0:
        # Get last input_code of Level 1 (same sheet_id, parent_id IS NULL)
        cursor.execute(
            "SELECT input_code FROM compliance_sheet_structure WHERE sheet_id = %s AND parent_id IS NULL "
            "ORDER BY input_code DESC LIMIT 1",
            (sheet_id,)
        )
        last_sibling = cursor.fetchone()

        next_code = str(int(last_sibling['input_code']) + 1) if last_sibling else "1"
        return jsonify({
            "parent_display": "Root",
            "last_sibling_code": last_sibling['input_code'] if last_sibling else None,
            "next_input_code": next_code
        })

    # If parent_id is NOT NULL (Adding a child)
    else:
        # Get Parent Display Name
        cursor.execute("SELECT input_display FROM compliance_sheet_structure WHERE id = %s", (parent_id,))
        parent = cursor.fetchone()

        # Get Last Input Code of Siblings (Same Parent, Same Sheet ID)
        cursor.execute(
            "SELECT input_code FROM compliance_sheet_structure WHERE parent_id = %s AND sheet_id = %s "
            "ORDER BY input_code DESC LIMIT 1",
            (parent_id, sheet_id)
        )
        last_sibling = cursor.fetchone()

        # Calculate Next Input Code (Child Level)
        if last_sibling:
            next_code = increment_last_segment(last_sibling['input_code'])
        else:
            cursor.execute(
                "SELECT input_code FROM compliance_sheet_structure WHERE id = %s AND sheet_id = %s "
                "ORDER BY input_code DESC LIMIT 1",
                (parent_id, sheet_id)
            )
            last_sibling = cursor.fetchone()
            next_code = last_sibling['input_code'] + ".1"

        conn.close()

        return jsonify({
            "parent_display": parent['input_display'] if parent else None,
            "last_sibling_code": last_sibling['input_code'] if last_sibling else None,
            "next_input_code": next_code
        })


@app.route('/compliance_sheet_form_get_field/<int:field_id>', methods=['GET'])
def compliance_sheet_form_get_field(field_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM compliance_sheet_structure WHERE id = %s", (field_id,))
    field = cursor.fetchone()
    conn.close()

    if not field:
        return jsonify({"error": f"Field with id {field_id} not found"}), 404  # Handle missing data

    if field:
        return jsonify({
            "id": field["id"],  # Access by column name, NOT index
            "sheet_id": field["sheet_id"],
            "input_code": field["input_code"],
            "parent_id": field["parent_id"],
            "is_header": field["is_header"],
            "input_display": field["input_display"],
            "input_type": field["input_type"],
            "is_mandatory": field["is_mandatory"],
            "select_value": field["select_value"],
            "is_upload": field["is_upload"]
        })
    else:
        return jsonify({"error": "Field not found"}), 404


@app.route('/compliance_sheet_form_add_field', methods=['POST'])
def compliance_sheet_form_add_field():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if input_type is valid
    if data['input_type'] not in VALID_INPUT_TYPES:
        return jsonify({"error": f"Invalid input_type. Allowed values: {', '.join(VALID_INPUT_TYPES)}"}), 400

    try:
        cursor.execute(
            "INSERT INTO compliance_sheet_structure (sheet_id, input_code, parent_id, is_header, "
            "input_display, input_type, is_mandatory, select_value, is_upload) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (data['sheet_id'], data['input_code'], data['parent_id'], data['is_header'], data['input_display'],
             data['input_type'], data['is_mandatory'], data.get('select_value'), data['is_upload'])
        )
        conn.commit()
        new_id = cursor.fetchone()[0]
        return jsonify({"message": "Field added successfully!", "id": new_id}), 201

    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return jsonify({"error": "Duplicate sheet_id and input_code detected!"}), 400

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        conn.close()


@app.route('/compliance_sheet_form_edit_field/<int:field_id>', methods=['PUT'])
def compliance_sheet_form_edit_field(field_id):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "UPDATE compliance_sheet_structure SET sheet_id=%s, input_code=%s, is_header=%s, "
            "input_display=%s, input_type=%s, "
            "is_mandatory=%s, select_value=%s, is_upload=%s WHERE id=%s",
            (data['sheet_id'], data['input_code'], data['is_header'], data['input_display'], data['input_type'],
             data['is_mandatory'], data.get('select_value'), data['is_upload'], field_id)
        )
        conn.commit()
        return jsonify({"message": "Field updated successfully!"})

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        conn.close()


@app.route('/compliance_sheet_form_delete_field/<int:field_id>', methods=['DELETE'])
def compliance_sheet_form_delete_field(field_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM compliance_sheet_structure WHERE id = %s", (field_id,))
        conn.commit()
        return jsonify({"message": "Field deleted successfully!"})

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        conn.close()


# Compliance Sheet Data -----------------------------------------------------------------------------------------------
@app.route('/compliance_sheet_data_input/<int:sheet_id>', methods=['GET'])
@app.route('/compliance_sheet_data_input/<int:sheet_id>/<string:input_code>', methods=['GET'])
def compliance_sheet_data_input(sheet_id, input_code=None):
    return render_template("compliance_sheet_data_input.html", sheet_id=sheet_id, input_code=input_code)


@app.route('/compliance_sheet_data_input_get_dataset_structure/<int:sheet_id>', methods=['GET'])
@app.route('/compliance_sheet_data_input_get_dataset_structure/<int:sheet_id>/<string:input_code>', methods=['GET'])
def compliance_sheet_data_input_get_dataset_structure(sheet_id, input_code=None):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    if input_code:
        # Fetch only the requested section
        cursor.execute("""
            WITH RECURSIVE dataset_tree AS (
                SELECT * FROM compliance_sheet_structure WHERE sheet_id = %s AND input_code = %s
                UNION ALL
                SELECT ds.* FROM compliance_sheet_structure ds
                INNER JOIN dataset_tree dt ON ds.parent_id = dt.id
            )
            SELECT * FROM dataset_tree ORDER BY input_code ASC
        """, (sheet_id, input_code))
    else:
        # Fetch the entire dataset
        cursor.execute("""
            SELECT * FROM compliance_sheet_structure WHERE sheet_id = %s ORDER BY input_code ASC
        """, (sheet_id,))

    dataset = cursor.fetchall()
    conn.close()
    return jsonify(dataset)


@app.route('/compliance_sheet_data_input_submit_form', methods=['POST'])
def compliance_sheet_data_input_submit_form():
    form_data = request.form.to_dict(flat=False)  # Get form data
    sheet_id = request.args.get('sheet_id')  # Pass sheet_id from request URL (optional)

    conn = get_db_connection()
    cursor = conn.cursor()

    for input_code, values in form_data.items():
        value = values[0]  # Extract first value (for text inputs)
        cursor.execute("""
            INSERT INTO compliance_sheet_entries (sheet_id, input_code, input_value)
            VALUES (%s, %s, %s)
        """, (sheet_id, input_code, value))

    conn.commit()
    conn.close()

    return jsonify({"message": "Data submitted successfully!"})


#  dataset Data =====================================================================================================

# dataset form ------------------------------------------------------------------------------------------------------
@app.route('/dataset_form_browser/<string:dataset_type>')
@app.route('/dataset_form_browser/<string:dataset_type>/<int:sheet_id>')
def dataset_form_browser(dataset_type, sheet_id=1001):  # Default to 1001 if no sheet_id is provided
    return render_template("dataset_form_browser.html", dataset_type=dataset_type, sheet_id=sheet_id)


@app.route('/dataset_form_tree/<string:dataset_type>/<int:sheet_id>', methods=['GET'])
def dataset_form_tree(dataset_type, sheet_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    table_name = "compliance_sheet_structure" if dataset_type == "compliance" else "corporate_structure"
    table_where = "sheet_id" if dataset_type == "compliance" else "corporate_id"

    # Recursive Common Table Expression (CTE) to fetch hierarchy
    query = f"""
    WITH RECURSIVE dataset_tree AS (
        SELECT id, {table_where}, input_code, parent_id, is_header, input_display, input_type, 
        is_mandatory, select_value, is_upload
        FROM {table_name}
        WHERE {table_where} = %s AND parent_id IS NULL  -- Fetch only top-level parents

        UNION ALL

        SELECT d.id, d.{table_where}, d.input_code, d.parent_id, d.is_header, d.input_display, d.input_type, 
        d.is_mandatory, d.select_value, d.is_upload
        FROM {table_name} d
        INNER JOIN dataset_tree dt ON d.parent_id = dt.id  -- Recursive relation
    )
    SELECT * FROM dataset_tree ORDER BY input_code;
    """

    cursor.execute(query, (sheet_id,))
    dataset = cursor.fetchall()
    conn.close()

    return jsonify(dataset)


@app.route('/dataset_form_add_and_edit.html')
def dataset_form_add_and_edit():
    return render_template('dataset_form_add_and_edit.html')  # Ensure file is in 'templates/' folder


@app.route('/dataset_form_get_parent_sibling_info/<string:dataset_type>/<int:parent_id>/<int:sheet_id>', methods=['GET'])
def dataset_form_get_parent_sibling_info(dataset_type, parent_id, sheet_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    table_name = "compliance_sheet_structure" if dataset_type == "compliance" else "corporate_structure"
    table_where = "sheet_id" if dataset_type == "compliance" else "corporate_id"

    # Check if parent_id is NULL (Level 1)
    if parent_id == 0:
        # Get last input_code of Level 1 (same sheet_id, parent_id IS NULL)
        cursor.execute(
            f"SELECT input_code FROM {table_name} WHERE {table_where} = %s AND parent_id IS NULL "
            "ORDER BY input_code DESC LIMIT 1",
            (sheet_id,)
        )
        last_sibling = cursor.fetchone()

        next_code = str(int(last_sibling['input_code']) + 1) if last_sibling else "1"
        return jsonify({
            "parent_display": "Root",
            "last_sibling_code": last_sibling['input_code'] if last_sibling else None,
            "next_input_code": next_code
        })

    # If parent_id is NOT NULL (Adding a child)
    else:
        # Get Parent Display Name
        cursor.execute(f"SELECT input_display FROM {table_name} WHERE id = %s", (parent_id,))
        parent = cursor.fetchone()

        # Get Last Input Code of Siblings (Same Parent, Same Sheet ID)
        cursor.execute(
            f"SELECT input_code FROM {table_name} WHERE parent_id = %s AND {table_where} = %s "
            "ORDER BY input_code DESC LIMIT 1",
            (parent_id, sheet_id)
        )
        last_sibling = cursor.fetchone()

        # Calculate Next Input Code (Child Level)
        if last_sibling:
            next_code = increment_last_segment(last_sibling['input_code'])
        else:
            cursor.execute(
                f"SELECT input_code FROM {table_name} WHERE id = %s AND {table_where} = %s "
                "ORDER BY input_code DESC LIMIT 1",
                (parent_id, sheet_id)
            )
            last_sibling = cursor.fetchone()
            next_code = last_sibling['input_code'] + ".1"

        conn.close()

        return jsonify({
            "parent_display": parent['input_display'] if parent else None,
            "last_sibling_code": last_sibling['input_code'] if last_sibling else None,
            "next_input_code": next_code
        })


@app.route('/dataset_form_get_field/<string:dataset_type>/<int:field_id>', methods=['GET'])
def dataset_form_get_field(dataset_type, field_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    table_name = "compliance_sheet_structure" if dataset_type == "compliance" else "corporate_structure"

    cursor.execute(f"SELECT * FROM {table_name} WHERE id = %s", (field_id,))
    field = cursor.fetchone()
    conn.close()

    if not field:
        return jsonify({"error": f"Field with id {field_id} not found"}), 404  # Handle missing data

    if field:
        return jsonify({
            "id": field["id"],  # Access by column name, NOT index
            "sheet_id": field["sheet_id"],
            "input_code": field["input_code"],
            "parent_id": field["parent_id"],
            "is_header": field["is_header"],
            "input_display": field["input_display"],
            "input_type": field["input_type"],
            "is_mandatory": field["is_mandatory"],
            "select_value": field["select_value"],
            "is_upload": field["is_upload"]
        })
    else:
        return jsonify({"error": "Field not found"}), 404


@app.route('/dataset_form_add_field/<string:dataset_type>', methods=['POST'])
def dataset_form_add_field(dataset_type):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()

    table_name = "compliance_sheet_structure" if dataset_type == "compliance" else "corporate_structure"
    table_where = "sheet_id" if dataset_type == "compliance" else "corporate_id"

    # Check if input_type is valid
    if data['input_type'] not in VALID_INPUT_TYPES:
        return jsonify({"error": f"Invalid input_type. Allowed values: {', '.join(VALID_INPUT_TYPES)}"}), 400

    try:
        cursor.execute(
            f"INSERT INTO {table_name} ({table_where}, input_code, parent_id, is_header, "
            "input_display, input_type, is_mandatory, select_value, is_upload) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (data[table_where], data['input_code'], data['parent_id'], data['is_header'], data['input_display'],
             data['input_type'], data['is_mandatory'], data.get('select_value'), data['is_upload'])
        )
        conn.commit()
        new_id = cursor.fetchone()[0]
        return jsonify({"message": "Field added successfully!", "id": new_id}), 201

    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return jsonify({"error": "Duplicate sheet_id and input_code detected!"}), 400

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        conn.close()


@app.route('/dataset_form_edit_field/<string:dataset_type>/<int:field_id>', methods=['PUT'])
def dataset_form_edit_field(dataset_type, field_id):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()

    table_name = "compliance_sheet_structure" if dataset_type == "compliance" else "corporate_structure"
    table_where = "sheet_id" if dataset_type == "compliance" else "corporate_id"

    try:
        cursor.execute(
            f"UPDATE {table_name} SET {table_where}=%s, input_code=%s, is_header=%s, "
            "input_display=%s, input_type=%s, "
            "is_mandatory=%s, select_value=%s, is_upload=%s WHERE id=%s",
            (data[table_where], data['input_code'], data['is_header'], data['input_display'], data['input_type'],
             data['is_mandatory'], data.get('select_value'), data['is_upload'], field_id)
        )
        conn.commit()
        return jsonify({"message": "Field updated successfully!"})

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        conn.close()


@app.route('/dataset_form_delete_field/<string:dataset_type>/<int:field_id>', methods=['DELETE'])
def dataset_form_delete_field(dataset_type, field_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    table_name = "compliance_sheet_structure" if dataset_type == "compliance" else "corporate_structure"

    try:
        cursor.execute(f"DELETE FROM {table_name} WHERE id = %s", (field_id,))
        conn.commit()
        return jsonify({"message": "Field deleted successfully!"})

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        conn.close()


# dataset Sheet Data -----------------------------------------------------------------------------------------------
@app.route('/dataset_data_input/<string:dataset_type>/<int:sheet_id>', methods=['GET'])
@app.route('/dataset_data_input/<string:dataset_type>/<int:sheet_id>/<string:input_code>', methods=['GET'])
def dataset_data_input(dataset_type, sheet_id, input_code=None):
    return render_template("dataset_data_input.html",
                           dataset_type=dataset_type, sheet_id=sheet_id, input_code=input_code)


@app.route('/dataset_data_input_get_dataset_structure/<string:dataset_type>/<int:the_id>', methods=['GET'])
@app.route('/dataset_data_input_get_dataset_structure/<string:dataset_type>/<int:the_id>/<string:input_code>', methods=['GET'])
def dataset_data_input_get_dataset_structure(dataset_type, the_id, input_code=None):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    table_name = "compliance_sheet_structure" if dataset_type == "compliance" else "corporate_structure"
    table_where = "sheet_id" if dataset_type == "compliance" else "corporate_id"

    if input_code:
        # Fetch only the requested section
        cursor.execute(f"""
            WITH RECURSIVE dataset_tree AS (
                SELECT * FROM {table_name} WHERE {table_where} = %s AND input_code = %s
                UNION ALL
                SELECT ds.* FROM {table_name} ds
                INNER JOIN dataset_tree dt ON ds.parent_id = dt.id
            )
            SELECT * FROM dataset_tree ORDER BY input_code ASC
        """, (the_id, input_code))
    else:
        # Fetch the entire dataset
        cursor.execute(f"""
            SELECT * FROM {table_name} WHERE {table_where} = %s ORDER BY input_code ASC
        """, ({table_where},))

    dataset = cursor.fetchall()
    conn.close()
    return jsonify(dataset)


@app.route('/dataset_data_input_submit_form/<string:dataset_type>', methods=['POST'])
def dataset_data_input_submit_form(dataset_type):
    form_data = request.form.to_dict(flat=False)  # Get form data
    the_id = request.args.get('the_id')  # Pass sheet_id from request URL (optional)

    conn = get_db_connection()
    cursor = conn.cursor()

    table_name = "compliance_sheet_structure" if dataset_type == "compliance" else "corporate_structure"
    table_where = "sheet_id" if dataset_type == "compliance" else "corporate_id"

    for input_code, values in form_data.items():
        value = values[0]  # Extract first value (for text inputs)
        cursor.execute(f"""
            INSERT INTO {table_name} ({table_where}, input_code, input_value)
            VALUES (%s, %s, %s)
        """, (the_id, input_code, value))

    conn.commit()
    conn.close()

    return jsonify({"message": "Data submitted successfully!"})

#  Main Application ===================================================================================================


if __name__ == '__main__':
    app.run(debug=True)
