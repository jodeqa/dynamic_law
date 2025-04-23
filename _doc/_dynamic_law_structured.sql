-- Step 1: Create ENUM type for input_type
CREATE TYPE input_type_enum AS ENUM (
    'text/free', 
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
    sheet_id INT NOT NULL,
    input_code VARCHAR(50) NOT NULL,
    user_id INT NOT NULL,
    value TEXT,
    file_path TEXT,
    is_original BOOLEAN DEFAULT FALSE,
    is_copy BOOLEAN DEFAULT FALSE,
    is_complete BOOLEAN DEFAULT FALSE,
    next_due_date DATE,
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
    created_at TIMEST
    AMP DEFAULT NOW()
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
    company_data_id INT NOT NULL REFERENCES company_data_browse(id),
    compliance_sheet_id INT REFERENCES compliance_sheet_browse(id),
    year SMALLINT NOT NULL,  -- enables multiple entries over time
    link_description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);



-- Step 10: Create company_data_entries
CREATE TABLE company_data_entries (
    id SERIAL PRIMARY KEY,
    company_id INT NOT NULL,
    input_code VARCHAR(50) NOT NULL,
    value TEXT,
    file_path TEXT,
    is_original BOOLEAN DEFAULT FALSE,
    is_copy BOOLEAN DEFAULT FALSE,
    is_complete BOOLEAN DEFAULT FALSE,
    next_due_date DATE,
    side_note TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);


-- Step 11: create View
SELECT company_id, COUNT(*) FILTER (WHERE value IS NOT NULL OR file_path IS NOT NULL) AS uploaded_count
FROM company_data_entries
GROUP BY company_id

