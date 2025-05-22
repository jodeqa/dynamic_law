SELECT MAX(id) FROM company_data_structure;
ALTER SEQUENCE company_data_structure_id_seq RESTART WITH 18;

SELECT MAX(id) FROM company_data_browse cdb ;
ALTER SEQUENCE company_data_browse_id_seq RESTART WITH 2;

SELECT MAX(id) FROM compliance_sheet_structure css;
ALTER SEQUENCE compliance_sheet_structure_id_seq RESTART WITH 18;

SELECT MAX(id) FROM compliance_sheet_browse csb;
ALTER SEQUENCE compliance_sheet_browse_seq RESTART WITH 2;