SELECT mapping.id, b.sheet_description, b.sheet_search_tag, mapping.year, mapping.created_at
FROM company_template_mapping mapping
JOIN compliance_sheet_browse b ON mapping.compliance_sheet_id = b.id
WHERE mapping.company_id = 2
ORDER BY mapping.year DESC, mapping.created_at DESC

SELECT * FROM company_template_mapping
WHERE company_id = 2
ORDER BY year DESC, created_at DESC
LIMIT 1

SELECT s.input_code, s.input_display, s.input_type, s.is_header, s.is_upload,
       e.value, e.file_path
FROM compliance_sheet_entries e
JOIN compliance_sheet_structure s
  ON s.input_code = e.input_code AND s.sheet_id = e.sheet_id
JOIN company_template_mapping m ON m.compliance_sheet_id = s.sheet_id
WHERE m.id = 1 AND e.company_id = 2
ORDER BY s.input_code
        
        SELECT mapping.compliance_sheet_id AS sheet_id
        FROM company_template_mapping mapping
        WHERE mapping.company_id = 2
        ORDER BY mapping.year DESC, mapping.created_at DESC
        LIMIT 1
        
ALTER TABLE company_data_structure
    ADD CONSTRAINT company_data_structure_parent_id_fkey FOREIGN KEY (company_data_id) REFERENCES company_data_structure(id);

ALTER TABLE company_template_mapping
ADD COLUMN year SMALLINT NOT NULL DEFAULT EXTRACT(YEAR FROM CURRENT_DATE),
ADD COLUMN link_description TEXT;



-- Repeat for corporate_entries and company_data_entries as needed.
INSERT INTO public.company_structure
(id, group_id, company_name, input_code, parent_id, next_inpection_date, created_at)
VALUES(nextval('company_structure_id_seq'::regclass), 1, 'PT Famon Awal Bros Sedaya Tbk', '1', null, '2026-4-12', now());
INSERT INTO public.company_structure
(id, group_id, company_name, input_code, parent_id, next_inpection_date, created_at)
VALUES(nextval('company_structure_id_seq'::regclass), 1, 'Awal Bros Group', '1.1', 1, '2026-4-12', now());
INSERT INTO public.company_structure
(id, group_id, company_name, input_code, parent_id, next_inpection_date, created_at)
VALUES(nextval('company_structure_id_seq'::regclass), 1, 'Primaya Group', '1.2', 1, '2026-4-12', now());
INSERT INTO public.company_structure
(id, group_id, company_name, input_code, parent_id, next_inpection_date, created_at)
VALUES(nextval('company_structure_id_seq'::regclass), 1, 'RS Awal Bros Pekanbaru', '1.1.1', 2, '2026-4-12', now());
INSERT INTO public.company_structure
(id, group_id, company_name, input_code, parent_id, next_inpection_date, created_at)
VALUES(nextval('company_structure_id_seq'::regclass), 1, 'RS Awal Bros Ujung Batu', '1.1.2', 2, '2026-4-12', now());
INSERT INTO public.company_structure
(id, group_id, company_name, input_code, parent_id, next_inpection_date, created_at)
VALUES(nextval('company_structure_id_seq'::regclass), 1, 'RS Awal Bros Panam', '1.1.3', 2, '2026-4-12', now());
INSERT INTO public.company_structure
(id, group_id, company_name, input_code, parent_id, next_inpection_date, created_at)
VALUES(nextval('company_structure_id_seq'::regclass), 1, 'RS Awal Bros A.Yani', '1.1.4', 2, '2026-4-12', now());
INSERT INTO public.company_structure
(id, group_id, company_name, input_code, parent_id, next_inpection_date, created_at)
VALUES(nextval('company_structure_id_seq'::regclass), 1, 'RS Awal Bros Hangtuah', '1.1.5', 2, '2026-4-12', now());
INSERT INTO public.company_structure
(id, group_id, company_name, input_code, parent_id, next_inpection_date, created_at)
VALUES(nextval('company_structure_id_seq'::regclass), 1, 'RS Awal Bros Batam', '1.1.6', 2, '2026-4-12', now());
INSERT INTO public.company_structure
(id, group_id, company_name, input_code, parent_id, next_inpection_date, created_at)
VALUES(nextval('company_structure_id_seq'::regclass), 1, 'RS Awal Bros Batam - Botania', '1.1.6.1', 9, '2026-4-12', now());
INSERT INTO public.company_structure
(id, group_id, company_name, input_code, parent_id, next_inpection_date, created_at)
VALUES(nextval('company_structure_id_seq'::regclass), 1, 'RS Awal Bros Batam - Batu Aji', '1.1.6.2', 9, '2026-4-12', now());
INSERT INTO public.company_structure
(id, group_id, company_name, input_code, parent_id, next_inpection_date, created_at)
VALUES(nextval('company_structure_id_seq'::regclass), 1, 'RS Awal Bros Dumai', '1.1.7', 2, '2026-4-12', now());
INSERT INTO public.company_structure
(id, group_id, company_name, input_code, parent_id, next_inpection_date, created_at)
VALUES(nextval('company_structure_id_seq'::regclass), 1, 'RS Awal Bros Bagan Batu', '1.1.8', 2, '2026-4-12', now());
INSERT INTO public.company_structure
(id, group_id, company_name, input_code, parent_id, next_inpection_date, created_at)
VALUES(nextval('company_structure_id_seq'::regclass), 1, 'RS Primaya Bekasi Barat', '1.2.1', 3, '2026-4-12', now());
INSERT INTO public.company_structure
(id, group_id, company_name, input_code, parent_id, next_inpection_date, created_at)
VALUES(nextval('company_structure_id_seq'::regclass), 1, 'RS Primaya Bekasi Timur', '1.2.2', 3, '2026-4-12', now());
INSERT INTO public.company_structure
(id, group_id, company_name, input_code, parent_id, next_inpection_date, created_at)
VALUES(nextval('company_structure_id_seq'::regclass), 1, 'RS Primaya Bekasi Utara', '1.2.3', 3, '2026-4-12', now());
INSERT INTO public.company_structure
(id, group_id, company_name, input_code, parent_id, next_inpection_date, created_at)
VALUES(nextval('company_structure_id_seq'::regclass), 1, 'RS Primaya Evasari Hospital', '1.2.2.1', 15, '2026-4-12', now());
INSERT INTO public.company_structure
(id, group_id, company_name, input_code, parent_id, next_inpection_date, created_at)
VALUES(nextval('company_structure_id_seq'::regclass), 1, 'RS Primaya Betang Pambelum', '1.2.4', 3, '2026-4-12', now());
INSERT INTO public.company_structure
(id, group_id, company_name, input_code, parent_id, next_inpection_date, created_at)
VALUES(nextval('company_structure_id_seq'::regclass), 1, 'RS Primaya Bhakti Wara', '1.2.5', 3, '2026-4-12', now());
