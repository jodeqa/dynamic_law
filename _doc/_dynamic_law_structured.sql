SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'dynamic_law' AND pid <> pg_backend_pid();

-- Step 1: Create ENUM type for input_type
CREATE TYPE input_type_enum AS ENUM (
    'text/free',
    'text/multiple',
    'text/matrix2',
    'text/number', 
    'text/email', 
    'text/date', 
    'text/links', 
    'select/radio', 
    'select/check', 
    'select/drop'
);


-- Step 2: Create compliance_sheet_browse table
CREATE TABLE compliance_sheet_browse (
    id SERIAL PRIMARY KEY,
    sheet_search_tag VARCHAR(50) NOT NULL,
    sheet_description TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);


-- Step 3: Create compliance_sheet_structure table
CREATE TABLE compliance_sheet_structure (
    id SERIAL PRIMARY KEY,
    sheet_id INT NOT NULL,
    input_code VARCHAR(50) NOT NULL,
    parent_id INT,  -- Parent ID for tree structure (NULL means root)
    is_header BOOLEAN NOT NULL DEFAULT FALSE,
    input_display TEXT NOT NULL,
    input_type VARCHAR(50),
    is_mandatory BOOLEAN DEFAULT FALSE,
    select_value TEXT, -- Stores 'option1, option2'
    is_upload BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_sheet_input UNIQUE (sheet_id, input_code),
    FOREIGN KEY (parent_id) REFERENCES compliance_sheet_structure(id) ON DELETE CASCADE
);


-- Step 4: Create compliance_sheet_entries table
CREATE TABLE compliance_sheet_entries (
    id SERIAL PRIMARY KEY,
    company_id INT,
    sheet_id INT NOT NULL,
    input_code VARCHAR(50) NOT NULL,
    user_id INT NOT NULL,
    value TEXT,
    file_path TEXT,
    is_original BOOLEAN DEFAULT FALSE,
    is_complete BOOLEAN DEFAULT FALSE,
    start_date DATE,
    next_due_date DATE,
    upload_date DATE,
    side_note TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);


-- step 5: Create corporate_group table
CREATE TABLE corporate_group (
    id SERIAL PRIMARY KEY,
    group_name VARCHAR(100) NOT NULL,
    group_description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);


-- Step 6: Create company_structure table
CREATE TABLE company_structure (
    id SERIAL PRIMARY KEY,
    group_id INT NOT NULL REFERENCES corporate_group(id),
    company_name TEXT NOT NULL,
    input_code VARCHAR(50) NOT NULL,  -- COA-style tree code
    parent_id INT REFERENCES company_structure(id) ON DELETE CASCADE,
    next_inspection_date DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_company_tree UNIQUE (group_id, input_code)
);


-- Step 7: Create company_data_structure table
CREATE TABLE company_data_browse (
    id SERIAL PRIMARY KEY,
    company_data_search_tag VARCHAR(50) NOT NULL,
    company_data_description TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);


-- Step 8: Create company_data_structure table
CREATE TABLE company_data_structure (
    id SERIAL PRIMARY KEY,
    company_data_id INT NOT NULL,
    input_code VARCHAR(50) NOT NULL,
    parent_id INT,
    is_header BOOLEAN NOT NULL DEFAULT FALSE,
    input_display TEXT NOT NULL,
    input_type VARCHAR(50),
    is_mandatory BOOLEAN DEFAULT FALSE,
    select_value TEXT,
    is_upload BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_company_data_input UNIQUE (company_data_id, input_code),
    FOREIGN KEY (parent_id) REFERENCES company_data_structure(id) ON DELETE CASCADE
);



-- Step 9: Create company_template_mapping table
CREATE TABLE company_template_mapping (
    id SERIAL PRIMARY KEY,
    company_id INT NOT NULL REFERENCES company_structure(id),
    company_data_id INT NULL REFERENCES company_data_browse(id),
    compliance_sheet_id INT REFERENCES compliance_sheet_browse(id),
    year SMALLINT NOT NULL,  -- enables multiple entries over time
    link_description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);


-- Step 10: Create company_data_entries
CREATE TABLE company_template_mapping_history (
    id SERIAL PRIMARY KEY,
    company_id INT NOT NULL,
    company_data_id INT,
    compliance_sheet_id INT,
    year SMALLINT,
    link_description TEXT,
    action_type VARCHAR(10) DEFAULT 'UPDATE', -- UPDATE/DELETE
    action_time TIMESTAMP DEFAULT NOW()
);


-- Step 11: Create company_data_entries
CREATE TABLE company_data_entries (
    id SERIAL PRIMARY KEY,
    company_id INT,
    company_data_id INT NOT NULL,
    input_code VARCHAR(50) NOT NULL,
    value TEXT,
    file_path TEXT,
    is_original BOOLEAN DEFAULT FALSE,
    is_complete BOOLEAN DEFAULT FALSE,
    start_date DATE,
    next_due_date DATE,
    upload_date DATE,
    side_note TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);


-- Step 12:
CREATE TABLE compliance_sheet_entries_history (
    id SERIAL PRIMARY KEY,
    sheet_id INT NOT NULL,
    company_id INT NOT NULL,
    input_code VARCHAR(50) NOT NULL,
    value TEXT,
    file_path TEXT,
    is_original BOOLEAN,
    start_date DATE,
    next_due_date DATE,
    upload_date DATE,
    side_note TEXT,
    action_type VARCHAR(10) DEFAULT 'UPDATE', -- UPDATE/DELETE
    action_time TIMESTAMP DEFAULT NOW()
);


-- Step 13:
CREATE TABLE company_data_entries_history (
    id SERIAL PRIMARY KEY,
    company_data_id INT NOT NULL,
    company_id INT NOT NULL,
    input_code VARCHAR(50) NOT NULL,
    value TEXT,
    file_path TEXT,
    is_original BOOLEAN,
    start_date DATE,
    next_due_date DATE,
    upload_date DATE,
    side_note TEXT,
    action_type VARCHAR(10) DEFAULT 'UPDATE',
    action_time TIMESTAMP DEFAULT NOW()
);



-- 14 sub template browse
CREATE TABLE sub_template_browse (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  description TEXT,
  created_at TIMESTAMP DEFAULT now()
);


-- 15 sub template structure
CREATE TABLE sub_template_structure (
  id SERIAL PRIMARY KEY,
  sub_template_id INT NOT NULL REFERENCES sub_template_browse(id) ON DELETE CASCADE,
  input_code VARCHAR(20) NOT NULL,
  parent_id INT, -- self-reference to another sub_template_structure.id
  is_header BOOLEAN DEFAULT FALSE,
  input_display TEXT NOT NULL,
  input_type VARCHAR(50),
  is_mandatory BOOLEAN DEFAULT FALSE,
  select_value TEXT,
  is_upload BOOLEAN DEFAULT FALSE,
  sort_order INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT now()
);


--16
CREATE TABLE sub_template_usage_log (
  id SERIAL PRIMARY KEY,
  sub_template_id INT REFERENCES sub_template_browse(id),
  used_in VARCHAR(20), -- e.g., 'company_data' or 'compliance'
  target_id INT,       -- company_data_id or compliance_sheet_id
  used_at TIMESTAMP DEFAULT now()
);



SELECT company_id, COUNT(*) FILTER (WHERE value IS NOT NULL OR file_path IS NOT NULL) AS uploaded_count
FROM company_data_entries
GROUP BY company_id

