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

-- Step 2: Create dataset_structure table
CREATE TABLE dataset_structure (
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


-- Step 3: Create dataset_entries table
CREATE TABLE dataset_entries (
    id SERIAL PRIMARY KEY,
    sheet_id INT NOT NULL,
    input_code VARCHAR(50) NOT NULL,
    user_id INT NOT NULL,
    value TEXT, -- Store text, number, selected options
    file_path TEXT, -- Store uploaded file path
    created_at TIMESTAMP DEFAULT NOW()
);
