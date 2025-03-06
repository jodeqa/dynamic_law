-- Step 1: Create ENUM type for input_type
CREATE TYPE input_type_enum AS ENUM (
    'text/free', 
    'text/number', 
    'text/email', 
    'text/date', 
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
    FOREIGN KEY (parent_id) REFERENCES dataset_structure(id) ON DELETE CASCADE
);


-- Step 4: Create compliance_sheet_entries table
CREATE TABLE compliance_sheet_entries (
    id SERIAL PRIMARY KEY,
    sheet_id INT NOT NULL,
    input_code VARCHAR(50) NOT NULL,
    user_id INT NOT NULL,
    value TEXT, -- Store text, number, selected options
    file_path TEXT, -- Store uploaded file path
    created_at TIMESTAMP DEFAULT NOW()
);


-- Step 5: Create corporate_browse table
CREATE TABLE corporate_browse (
    id SERIAL PRIMARY KEY,
    corporate_name VARCHAR(50) NOT NULL,
    corporate_description TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);


-- Step 6: Create corporate_structure table
CREATE TABLE corporate_structure (
    id SERIAL PRIMARY KEY,
    corporate_id INT NOT NULL,
    input_code VARCHAR(50) NOT NULL,
    parent_id INT,  -- Parent ID for tree structure (NULL means root)
    is_header BOOLEAN NOT NULL DEFAULT FALSE,
    input_display TEXT NOT NULL,
    input_type VARCHAR(50),
    is_mandatory BOOLEAN DEFAULT FALSE,
    select_value TEXT, -- Stores 'option1, option2'
    is_upload BOOLEAN DEFAULT FALSE,
    sheet_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_corporate_input UNIQUE (corporate_id, input_code),
    CONSTRAINT fk_corporate_compliance FOREIGN KEY (sheet_id) REFERENCES compliance_sheet_browse(id) ON DELETE SET null,
    FOREIGN KEY (parent_id) REFERENCES corporate_structure(id) ON DELETE CASCADE
);


-- Step 7: Create corporate_entries table
CREATE TABLE corporate_entries (
    id SERIAL PRIMARY KEY,
    sheet_id INT NOT NULL,
    input_code VARCHAR(50) NOT NULL,
    user_id INT NOT NULL,
    value TEXT, -- Store text, number, selected options
    file_path TEXT, -- Store uploaded file path
    created_at TIMESTAMP DEFAULT NOW()
);
