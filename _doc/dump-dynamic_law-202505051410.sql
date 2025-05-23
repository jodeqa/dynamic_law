PGDMP  ;    
                }            dynamic_law    17.3    17.3 c    P           0    0    ENCODING    ENCODING        SET client_encoding = 'UTF8';
                           false            Q           0    0 
   STDSTRINGS 
   STDSTRINGS     (   SET standard_conforming_strings = 'on';
                           false            R           0    0 
   SEARCHPATH 
   SEARCHPATH     8   SELECT pg_catalog.set_config('search_path', '', false);
                           false            S           1262    43607    dynamic_law    DATABASE     �   CREATE DATABASE dynamic_law WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'English_Indonesia.1252';
    DROP DATABASE dynamic_law;
                     postgres    false            e           1247    43609    input_type_enum    TYPE     �   CREATE TYPE public.input_type_enum AS ENUM (
    'text/free',
    'text/number',
    'text/email',
    'text/date',
    'text/links',
    'select/radio',
    'select/check',
    'select/drop'
);
 "   DROP TYPE public.input_type_enum;
       public               postgres    false            �            1259    43625    company_data_browse    TABLE     �   CREATE TABLE public.company_data_browse (
    id integer NOT NULL,
    company_data_search_tag character varying(50) NOT NULL,
    company_data_description text NOT NULL,
    created_at timestamp without time zone DEFAULT now()
);
 '   DROP TABLE public.company_data_browse;
       public         heap r       postgres    false            �            1259    43631    company_data_browse_id_seq    SEQUENCE     �   CREATE SEQUENCE public.company_data_browse_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 1   DROP SEQUENCE public.company_data_browse_id_seq;
       public               postgres    false    217            T           0    0    company_data_browse_id_seq    SEQUENCE OWNED BY     Y   ALTER SEQUENCE public.company_data_browse_id_seq OWNED BY public.company_data_browse.id;
          public               postgres    false    218            �            1259    43632    company_data_entries    TABLE     �  CREATE TABLE public.company_data_entries (
    id integer NOT NULL,
    company_data_id integer NOT NULL,
    input_code character varying(50) NOT NULL,
    value text,
    file_path text,
    is_original boolean DEFAULT false,
    is_complete boolean DEFAULT false,
    start_date date,
    next_due_date date,
    upload_date date,
    side_note text,
    created_at timestamp without time zone DEFAULT now()
);
 (   DROP TABLE public.company_data_entries;
       public         heap r       postgres    false            �            1259    43640    company_data_entries_history    TABLE     �  CREATE TABLE public.company_data_entries_history (
    id integer NOT NULL,
    company_data_id integer NOT NULL,
    company_id integer NOT NULL,
    input_code character varying(50) NOT NULL,
    value text,
    file_path text,
    is_original boolean,
    start_date date,
    next_due_date date,
    upload_date date,
    side_note text,
    action_type character varying(10) DEFAULT 'UPDATE'::character varying,
    action_time timestamp without time zone DEFAULT now()
);
 0   DROP TABLE public.company_data_entries_history;
       public         heap r       postgres    false            �            1259    43647 #   company_data_entries_history_id_seq    SEQUENCE     �   CREATE SEQUENCE public.company_data_entries_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 :   DROP SEQUENCE public.company_data_entries_history_id_seq;
       public               postgres    false    220            U           0    0 #   company_data_entries_history_id_seq    SEQUENCE OWNED BY     k   ALTER SEQUENCE public.company_data_entries_history_id_seq OWNED BY public.company_data_entries_history.id;
          public               postgres    false    221            �            1259    43648    company_data_entries_id_seq    SEQUENCE     �   CREATE SEQUENCE public.company_data_entries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 2   DROP SEQUENCE public.company_data_entries_id_seq;
       public               postgres    false    219            V           0    0    company_data_entries_id_seq    SEQUENCE OWNED BY     [   ALTER SEQUENCE public.company_data_entries_id_seq OWNED BY public.company_data_entries.id;
          public               postgres    false    222            �            1259    43649    company_data_structure    TABLE     �  CREATE TABLE public.company_data_structure (
    id integer NOT NULL,
    company_data_id integer NOT NULL,
    input_code character varying(50) NOT NULL,
    parent_id integer,
    is_header boolean DEFAULT false NOT NULL,
    input_display text NOT NULL,
    input_type character varying(50),
    is_mandatory boolean DEFAULT false,
    select_value text,
    is_upload boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT now()
);
 *   DROP TABLE public.company_data_structure;
       public         heap r       postgres    false            �            1259    43658    company_data_structure_id_seq    SEQUENCE     �   CREATE SEQUENCE public.company_data_structure_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 4   DROP SEQUENCE public.company_data_structure_id_seq;
       public               postgres    false    223            W           0    0    company_data_structure_id_seq    SEQUENCE OWNED BY     _   ALTER SEQUENCE public.company_data_structure_id_seq OWNED BY public.company_data_structure.id;
          public               postgres    false    224            �            1259    43659    company_structure    TABLE     !  CREATE TABLE public.company_structure (
    id integer NOT NULL,
    group_id integer NOT NULL,
    company_name text NOT NULL,
    input_code character varying(50) NOT NULL,
    parent_id integer,
    next_inspection_date date,
    created_at timestamp without time zone DEFAULT now()
);
 %   DROP TABLE public.company_structure;
       public         heap r       postgres    false            �            1259    43665    company_structure_id_seq    SEQUENCE     �   CREATE SEQUENCE public.company_structure_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 /   DROP SEQUENCE public.company_structure_id_seq;
       public               postgres    false    225            X           0    0    company_structure_id_seq    SEQUENCE OWNED BY     U   ALTER SEQUENCE public.company_structure_id_seq OWNED BY public.company_structure.id;
          public               postgres    false    226            �            1259    43666    company_template_mapping    TABLE       CREATE TABLE public.company_template_mapping (
    id integer NOT NULL,
    company_id integer NOT NULL,
    company_data_id integer,
    compliance_sheet_id integer,
    year smallint NOT NULL,
    link_description text,
    created_at timestamp without time zone DEFAULT now()
);
 ,   DROP TABLE public.company_template_mapping;
       public         heap r       postgres    false            �            1259    43672     company_template_mapping_history    TABLE     e  CREATE TABLE public.company_template_mapping_history (
    id integer NOT NULL,
    company_id integer NOT NULL,
    company_data_id integer,
    compliance_sheet_id integer,
    year smallint,
    link_description text,
    action_type character varying(10) DEFAULT 'UPDATE'::character varying,
    action_time timestamp without time zone DEFAULT now()
);
 4   DROP TABLE public.company_template_mapping_history;
       public         heap r       postgres    false            �            1259    43679 '   company_template_mapping_history_id_seq    SEQUENCE     �   CREATE SEQUENCE public.company_template_mapping_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 >   DROP SEQUENCE public.company_template_mapping_history_id_seq;
       public               postgres    false    228            Y           0    0 '   company_template_mapping_history_id_seq    SEQUENCE OWNED BY     s   ALTER SEQUENCE public.company_template_mapping_history_id_seq OWNED BY public.company_template_mapping_history.id;
          public               postgres    false    229            �            1259    43680    company_template_mapping_id_seq    SEQUENCE     �   CREATE SEQUENCE public.company_template_mapping_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 6   DROP SEQUENCE public.company_template_mapping_id_seq;
       public               postgres    false    227            Z           0    0    company_template_mapping_id_seq    SEQUENCE OWNED BY     c   ALTER SEQUENCE public.company_template_mapping_id_seq OWNED BY public.company_template_mapping.id;
          public               postgres    false    230            �            1259    43681    compliance_sheet_browse    TABLE     �   CREATE TABLE public.compliance_sheet_browse (
    id integer NOT NULL,
    sheet_search_tag character varying(50) NOT NULL,
    sheet_description text NOT NULL,
    created_at timestamp without time zone DEFAULT now()
);
 +   DROP TABLE public.compliance_sheet_browse;
       public         heap r       postgres    false            �            1259    43687    compliance_sheet_browse_id_seq    SEQUENCE     �   CREATE SEQUENCE public.compliance_sheet_browse_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 5   DROP SEQUENCE public.compliance_sheet_browse_id_seq;
       public               postgres    false    231            [           0    0    compliance_sheet_browse_id_seq    SEQUENCE OWNED BY     a   ALTER SEQUENCE public.compliance_sheet_browse_id_seq OWNED BY public.compliance_sheet_browse.id;
          public               postgres    false    232            �            1259    43688    compliance_sheet_entries    TABLE     �  CREATE TABLE public.compliance_sheet_entries (
    id integer NOT NULL,
    sheet_id integer NOT NULL,
    input_code character varying(50) NOT NULL,
    user_id integer NOT NULL,
    value text,
    file_path text,
    is_original boolean DEFAULT false,
    is_complete boolean DEFAULT false,
    start_date date,
    next_due_date date,
    upload_date date,
    side_note text,
    created_at timestamp without time zone DEFAULT now()
);
 ,   DROP TABLE public.compliance_sheet_entries;
       public         heap r       postgres    false            �            1259    43696     compliance_sheet_entries_history    TABLE     �  CREATE TABLE public.compliance_sheet_entries_history (
    id integer NOT NULL,
    sheet_id integer NOT NULL,
    company_id integer NOT NULL,
    input_code character varying(50) NOT NULL,
    value text,
    file_path text,
    is_original boolean,
    start_date date,
    next_due_date date,
    upload_date date,
    side_note text,
    action_type character varying(10) DEFAULT 'UPDATE'::character varying,
    action_time timestamp without time zone DEFAULT now()
);
 4   DROP TABLE public.compliance_sheet_entries_history;
       public         heap r       postgres    false            �            1259    43703 '   compliance_sheet_entries_history_id_seq    SEQUENCE     �   CREATE SEQUENCE public.compliance_sheet_entries_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 >   DROP SEQUENCE public.compliance_sheet_entries_history_id_seq;
       public               postgres    false    234            \           0    0 '   compliance_sheet_entries_history_id_seq    SEQUENCE OWNED BY     s   ALTER SEQUENCE public.compliance_sheet_entries_history_id_seq OWNED BY public.compliance_sheet_entries_history.id;
          public               postgres    false    235            �            1259    43704    compliance_sheet_entries_id_seq    SEQUENCE     �   CREATE SEQUENCE public.compliance_sheet_entries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 6   DROP SEQUENCE public.compliance_sheet_entries_id_seq;
       public               postgres    false    233            ]           0    0    compliance_sheet_entries_id_seq    SEQUENCE OWNED BY     c   ALTER SEQUENCE public.compliance_sheet_entries_id_seq OWNED BY public.compliance_sheet_entries.id;
          public               postgres    false    236            �            1259    43705    compliance_sheet_structure    TABLE     �  CREATE TABLE public.compliance_sheet_structure (
    id integer NOT NULL,
    sheet_id integer NOT NULL,
    input_code character varying(50) NOT NULL,
    parent_id integer,
    is_header boolean DEFAULT false NOT NULL,
    input_display text NOT NULL,
    input_type character varying(50),
    is_mandatory boolean DEFAULT false,
    select_value text,
    is_upload boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT now()
);
 .   DROP TABLE public.compliance_sheet_structure;
       public         heap r       postgres    false            �            1259    43714 !   compliance_sheet_structure_id_seq    SEQUENCE     �   CREATE SEQUENCE public.compliance_sheet_structure_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 8   DROP SEQUENCE public.compliance_sheet_structure_id_seq;
       public               postgres    false    237            ^           0    0 !   compliance_sheet_structure_id_seq    SEQUENCE OWNED BY     g   ALTER SEQUENCE public.compliance_sheet_structure_id_seq OWNED BY public.compliance_sheet_structure.id;
          public               postgres    false    238            �            1259    43715    corporate_group    TABLE     �   CREATE TABLE public.corporate_group (
    id integer NOT NULL,
    group_name character varying(100) NOT NULL,
    group_description text,
    created_at timestamp without time zone DEFAULT now()
);
 #   DROP TABLE public.corporate_group;
       public         heap r       postgres    false            �            1259    43721    corporate_group_id_seq    SEQUENCE     �   CREATE SEQUENCE public.corporate_group_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 -   DROP SEQUENCE public.corporate_group_id_seq;
       public               postgres    false    239            _           0    0    corporate_group_id_seq    SEQUENCE OWNED BY     Q   ALTER SEQUENCE public.corporate_group_id_seq OWNED BY public.corporate_group.id;
          public               postgres    false    240            [           2604    43722    company_data_browse id    DEFAULT     �   ALTER TABLE ONLY public.company_data_browse ALTER COLUMN id SET DEFAULT nextval('public.company_data_browse_id_seq'::regclass);
 E   ALTER TABLE public.company_data_browse ALTER COLUMN id DROP DEFAULT;
       public               postgres    false    218    217            ]           2604    43723    company_data_entries id    DEFAULT     �   ALTER TABLE ONLY public.company_data_entries ALTER COLUMN id SET DEFAULT nextval('public.company_data_entries_id_seq'::regclass);
 F   ALTER TABLE public.company_data_entries ALTER COLUMN id DROP DEFAULT;
       public               postgres    false    222    219            a           2604    43724    company_data_entries_history id    DEFAULT     �   ALTER TABLE ONLY public.company_data_entries_history ALTER COLUMN id SET DEFAULT nextval('public.company_data_entries_history_id_seq'::regclass);
 N   ALTER TABLE public.company_data_entries_history ALTER COLUMN id DROP DEFAULT;
       public               postgres    false    221    220            d           2604    43725    company_data_structure id    DEFAULT     �   ALTER TABLE ONLY public.company_data_structure ALTER COLUMN id SET DEFAULT nextval('public.company_data_structure_id_seq'::regclass);
 H   ALTER TABLE public.company_data_structure ALTER COLUMN id DROP DEFAULT;
       public               postgres    false    224    223            i           2604    43726    company_structure id    DEFAULT     |   ALTER TABLE ONLY public.company_structure ALTER COLUMN id SET DEFAULT nextval('public.company_structure_id_seq'::regclass);
 C   ALTER TABLE public.company_structure ALTER COLUMN id DROP DEFAULT;
       public               postgres    false    226    225            k           2604    43727    company_template_mapping id    DEFAULT     �   ALTER TABLE ONLY public.company_template_mapping ALTER COLUMN id SET DEFAULT nextval('public.company_template_mapping_id_seq'::regclass);
 J   ALTER TABLE public.company_template_mapping ALTER COLUMN id DROP DEFAULT;
       public               postgres    false    230    227            m           2604    43728 #   company_template_mapping_history id    DEFAULT     �   ALTER TABLE ONLY public.company_template_mapping_history ALTER COLUMN id SET DEFAULT nextval('public.company_template_mapping_history_id_seq'::regclass);
 R   ALTER TABLE public.company_template_mapping_history ALTER COLUMN id DROP DEFAULT;
       public               postgres    false    229    228            p           2604    43729    compliance_sheet_browse id    DEFAULT     �   ALTER TABLE ONLY public.compliance_sheet_browse ALTER COLUMN id SET DEFAULT nextval('public.compliance_sheet_browse_id_seq'::regclass);
 I   ALTER TABLE public.compliance_sheet_browse ALTER COLUMN id DROP DEFAULT;
       public               postgres    false    232    231            r           2604    43730    compliance_sheet_entries id    DEFAULT     �   ALTER TABLE ONLY public.compliance_sheet_entries ALTER COLUMN id SET DEFAULT nextval('public.compliance_sheet_entries_id_seq'::regclass);
 J   ALTER TABLE public.compliance_sheet_entries ALTER COLUMN id DROP DEFAULT;
       public               postgres    false    236    233            v           2604    43731 #   compliance_sheet_entries_history id    DEFAULT     �   ALTER TABLE ONLY public.compliance_sheet_entries_history ALTER COLUMN id SET DEFAULT nextval('public.compliance_sheet_entries_history_id_seq'::regclass);
 R   ALTER TABLE public.compliance_sheet_entries_history ALTER COLUMN id DROP DEFAULT;
       public               postgres    false    235    234            y           2604    43732    compliance_sheet_structure id    DEFAULT     �   ALTER TABLE ONLY public.compliance_sheet_structure ALTER COLUMN id SET DEFAULT nextval('public.compliance_sheet_structure_id_seq'::regclass);
 L   ALTER TABLE public.compliance_sheet_structure ALTER COLUMN id DROP DEFAULT;
       public               postgres    false    238    237            ~           2604    43733    corporate_group id    DEFAULT     x   ALTER TABLE ONLY public.corporate_group ALTER COLUMN id SET DEFAULT nextval('public.corporate_group_id_seq'::regclass);
 A   ALTER TABLE public.corporate_group ALTER COLUMN id DROP DEFAULT;
       public               postgres    false    240    239            6          0    43625    company_data_browse 
   TABLE DATA                 public               postgres    false    217   >�       8          0    43632    company_data_entries 
   TABLE DATA                 public               postgres    false    219   ��       9          0    43640    company_data_entries_history 
   TABLE DATA                 public               postgres    false    220   �       <          0    43649    company_data_structure 
   TABLE DATA                 public               postgres    false    223   -�       >          0    43659    company_structure 
   TABLE DATA                 public               postgres    false    225   �       @          0    43666    company_template_mapping 
   TABLE DATA                 public               postgres    false    227   �       A          0    43672     company_template_mapping_history 
   TABLE DATA                 public               postgres    false    228   &�       D          0    43681    compliance_sheet_browse 
   TABLE DATA                 public               postgres    false    231   @�       F          0    43688    compliance_sheet_entries 
   TABLE DATA                 public               postgres    false    233   ʌ       G          0    43696     compliance_sheet_entries_history 
   TABLE DATA                 public               postgres    false    234   �       J          0    43705    compliance_sheet_structure 
   TABLE DATA                 public               postgres    false    237   ��       L          0    43715    corporate_group 
   TABLE DATA                 public               postgres    false    239   ��       `           0    0    company_data_browse_id_seq    SEQUENCE SET     H   SELECT pg_catalog.setval('public.company_data_browse_id_seq', 2, true);
          public               postgres    false    218            a           0    0 #   company_data_entries_history_id_seq    SEQUENCE SET     R   SELECT pg_catalog.setval('public.company_data_entries_history_id_seq', 1, false);
          public               postgres    false    221            b           0    0    company_data_entries_id_seq    SEQUENCE SET     J   SELECT pg_catalog.setval('public.company_data_entries_id_seq', 1, false);
          public               postgres    false    222            c           0    0    company_data_structure_id_seq    SEQUENCE SET     L   SELECT pg_catalog.setval('public.company_data_structure_id_seq', 60, true);
          public               postgres    false    224            d           0    0    company_structure_id_seq    SEQUENCE SET     F   SELECT pg_catalog.setval('public.company_structure_id_seq', 9, true);
          public               postgres    false    226            e           0    0 '   company_template_mapping_history_id_seq    SEQUENCE SET     V   SELECT pg_catalog.setval('public.company_template_mapping_history_id_seq', 1, false);
          public               postgres    false    229            f           0    0    company_template_mapping_id_seq    SEQUENCE SET     N   SELECT pg_catalog.setval('public.company_template_mapping_id_seq', 1, false);
          public               postgres    false    230            g           0    0    compliance_sheet_browse_id_seq    SEQUENCE SET     L   SELECT pg_catalog.setval('public.compliance_sheet_browse_id_seq', 1, true);
          public               postgres    false    232            h           0    0 '   compliance_sheet_entries_history_id_seq    SEQUENCE SET     V   SELECT pg_catalog.setval('public.compliance_sheet_entries_history_id_seq', 1, false);
          public               postgres    false    235            i           0    0    compliance_sheet_entries_id_seq    SEQUENCE SET     N   SELECT pg_catalog.setval('public.compliance_sheet_entries_id_seq', 1, false);
          public               postgres    false    236            j           0    0 !   compliance_sheet_structure_id_seq    SEQUENCE SET     R   SELECT pg_catalog.setval('public.compliance_sheet_structure_id_seq', 1092, true);
          public               postgres    false    238            k           0    0    corporate_group_id_seq    SEQUENCE SET     D   SELECT pg_catalog.setval('public.corporate_group_id_seq', 1, true);
          public               postgres    false    240            �           2606    43735 ,   company_data_browse company_data_browse_pkey 
   CONSTRAINT     j   ALTER TABLE ONLY public.company_data_browse
    ADD CONSTRAINT company_data_browse_pkey PRIMARY KEY (id);
 V   ALTER TABLE ONLY public.company_data_browse DROP CONSTRAINT company_data_browse_pkey;
       public                 postgres    false    217            �           2606    43737 >   company_data_entries_history company_data_entries_history_pkey 
   CONSTRAINT     |   ALTER TABLE ONLY public.company_data_entries_history
    ADD CONSTRAINT company_data_entries_history_pkey PRIMARY KEY (id);
 h   ALTER TABLE ONLY public.company_data_entries_history DROP CONSTRAINT company_data_entries_history_pkey;
       public                 postgres    false    220            �           2606    43739 .   company_data_entries company_data_entries_pkey 
   CONSTRAINT     l   ALTER TABLE ONLY public.company_data_entries
    ADD CONSTRAINT company_data_entries_pkey PRIMARY KEY (id);
 X   ALTER TABLE ONLY public.company_data_entries DROP CONSTRAINT company_data_entries_pkey;
       public                 postgres    false    219            �           2606    43741 2   company_data_structure company_data_structure_pkey 
   CONSTRAINT     p   ALTER TABLE ONLY public.company_data_structure
    ADD CONSTRAINT company_data_structure_pkey PRIMARY KEY (id);
 \   ALTER TABLE ONLY public.company_data_structure DROP CONSTRAINT company_data_structure_pkey;
       public                 postgres    false    223            �           2606    43743 (   company_structure company_structure_pkey 
   CONSTRAINT     f   ALTER TABLE ONLY public.company_structure
    ADD CONSTRAINT company_structure_pkey PRIMARY KEY (id);
 R   ALTER TABLE ONLY public.company_structure DROP CONSTRAINT company_structure_pkey;
       public                 postgres    false    225            �           2606    43745 F   company_template_mapping_history company_template_mapping_history_pkey 
   CONSTRAINT     �   ALTER TABLE ONLY public.company_template_mapping_history
    ADD CONSTRAINT company_template_mapping_history_pkey PRIMARY KEY (id);
 p   ALTER TABLE ONLY public.company_template_mapping_history DROP CONSTRAINT company_template_mapping_history_pkey;
       public                 postgres    false    228            �           2606    43747 6   company_template_mapping company_template_mapping_pkey 
   CONSTRAINT     t   ALTER TABLE ONLY public.company_template_mapping
    ADD CONSTRAINT company_template_mapping_pkey PRIMARY KEY (id);
 `   ALTER TABLE ONLY public.company_template_mapping DROP CONSTRAINT company_template_mapping_pkey;
       public                 postgres    false    227            �           2606    43749 4   compliance_sheet_browse compliance_sheet_browse_pkey 
   CONSTRAINT     r   ALTER TABLE ONLY public.compliance_sheet_browse
    ADD CONSTRAINT compliance_sheet_browse_pkey PRIMARY KEY (id);
 ^   ALTER TABLE ONLY public.compliance_sheet_browse DROP CONSTRAINT compliance_sheet_browse_pkey;
       public                 postgres    false    231            �           2606    43751 F   compliance_sheet_entries_history compliance_sheet_entries_history_pkey 
   CONSTRAINT     �   ALTER TABLE ONLY public.compliance_sheet_entries_history
    ADD CONSTRAINT compliance_sheet_entries_history_pkey PRIMARY KEY (id);
 p   ALTER TABLE ONLY public.compliance_sheet_entries_history DROP CONSTRAINT compliance_sheet_entries_history_pkey;
       public                 postgres    false    234            �           2606    43753 6   compliance_sheet_entries compliance_sheet_entries_pkey 
   CONSTRAINT     t   ALTER TABLE ONLY public.compliance_sheet_entries
    ADD CONSTRAINT compliance_sheet_entries_pkey PRIMARY KEY (id);
 `   ALTER TABLE ONLY public.compliance_sheet_entries DROP CONSTRAINT compliance_sheet_entries_pkey;
       public                 postgres    false    233            �           2606    43755 :   compliance_sheet_structure compliance_sheet_structure_pkey 
   CONSTRAINT     x   ALTER TABLE ONLY public.compliance_sheet_structure
    ADD CONSTRAINT compliance_sheet_structure_pkey PRIMARY KEY (id);
 d   ALTER TABLE ONLY public.compliance_sheet_structure DROP CONSTRAINT compliance_sheet_structure_pkey;
       public                 postgres    false    237            �           2606    43757 $   corporate_group corporate_group_pkey 
   CONSTRAINT     b   ALTER TABLE ONLY public.corporate_group
    ADD CONSTRAINT corporate_group_pkey PRIMARY KEY (id);
 N   ALTER TABLE ONLY public.corporate_group DROP CONSTRAINT corporate_group_pkey;
       public                 postgres    false    239            �           2606    43759 0   company_data_structure unique_company_data_input 
   CONSTRAINT     �   ALTER TABLE ONLY public.company_data_structure
    ADD CONSTRAINT unique_company_data_input UNIQUE (company_data_id, input_code);
 Z   ALTER TABLE ONLY public.company_data_structure DROP CONSTRAINT unique_company_data_input;
       public                 postgres    false    223    223            �           2606    43761 %   company_structure unique_company_tree 
   CONSTRAINT     p   ALTER TABLE ONLY public.company_structure
    ADD CONSTRAINT unique_company_tree UNIQUE (group_id, input_code);
 O   ALTER TABLE ONLY public.company_structure DROP CONSTRAINT unique_company_tree;
       public                 postgres    false    225    225            �           2606    43763 -   compliance_sheet_structure unique_sheet_input 
   CONSTRAINT     x   ALTER TABLE ONLY public.compliance_sheet_structure
    ADD CONSTRAINT unique_sheet_input UNIQUE (sheet_id, input_code);
 W   ALTER TABLE ONLY public.compliance_sheet_structure DROP CONSTRAINT unique_sheet_input;
       public                 postgres    false    237    237            �           2606    43764 <   company_data_structure company_data_structure_parent_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.company_data_structure
    ADD CONSTRAINT company_data_structure_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.company_data_structure(id) ON DELETE CASCADE;
 f   ALTER TABLE ONLY public.company_data_structure DROP CONSTRAINT company_data_structure_parent_id_fkey;
       public               postgres    false    223    223    4743            �           2606    43769 1   company_structure company_structure_group_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.company_structure
    ADD CONSTRAINT company_structure_group_id_fkey FOREIGN KEY (group_id) REFERENCES public.corporate_group(id);
 [   ALTER TABLE ONLY public.company_structure DROP CONSTRAINT company_structure_group_id_fkey;
       public               postgres    false    239    4765    225            �           2606    43774 2   company_structure company_structure_parent_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.company_structure
    ADD CONSTRAINT company_structure_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.company_structure(id) ON DELETE CASCADE;
 \   ALTER TABLE ONLY public.company_structure DROP CONSTRAINT company_structure_parent_id_fkey;
       public               postgres    false    225    4747    225            �           2606    43779 F   company_template_mapping company_template_mapping_company_data_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.company_template_mapping
    ADD CONSTRAINT company_template_mapping_company_data_id_fkey FOREIGN KEY (company_data_id) REFERENCES public.company_data_browse(id);
 p   ALTER TABLE ONLY public.company_template_mapping DROP CONSTRAINT company_template_mapping_company_data_id_fkey;
       public               postgres    false    217    227    4737            �           2606    43784 A   company_template_mapping company_template_mapping_company_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.company_template_mapping
    ADD CONSTRAINT company_template_mapping_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.company_structure(id);
 k   ALTER TABLE ONLY public.company_template_mapping DROP CONSTRAINT company_template_mapping_company_id_fkey;
       public               postgres    false    227    4747    225            �           2606    43789 J   company_template_mapping company_template_mapping_compliance_sheet_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.company_template_mapping
    ADD CONSTRAINT company_template_mapping_compliance_sheet_id_fkey FOREIGN KEY (compliance_sheet_id) REFERENCES public.compliance_sheet_browse(id);
 t   ALTER TABLE ONLY public.company_template_mapping DROP CONSTRAINT company_template_mapping_compliance_sheet_id_fkey;
       public               postgres    false    227    231    4755            �           2606    43794 D   compliance_sheet_structure compliance_sheet_structure_parent_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.compliance_sheet_structure
    ADD CONSTRAINT compliance_sheet_structure_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.compliance_sheet_structure(id) ON DELETE CASCADE;
 n   ALTER TABLE ONLY public.compliance_sheet_structure DROP CONSTRAINT compliance_sheet_structure_parent_id_fkey;
       public               postgres    false    4761    237    237            6   �   x���M�PE���٩P�M��u!�EZ[?��|�G�O�������a��$8����1��V�gK͔�4P�w��Wpu�K���6 �Ս�z��ʗ �K�?��r�NU7�t'j u�-�en�9:r��ij��td�����Z��ЍS�����'�I]�n���3pK�o�H�      8   
   x���          9   
   x���          <   �  x���_��@����f�f�䏱O� Z+u��2�fiؘ�F�߾q���1/��L!�	y�1ssH�d����7�=<e�z�.6[��u����.�D�����K�N�Eu�d�/�٬/�;���}�7�l�^��ȣ��W$<�p$���E$���Ow�����NiA�T�e��ңϛ���l��t�W&�ʏ/�$i��Q>��EP��%j�d����s��U��Z��ʉ*bU`��R; ^��b����*fTd��s"��Jz���jYMz)�&����ˤ�������/�J����"��b��X.�J���\�K�
l��̒!�B��0�dĬ�j��喉x���E^��N���ɩaCY$�4K_�j_=}��uz��l�y���3�`�H2�lR!�$�6���yJ�_��.b��\�N�F���.P�F��D�6Ot?��7��g�r?O��&����]�r��'�������b��<?vP&��y�"^��d�p1Nq"��.x�W{����f���p�|�T��LQ#8"9�U,�#�Ѧ@@�����g�O��V�
+d�Q��"f�^�@DCa:�*f�TA�|�VKL60T�a�@�
����*U .�]�R�
�(U ��I�R�*U ,��7�*�	vL��^#B�*�d�T���]�R�R5��R���T��&�J�+d�T��L�CJȤ7�T���t{����^���T������r|J      >   �   x���Ak�0���ܠ����IA����^G*R����~�e{"��x��/�!/��� !���ӹ��^�ow�?>��a��ih���*;�K�3���p�� ϭkr`^1f��Fo>5�b��  ;?��Q�����w�g��*�_Z=��ޯX��̡T�4"Zf��
`%�k�&���F߮=��2-�L�P]��_�����W�T�e8��N��T;���뙘w)~�s�Q��      @   
   x���          A   
   x���          D   z   x���v
Q���W((M��L�K��-��L�KN�/�HM-�O*�//NUs�	uV�0�QPwIMK,�)Q�IL)�Wp��P�P�����x Z� �-���MM-�5���� �I'6      F   
   x���          G   
   x���          J      x�ݝks�ȑ����'��1cu�ϧ��&�^��:P�P�}���?����#�Id��p�wFz����uͺ��=��.��>ϻ�y��ϟV��y�,?���<���ߛ�z�i�[���F��g��Q�s���]��������� �'���������]����M�����G�����L�����H�E�a��Zj!������Ș%�s�5`׫�j\,��Yp��w��)	��/N~
~	���7Y�ܜ���oI�^$�M ���7tC�H����>'�MA3>����n������u��ҽ�r�X�˖��n��Ӏi��`�d�>��Yp�n�ي�@D�����;(ex�+
]0��W�du�1�ȝ�4p�E�a��yc�%c��2Ȥ��q�ye�'ʦCG�#���2�E���!2�(�]4�;͇(c�H'��)ސ��~Y\C��1��!2�(c�E�Ӽ�2��e���2G�Ue^��r�"��2��q�i^D�VMzk��f�~�oA��?s���&���_��c�l�_L�E�������%���h<����jиA5Y)��D_��6Ňݤ������S�i�𽛤�M��}��ƫ��l�H6ٻ7ōZ\�p�}�8yXg�6YnW�`4]dy�����4}^��M�o�M`m8j��.�w�2yj�i�[<���2��N ��m��m��]�y�W�i2���N��\�޶;E,0���k�� Y��l�8�-�P4�����\�dNW��"�)�N�٪�����_�'��q0�:]����-n���0.�U�<]��[��Z~ͅ���M�ޏ��R����|5O�/�g��sp4O.��9nw�d������������J��i�1=�7�O�N���O����&'�8�Ect�d���+�"iZ�|l3�⊨c�b��m�A���-�0K��#�*�/L��[>���j�̃�X;�{�-�D��+��N�ަ�m�9��w�d��y��!xt{�����1�jm@ �*����M�Xa�j�i�8�EK�Q D�D�-����-�Q��&��H����N?��ή�F����zt�������������r"�OTS]�n��a�6�`�~��?9ڤ�|����̢a��9bm��CR�?�ҙo��c���I�ם�� �B^��T�!0Rݖ�q��rK!��_��1䓘��e�p�!�S��@�U�1WZ��6]W�r�.?��s���7��b ���AQ�1F*(J@4��huDI�&[�#T
�$���*�$��y2����|
�Q(��*���f�.ǟʕ�b�\�V
�.&�����D���r�C�����q�F+'�A6���M�����i��q9��\jY%b��>- �Bd�ҧ%�ӈ�@�4�
�#}�xs`m�� �en���6��ն�q�F�m&�l�Qꅉ �DdHu���kdU��D� �L#2U3���+d��,m��~9���,�e�\~�:�i|���>�s��Q��G��N��������IV���M���W����c��h��^�8B�d���R ���Ԡ���O">���8�|
����i�gJ�J�9�#��c�������]�D���[PsHm5������}��6)W6�Bd!��Tn�F��;r��ӂR�c���UĪrB�jށV���d�c�G�{ñq!���<�����m�i�"K����mp`�AC!
C�Y!f��B`H��q&X���U5P.[��H3
9Dc�t���q��h3
%��~��
JLH?�B	U��|��jL��3
c�m07��G!D�k�CF��kz9m�T=
�{Fs!��b�E���Ӌ�g	St>�#�(�.���>�A#�B+M�Z�����P>�`��u+"�� 4�!�h��PB8��|��b
��� �1H(1��P�!���B���z;er�M!�LA��F:d:��3���V#��̸�C�1e���1��P�����=��ȅ���A(g.������*O|2x�8��w߷�@Cp�7�a�1'�7h��馼-Ss�K�s�m�Λl���d9<��ݏ�4W�a4��2��c8_���@L�1IR;n�J��P�U��f�|�	r����d�5��M����:	~z+8��TQ	� Gn��p��&��.�x���.��Am��d�Oȏ��P">�@Z�ԍ��PaF��K� t�q�����NF՝3�����ug�Q����D�)C̨^�NN֝2¨zow
��d�Ѽܝ��;9F��v���N�?��S��g׋�����ЎE��F��C;n��#Mա;�~Ǐ4]�v�(�oH��CUǐ��q$C֡
9���x�y�r,��M?����SX���,*��1G;YT���ϗɢR.��A=�,*��l*�&��`F�}�,����I5Y�!f/w'�dQGU��N�ɢf�Q�ܝt�E�1��۝T�E-0�y�;�&�Zb�xowRM5�;Y�ߟt�E����fD5Y�3�~Ǎ�&���F�~;��,��E��Gt�E��h�!QMMǐ��q$�ɢA�$�8�b�h�}���OY�k�9��a �\8��h'�F�x��2Y4�5�'�E#>�ƣ�bbF�}�,�F�{��j�3�(^�N��b�1��۝T��X`F�rw�Mc�Q��,�
3����n�k���N��b���N��'�d1�z�~3"�,��cF���d��7����d��;�~Ǐ�&�,��Q�ߐ�&�,�R�;�D6Yd!r$���/>�e�a}�����.���.�n�oG��rtq}��Q/�[���n_�U�ުB��r����,8�����;����Kf����\P�r/I񥡼�h����bP�sw��zL���DX�(���;���9�dE!��z5��^����Y\)����C�WV޲�x�P�N��4��Mֹ�f�m��?��U��j�����V�<6�n/r�<��B����Eu��f;��k��E�m��{;N����,Z��^$�w/a
ۇ�a�}�GmP��a0��>��c��j�VR����ʢ��2��䱸��,�P�OQѲ�����2�ۋ*���SΓE]�X�1䉽nz�9�Rʼ��1�LHa~���F��O�����f�c��ֹAu��1�RrL�';�G�
L���-�Đ�b ���e�*Ưg���<�U���v7-o�|Mf�_�f<r�+f�S���%g.&���&�]��e���\�+�f�T^a���3�֛�l]�O`��ůDyͥ�&�$R��̨���}t�dR�ۦS[��n������%O��	u��2�T�!Ny�Ee=�ޥ}����  �vmľE�����շ(s��Q@��X����x��Ee=�ޅv2k�}a�7�(蘖�҉��ut��N��wQб2YGA�Xp���8��xtcA�x���x���8��{||N����O�,��M�1������c̛��[J�)�}��-	EK(0�/�!R��CR��H�:�!yo}�m��7��Ie�?k3�Eq|�v(�j�pN�r�r8t�B��*��|*t���5��`���3I�I�O,�/;�O�*B�y�5��Y�!g�]�!V!�՗!g�ƷZ�8�UuY�X�8\c��_�8�t �j)�pָ�:�Z���[��/F�ر�7[�8���c�,G�1�W]�8���.�gD��g�<�� 8O6��8r3�F�{NPG�r9Y��]h��i��q/�'^G��l���^�:ֱ/k���|7q����d=��ũ�\h��I��8��g�p9�>
0I6�����l���]i���WY�=�y��	#[���Ȗ.�g�ݘ�B��� ������E����]�%�=���cX�7�18Uŭ�\8��6���<��;��U�x�e�h��n���2[>Ϊg�γ���q�T��?p���5V�m��k�FR}�8l)�l�p���Z��s��+x��P`��9��q,������R����:�9�57��{�����<�m׫e6<{���L�=1�1{dK�0�O٣ZN�9���
H�=�5�({no?��"[~^��    ��6-�N����l��k���|�J#���j��b�4�����Ò�9�� �&[p��?Y�������>+��ի�4=�`;lK"0��b�o�R����b�.�.���n�����P�fO<�5�9��j#���w
<T��ԿH05�#��i4uB۝@x{�B�Ӷd���j5-n�_�'W?����JD؄qܓs�����E.cEyw��G��P�-�5�� ��B�虦PǀD��ԿP5�� �R� ��@�e=���cl������o�� sK���,ge=��� s-L�1��ȋA����ˆ�h7Ͷ�D7�,����s1[�O����
-�j�ϋWÿ�����/�@�.�%�9�Q�ߏ
�1�W,�� ���k�i�{:���Bɇ��>�&��V��o-I�C���tt�>���~?��~?��/N�'�g]���8)p���iw?oxĨA� 9ͫ����DY�o�������0�h�� c-��r`���ST�SR�8�0E�$j��(���l����7��_n&��Kzu]
�m�ҿ��:E��z8�V�u**h��1A��m�»�R\�.'���.(0&V��������cq"'8M��,����0�m�<LEcV�խ����P�Iz0���un��|5��".@��E�h�@H��0�'c � %�){�5�{���F����d�ٸt�V��p�������L*Ö�!!�Ig�Eq�4�KgE}X�TTF �
�N��  � �eA�u��t�ȕ�rLZ�-YG
�'0��I��(�n��0n�i� �
/qQr?�GCP�A}JI9&%O��	�G�>�q �����W�<l�xH����~��p��l��P�*W^����
T�:��S�1�F<hS�qL�{Zy��Q`DoF�JAN�9��6��Y�>{侩�hH�z)�Up~xxH�B�}��[<�����L+;��U4��1�F,;:�t�� ;�AD����!�Ĝ�Ȏ�R�R�ˎN�����,��,IeG���2�J�*Φ!�lԲc �t^�NF�FvL9%��DvL)U/%���4�_v��sRԧ���n<���f#�#!�t>ȎQQ`DdGCN�9}�)U/%�� ��{F;���h;1�{��Ğ�NA6�وU'f��c:T'�Q`DoT'�SbNOT'��R�R��N�F�[�I�è���MUǧD�Cwdc��ZwbH�1��#�"
���0��s��;"d�R�RR����=����-"v�[<g�ǟ��G��r��V�|�J��0���PA:���F�G䔘���!��$ן����;�׫%��D������ϓu�9�%���my{����J+#O��E�!�l�Z	H�1��I�'0�����s��!�'����""�`Ɠɍ�dc��:abH�1u°�	�G�0�	Gn��S��+�=V"[a�V�}ֲ-^d	㐍a6�,a�qLG�%�	�G�%���o��d���i�5�a����{fҀ38��\�:�.���Y��,c�0`}��A8������b�6	��̶;�ڶ��#P?�z3�n�H{Z��$Ѡ������o�5;�<?�'Fy�Wy?x����g{�6���mՁ��Ћ\W�cD�r]CT�Q��u9%��u�:���������yR��c>�x�MnL��9>	@��"����܂AD�}Jn�!����$��SbN��nK��&�iR�I��"�;�~���ᳺ���^�&�uȽHzR<��C�U�J�|) �� ��D�S@��T=�t>�N[@��k������z����oO��\~q�@�@��UO�'�E{�_���͹f�P�T�y��
�
��OZk�)1'MZo�آ{�
ո�6���ع���f�P!dc��8�U�8��)����z�ӊCN�9Ir���/ߡ��$���v�'�v��D}ݿ�\(A{�.����	�m�L��q�u6� V�e��H�N��kQ�� ��e��/��Yސ�t�����m���:�.�'w�����edS��l�j �l�C:��|кF�lj�:�ԺY	�M9V�4�Z�
}.ި}l ���Cڿ+�F�b��^����#����O]����y����s.���2��~��(lOR�+����RG���;��Q4��k�Z�N����ɂT������=�C˦qQ9F%�����,�r��0#:N��s��\ܳ�pW�f�\V��ѓR���o�C��5#�e.�Ƽ<D,w!�$�&��
�7�;^ݍ�C։�&䁺�2ꏺ��r�J��Ƹ����=Q��唘�#u�C�U�|t��=�\^�y}P����C��{<���G}=�Y2O~|�fp'��g���|#V	�f#^����Χ��XCT�Q��)6Ob<_�k�b��^�]��a5�ߜT6e�8C����ߠ�����A��G�_R�a�=ը��G���y+�Y�~���Z>��ːfK�"Pp����zp�Q�"r�葚�PAT�QmU�C�5�З�Uȩ0'�(S�q����'ט�C6��s��*��<���>���~9�|=AF!��
Ԟ����<2w�`��lE^u���Ȉ��#��Hjõ8���C��i>�YT>��a:�S��s���+]X�a�Ƀd/&��e��<�����A�}0�qF�"�c�cHO���.���>%7�\X�a���9����>ht0Sc3�3e\>���B���w_2���K0�'�`TD��xT��\�Xc?ՊZ� ۂ��ֳy�� J(�%:X?t��`4�Y��Y���%�vA�u�uh�1.*Ǩ���80v��w=�\��tV�5*]T����sz|���:�G.����s���$���Z&�fzJ?�w�����8��]�?�������[�`+�^�"dr�U�;�l�Ņ�0�?ť��1*�Dq�
�DiUv>;�D�P�L�%�q-^K�pY {bh�yI1����T��b�T
1��G(���RˤO`<DRH*��R#���jDz��B�6h���ÑB����6�u�,��޴���إ�o�z �2��c�#�2���R�dO`<�Rr*��R(���jDz,�R�6h�����J����Vo�M�O���%�wi &ØidA9��HB<����HAP����T�#�c�T�A�6�h��#�F��ntu2:����Q0:����\6p��"B	�l*1��G6�����˦�x�y$�1��qI)�:��jDz,�:�mи$��V;��E|צ�U�ɖy��k4��j���@%ǃ������͸Zm��=��<� ̢�^4����hw���~Ԗ=���ґ������yR[�@�;��KWj�v������gm����C���\����Y�k��D���4����^����#F������F���Rk�Q.����h��.�Ĩ�
e\8ՉIr��]B�?k<��ر)^k(��#��𠽜X��x����7)�9�d�!���Z�c	���G�cAe\2�d�qjȩ���Z	<������\ȞH��;���b2��.�0����
��]R!���?.�uI�r����.����ե_��%_��^KL�tICL�1=�%A9%ץ�	��.E!��q�.E�T��c]��YI�K�l��8U��^���T���c��T����R+U� ��x)����?.}P*9����Y��}�Z�(��T[4�z�v�O�/ɲ(�W�+�SQkhVo���T�?�1��Y�-Zg�3���u���x�ʃ���|߲�7���E��`���cPjh�*���;x���J��m�����=_�cUm�/�H{�mᅺ�d	����-�PW�s0�����g�P����ϓ��R��_������x������ւB�������6y
�X#�7��y�B^Y��.+����v�_�Qm������R��`2Ւ1Lv`���t��1۫�4=�Ҵ�S��Fq�({㯜�SNCۢ
����D�^��϶�*ώ8�$���W���    �q:��������@5����x���R�������a2b�l�,�J)!�7J�[ЕRBJO��-��+��ğJiZF�'�Rʸ��D)�����K/L�E0N�Y�&X�k�.�J&%.�B�m�Sɤ��S��öʂ�dR��!�ɶԂ�dRz"�m)S�d'��e�-�`*��D�d�-�`*�������B�d�|�v�w��&�f������'���XLlV���m}��
b�xU��%b+�=G�����[A4�	b[7!���{X�ġ#Q��jO$��au���[%��:=o�w�L�;��������`|vwv�~4>��0]�g��./��xv�%Y�c�q��b$�)�=��O�S��	�ީUx�渉��	Y6�-%Ô'��yVpR%s]5A�[��d�P�@��N.���m1S�_uؠ�+!�zP�����.u���AH	�QW7�֢e��8d����+kb���d7�f�Ӱ�t�-|�d���>+t�`�_�FP�b�ҝU�;Y�ꖕa�:x��-���嘖F<������xs��4��؛:�60MԲ2��]`��rLK��q%�3��l��٬�6*j���V���"��vݎ��ă����M[^"ʓ�|��+��XNw���%��RFJ�	+��uثd�� '�p����Adsq�!'ǜ�V�����z�c▓�&Ҙ���b��C@f�'�0y�r��/�3��1�O�s�*0�7�����n/1�c'���+��:��d���sz�A�
��O��d����͆O##�Ӣ�C#�a9Y�ӓ4�!��sz�F:�U`T_�H���d�F��K6ޣ��r�N�������4��j�O"/>>��a�;���s�\}���d�Y`��|T"9Y�s���1���'%�B�*0�7JE-'�#�T� p�SQ�aNEr��/9	��1�W9%!������)���)�S�攏>��:���T99��)�XQF�&��)�s�d��#�h�N�\?&�lS]�Y<d�<���g�xQu��d��0�GOs��Ě���a�r'�,�Q��2N�rr��Ub��S N�Z��A�$u�0%�ߓ/�Cp�<瑈ΣG�O~�m}����4��i�,.@��s��cs�ج�&�h�a �Ö�aJ�0@}v)��K=pJ���$\������g��w�����V�u�[|�-�9N~K6����r
�g�����&���lE�^�_����y���/1麆�n�*�å3]W1��B��3]�1�ͫA�7�XW2���A��.�c��0����*�"�"�Ut�f��H"�u����w�N�_�(�;p�.m���x�fy�>�C6�و�GH�1�7�#$���^}������h��0"��Ȥ1���W��j섡1�8���w���H�"R���|pՓ��Ԛ�ʽ^�'��v�xH�A��S%��SF��������1�F�͒C:���f) �����,%�@�Y*��0"�6K�21�/�ޤ�y���sJ������d�3�l�+�
!�tԂ�"�'0^!(dh�I�v�ϋ:��C#r��0"��(`|��L�ͧd���8WL��7+_V���l�Q���tӑ���x��Ǭ�'y|_��Y���r�ûq(Ltmi%�=@�%�!$S��W��/&� �Ƅ?�|#�x�v}29.�=���ܓ�^�;�Eu4]k�	U�	��0�a�w0��p�({�)H'0��hH&1��)�kiU�˹#[�4f��;LB"��IV屣�� _��z��>(�a�a4Z�3�qG�pF@:���HH&1�g
g�U�~�T8�!��l$
g ��$��Xָa�����C	���ۀ�pK�.���o����6�t\>X�#Є�qO����� $끜��W��[�}Of]jm(�����,�9�˦	xh�M�y�����!@lh��^'	!Y���Zd^�F� �gC;@�[ �������oޡ>(O�WU�և�,	��f�}U�`>�O�p����gzJ����ǁ�L}+�4Z�����(��~L�?qp���x%o�7�m�`2���6S_�7͡J��pNe���9Q頑ΩL}��4�(Q�m�uF4q1��{��t��ۦ�_o��L;08ݥ�i6�g�i�g�����Tބ��pý�ّ�1c��1&E�E�8
��n�m�\>�%Eu��/�PM�Jh�7b�a4ڜ�8�����t=' ��p$� �@�L����>��m�98I���d���x�� &!lF����i��0qF�1��r��[g�|���b(0 EV0�g�z�I��l�m�NL���0�S`�1�F��C8���S�	(0 I
4���L�<�E1�g�ءx�خ,�&eqtdU��V�4 ��ʓ<5�a4�<�!�p�Lhx�b�N.��ŝ��l�͖�������q�G��
A�Up�F�A�!����N`8
��M؄�={:�,�(�oع4|��żXn�]�����j�0��K��{ ��%?6��!����O "���� �T� �N Pm��!��`�.��$�����-���e!���.1������T�aTO�WCH��]�H,����J?#@�R�"@F�Xw"�L�%�`�Q��"�~�D9O6�{9M�����"���t�¦�~����aTOR\AH��]�kH,�� Q��CH�� Bb݉ 2�W3�B���D�<�v|sybsdP%W�~��2JXO�)���\U�q�F�*���~�\U�IG(�)F"�4�����za+�W��o��d�<�:��h��j	~f�����1�F���A8���Bs&0EBh�f�t��F5p��,}IZ��?�FW'����:�p1���hX+H�0)i�j��1q�'0���!��БI�	!��`R�<�ߡ����tt�>���LFF�﯉~0�5��R�t��+�XW���Wg=g����d@^_=��s2ƛ�x}�<�O�oj����y\�|1�C��zyl�b���.��l5�W6&ɗd]O�>��B}�<���W�sx0X܂1Fm�m�>~b��w0PmKn�辛�כ�_��!��2�c�v2|q���L��/�-�`�*��c4꼐-��l$y�؂@y���<x�7&a����Z����ӤX�L��m���[����(�c�|ܶȖ�<?�6�Mpt�� yL�W��F�h����M5ʄ�3��U���R��:ʇ����&���][0�S�G���=�����-�l�2�7�-�t��*��K�S`NՎ��%�O�������T?� ���9�Ǖ���Xn�f#���qL�M�����9A���9�^>�����$��R��cO���s�f�͒�;t�'G$<��H��@�q�m��"8����z��fE�<�v��\&�mybe�M˧Ȏn��Gw��'�#�+�fP��lGT�1����0�$�l~[��Tx����]�&���!��"i���Qԙ��]��?^�__�G�C�A}=�󑂳���I�Z��$�p\_F���k���m�]f�E�zVZ��}|�fC�:����Ӓ���m�}.�0͓��̎YBe)�=u�00�X���n�8f�+�w�-��t�����Sv8�l���@���8�ʫ�6�W�С3�� ��s��>�9s;�h�]�!�7&�8����1�v�s�'�ۜo�lI>�t@���6�وeE;t��}��p��P$�6;�ʧ�æ��A9t����1'��	�
u��(�M@�����6�y�Q57=�.�
?��B9l��v�8��NS���]����dY*�5����"y\��l\&�r�5:c%�	�t�Z/���6��h3Vr��c:⌕��<����!���$cks`xE����>�����h����������j���>xd��E<]�v�4�5���I����bp:��Y>z\���|�8��w}�B�p����x[6��h���m�8��P.�Of��#�q}�ۢ
�J,��%p�'1�3�q}�"�N��E}ܒiLF�J&�� �  �ջ��&���xJC�J��vce6�و/v�8��H�t�
�J�x:r�$��@�4sU��Os�Lc2
����^śe�lp���!첓'w�c�6��hOk��c:��8��R^��I�����AT�$<9d�Q�i���	�8]'Oř���ÊMkv�gڧ�˻X� F@*���~���l�Bl�C�1�GBl��*0*���I����r����	�i�qCWÈ�bU�{�?3��a6ZE��C�1�G�U`TbE���'1��+QaDE�>����<>>t��A��b�Gi�8�6��H%%
�����M�Y#�U`VZQ����'1����aT��@Vr(��OW�gk���v��69t��DE�쁾� ʡc:j����y%1ƁXr��@��Ad�ЁTH��Z������r�Nf��ϗ��C�w�p�wp�0Q�]���䐳&ŵ��E���u����L��C�:�������L��G�gW'�hȥC�;�m=��x�+�//^8!CV��	��s�����ß�E6�f�;-��t7�d�v�e��1�"V�T�f�i��s��R��&�7��Kʯ�<�$Y���&���O�ıC�_�E�Y�r�=&�a��l:�i.�OY�Hs-�d����н��S׶TK���6������k1a}���mmE�Y����w�B����7��c.׫y��,W����S6�=�Q��us��♇EA�ܾ��M��cRuy>A����&���7	�_���d�E�vp7?�n�~�n�+ҹuS�{�į��&����Z#�u���Tm&��m�:��Ѽ*`8-�v�-��Y��Y)����ߗ�h�w�o~��%`��f����x��c�[GxE@� ��7 _U;���J��`1�V�[ �ħ���֧r|�UZ>%Ӫ�a9#H�6�N�����<���N#9���O	栊*M	�N�Q>����?�hT
-�鹞�΋��I$��N�/��c<�$R � z�D�AT�$�^$pϳ-�'f��n[��*�gֳ�d�(�|���n�O6�O��_>�W���e����y��[M��
oLJ���Q痌@�$O+�B�!�I+�z�D�C�l�'L�K��FcD?�?,9�~����"���Ε.���"��֫�ͤ���R</7�'������/o�:(6����A+$lEݎ7�_O9x��G���@zE0��)B�N��"T�"ç�+-���<���Wċ<���N	pEZ639H����l&p��C}E,�`�A.����o;�M�]�����k�Nf�6ؤ�47�o����w(�Ū}b��؜N���8p^���F}�\x�z�|-��w¦xc�n�e�[ת��C�]�"�q�X�\�b�w ��	\�V�e���|�[�36#h:����q����,�u*�h�[���`�>��+Rr�Rw�����=x��t¡3:w�����`����Bac�o��^��t��?�lǁk��j���t��;�K�v��~�+�@��m�@`wv���8��t��/�,�2�6�<��=^;���� 7��?w����V�1�f���u3���)y���⺙k!P#�(��L��o�Ur�L� �Ip��|�m$��e>R���ٶ-����/ͯ�#���w��~�&��hl��~I8~�m��`+�vv��퀲>P�� l��mŰ�uu��ȣ\�7�E!P�\�7�E�}*p��4e�N؅����bZ�      L   j   x���v
Q���W((M��L�K�/*�/J,I�O/�/-Ps�	uV�0�QPw�q�Up���!
���l����T� �̭��LM��LM͌�5���� 42>     