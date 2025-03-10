PGDMP  0    ;                }            dynamic_law    17.2    17.2                0    0    ENCODING    ENCODING        SET client_encoding = 'UTF8';
                           false                       0    0 
   STDSTRINGS 
   STDSTRINGS     (   SET standard_conforming_strings = 'on';
                           false                       0    0 
   SEARCHPATH 
   SEARCHPATH     8   SELECT pg_catalog.set_config('search_path', '', false);
                           false                       1262    40960    dynamic_law    DATABASE     �   CREATE DATABASE dynamic_law WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'English_United States.1252';
    DROP DATABASE dynamic_law;
                     postgres    false                        2615    2200    public    SCHEMA        CREATE SCHEMA public;
    DROP SCHEMA public;
                     pg_database_owner    false                       0    0    SCHEMA public    COMMENT     6   COMMENT ON SCHEMA public IS 'standard public schema';
                        pg_database_owner    false    4            Q           1247    40972    input_type_enum    TYPE     �   CREATE TYPE public.input_type_enum AS ENUM (
    'text/free',
    'text/number',
    'text/email',
    'text/date',
    'select/radio',
    'select/check',
    'select/drop'
);
 "   DROP TYPE public.input_type_enum;
       public               postgres    false    4            �            1259    41003    dataset_entries    TABLE       CREATE TABLE public.dataset_entries (
    id integer NOT NULL,
    sheet_id integer NOT NULL,
    input_code character varying(50) NOT NULL,
    user_id integer NOT NULL,
    value text,
    file_path text,
    created_at timestamp without time zone DEFAULT now()
);
 #   DROP TABLE public.dataset_entries;
       public         heap r       postgres    false    4            �            1259    41002    dataset_entries_id_seq    SEQUENCE     �   CREATE SEQUENCE public.dataset_entries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 -   DROP SEQUENCE public.dataset_entries_id_seq;
       public               postgres    false    4    218            	           0    0    dataset_entries_id_seq    SEQUENCE OWNED BY     Q   ALTER SEQUENCE public.dataset_entries_id_seq OWNED BY public.dataset_entries.id;
          public               postgres    false    217            �            1259    41033    dataset_structure    TABLE     �  CREATE TABLE public.dataset_structure (
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
 %   DROP TABLE public.dataset_structure;
       public         heap r       postgres    false    4            �            1259    41032    dataset_structure_id_seq    SEQUENCE     �   CREATE SEQUENCE public.dataset_structure_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
 /   DROP SEQUENCE public.dataset_structure_id_seq;
       public               postgres    false    4    220            
           0    0    dataset_structure_id_seq    SEQUENCE OWNED BY     U   ALTER SEQUENCE public.dataset_structure_id_seq OWNED BY public.dataset_structure.id;
          public               postgres    false    219            _           2604    41006    dataset_entries id    DEFAULT     x   ALTER TABLE ONLY public.dataset_entries ALTER COLUMN id SET DEFAULT nextval('public.dataset_entries_id_seq'::regclass);
 A   ALTER TABLE public.dataset_entries ALTER COLUMN id DROP DEFAULT;
       public               postgres    false    217    218    218            a           2604    41036    dataset_structure id    DEFAULT     |   ALTER TABLE ONLY public.dataset_structure ALTER COLUMN id SET DEFAULT nextval('public.dataset_structure_id_seq'::regclass);
 C   ALTER TABLE public.dataset_structure ALTER COLUMN id DROP DEFAULT;
       public               postgres    false    220    219    220            �          0    41003    dataset_entries 
   TABLE DATA                 public               postgres    false    218                    0    41033    dataset_structure 
   TABLE DATA                 public               postgres    false    220   9                  0    0    dataset_entries_id_seq    SEQUENCE SET     E   SELECT pg_catalog.setval('public.dataset_entries_id_seq', 1, false);
          public               postgres    false    217                       0    0    dataset_structure_id_seq    SEQUENCE SET     G   SELECT pg_catalog.setval('public.dataset_structure_id_seq', 16, true);
          public               postgres    false    219            g           2606    41011 $   dataset_entries dataset_entries_pkey 
   CONSTRAINT     b   ALTER TABLE ONLY public.dataset_entries
    ADD CONSTRAINT dataset_entries_pkey PRIMARY KEY (id);
 N   ALTER TABLE ONLY public.dataset_entries DROP CONSTRAINT dataset_entries_pkey;
       public                 postgres    false    218            i           2606    41044 (   dataset_structure dataset_structure_pkey 
   CONSTRAINT     f   ALTER TABLE ONLY public.dataset_structure
    ADD CONSTRAINT dataset_structure_pkey PRIMARY KEY (id);
 R   ALTER TABLE ONLY public.dataset_structure DROP CONSTRAINT dataset_structure_pkey;
       public                 postgres    false    220            k           2606    41046 $   dataset_structure unique_sheet_input 
   CONSTRAINT     o   ALTER TABLE ONLY public.dataset_structure
    ADD CONSTRAINT unique_sheet_input UNIQUE (sheet_id, input_code);
 N   ALTER TABLE ONLY public.dataset_structure DROP CONSTRAINT unique_sheet_input;
       public                 postgres    false    220    220            l           2606    41047 2   dataset_structure dataset_structure_parent_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.dataset_structure
    ADD CONSTRAINT dataset_structure_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.dataset_structure(id) ON DELETE CASCADE;
 \   ALTER TABLE ONLY public.dataset_structure DROP CONSTRAINT dataset_structure_parent_id_fkey;
       public               postgres    false    4713    220    220            �   
   x���             �  x�ŕQo�0���+�F+��1�t�S�EZ�(���ҞV�܀U��m���τL�H�T��kl���c<[,�+4[��QQ�3�F15T����*�)�����t���!�1���{C�x�χ�N;����fh&6R��p)�9�[�`]`r�'��\G��*�a����j�P��T��I�p��A�V�Q%�}��LWP?e�Ђ�`�=���FAU��}���&i�D��A��:HAi[!ANy�@�U�2ES�Ӛ+��t�`�O�oޤ��.N�&���.H�����Ø��T��U���-5eu�<0s�h�e��'_JeY-U �=����U�����c_:� �},�`ph��e_���!"{� �,;�þ��?.�j��A�m��,��Z˨�\���E�TP�%���Ġ���n�.Ht��g5���`/�gl�I�4.�)�o?rQ�̅�n� �yK[�dцMHa�خ���������q�`6�x�^��2s0�gۧ�     