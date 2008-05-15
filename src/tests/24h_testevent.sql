--
-- PostgreSQL database dump
--

SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

SET search_path = public, pg_catalog;

ALTER TABLE ONLY public.team DROP CONSTRAINT team_fk_responsible;
ALTER TABLE ONLY public.team DROP CONSTRAINT team_fk_category;
ALTER TABLE ONLY public.sistation DROP CONSTRAINT sistation_fk_control;
ALTER TABLE ONLY public.sicard DROP CONSTRAINT sicard_fk_runner;
ALTER TABLE ONLY public.runner DROP CONSTRAINT runner_fk_team;
ALTER TABLE ONLY public.runner DROP CONSTRAINT runner_fk_category;
ALTER TABLE ONLY public.run DROP CONSTRAINT run_fk_sicard;
ALTER TABLE ONLY public.run DROP CONSTRAINT run_fk_course;
ALTER TABLE ONLY public.punch DROP CONSTRAINT punch_fk_sistation;
ALTER TABLE ONLY public.punch DROP CONSTRAINT punch_fk_run;
ALTER TABLE ONLY public.controlsequence DROP CONSTRAINT controlsequence_fk_course;
ALTER TABLE ONLY public.controlsequence DROP CONSTRAINT controlsequence_fk_control;
DROP INDEX public.idx_team_runner;
DROP INDEX public.idx_solvnr_runner;
DROP INDEX public.idx_sicard_course_run;
DROP INDEX public.idx_runner_sicard;
DROP INDEX public.idx_run_sistation_punchtime_punch;
DROP INDEX public.idx_number_team;
DROP INDEX public.idx_number_runner;
DROP INDEX public.idx_name_team;
DROP INDEX public.idx_name_category;
DROP INDEX public.idx_code_course;
ALTER TABLE ONLY public.team DROP CONSTRAINT pk_team;
ALTER TABLE ONLY public.sistation DROP CONSTRAINT pk_sistation;
ALTER TABLE ONLY public.sicard DROP CONSTRAINT pk_sicard;
ALTER TABLE ONLY public.runner DROP CONSTRAINT pk_runner;
ALTER TABLE ONLY public.run DROP CONSTRAINT pk_run;
ALTER TABLE ONLY public.punch DROP CONSTRAINT pk_punch;
ALTER TABLE ONLY public.coursecontrol DROP CONSTRAINT pk_coursecontrol;
ALTER TABLE ONLY public.course DROP CONSTRAINT pk_course;
ALTER TABLE ONLY public.controlsequence DROP CONSTRAINT pk_controlsequence;
ALTER TABLE ONLY public.control DROP CONSTRAINT pk_control;
ALTER TABLE ONLY public.category DROP CONSTRAINT pk_category;
ALTER TABLE public.team ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.runner ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.run ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.punch ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.coursecontrol ALTER COLUMN controlid DROP DEFAULT;
ALTER TABLE public.coursecontrol ALTER COLUMN courseid DROP DEFAULT;
ALTER TABLE public.course ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.controlsequence ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.control ALTER COLUMN id DROP DEFAULT;
ALTER TABLE public.category ALTER COLUMN id DROP DEFAULT;
DROP SEQUENCE public.team_id_seq;
DROP SEQUENCE public.runner_id_seq;
DROP SEQUENCE public.run_id_seq;
DROP SEQUENCE public.punch_id_seq;
DROP SEQUENCE public.coursecontrol_courseid_seq;
DROP SEQUENCE public.coursecontrol_controlid_seq;
DROP SEQUENCE public.course_id_seq;
DROP SEQUENCE public.controlsequence_id_seq;
DROP SEQUENCE public.control_id_seq;
DROP SEQUENCE public.category_id_seq;
DROP TABLE public.team;
DROP TABLE public.sistation;
DROP TABLE public.sicard;
DROP TABLE public.runner;
DROP TYPE public.sex;
DROP TABLE public.run;
DROP TABLE public.punch;
DROP TABLE public.coursecontrol;
DROP TABLE public.course;
DROP TABLE public.controlsequence;
DROP TABLE public.control;
DROP TABLE public.category;
DROP SCHEMA public;
--
-- Name: public; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA public;


ALTER SCHEMA public OWNER TO postgres;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA public IS 'standard public schema';


SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: category; Type: TABLE; Schema: public; Owner: gaudenz; Tablespace: 
--

CREATE TABLE category (
    id integer NOT NULL,
    name character varying(255) NOT NULL
);


ALTER TABLE public.category OWNER TO gaudenz;

--
-- Name: control; Type: TABLE; Schema: public; Owner: gaudenz; Tablespace: 
--

CREATE TABLE control (
    id integer NOT NULL,
    code character varying(255) NOT NULL,
    override boolean DEFAULT false
);


ALTER TABLE public.control OWNER TO gaudenz;

--
-- Name: controlsequence; Type: TABLE; Schema: public; Owner: gaudenz; Tablespace: 
--

CREATE TABLE controlsequence (
    id integer NOT NULL,
    course integer NOT NULL,
    control integer NOT NULL,
    sequence_number integer,
    length integer,
    climb integer
);


ALTER TABLE public.controlsequence OWNER TO gaudenz;

--
-- Name: course; Type: TABLE; Schema: public; Owner: gaudenz; Tablespace: 
--

CREATE TABLE course (
    id integer NOT NULL,
    code character varying(255) NOT NULL,
    length integer,
    climb integer
);


ALTER TABLE public.course OWNER TO gaudenz;

--
-- Name: coursecontrol; Type: TABLE; Schema: public; Owner: gaudenz; Tablespace: 
--

CREATE TABLE coursecontrol (
    courseid integer NOT NULL,
    controlid integer NOT NULL
);


ALTER TABLE public.coursecontrol OWNER TO gaudenz;

--
-- Name: punch; Type: TABLE; Schema: public; Owner: gaudenz; Tablespace: 
--

CREATE TABLE punch (
    id integer NOT NULL,
    run integer NOT NULL,
    sistation integer NOT NULL,
    card_punchtime timestamp without time zone,
    manual_punchtime timestamp without time zone,
    ignore boolean DEFAULT false,
    sequence integer
);


ALTER TABLE public.punch OWNER TO gaudenz;

--
-- Name: run; Type: TABLE; Schema: public; Owner: gaudenz; Tablespace: 
--

CREATE TABLE run (
    id integer NOT NULL,
    sicard integer NOT NULL,
    course integer,
    complete boolean DEFAULT false,
    override integer,
    readout_time timestamp without time zone
);


ALTER TABLE public.run OWNER TO gaudenz;

--
-- Name: sex; Type: TYPE; Schema: public; Owner: gaudenz
--

CREATE TYPE sex AS ENUM (
    'male',
    'female'
);


ALTER TYPE public.sex OWNER TO gaudenz;

--
-- Name: runner; Type: TABLE; Schema: public; Owner: gaudenz; Tablespace: 
--

CREATE TABLE runner (
    id integer NOT NULL,
    number character varying(255),
    given_name character varying(255) NOT NULL,
    surname character varying(255) NOT NULL,
    dateofbirth date,
    sex sex,
    nation integer,
    solvnr character varying(6),
    startblock integer,
    starttime timestamp without time zone,
    category integer,
    club integer,
    address1 character varying(255) DEFAULT NULL::character varying,
    address2 character varying(255),
    zipcode character varying(20) DEFAULT NULL::character varying,
    city character varying(255) DEFAULT NULL::character varying,
    address_country_id integer,
    email character varying(255) DEFAULT NULL::character varying,
    startfee integer,
    paid boolean,
    comment text,
    team integer
);


ALTER TABLE public.runner OWNER TO gaudenz;

--
-- Name: sicard; Type: TABLE; Schema: public; Owner: gaudenz; Tablespace: 
--

CREATE TABLE sicard (
    id integer NOT NULL,
    runner integer
);


ALTER TABLE public.sicard OWNER TO gaudenz;

--
-- Name: sistation; Type: TABLE; Schema: public; Owner: gaudenz; Tablespace: 
--

CREATE TABLE sistation (
    id integer NOT NULL,
    control integer
);


ALTER TABLE public.sistation OWNER TO gaudenz;

--
-- Name: team; Type: TABLE; Schema: public; Owner: gaudenz; Tablespace: 
--

CREATE TABLE team (
    id integer NOT NULL,
    number character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    official boolean DEFAULT true NOT NULL,
    responsible integer,
    category integer NOT NULL,
    override integer
);


ALTER TABLE public.team OWNER TO gaudenz;

--
-- Name: category_id_seq; Type: SEQUENCE; Schema: public; Owner: gaudenz
--

CREATE SEQUENCE category_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.category_id_seq OWNER TO gaudenz;

--
-- Name: category_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: gaudenz
--

ALTER SEQUENCE category_id_seq OWNED BY category.id;


--
-- Name: category_id_seq; Type: SEQUENCE SET; Schema: public; Owner: gaudenz
--

SELECT pg_catalog.setval('category_id_seq', 2, true);


--
-- Name: control_id_seq; Type: SEQUENCE; Schema: public; Owner: gaudenz
--

CREATE SEQUENCE control_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.control_id_seq OWNER TO gaudenz;

--
-- Name: control_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: gaudenz
--

ALTER SEQUENCE control_id_seq OWNED BY control.id;


--
-- Name: control_id_seq; Type: SEQUENCE SET; Schema: public; Owner: gaudenz
--

SELECT pg_catalog.setval('control_id_seq', 34, true);


--
-- Name: controlsequence_id_seq; Type: SEQUENCE; Schema: public; Owner: gaudenz
--

CREATE SEQUENCE controlsequence_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.controlsequence_id_seq OWNER TO gaudenz;

--
-- Name: controlsequence_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: gaudenz
--

ALTER SEQUENCE controlsequence_id_seq OWNED BY controlsequence.id;


--
-- Name: controlsequence_id_seq; Type: SEQUENCE SET; Schema: public; Owner: gaudenz
--

SELECT pg_catalog.setval('controlsequence_id_seq', 246, true);


--
-- Name: course_id_seq; Type: SEQUENCE; Schema: public; Owner: gaudenz
--

CREATE SEQUENCE course_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.course_id_seq OWNER TO gaudenz;

--
-- Name: course_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: gaudenz
--

ALTER SEQUENCE course_id_seq OWNED BY course.id;


--
-- Name: course_id_seq; Type: SEQUENCE SET; Schema: public; Owner: gaudenz
--

SELECT pg_catalog.setval('course_id_seq', 41, true);


--
-- Name: coursecontrol_controlid_seq; Type: SEQUENCE; Schema: public; Owner: gaudenz
--

CREATE SEQUENCE coursecontrol_controlid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.coursecontrol_controlid_seq OWNER TO gaudenz;

--
-- Name: coursecontrol_controlid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: gaudenz
--

ALTER SEQUENCE coursecontrol_controlid_seq OWNED BY coursecontrol.controlid;


--
-- Name: coursecontrol_controlid_seq; Type: SEQUENCE SET; Schema: public; Owner: gaudenz
--

SELECT pg_catalog.setval('coursecontrol_controlid_seq', 1, false);


--
-- Name: coursecontrol_courseid_seq; Type: SEQUENCE; Schema: public; Owner: gaudenz
--

CREATE SEQUENCE coursecontrol_courseid_seq
    START WITH 1
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.coursecontrol_courseid_seq OWNER TO gaudenz;

--
-- Name: coursecontrol_courseid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: gaudenz
--

ALTER SEQUENCE coursecontrol_courseid_seq OWNED BY coursecontrol.courseid;


--
-- Name: coursecontrol_courseid_seq; Type: SEQUENCE SET; Schema: public; Owner: gaudenz
--

SELECT pg_catalog.setval('coursecontrol_courseid_seq', 1, false);


--
-- Name: punch_id_seq; Type: SEQUENCE; Schema: public; Owner: gaudenz
--

CREATE SEQUENCE punch_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.punch_id_seq OWNER TO gaudenz;

--
-- Name: punch_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: gaudenz
--

ALTER SEQUENCE punch_id_seq OWNED BY punch.id;


--
-- Name: punch_id_seq; Type: SEQUENCE SET; Schema: public; Owner: gaudenz
--

SELECT pg_catalog.setval('punch_id_seq', 2482, true);


--
-- Name: run_id_seq; Type: SEQUENCE; Schema: public; Owner: gaudenz
--

CREATE SEQUENCE run_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.run_id_seq OWNER TO gaudenz;

--
-- Name: run_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: gaudenz
--

ALTER SEQUENCE run_id_seq OWNED BY run.id;


--
-- Name: run_id_seq; Type: SEQUENCE SET; Schema: public; Owner: gaudenz
--

SELECT pg_catalog.setval('run_id_seq', 327, true);


--
-- Name: runner_id_seq; Type: SEQUENCE; Schema: public; Owner: gaudenz
--

CREATE SEQUENCE runner_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.runner_id_seq OWNER TO gaudenz;

--
-- Name: runner_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: gaudenz
--

ALTER SEQUENCE runner_id_seq OWNED BY runner.id;


--
-- Name: runner_id_seq; Type: SEQUENCE SET; Schema: public; Owner: gaudenz
--

SELECT pg_catalog.setval('runner_id_seq', 49, true);


--
-- Name: team_id_seq; Type: SEQUENCE; Schema: public; Owner: gaudenz
--

CREATE SEQUENCE team_id_seq
    INCREMENT BY 1
    NO MAXVALUE
    NO MINVALUE
    CACHE 1;


ALTER TABLE public.team_id_seq OWNER TO gaudenz;

--
-- Name: team_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: gaudenz
--

ALTER SEQUENCE team_id_seq OWNED BY team.id;


--
-- Name: team_id_seq; Type: SEQUENCE SET; Schema: public; Owner: gaudenz
--

SELECT pg_catalog.setval('team_id_seq', 8, true);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: gaudenz
--

ALTER TABLE category ALTER COLUMN id SET DEFAULT nextval('category_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: gaudenz
--

ALTER TABLE control ALTER COLUMN id SET DEFAULT nextval('control_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: gaudenz
--

ALTER TABLE controlsequence ALTER COLUMN id SET DEFAULT nextval('controlsequence_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: gaudenz
--

ALTER TABLE course ALTER COLUMN id SET DEFAULT nextval('course_id_seq'::regclass);


--
-- Name: courseid; Type: DEFAULT; Schema: public; Owner: gaudenz
--

ALTER TABLE coursecontrol ALTER COLUMN courseid SET DEFAULT nextval('coursecontrol_courseid_seq'::regclass);


--
-- Name: controlid; Type: DEFAULT; Schema: public; Owner: gaudenz
--

ALTER TABLE coursecontrol ALTER COLUMN controlid SET DEFAULT nextval('coursecontrol_controlid_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: gaudenz
--

ALTER TABLE punch ALTER COLUMN id SET DEFAULT nextval('punch_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: gaudenz
--

ALTER TABLE run ALTER COLUMN id SET DEFAULT nextval('run_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: gaudenz
--

ALTER TABLE runner ALTER COLUMN id SET DEFAULT nextval('runner_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: gaudenz
--

ALTER TABLE team ALTER COLUMN id SET DEFAULT nextval('team_id_seq'::regclass);


--
-- Data for Name: category; Type: TABLE DATA; Schema: public; Owner: gaudenz
--

COPY category (id, name) FROM stdin;
1	24h
2	12h
\.


--
-- Data for Name: control; Type: TABLE DATA; Schema: public; Owner: gaudenz
--

COPY control (id, code, override) FROM stdin;
1	S1	f
2	Z1	f
3	131	f
4	132	f
5	133	f
6	134	f
7	135	f
8	136	f
10	138	f
11	139	f
12	140	f
13	141	f
14	142	f
15	143	f
16	144	f
17	145	f
18	146	f
19	147	f
20	148	f
21	149	f
22	150	f
23	151	f
24	152	f
25	153	f
26	154	f
27	155	f
28	156	f
29	157	f
30	158	f
31	159	f
32	160	f
33	199	f
34	200	f
9	137	t
\.


--
-- Data for Name: controlsequence; Type: TABLE DATA; Schema: public; Owner: gaudenz
--

COPY controlsequence (id, course, control, sequence_number, length, climb) FROM stdin;
1	1	3	1	296	0
2	1	4	2	207	0
3	1	5	3	192	0
4	1	6	4	152	0
5	1	7	5	199	0
6	1	33	6	307	0
7	2	4	1	420	0
8	2	5	2	192	0
9	2	6	3	152	0
10	2	7	4	199	0
11	2	8	5	139	0
12	2	34	6	256	0
13	3	5	1	529	0
14	3	6	2	152	0
15	3	7	3	199	0
16	3	8	4	139	0
17	3	9	5	150	0
18	3	33	6	370	0
19	4	6	1	504	0
20	4	7	2	199	0
21	4	8	3	139	0
22	4	9	4	150	0
23	4	10	5	224	0
24	4	34	6	349	0
25	5	7	1	527	0
26	5	8	2	139	0
27	5	9	3	150	0
28	5	10	4	224	0
29	5	11	5	123	0
30	5	33	6	439	0
31	6	8	1	535	0
32	6	9	2	150	0
33	6	10	3	224	0
34	6	11	4	123	0
35	6	12	5	179	0
36	6	34	6	401	0
37	7	10	1	531	0
38	7	11	2	123	0
39	7	12	3	179	0
40	7	13	4	194	0
41	7	14	5	339	0
42	7	33	6	600	0
43	8	9	1	547	0
44	8	10	2	224	0
45	8	11	3	123	0
46	8	12	4	179	0
47	8	13	5	194	0
48	8	33	6	530	0
49	9	11	1	480	0
50	9	12	2	179	0
51	9	13	3	194	0
52	9	14	4	339	0
53	9	15	5	213	0
54	9	34	6	694	0
55	10	12	1	397	0
56	10	13	2	194	0
57	10	14	3	339	0
58	10	15	4	213	0
59	10	16	5	188	0
60	10	34	6	772	0
61	11	13	1	397	0
62	11	14	2	339	0
63	11	15	3	213	0
64	11	16	4	188	0
65	11	17	5	137	0
66	11	34	6	717	0
67	12	14	1	383	0
68	12	15	2	213	0
69	12	16	3	188	0
70	12	17	4	137	0
71	12	18	5	152	0
72	12	34	6	594	0
73	13	15	1	415	0
74	13	16	2	188	0
75	13	17	3	137	0
76	13	18	4	152	0
77	13	19	5	231	0
78	13	33	6	518	0
79	14	16	1	506	0
80	14	17	2	137	0
81	14	18	3	152	0
82	14	19	4	231	0
83	14	20	5	295	0
84	14	33	6	502	0
85	15	17	1	474	0
86	15	18	2	152	0
87	15	19	3	231	0
88	15	20	4	295	0
89	15	21	5	230	0
90	15	33	6	463	0
91	16	22	1	660	0
92	16	23	2	232	0
93	16	19	3	855	0
94	16	26	4	1147	0
95	16	24	5	449	0
96	16	34	6	485	0
97	17	18	1	384	0
98	17	19	2	231	0
99	17	20	3	295	0
100	17	21	4	230	0
101	17	22	5	246	0
102	17	34	6	431	0
103	18	18	1	384	0
104	18	19	2	231	0
105	18	20	3	295	0
106	18	21	4	230	0
107	18	23	5	469	0
108	18	33	6	459	0
109	19	19	1	496	0
110	19	20	2	295	0
111	19	21	3	230	0
112	19	22	4	246	0
113	19	23	5	232	0
114	19	33	6	459	0
115	20	21	1	634	0
116	20	22	2	246	0
117	20	23	3	232	0
118	20	24	4	346	0
119	20	25	5	235	0
120	20	34	6	555	0
121	21	22	1	660	0
122	21	23	2	232	0
123	21	24	3	346	0
124	21	25	4	235	0
125	21	26	5	239	0
126	21	34	6	575	0
127	22	23	1	675	0
128	22	24	2	346	0
129	22	25	3	235	0
130	22	26	4	239	0
131	22	27	5	355	0
132	22	33	6	690	0
133	23	26	1	674	0
134	23	27	2	355	0
135	23	28	3	316	0
136	23	29	4	419	0
137	23	30	5	315	0
138	23	34	6	992	0
139	24	28	1	553	0
140	24	29	2	419	0
141	24	30	3	315	0
142	24	31	4	292	0
143	24	32	5	285	0
144	24	34	6	785	0
145	25	32	1	586	0
146	25	31	2	285	0
147	25	30	3	292	0
148	25	29	4	315	0
149	25	28	5	419	0
150	25	33	6	731	0
151	26	31	1	700	0
152	26	30	2	292	0
153	26	28	3	693	0
154	26	27	4	316	0
155	26	26	5	355	0
156	26	33	6	649	0
157	27	30	1	714	0
158	27	28	2	693	0
159	27	22	3	1166	0
160	27	19	4	696	0
161	27	12	5	889	0
162	27	34	6	401	0
163	28	29	1	665	0
164	28	26	2	1042	0
165	28	20	3	1145	0
166	28	14	4	925	0
167	28	7	5	905	0
168	28	33	6	307	0
169	29	28	1	553	0
170	29	24	2	996	0
171	29	17	3	1198	0
172	29	8	4	947	0
173	29	4	5	577	0
174	29	34	6	446	0
175	30	27	1	596	0
176	30	24	2	759	0
177	30	17	3	1198	0
178	30	10	4	1005	0
179	30	6	5	644	0
180	30	34	6	342	0
187	32	25	1	743	0
188	32	20	2	1099	0
189	32	18	3	500	0
190	32	17	4	152	0
191	32	16	5	137	0
192	32	34	6	772	0
193	33	30	1	714	0
194	33	24	2	1438	0
195	33	31	3	1431	0
196	33	25	4	1438	0
197	33	32	5	1318	0
198	33	33	6	693	0
199	34	20	1	600	0
200	34	19	2	295	0
201	34	18	3	231	0
202	34	17	4	152	0
203	34	15	5	283	0
204	34	33	6	629	0
205	35	12	1	397	0
206	35	25	2	453	0
207	35	21	3	960	0
208	35	11	4	849	0
209	35	24	5	389	0
210	35	34	6	485	0
211	36	3	1	296	0
212	36	5	2	390	0
213	36	7	3	351	0
214	36	9	4	287	0
215	36	11	5	329	0
216	36	33	6	439	0
217	37	13	1	397	0
218	37	17	2	750	0
219	37	25	3	1217	0
220	37	20	4	1099	0
221	37	21	5	230	0
222	37	33	6	463	0
223	38	9	1	547	0
224	38	3	2	728	0
225	38	28	3	792	0
226	38	32	4	945	0
227	38	19	5	267	0
228	38	34	6	609	0
229	39	20	1	600	0
230	39	27	2	1177	0
231	39	19	3	1089	0
232	39	26	4	1147	0
233	39	18	5	1057	0
234	39	33	6	503	0
235	40	25	1	743	0
236	40	18	2	1118	0
237	40	26	3	1057	0
238	40	19	4	1147	0
239	40	27	5	1089	0
240	40	34	6	655	0
241	41	31	1	700	0
242	41	23	2	1304	0
243	41	29	3	1332	0
244	41	22	4	1322	0
245	41	30	5	1317	0
246	41	33	6	922	0
\.


--
-- Data for Name: course; Type: TABLE DATA; Schema: public; Owner: gaudenz
--

COPY course (id, code, length, climb) FROM stdin;
1	SF1	1450	0
2	SF2	1450	0
3	SF3	1640	0
4	SF4	1660	0
5	SE1	1700	0
6	SE2	1700	0
7	SE3	2060	0
8	SE4	1900	0
9	LDN1	2190	0
10	LDN2	2190	0
11	LDN3	2080	0
12	LEN1	1760	0
13	LEN2	1740	0
14	LEN3	1920	0
15	LEN4	1940	0
16	SDN1	3920	0
17	SDN2	1910	0
18	SDN3	2170	0
19	SDN4	2060	0
20	SEN1	2340	0
21	SEN2	2380	0
22	SEN3	2640	0
23	SEN4	3160	0
24	SEN5	2740	0
25	LD1	2730	0
26	LD2	3110	0
27	LD3	4650	0
28	LD4	5090	0
29	LE1	4810	0
30	LE2	4630	0
32	SD1	3490	0
33	SD2	7130	0
34	SD3	2290	0
35	SD4	3620	0
36	FF1	2190	0
37	FF2	4260	0
38	FF3	3980	0
39	FF4	5670	0
40	FF5	5900	0
41	FF6	7000	0
\.


--
-- Data for Name: coursecontrol; Type: TABLE DATA; Schema: public; Owner: gaudenz
--

COPY coursecontrol (courseid, controlid) FROM stdin;
\.


--
-- Data for Name: punch; Type: TABLE DATA; Schema: public; Owner: gaudenz
--

COPY punch (id, run, sistation, card_punchtime, manual_punchtime, ignore, sequence) FROM stdin;
399	50	2	2008-04-30 22:59:35	\N	f	\N
400	50	4	2008-04-30 16:56:23	\N	f	\N
229	33	2	2008-04-30 22:03:34	\N	f	\N
230	33	4	2008-04-30 16:57:45	\N	f	\N
351	47	2	2008-04-30 15:40:21	2008-04-30 22:58:55	f	\N
2470	155	1	\N	2008-04-30 23:30:00	f	\N
2471	83	157	\N	2008-04-30 23:10:45	f	\N
2472	73	31	2008-04-30 23:05:30	\N	f	6
237	34	2	2008-04-30 22:11:29	\N	f	\N
238	34	4	2008-04-30 16:58:03	\N	f	\N
245	35	2	2008-04-30 22:03:26	\N	f	\N
246	35	4	2008-04-30 16:59:39	\N	f	\N
253	36	2	2008-04-30 22:06:50	\N	f	\N
254	36	4	2008-04-30 16:55:52	\N	f	\N
261	37	2	2008-04-30 22:13:41	\N	f	\N
262	37	4	2008-04-30 16:56:30	\N	f	\N
269	38	2	2008-04-30 22:04:19	\N	f	\N
270	38	4	2008-04-30 16:58:41	\N	f	\N
277	39	2	2008-04-30 22:12:01	\N	f	\N
278	39	4	2008-04-30 16:56:59	\N	f	\N
285	40	2	2008-04-30 22:12:21	\N	f	\N
286	40	4	2008-04-30 16:57:18	\N	f	\N
293	41	2	2008-04-30 22:03:28	\N	f	\N
294	41	4	2008-04-30 16:56:33	\N	f	\N
301	42	2	2008-04-30 22:06:45	\N	f	\N
302	42	4	2008-04-30 16:56:45	\N	f	\N
309	43	2	2008-04-30 22:49:03	\N	f	\N
310	43	4	2008-04-30 16:56:30	\N	f	\N
317	44	2	2008-04-30 22:57:37	\N	f	\N
318	44	4	2008-04-30 16:57:32	\N	f	\N
326	45	4	2008-04-30 16:56:22	\N	f	\N
447	56	2	2008-04-30 23:01:20	\N	f	\N
448	56	4	2008-04-30 16:56:05	\N	f	\N
455	57	2	2008-04-30 23:02:08	\N	f	\N
456	57	4	2008-04-30 16:56:59	\N	f	\N
463	58	2	2008-04-30 23:02:34	\N	f	\N
352	47	4	2008-04-30 14:43:00	\N	f	\N
401	50	134	2008-04-30 22:59:08	\N	f	1
402	50	135	2008-04-30 22:59:13	\N	f	2
403	50	136	2008-04-30 22:59:15	\N	f	3
404	50	137	2008-04-30 22:59:20	\N	f	4
464	58	4	2008-04-30 16:58:36	\N	f	\N
471	59	2	2008-04-30 23:02:36	\N	f	\N
472	59	4	2008-04-30 16:58:09	\N	f	\N
384	49	2	2008-04-30 22:59:12	\N	f	\N
385	49	4	2008-04-30 14:15:32	\N	f	\N
407	51	2	2008-04-30 22:59:57	\N	f	\N
408	51	4	2008-04-30 16:55:56	\N	f	\N
664	84	2	2008-04-30 23:12:10	\N	f	\N
665	84	4	2008-04-30 16:59:03	\N	f	\N
519	66	2	2008-04-30 23:02:49	\N	f	\N
520	66	4	2008-04-30 16:58:09	\N	f	\N
431	54	2	2008-04-30 23:00:42	\N	f	\N
432	54	4	2008-04-30 16:57:13	\N	f	\N
439	55	2	2008-04-30 23:00:44	\N	f	\N
440	55	4	2008-04-30 16:56:23	\N	f	\N
573	73	2	2008-04-30 23:05:56	\N	f	\N
574	73	4	2008-04-30 16:56:03	\N	f	\N
580	74	2	2008-04-30 23:06:41	\N	f	\N
581	74	4	2008-04-30 16:57:27	\N	f	\N
503	64	2	2008-04-30 23:04:53	\N	f	\N
504	64	4	2008-04-30 16:59:17	\N	f	\N
512	65	4	2008-04-30 16:58:46	\N	f	\N
527	67	2	2008-04-30 23:03:56	\N	f	\N
528	67	4	2008-04-30 16:58:33	\N	f	\N
535	68	2	2008-04-30 23:04:25	\N	f	\N
536	68	4	2008-04-30 16:58:04	\N	f	\N
588	75	2	2008-04-30 23:06:49	\N	f	\N
589	75	4	2008-04-30 16:56:57	\N	f	\N
551	70	2	2008-04-30 23:05:25	\N	f	\N
552	70	4	2008-04-30 16:58:02	\N	f	\N
465	58	132	2008-04-30 23:01:59	\N	f	1
466	58	133	2008-04-30 23:02:03	\N	f	2
467	58	134	2008-04-30 23:02:06	\N	f	3
468	58	135	2008-04-30 23:02:09	\N	f	4
469	58	136	2008-04-30 23:02:13	\N	f	5
470	58	35	2008-04-30 23:02:27	\N	f	6
473	59	143	2008-04-30 23:02:09	\N	f	1
474	59	144	2008-04-30 23:02:14	\N	f	2
475	59	145	2008-04-30 23:02:19	\N	f	3
596	76	2	2008-04-30 23:08:08	\N	f	\N
597	76	4	2008-04-30 16:58:52	\N	f	\N
672	85	2	2008-04-30 23:12:13	\N	f	\N
673	85	4	2008-04-30 16:59:13	\N	f	\N
609	78	2	2008-04-30 23:08:23	\N	f	\N
610	78	4	2008-04-30 16:58:52	\N	f	\N
617	79	2	2008-04-30 23:08:32	\N	f	\N
618	79	4	2008-04-30 16:58:02	\N	f	\N
625	80	2	2008-04-30 23:10:37	\N	f	\N
626	80	4	2008-04-30 16:59:21	\N	f	\N
633	81	2	2008-04-30 23:10:41	\N	f	\N
634	81	4	2008-04-30 16:57:41	\N	f	\N
641	82	2	2008-04-30 23:11:09	\N	f	\N
642	82	4	2008-04-30 16:59:08	\N	f	\N
649	83	2	2008-04-30 23:11:12	\N	f	\N
650	83	4	2008-04-30 13:26:23	\N	f	\N
677	86	2	2008-04-30 23:12:12	\N	f	\N
678	86	4	2008-04-30 16:55:55	\N	f	\N
685	87	2	2008-04-30 23:12:19	\N	f	\N
686	87	4	2008-04-30 16:59:09	\N	f	\N
693	88	2	2008-04-30 23:12:32	\N	f	\N
694	88	4	2008-04-30 16:56:52	\N	f	\N
701	89	2	2008-04-30 23:12:33	\N	f	\N
702	89	4	2008-04-30 16:56:53	\N	f	\N
710	90	4	2008-04-30 16:55:32	\N	f	\N
797	101	2	2008-04-30 23:15:37	\N	f	\N
798	101	4	2008-04-30 16:58:45	\N	f	\N
734	93	4	2008-04-30 16:58:08	\N	f	\N
742	94	4	2008-04-30 16:58:56	\N	f	\N
749	95	2	2008-04-30 23:14:30	\N	f	\N
750	95	4	2008-04-30 16:58:52	\N	f	\N
757	96	2	2008-04-30 23:14:32	\N	f	\N
758	96	4	2008-04-30 16:55:35	\N	f	\N
765	97	2	2008-04-30 23:14:34	\N	f	\N
766	97	4	2008-04-30 16:57:49	\N	f	\N
773	98	2	2008-04-30 23:14:49	\N	f	\N
774	98	4	2008-04-30 16:57:48	\N	f	\N
781	99	2	2008-04-30 23:15:14	\N	f	\N
782	99	4	2008-04-30 16:59:16	\N	f	\N
805	102	2	2008-04-30 23:15:47	\N	f	\N
806	102	4	2008-04-30 16:59:12	\N	f	\N
813	103	2	2008-04-30 23:15:53	\N	f	\N
814	103	4	2008-04-30 16:57:09	\N	f	\N
1239	156	2	2008-04-30 23:31:47	\N	f	\N
1240	156	4	2008-04-30 16:57:32	\N	f	\N
829	105	2	2008-04-30 23:15:54	\N	f	\N
830	105	4	2008-04-30 16:56:57	\N	f	\N
837	106	2	2008-04-30 23:16:11	\N	f	\N
838	106	4	2008-04-30 16:56:59	\N	f	\N
845	107	2	2008-04-30 23:16:13	\N	f	\N
846	107	4	2008-04-30 16:58:14	\N	f	\N
853	108	2	2008-04-30 23:16:16	\N	f	\N
854	108	4	2008-04-30 16:56:44	\N	f	\N
861	109	2	2008-04-30 23:17:05	\N	f	\N
862	109	4	2008-04-30 16:57:12	\N	f	\N
1164	147	2	2008-04-30 23:22:12	\N	f	\N
1165	147	4	2008-04-30 14:21:23	\N	f	\N
877	111	2	2008-04-30 23:19:24	\N	f	\N
878	111	4	2008-04-30 16:55:28	\N	f	\N
885	112	2	2008-04-30 23:19:29	\N	f	\N
886	112	4	2008-04-30 16:55:59	\N	f	\N
893	113	2	2008-04-30 23:19:34	\N	f	\N
894	113	4	2008-04-30 16:55:57	\N	f	\N
901	114	2	2008-04-30 23:19:35	\N	f	\N
902	114	4	2008-04-30 16:59:42	\N	f	\N
909	115	2	2008-04-30 23:19:37	\N	f	\N
910	115	4	2008-04-30 16:58:19	\N	f	\N
917	116	2	2008-04-30 23:20:49	\N	f	\N
918	116	4	2008-04-30 16:57:38	\N	f	\N
925	117	2	2008-04-30 23:21:00	\N	f	\N
926	117	4	2008-04-30 16:56:03	\N	f	\N
933	118	2	2008-04-30 23:21:04	\N	f	\N
934	118	4	2008-04-30 16:56:27	\N	f	\N
944	120	2	2008-04-30 23:21:25	\N	f	\N
945	120	4	2008-04-30 16:57:53	\N	f	\N
952	121	2	2008-04-30 23:21:28	\N	f	\N
953	121	4	2008-04-30 16:58:09	\N	f	\N
960	122	2	2008-04-30 23:21:51	\N	f	\N
961	122	4	2008-04-30 16:57:30	\N	f	\N
1175	148	2	2008-04-30 23:25:31	\N	f	\N
1176	148	4	2008-04-30 16:57:30	\N	f	\N
1183	149	2	2008-04-30 23:25:36	\N	f	\N
1184	149	4	2008-04-30 16:58:26	\N	f	\N
976	124	2	2008-04-30 23:22:11	\N	f	\N
977	124	4	2008-04-30 16:55:39	\N	f	\N
984	125	2	2008-04-30 23:22:10	\N	f	\N
985	125	4	2008-04-30 16:56:33	\N	f	\N
992	126	2	2008-04-30 23:21:52	\N	f	\N
993	126	4	2008-04-30 16:59:43	\N	f	\N
1000	127	2	2008-04-30 23:22:33	\N	f	\N
1001	127	4	2008-04-30 16:59:30	\N	f	\N
1008	128	2	2008-04-30 23:22:46	\N	f	\N
1009	128	4	2008-04-30 16:59:07	\N	f	\N
1016	129	2	2008-04-30 23:22:57	\N	f	\N
1017	129	4	2008-04-30 16:55:45	\N	f	\N
1024	130	2	2008-04-30 23:24:00	\N	f	\N
1025	130	4	2008-04-30 16:57:00	\N	f	\N
1032	131	2	2008-04-30 23:24:09	\N	f	\N
1033	131	4	2008-04-30 16:56:05	\N	f	\N
1040	132	2	2008-04-30 23:24:10	\N	f	\N
1041	132	4	2008-04-30 16:55:53	\N	f	\N
1048	133	2	2008-04-30 23:24:21	\N	f	\N
1049	133	4	2008-04-30 16:57:47	\N	f	\N
1056	134	2	2008-04-30 23:24:15	\N	f	\N
1057	134	4	2008-04-30 16:57:51	\N	f	\N
1064	135	2	2008-04-30 23:24:38	\N	f	\N
1065	135	4	2008-04-30 16:56:59	\N	f	\N
1072	136	2	2008-04-30 23:24:50	\N	f	\N
1073	136	4	2008-04-30 16:58:58	\N	f	\N
1080	137	2	2008-04-30 23:24:56	\N	f	\N
1081	137	4	2008-04-30 16:55:59	\N	f	\N
1199	151	2	2008-04-30 23:26:11	\N	f	\N
1200	151	4	2008-04-30 16:59:41	\N	f	\N
1207	152	2	2008-04-30 23:27:48	\N	f	\N
1208	152	4	2008-04-30 16:58:38	\N	f	\N
1120	142	2	2008-04-30 23:24:58	\N	f	\N
1121	142	4	2008-04-30 16:56:26	\N	f	\N
1128	143	2	2008-04-30 23:25:00	\N	f	\N
1129	143	4	2008-04-30 16:58:33	\N	f	\N
1136	144	2	2008-04-30 23:25:13	\N	f	\N
1137	144	4	2008-04-30 16:58:30	\N	f	\N
1215	153	2	2008-04-30 23:27:53	\N	f	\N
1216	153	4	2008-04-30 16:57:32	\N	f	\N
1156	146	2	2008-04-30 23:25:17	\N	f	\N
1157	146	4	2008-04-30 16:58:12	\N	f	\N
1223	154	2	2008-04-30 23:27:57	\N	f	\N
1224	154	4	2008-04-30 16:59:19	\N	f	\N
1231	155	2	2008-04-30 23:30:56	\N	f	\N
1232	155	4	2008-04-30 16:58:23	\N	f	\N
1247	157	2	2008-04-30 23:31:53	\N	f	\N
1248	157	4	2008-04-30 16:58:21	\N	f	\N
1255	158	2	2008-04-30 23:32:32	\N	f	\N
1256	158	4	2008-04-30 16:57:23	\N	f	\N
1263	159	2	2008-04-30 23:33:13	\N	f	\N
1264	159	4	2008-04-30 16:55:31	\N	f	\N
1271	160	2	2008-04-30 23:33:23	\N	f	\N
1272	160	4	2008-04-30 16:58:10	\N	f	\N
1279	161	2	2008-04-30 23:33:31	\N	f	\N
1280	161	4	2008-04-30 16:55:45	\N	f	\N
1287	162	2	2008-04-30 23:33:32	\N	f	\N
1288	162	4	2008-04-30 16:57:14	\N	f	\N
1295	163	2	2008-04-30 23:33:41	\N	f	\N
1296	163	4	2008-04-30 16:57:56	\N	f	\N
1303	164	2	2008-04-30 23:33:43	\N	f	\N
1304	164	4	2008-04-30 16:58:47	\N	f	\N
1311	165	2	2008-04-30 23:34:06	\N	f	\N
1312	165	4	2008-04-30 16:56:34	\N	f	\N
1327	167	2	2008-04-30 23:34:09	\N	f	\N
1328	167	4	2008-04-30 16:58:22	\N	f	\N
1335	168	2	2008-04-30 23:34:14	\N	f	\N
1336	168	4	2008-04-30 16:59:19	\N	f	\N
1343	169	2	2008-04-30 23:34:20	\N	f	\N
1344	169	4	2008-04-30 16:59:15	\N	f	\N
1350	170	2	2008-04-30 23:34:29	\N	f	\N
1351	170	4	2008-04-30 16:56:26	\N	f	\N
1358	171	2	2008-04-30 23:34:24	\N	f	\N
1359	171	4	2008-04-30 16:58:06	\N	f	\N
1366	172	2	2008-04-30 23:34:39	\N	f	\N
1367	172	4	2008-04-30 16:56:15	\N	f	\N
1372	173	2	2008-04-30 23:34:33	\N	f	\N
1373	173	4	2008-04-30 16:58:36	\N	f	\N
1380	174	2	2008-04-30 23:35:02	\N	f	\N
1381	174	4	2008-04-30 16:57:16	\N	f	\N
1388	175	2	2008-04-30 23:35:12	\N	f	\N
1389	175	4	2008-04-30 16:58:10	\N	f	\N
1396	176	2	2008-04-30 23:35:42	\N	f	\N
1397	176	4	2008-04-30 16:59:16	\N	f	\N
1404	177	2	2008-04-30 23:35:53	\N	f	\N
1405	177	4	2008-04-30 16:56:25	\N	f	\N
1412	178	2	2008-04-30 23:36:15	\N	f	\N
1413	178	4	2008-04-30 16:58:21	\N	f	\N
1420	179	2	2008-04-30 23:36:28	\N	f	\N
1421	179	4	2008-04-30 16:56:47	\N	f	\N
1428	180	2	2008-04-30 23:36:36	\N	f	\N
1429	180	4	2008-04-30 16:56:56	\N	f	\N
1436	181	2	2008-04-30 23:36:42	\N	f	\N
1437	181	4	2008-04-30 16:57:06	\N	f	\N
1444	182	2	2008-04-30 23:36:43	\N	f	\N
1445	182	4	2008-04-30 16:57:35	\N	f	\N
1452	183	2	2008-04-30 23:36:47	\N	f	\N
1453	183	4	2008-04-30 16:59:06	\N	f	\N
1460	184	2	2008-04-30 23:37:02	\N	f	\N
1461	184	4	2008-04-30 16:57:05	\N	f	\N
1468	185	2	2008-04-30 23:37:05	\N	f	\N
1469	185	4	2008-04-30 16:55:56	\N	f	\N
1476	186	2	2008-04-30 23:37:06	\N	f	\N
1477	186	4	2008-04-30 16:56:15	\N	f	\N
1484	187	2	2008-04-30 23:37:18	\N	f	\N
1485	187	4	2008-04-30 16:59:32	\N	f	\N
1492	188	2	2008-04-30 23:37:25	\N	f	\N
1493	188	4	2008-04-30 16:55:28	\N	f	\N
1500	189	2	2008-04-30 23:37:41	\N	f	\N
1501	189	4	2008-04-30 16:59:06	\N	f	\N
1516	191	2	2008-04-30 23:37:45	\N	f	\N
1517	191	4	2008-04-30 16:57:09	\N	f	\N
1524	192	2	2008-04-30 23:37:50	\N	f	\N
1525	192	4	2008-04-30 16:56:35	\N	f	\N
1532	193	2	2008-04-30 23:38:06	\N	f	\N
1533	193	4	2008-04-30 16:56:17	\N	f	\N
1540	194	2	2008-04-30 23:38:08	\N	f	\N
1541	194	4	2008-04-30 16:58:00	\N	f	\N
1548	195	2	2008-04-30 23:38:12	\N	f	\N
1549	195	4	2008-04-30 16:55:51	\N	f	\N
1556	196	2	2008-04-30 23:38:14	\N	f	\N
1557	196	4	2008-04-30 16:57:05	\N	f	\N
1564	197	2	2008-04-30 23:38:23	\N	f	\N
1565	197	4	2008-04-30 16:57:47	\N	f	\N
1572	198	2	2008-04-30 23:39:33	\N	f	\N
1573	198	4	2008-04-30 16:58:33	\N	f	\N
1580	199	2	2008-04-30 23:40:24	\N	f	\N
1581	199	4	2008-04-30 16:59:15	\N	f	\N
1588	200	2	2008-04-30 23:37:47	\N	f	\N
1589	200	4	2008-04-30 16:59:18	\N	f	\N
1596	201	2	2008-04-30 23:40:30	\N	f	\N
1597	201	4	2008-04-30 16:55:45	\N	f	\N
1604	202	2	2008-04-30 23:40:32	\N	f	\N
1605	202	4	2008-04-30 16:58:19	\N	f	\N
1620	204	2	2008-04-30 23:40:51	\N	f	\N
1621	204	4	2008-04-30 16:58:23	\N	f	\N
1628	205	2	2008-04-30 23:41:34	\N	f	\N
1629	205	4	2008-04-30 16:55:42	\N	f	\N
1636	206	2	2008-04-30 23:41:54	\N	f	\N
1637	206	4	2008-04-30 16:58:59	\N	f	\N
1644	207	2	2008-04-30 23:42:00	\N	f	\N
1645	207	4	2008-04-30 16:56:20	\N	f	\N
1652	208	2	2008-04-30 23:42:07	\N	f	\N
1653	208	4	2008-04-30 16:58:42	\N	f	\N
1660	209	2	2008-04-30 23:42:16	\N	f	\N
1661	209	4	2008-04-30 16:58:12	\N	f	\N
1668	210	2	2008-04-30 23:42:13	\N	f	\N
1669	210	4	2008-04-30 16:59:16	\N	f	\N
1676	211	2	2008-04-30 23:42:32	\N	f	\N
1677	211	4	2008-04-30 16:58:14	\N	f	\N
1684	212	2	2008-04-30 23:43:19	\N	f	\N
1685	212	4	2008-04-30 16:57:13	\N	f	\N
1692	213	2	2008-04-30 23:43:41	\N	f	\N
1693	213	4	2008-04-30 16:56:26	\N	f	\N
1702	215	2	2008-04-30 23:44:35	\N	f	\N
1703	215	4	2008-04-30 16:56:15	\N	f	\N
1710	216	2	2008-04-30 23:44:37	\N	f	\N
1711	216	4	2008-04-30 16:56:28	\N	f	\N
1718	217	2	2008-04-30 23:45:02	\N	f	\N
1719	217	4	2008-04-30 16:55:32	\N	f	\N
1726	218	2	2008-04-30 23:45:07	\N	f	\N
1727	218	4	2008-04-30 16:58:01	\N	f	\N
1734	219	2	2008-04-30 23:45:31	\N	f	\N
1735	219	4	2008-04-30 16:59:41	\N	f	\N
1750	221	2	2008-04-30 23:45:41	\N	f	\N
1751	221	4	2008-04-30 16:56:38	\N	f	\N
1766	223	2	2008-04-30 23:45:45	\N	f	\N
1767	223	4	2008-04-30 16:56:21	\N	f	\N
1774	224	2	2008-04-30 23:45:47	\N	f	\N
1775	224	4	2008-04-30 16:56:21	\N	f	\N
1782	225	2	2008-04-30 23:46:12	\N	f	\N
1783	225	4	2008-04-30 16:58:43	\N	f	\N
1790	226	2	2008-04-30 23:46:27	\N	f	\N
1791	226	4	2008-04-30 16:57:41	\N	f	\N
1798	227	2	2008-04-30 23:46:44	\N	f	\N
1799	227	4	2008-04-30 16:58:30	\N	f	\N
1806	228	2	2008-04-30 23:46:58	\N	f	\N
1807	228	4	2008-04-30 16:57:27	\N	f	\N
1814	229	2	2008-04-30 23:47:44	\N	f	\N
1815	229	4	2008-04-30 16:56:35	\N	f	\N
1822	230	2	2008-04-30 23:47:57	\N	f	\N
1823	230	4	2008-04-30 16:57:28	\N	f	\N
1830	231	2	2008-04-30 23:48:02	\N	f	\N
1831	231	4	2008-04-30 16:57:42	\N	f	\N
1838	232	2	2008-04-30 23:48:08	\N	f	\N
1839	232	4	2008-04-30 16:56:57	\N	f	\N
1846	233	2	2008-04-30 23:48:22	\N	f	\N
1847	233	4	2008-04-30 16:59:25	\N	f	\N
1854	234	2	2008-04-30 23:48:38	\N	f	\N
1855	234	4	2008-04-30 16:55:40	\N	f	\N
1862	235	2	2008-04-30 23:48:42	\N	f	\N
1863	235	4	2008-04-30 16:56:51	\N	f	\N
1870	236	2	2008-04-30 23:48:44	\N	f	\N
1871	236	4	2008-04-30 16:56:12	\N	f	\N
1878	237	2	2008-04-30 23:48:48	\N	f	\N
1879	237	4	2008-04-30 16:57:06	\N	f	\N
1886	238	2	2008-04-30 23:48:52	\N	f	\N
1887	238	4	2008-04-30 16:59:03	\N	f	\N
1894	239	2	2008-04-30 23:49:02	\N	f	\N
1895	239	4	2008-04-30 16:59:06	\N	f	\N
1902	240	2	2008-04-30 23:49:10	\N	f	\N
1903	240	4	2008-04-30 16:56:55	\N	f	\N
1910	241	2	2008-04-30 23:49:13	\N	f	\N
1911	241	4	2008-04-30 16:57:54	\N	f	\N
1918	242	2	2008-04-30 23:49:28	\N	f	\N
1919	242	4	2008-04-30 16:58:25	\N	f	\N
1926	243	2	2008-04-30 23:49:47	\N	f	\N
1927	243	4	2008-04-30 16:59:03	\N	f	\N
1934	244	2	2008-04-30 23:49:50	\N	f	\N
1943	245	2	2008-04-30 23:49:55	\N	f	\N
1944	245	4	2008-04-30 16:55:55	\N	f	\N
1951	246	2	2008-04-30 23:49:58	\N	f	\N
1952	246	4	2008-04-30 16:55:33	\N	f	\N
1959	247	2	2008-04-30 23:50:00	\N	f	\N
1960	247	4	2008-04-30 16:55:58	\N	f	\N
1967	248	2	2008-04-30 23:50:10	\N	f	\N
1968	248	4	2008-04-30 16:56:10	\N	f	\N
1975	249	2	2008-04-30 23:50:18	\N	f	\N
1976	249	4	2008-04-30 16:57:53	\N	f	\N
1983	250	2	2008-04-30 23:50:42	\N	f	\N
1984	250	4	2008-04-30 16:59:09	\N	f	\N
1991	251	2	2008-04-30 23:51:04	\N	f	\N
1992	251	4	2008-04-30 16:55:58	\N	f	\N
2005	252	2	2008-04-30 23:51:12	\N	f	\N
2006	252	4	2008-04-30 16:58:13	\N	f	\N
2013	253	2	2008-04-30 23:51:14	\N	f	\N
2014	253	4	2008-04-30 16:57:02	\N	f	\N
2021	254	2	2008-04-30 23:51:26	\N	f	\N
2022	254	4	2008-04-30 16:56:58	\N	f	\N
2029	255	2	2008-04-30 23:51:27	\N	f	\N
2030	255	4	2008-04-30 16:56:58	\N	f	\N
2037	256	2	2008-04-30 23:51:39	\N	f	\N
2038	256	4	2008-04-30 16:56:33	\N	f	\N
2045	257	2	2008-04-30 23:52:03	\N	f	\N
2046	257	4	2008-04-30 16:56:49	\N	f	\N
2053	258	2	2008-04-30 23:52:08	\N	f	\N
2054	258	4	2008-04-30 16:56:04	\N	f	\N
2061	259	2	2008-04-30 23:52:11	\N	f	\N
2062	259	4	2008-04-30 16:59:21	\N	f	\N
2069	260	2	2008-04-30 23:52:16	\N	f	\N
2070	260	4	2008-04-30 16:58:17	\N	f	\N
2083	262	2	2008-04-30 23:52:35	\N	f	\N
2084	262	4	2008-04-30 16:59:15	\N	f	\N
2091	263	2	2008-04-30 23:52:43	\N	f	\N
2092	263	4	2008-04-30 16:57:54	\N	f	\N
2099	264	2	2008-04-30 23:52:47	\N	f	\N
2100	264	4	2008-04-30 16:55:51	\N	f	\N
2107	265	2	2008-04-30 23:52:49	\N	f	\N
2108	265	4	2008-04-30 16:55:46	\N	f	\N
2123	267	2	2008-04-30 23:52:50	\N	f	\N
2124	267	4	2008-04-30 16:57:42	\N	f	\N
2147	270	2	2008-04-30 23:53:02	\N	f	\N
2148	270	4	2008-04-30 16:57:27	\N	f	\N
2155	271	2	2008-04-30 23:53:30	\N	f	\N
2156	271	4	2008-04-30 16:56:46	\N	f	\N
2163	272	2	2008-04-30 23:53:42	\N	f	\N
2164	272	4	2008-04-30 16:57:49	\N	f	\N
2171	273	2	2008-04-30 23:53:43	\N	f	\N
2172	273	4	2008-04-30 16:59:14	\N	f	\N
2179	274	2	2008-04-30 23:53:49	\N	f	\N
2180	274	4	2008-04-30 16:57:47	\N	f	\N
2187	275	2	2008-04-30 23:53:51	\N	f	\N
2188	275	4	2008-04-30 16:56:55	\N	f	\N
2195	276	2	2008-04-30 23:53:54	\N	f	\N
2196	276	4	2008-04-30 16:59:21	\N	f	\N
2203	277	2	2008-04-30 23:54:41	\N	f	\N
2204	277	4	2008-04-30 16:57:19	\N	f	\N
2225	279	2	2008-04-30 23:55:05	\N	f	\N
2226	279	4	2008-04-30 16:59:03	\N	f	\N
2233	280	2	2008-04-30 23:55:23	\N	f	\N
2234	280	4	2008-04-30 16:58:06	\N	f	\N
2241	281	2	2008-04-30 23:55:33	\N	f	\N
2242	281	4	2008-04-30 16:57:48	\N	f	\N
2249	282	2	2008-04-30 23:55:39	\N	f	\N
2250	282	4	2008-04-30 16:56:22	\N	f	\N
2257	283	2	2008-04-30 23:55:50	\N	f	\N
2258	283	4	2008-04-30 16:59:00	\N	f	\N
2265	284	2	2008-04-30 23:56:03	\N	f	\N
2266	284	4	2008-04-30 16:58:27	\N	f	\N
2273	285	2	2008-04-30 23:56:18	\N	f	\N
2274	285	4	2008-04-30 16:56:33	\N	f	\N
2281	286	2	2008-04-30 23:56:27	\N	f	\N
2282	286	4	2008-04-30 16:55:58	\N	f	\N
2289	287	2	2008-04-30 23:56:33	\N	f	\N
2290	287	4	2008-04-30 16:56:06	\N	f	\N
2297	288	2	2008-04-30 23:56:55	\N	f	\N
2298	288	4	2008-04-30 16:57:39	\N	f	\N
2305	289	2	2008-04-30 23:57:05	\N	f	\N
2306	289	4	2008-04-30 16:59:38	\N	f	\N
2313	290	2	2008-04-30 23:57:27	\N	f	\N
2314	290	4	2008-04-30 16:58:05	\N	f	\N
2321	291	2	2008-04-30 23:56:51	\N	f	\N
2322	291	4	2008-04-30 16:59:07	\N	f	\N
2329	292	2	2008-04-30 23:57:10	\N	f	\N
2330	292	4	2008-04-30 16:56:27	\N	f	\N
2337	293	2	2008-04-30 23:57:39	\N	f	\N
2338	293	4	2008-04-30 16:57:50	\N	f	\N
2345	294	2	2008-04-30 23:57:41	\N	f	\N
2346	294	4	2008-04-30 16:56:17	\N	f	\N
2365	297	2	2008-04-30 23:58:10	\N	f	\N
2366	297	4	2008-05-01 04:57:49	\N	f	\N
2373	298	2	2008-04-30 23:58:31	\N	f	\N
2374	298	4	2008-05-01 04:57:11	\N	f	\N
2381	299	2	2008-04-30 23:58:33	\N	f	\N
2382	299	4	2008-05-01 04:57:41	\N	f	\N
2389	300	2	2008-04-30 23:58:34	\N	f	\N
2390	300	4	2008-05-01 04:58:41	\N	f	\N
2397	301	2	2008-04-30 23:59:08	\N	f	\N
2398	301	4	2008-05-01 04:55:47	\N	f	\N
2405	302	2	2008-04-30 23:59:21	\N	f	\N
2406	302	4	2008-05-01 04:56:05	\N	f	\N
2413	303	2	2008-04-30 23:59:48	\N	f	\N
2414	303	4	2008-05-01 04:58:38	\N	f	\N
2421	304	2	2008-04-30 23:59:55	\N	f	\N
2422	304	4	2008-05-01 04:58:05	\N	f	\N
2429	305	2	2008-04-30 23:59:57	\N	f	\N
2430	305	4	2008-05-01 04:58:46	\N	f	\N
2437	306	2	2008-05-01 00:00:33	\N	f	\N
2438	306	4	2008-05-01 04:58:19	\N	f	\N
2451	308	2	2008-05-01 00:00:53	\N	f	\N
2452	308	4	2008-05-01 04:56:55	\N	f	\N
446	55	141	\N	2008-04-30 23:00:32	f	3
2459	309	2	2008-05-01 00:00:54	\N	f	\N
2460	309	4	2008-05-01 04:58:18	\N	f	\N
325	45	2	2008-04-30 22:58:34	\N	f	\N
511	65	2	2008-04-30 23:05:46	\N	f	\N
709	90	2	2008-04-30 23:14:03	\N	f	\N
733	93	2	2008-04-30 23:14:19	\N	f	\N
741	94	2	2008-04-30 23:14:38	\N	f	\N
405	50	138	2008-04-30 22:59:23	\N	f	5
406	50	35	2008-04-30 22:59:32	\N	f	6
231	33	134	2008-04-30 22:03:07	\N	f	1
232	33	135	2008-04-30 22:03:10	\N	f	2
233	33	136	2008-04-30 22:03:14	\N	f	3
234	33	137	2008-04-30 22:03:18	\N	f	4
235	33	138	2008-04-30 22:03:22	\N	f	5
236	33	35	2008-04-30 22:03:30	\N	f	6
239	34	131	2008-04-30 22:10:55	\N	f	1
240	34	132	2008-04-30 22:10:58	\N	f	2
241	34	133	2008-04-30 22:11:04	\N	f	3
242	34	134	2008-04-30 22:11:08	\N	f	4
243	34	135	2008-04-30 22:11:12	\N	f	5
244	34	31	2008-04-30 22:11:25	\N	f	6
247	35	131	2008-04-30 22:03:01	\N	f	1
248	35	132	2008-04-30 22:03:03	\N	f	2
249	35	133	2008-04-30 22:03:06	\N	f	3
250	35	134	2008-04-30 22:03:08	\N	f	4
251	35	135	2008-04-30 22:03:12	\N	f	5
252	35	31	2008-04-30 22:03:22	\N	f	6
255	36	134	2008-04-30 22:06:24	\N	f	1
256	36	135	2008-04-30 22:06:28	\N	f	2
257	36	136	2008-04-30 22:06:32	\N	f	3
258	36	137	2008-04-30 22:06:37	\N	f	4
259	36	138	2008-04-30 22:06:40	\N	f	5
260	36	35	2008-04-30 22:06:46	\N	f	6
263	37	133	2008-04-30 22:13:19	\N	f	1
264	37	134	2008-04-30 22:13:21	\N	f	2
265	37	135	2008-04-30 22:13:25	\N	f	3
266	37	136	2008-04-30 22:13:28	\N	f	4
267	37	137	2008-04-30 22:13:33	\N	f	5
268	37	31	2008-04-30 22:13:38	\N	f	6
271	38	131	2008-04-30 22:03:34	\N	f	1
272	38	132	2008-04-30 22:03:41	\N	f	2
273	38	133	2008-04-30 22:03:47	\N	f	3
274	38	134	2008-04-30 22:03:52	\N	f	4
275	38	135	2008-04-30 22:03:57	\N	f	5
276	38	31	2008-04-30 22:04:11	\N	f	6
279	39	134	2008-04-30 22:11:26	\N	f	1
280	39	135	2008-04-30 22:11:30	\N	f	2
281	39	136	2008-04-30 22:11:34	\N	f	3
282	39	137	2008-04-30 22:11:39	\N	f	4
283	39	138	2008-04-30 22:11:42	\N	f	5
284	39	35	2008-04-30 22:11:55	\N	f	6
287	40	133	2008-04-30 22:03:04	\N	f	1
288	40	134	2008-04-30 22:03:11	\N	f	2
289	40	135	2008-04-30 22:03:18	\N	f	3
290	40	136	2008-04-30 22:03:22	\N	f	4
291	40	137	2008-04-30 22:03:26	\N	f	5
292	40	31	2008-04-30 22:03:53	\N	f	6
295	41	131	2008-04-30 22:03:02	\N	f	1
296	41	132	2008-04-30 22:03:06	\N	f	2
297	41	133	2008-04-30 22:03:09	\N	f	3
298	41	134	2008-04-30 22:03:13	\N	f	4
299	41	135	2008-04-30 22:03:15	\N	f	5
300	41	31	2008-04-30 22:03:24	\N	f	6
303	42	132	2008-04-30 22:06:26	\N	f	1
304	42	133	2008-04-30 22:06:29	\N	f	2
305	42	134	2008-04-30 22:06:32	\N	f	3
306	42	135	2008-04-30 22:06:35	\N	f	4
307	42	136	2008-04-30 22:06:37	\N	f	5
308	42	35	2008-04-30 22:06:43	\N	f	6
311	43	133	2008-04-30 22:10:46	\N	f	1
312	43	134	2008-04-30 22:10:48	\N	f	2
313	43	135	2008-04-30 22:10:51	\N	f	3
314	43	136	2008-04-30 22:10:53	\N	f	4
315	43	137	2008-04-30 22:10:55	\N	f	5
316	43	31	2008-04-30 22:11:02	\N	f	6
319	44	132	2008-04-30 22:57:00	\N	f	1
320	44	133	2008-04-30 22:57:03	\N	f	2
321	44	134	2008-04-30 22:57:06	\N	f	3
322	44	135	2008-04-30 22:57:10	\N	f	4
323	44	136	2008-04-30 22:57:13	\N	f	5
324	44	35	2008-04-30 22:57:32	\N	f	6
327	45	132	2008-04-30 22:58:10	\N	f	1
328	45	133	2008-04-30 22:58:13	\N	f	2
329	45	134	2008-04-30 22:58:16	\N	f	3
330	45	135	2008-04-30 22:58:21	\N	f	4
331	45	136	2008-04-30 22:58:25	\N	f	5
332	45	35	2008-04-30 22:58:31	\N	f	6
449	56	131	2008-04-30 23:00:37	\N	f	1
450	56	132	2008-04-30 23:00:40	\N	f	2
451	56	133	2008-04-30 23:00:43	\N	f	3
452	56	134	2008-04-30 23:00:46	\N	f	4
453	56	135	2008-04-30 23:00:49	\N	f	5
454	56	31	2008-04-30 23:01:17	\N	f	6
457	57	140	2008-04-30 23:01:41	\N	f	1
458	57	141	2008-04-30 23:01:44	\N	f	2
459	57	142	2008-04-30 23:01:48	\N	f	3
460	57	143	2008-04-30 23:01:52	\N	f	4
461	57	144	2008-04-30 23:01:56	\N	f	5
462	57	35	2008-04-30 23:02:05	\N	f	6
476	59	146	2008-04-30 23:02:23	\N	f	4
477	59	147	2008-04-30 23:02:27	\N	f	5
478	59	31	2008-04-30 23:02:32	\N	f	6
386	49	135	2008-04-30 14:20:51	\N	f	1
387	49	35	2008-04-30 14:30:09	\N	f	2
388	49	140	2008-04-30 14:32:30	\N	f	3
389	49	147	2008-04-30 14:41:14	\N	f	4
390	49	149	2008-04-30 14:43:56	\N	f	5
391	49	151	2008-04-30 14:46:03	\N	f	6
392	49	157	2008-04-30 14:48:11	\N	f	7
393	49	131	2008-04-30 22:58:45	\N	f	8
394	49	132	2008-04-30 22:58:49	\N	f	9
395	49	133	2008-04-30 22:58:51	\N	f	10
396	49	134	2008-04-30 22:58:55	\N	f	11
397	49	135	2008-04-30 22:58:58	\N	f	12
398	49	31	2008-04-30 22:59:08	\N	f	13
409	51	133	2008-04-30 22:59:32	\N	f	1
410	51	134	2008-04-30 22:59:36	\N	f	2
411	51	135	2008-04-30 22:59:40	\N	f	3
412	51	136	2008-04-30 22:59:44	\N	f	4
413	51	137	2008-04-30 22:59:48	\N	f	5
414	51	31	2008-04-30 22:59:54	\N	f	6
666	84	158	2008-04-30 23:11:39	\N	f	1
667	84	156	2008-04-30 23:11:43	\N	f	2
668	84	150	2008-04-30 23:11:47	\N	f	3
521	66	134	2008-04-30 23:02:26	\N	f	1
522	66	135	2008-04-30 23:02:29	\N	f	2
433	54	132	2008-04-30 23:00:16	\N	f	1
434	54	133	2008-04-30 23:00:19	\N	f	2
435	54	134	2008-04-30 23:00:23	\N	f	3
436	54	135	2008-04-30 23:00:27	\N	f	4
437	54	136	2008-04-30 23:00:30	\N	f	5
438	54	35	2008-04-30 23:00:40	\N	f	6
441	55	139	2008-04-30 23:00:26	\N	f	1
442	55	140	2008-04-30 23:00:31	\N	f	2
443	55	142	2008-04-30 23:00:34	\N	f	4
444	55	143	2008-04-30 23:00:38	\N	f	5
445	55	35	2008-04-30 23:00:42	\N	f	6
669	84	147	2008-04-30 23:11:53	\N	f	4
670	84	140	2008-04-30 23:12:01	\N	f	5
575	73	131	2008-04-30 23:04:58	\N	f	1
576	73	132	2008-04-30 23:05:02	\N	f	2
577	73	133	2008-04-30 23:05:04	\N	f	3
578	73	134	2008-04-30 23:05:07	\N	f	4
579	73	135	2008-04-30 23:05:11	\N	f	5
582	74	143	2008-04-30 23:06:22	\N	f	1
505	64	144	2008-04-30 23:04:30	\N	f	1
506	64	145	2008-04-30 23:04:34	\N	f	2
507	64	146	2008-04-30 23:04:37	\N	f	3
508	64	147	2008-04-30 23:04:41	\N	f	4
509	64	148	2008-04-30 23:04:45	\N	f	5
510	64	31	2008-04-30 23:04:49	\N	f	6
513	65	149	2008-04-30 23:02:22	\N	f	1
514	65	150	2008-04-30 23:02:25	\N	f	2
515	65	151	2008-04-30 23:02:29	\N	f	3
516	65	152	2008-04-30 23:02:32	\N	f	4
517	65	153	2008-04-30 23:02:36	\N	f	5
518	65	35	2008-04-30 23:02:43	\N	f	6
523	66	136	2008-04-30 23:02:32	\N	f	3
524	66	137	2008-04-30 23:02:34	\N	f	4
525	66	138	2008-04-30 23:02:38	\N	f	5
526	66	35	2008-04-30 23:02:46	\N	f	6
529	67	141	2008-04-30 23:03:31	\N	f	1
530	67	142	2008-04-30 23:03:34	\N	f	2
531	67	143	2008-04-30 23:03:37	\N	f	3
532	67	144	2008-04-30 23:03:41	\N	f	4
533	67	145	2008-04-30 23:03:45	\N	f	5
534	67	35	2008-04-30 23:03:53	\N	f	6
537	68	132	2008-04-30 23:04:05	\N	f	1
538	68	133	2008-04-30 23:04:08	\N	f	2
539	68	134	2008-04-30 23:04:10	\N	f	3
540	68	135	2008-04-30 23:04:13	\N	f	4
541	68	136	2008-04-30 23:04:18	\N	f	5
542	68	35	2008-04-30 23:04:23	\N	f	6
583	74	144	2008-04-30 23:06:24	\N	f	2
584	74	145	2008-04-30 23:06:27	\N	f	3
585	74	146	2008-04-30 23:06:29	\N	f	4
586	74	147	2008-04-30 23:06:32	\N	f	5
587	74	31	2008-04-30 23:06:36	\N	f	6
590	75	145	2008-04-30 23:06:21	\N	f	1
553	70	141	2008-04-30 23:05:05	\N	f	1
554	70	142	2008-04-30 23:05:07	\N	f	2
555	70	143	2008-04-30 23:05:10	\N	f	3
556	70	144	2008-04-30 23:05:13	\N	f	4
557	70	145	2008-04-30 23:05:16	\N	f	5
558	70	35	2008-04-30 23:05:23	\N	f	6
358	47	148	2008-04-30 15:10:18	\N	f	6
591	75	146	2008-04-30 23:06:24	\N	f	2
592	75	147	2008-04-30 23:06:27	\N	f	3
593	75	148	2008-04-30 23:06:29	\N	f	4
594	75	149	2008-04-30 23:06:32	\N	f	5
595	75	31	2008-04-30 23:06:37	\N	f	6
598	76	159	2008-04-30 23:07:53	\N	f	1
599	76	158	2008-04-30 23:07:55	\N	f	2
600	76	156	2008-04-30 23:07:58	\N	f	3
601	76	154	2008-04-30 23:08:02	\N	f	4
602	76	31	2008-04-30 23:08:05	\N	f	5
671	84	35	2008-04-30 23:12:09	\N	f	6
674	85	144	2008-04-30 23:11:52	\N	f	1
675	85	145	2008-04-30 23:11:54	\N	f	2
676	85	146	2008-04-30 23:11:56	\N	f	3
611	78	156	2008-04-30 23:08:05	\N	f	1
612	78	157	2008-04-30 23:08:08	\N	f	2
613	78	158	2008-04-30 23:08:11	\N	f	3
614	78	159	2008-04-30 23:08:14	\N	f	4
615	78	160	2008-04-30 23:08:16	\N	f	5
616	78	35	2008-04-30 23:08:21	\N	f	6
619	79	142	2008-04-30 23:08:14	\N	f	1
620	79	143	2008-04-30 23:08:16	\N	f	2
621	79	144	2008-04-30 23:08:18	\N	f	3
622	79	145	2008-04-30 23:08:20	\N	f	4
623	79	146	2008-04-30 23:08:23	\N	f	5
624	79	35	2008-04-30 23:08:30	\N	f	6
627	80	140	2008-04-30 23:10:17	\N	f	1
628	80	141	2008-04-30 23:10:19	\N	f	2
629	80	142	2008-04-30 23:10:23	\N	f	3
630	80	143	2008-04-30 23:10:26	\N	f	4
631	80	144	2008-04-30 23:10:29	\N	f	5
632	80	35	2008-04-30 23:10:34	\N	f	6
635	81	141	2008-04-30 23:10:17	\N	f	1
636	81	142	2008-04-30 23:10:20	\N	f	2
637	81	143	2008-04-30 23:10:23	\N	f	3
638	81	144	2008-04-30 23:10:27	\N	f	4
639	81	145	2008-04-30 23:10:31	\N	f	5
640	81	35	2008-04-30 23:10:37	\N	f	6
643	82	132	2008-04-30 23:06:49	\N	f	1
644	82	133	2008-04-30 23:06:51	\N	f	2
645	82	134	2008-04-30 23:06:54	\N	f	3
646	82	135	2008-04-30 23:06:57	\N	f	4
647	82	136	2008-04-30 23:07:00	\N	f	5
648	82	35	2008-04-30 23:07:09	\N	f	6
651	83	131	2008-04-30 13:35:06	\N	f	1
652	83	134	2008-04-30 13:37:37	\N	f	2
653	83	133	2008-04-30 13:39:24	\N	f	3
654	83	142	2008-04-30 13:48:35	\N	f	4
655	83	144	2008-04-30 13:54:18	\N	f	5
656	83	147	2008-04-30 14:00:33	\N	f	6
657	83	152	2008-04-30 14:17:10	\N	f	7
658	83	157	2008-04-30 14:19:56	\N	f	8
659	83	160	2008-04-30 23:10:31	\N	f	9
660	83	159	2008-04-30 23:10:37	\N	f	10
661	83	158	2008-04-30 23:10:44	\N	f	11
662	83	156	2008-04-30 23:10:49	\N	f	12
663	83	31	2008-04-30 23:11:06	\N	f	13
679	86	143	2008-04-30 23:11:52	\N	f	1
680	86	144	2008-04-30 23:11:54	\N	f	2
681	86	145	2008-04-30 23:11:58	\N	f	3
682	86	146	2008-04-30 23:12:00	\N	f	4
683	86	147	2008-04-30 23:12:02	\N	f	5
684	86	31	2008-04-30 23:12:08	\N	f	6
687	87	141	2008-04-30 23:11:58	\N	f	1
688	87	142	2008-04-30 23:12:02	\N	f	2
689	87	143	2008-04-30 23:12:05	\N	f	3
690	87	144	2008-04-30 23:12:09	\N	f	4
691	87	145	2008-04-30 23:12:12	\N	f	5
692	87	35	2008-04-30 23:12:17	\N	f	6
695	88	156	2008-04-30 23:12:13	\N	f	1
696	88	157	2008-04-30 23:12:17	\N	f	2
697	88	158	2008-04-30 23:12:20	\N	f	3
698	88	159	2008-04-30 23:12:23	\N	f	4
699	88	160	2008-04-30 23:12:27	\N	f	5
700	88	35	2008-04-30 23:12:29	\N	f	6
703	89	149	2008-04-30 23:12:14	\N	f	1
704	89	150	2008-04-30 23:12:17	\N	f	2
705	89	151	2008-04-30 23:12:20	\N	f	3
706	89	152	2008-04-30 23:12:23	\N	f	4
707	89	153	2008-04-30 23:12:26	\N	f	5
708	89	35	2008-04-30 23:12:31	\N	f	6
799	101	132	2008-04-30 23:15:11	\N	f	1
800	101	133	2008-04-30 23:15:13	\N	f	2
801	101	134	2008-04-30 23:15:16	\N	f	3
802	101	135	2008-04-30 23:15:18	\N	f	4
803	101	136	2008-04-30 23:15:21	\N	f	5
804	101	35	2008-04-30 23:15:31	\N	f	6
735	93	159	2008-04-30 23:13:40	\N	f	1
736	93	158	2008-04-30 23:13:51	\N	f	2
737	93	156	2008-04-30 23:13:58	\N	f	3
738	93	155	2008-04-30 23:14:04	\N	f	4
739	93	154	2008-04-30 23:14:10	\N	f	5
740	93	31	2008-04-30 23:14:14	\N	f	6
743	94	155	2008-04-30 23:13:41	\N	f	1
744	94	152	2008-04-30 23:13:46	\N	f	2
745	94	145	2008-04-30 23:13:50	\N	f	3
746	94	138	2008-04-30 23:13:57	\N	f	4
747	94	134	2008-04-30 23:14:00	\N	f	5
748	94	35	2008-04-30 23:14:06	\N	f	6
751	95	142	2008-04-30 23:14:13	\N	f	1
752	95	143	2008-04-30 23:14:16	\N	f	2
753	95	144	2008-04-30 23:14:19	\N	f	3
754	95	145	2008-04-30 23:14:22	\N	f	4
755	95	146	2008-04-30 23:14:25	\N	f	5
756	95	35	2008-04-30 23:14:28	\N	f	6
759	96	145	2008-04-30 23:14:11	\N	f	1
760	96	146	2008-04-30 23:14:14	\N	f	2
761	96	147	2008-04-30 23:14:17	\N	f	3
762	96	148	2008-04-30 23:14:21	\N	f	4
763	96	149	2008-04-30 23:14:24	\N	f	5
764	96	31	2008-04-30 23:14:27	\N	f	6
767	97	145	2008-04-30 23:14:13	\N	f	1
768	97	146	2008-04-30 23:14:16	\N	f	2
769	97	147	2008-04-30 23:14:20	\N	f	3
770	97	148	2008-04-30 23:14:23	\N	f	4
771	97	149	2008-04-30 23:14:25	\N	f	5
772	97	31	2008-04-30 23:14:29	\N	f	6
775	98	151	2008-04-30 23:14:34	\N	f	1
776	98	152	2008-04-30 23:14:38	\N	f	2
777	98	153	2008-04-30 23:14:40	\N	f	3
778	98	154	2008-04-30 23:14:43	\N	f	4
779	98	155	2008-04-30 23:14:45	\N	f	5
780	98	31	2008-04-30 23:14:47	\N	f	6
783	99	144	2008-04-30 23:14:55	\N	f	1
784	99	145	2008-04-30 23:14:57	\N	f	2
785	99	146	2008-04-30 23:14:59	\N	f	3
786	99	147	2008-04-30 23:15:01	\N	f	4
787	99	148	2008-04-30 23:15:03	\N	f	5
788	99	31	2008-04-30 23:15:12	\N	f	6
807	102	160	2008-04-30 23:15:26	\N	f	1
808	102	159	2008-04-30 23:15:30	\N	f	2
809	102	158	2008-04-30 23:15:33	\N	f	3
810	102	157	2008-04-30 23:15:36	\N	f	4
811	102	156	2008-04-30 23:15:40	\N	f	5
812	102	31	2008-04-30 23:15:44	\N	f	6
815	103	150	2008-04-30 23:15:29	\N	f	1
816	103	151	2008-04-30 23:15:32	\N	f	2
817	103	147	2008-04-30 23:15:38	\N	f	3
818	103	154	2008-04-30 23:15:43	\N	f	4
819	103	152	2008-04-30 23:15:47	\N	f	5
820	103	35	2008-04-30 23:15:51	\N	f	6
1241	156	150	2008-04-30 23:31:30	\N	f	1
1242	156	151	2008-04-30 23:31:33	\N	f	2
1243	156	152	2008-04-30 23:31:35	\N	f	3
1244	156	153	2008-04-30 23:31:37	\N	f	4
1245	156	154	2008-04-30 23:31:40	\N	f	5
1246	156	35	2008-04-30 23:31:43	\N	f	6
831	105	150	2008-04-30 23:15:36	\N	f	1
832	105	151	2008-04-30 23:15:39	\N	f	2
833	105	147	2008-04-30 23:15:42	\N	f	3
834	105	154	2008-04-30 23:15:45	\N	f	4
835	105	152	2008-04-30 23:15:48	\N	f	5
836	105	35	2008-04-30 23:15:52	\N	f	6
839	106	147	2008-04-30 23:15:57	\N	f	1
840	106	148	2008-04-30 23:15:59	\N	f	2
841	106	149	2008-04-30 23:16:01	\N	f	3
842	106	150	2008-04-30 23:16:04	\N	f	4
843	106	151	2008-04-30 23:16:06	\N	f	5
844	106	31	2008-04-30 23:16:09	\N	f	6
847	107	150	2008-04-30 23:15:53	\N	f	1
848	107	151	2008-04-30 23:15:56	\N	f	2
849	107	147	2008-04-30 23:16:00	\N	f	3
850	107	154	2008-04-30 23:16:04	\N	f	4
851	107	152	2008-04-30 23:16:07	\N	f	5
852	107	35	2008-04-30 23:16:10	\N	f	6
855	108	158	2008-04-30 23:15:31	\N	f	1
856	108	156	2008-04-30 23:15:37	\N	f	2
857	108	150	2008-04-30 23:15:46	\N	f	3
858	108	147	2008-04-30 23:15:55	\N	f	4
859	108	140	2008-04-30 23:16:05	\N	f	5
860	108	35	2008-04-30 23:16:13	\N	f	6
863	109	145	2008-04-30 23:16:38	\N	f	1
864	109	146	2008-04-30 23:16:41	\N	f	2
865	109	147	2008-04-30 23:16:46	\N	f	3
866	109	148	2008-04-30 23:16:48	\N	f	4
867	109	149	2008-04-30 23:16:51	\N	f	5
868	109	31	2008-04-30 23:17:00	\N	f	6
1166	147	134	2008-04-30 14:29:21	\N	f	1
1167	147	138	2008-04-30 14:32:47	\N	f	2
1168	147	142	2008-04-30 14:37:10	\N	f	3
1169	147	144	2008-04-30 14:41:57	\N	f	4
1170	147	147	2008-04-30 14:48:17	\N	f	5
1171	147	153	2008-04-30 14:51:45	\N	f	6
879	111	131	2008-04-30 23:18:47	\N	f	1
880	111	132	2008-04-30 23:18:49	\N	f	2
881	111	133	2008-04-30 23:18:52	\N	f	3
882	111	134	2008-04-30 23:18:55	\N	f	4
883	111	135	2008-04-30 23:18:58	\N	f	5
884	111	31	2008-04-30 23:19:19	\N	f	6
887	112	146	2008-04-30 23:19:12	\N	f	1
888	112	147	2008-04-30 23:19:15	\N	f	2
889	112	148	2008-04-30 23:19:18	\N	f	3
890	112	149	2008-04-30 23:19:21	\N	f	4
891	112	150	2008-04-30 23:19:23	\N	f	5
892	112	35	2008-04-30 23:19:26	\N	f	6
895	113	153	2008-04-30 23:19:03	\N	f	1
896	113	148	2008-04-30 23:19:09	\N	f	2
897	113	146	2008-04-30 23:19:13	\N	f	3
898	113	141	2008-04-30 23:19:20	\N	f	4
899	113	144	2008-04-30 23:19:25	\N	f	5
900	113	35	2008-04-30 23:19:30	\N	f	6
903	114	149	2008-04-30 23:19:22	\N	f	1
904	114	150	2008-04-30 23:19:25	\N	f	2
905	114	151	2008-04-30 23:19:27	\N	f	3
906	114	152	2008-04-30 23:19:29	\N	f	4
907	114	153	2008-04-30 23:19:31	\N	f	5
908	114	35	2008-04-30 23:19:34	\N	f	6
911	115	146	2008-04-30 23:19:22	\N	f	1
912	115	147	2008-04-30 23:19:24	\N	f	2
913	115	148	2008-04-30 23:19:26	\N	f	3
914	115	149	2008-04-30 23:19:29	\N	f	4
915	115	150	2008-04-30 23:19:31	\N	f	5
916	115	35	2008-04-30 23:19:36	\N	f	6
919	116	155	2008-04-30 23:20:02	\N	f	1
920	116	152	2008-04-30 23:20:09	\N	f	2
921	116	145	2008-04-30 23:20:21	\N	f	3
922	116	138	2008-04-30 23:20:35	\N	f	4
923	116	134	2008-04-30 23:20:40	\N	f	5
924	116	35	2008-04-30 23:20:47	\N	f	6
927	117	146	2008-04-30 23:20:45	\N	f	1
928	117	147	2008-04-30 23:20:47	\N	f	2
929	117	148	2008-04-30 23:20:50	\N	f	3
930	117	149	2008-04-30 23:20:53	\N	f	4
931	117	151	2008-04-30 23:20:55	\N	f	5
932	117	31	2008-04-30 23:20:58	\N	f	6
935	118	150	2008-04-30 23:20:41	\N	f	1
936	118	151	2008-04-30 23:20:43	\N	f	2
937	118	147	2008-04-30 23:20:49	\N	f	3
938	118	154	2008-04-30 23:20:53	\N	f	4
939	118	152	2008-04-30 23:20:56	\N	f	5
940	118	35	2008-04-30 23:21:02	\N	f	6
1172	147	151	2008-04-30 14:58:22	\N	f	7
1173	147	154	2008-04-30 15:00:19	\N	f	8
1174	147	158	2008-04-30 15:05:04	\N	f	9
946	120	146	2008-04-30 23:21:12	\N	f	1
947	120	147	2008-04-30 23:21:15	\N	f	2
948	120	148	2008-04-30 23:21:17	\N	f	3
949	120	149	2008-04-30 23:21:19	\N	f	4
950	120	151	2008-04-30 23:21:21	\N	f	5
951	120	31	2008-04-30 23:21:24	\N	f	6
954	121	155	2008-04-30 23:21:00	\N	f	1
955	121	152	2008-04-30 23:21:03	\N	f	2
956	121	145	2008-04-30 23:21:07	\N	f	3
957	121	138	2008-04-30 23:21:13	\N	f	4
958	121	134	2008-04-30 23:21:17	\N	f	5
959	121	35	2008-04-30 23:21:26	\N	f	6
962	122	145	2008-04-30 23:21:09	\N	f	1
963	122	146	2008-04-30 23:21:11	\N	f	2
964	122	147	2008-04-30 23:21:13	\N	f	3
1177	148	151	2008-04-30 23:25:17	\N	f	1
1178	148	152	2008-04-30 23:25:19	\N	f	2
1179	148	153	2008-04-30 23:25:21	\N	f	3
1180	148	154	2008-04-30 23:25:24	\N	f	4
1181	148	155	2008-04-30 23:25:26	\N	f	5
1182	148	31	2008-04-30 23:25:29	\N	f	6
1185	149	157	2008-04-30 23:25:05	\N	f	1
978	124	146	2008-04-30 23:21:59	\N	f	1
979	124	147	2008-04-30 23:22:00	\N	f	2
980	124	148	2008-04-30 23:22:01	\N	f	3
981	124	149	2008-04-30 23:22:04	\N	f	4
982	124	150	2008-04-30 23:22:07	\N	f	5
983	124	35	2008-04-30 23:22:10	\N	f	6
986	125	147	2008-04-30 23:21:55	\N	f	1
987	125	148	2008-04-30 23:21:57	\N	f	2
988	125	149	2008-04-30 23:22:00	\N	f	3
989	125	150	2008-04-30 23:22:02	\N	f	4
990	125	151	2008-04-30 23:22:05	\N	f	5
991	125	31	2008-04-30 23:22:08	\N	f	6
994	126	136	2008-04-30 23:21:32	\N	f	1
995	126	137	2008-04-30 23:21:36	\N	f	2
996	126	138	2008-04-30 23:21:39	\N	f	3
997	126	139	2008-04-30 23:21:42	\N	f	4
998	126	140	2008-04-30 23:21:45	\N	f	5
999	126	35	2008-04-30 23:21:49	\N	f	6
1002	127	143	2008-04-30 23:22:17	\N	f	1
1003	127	144	2008-04-30 23:22:21	\N	f	2
1004	127	142	2008-04-30 23:22:24	\N	f	3
1005	127	146	2008-04-30 23:22:26	\N	f	4
1006	127	147	2008-04-30 23:22:29	\N	f	5
1007	127	31	2008-04-30 23:22:32	\N	f	6
1010	128	150	2008-04-30 23:22:32	\N	f	1
1011	128	151	2008-04-30 23:22:34	\N	f	2
1012	128	147	2008-04-30 23:22:36	\N	f	3
1013	128	154	2008-04-30 23:22:39	\N	f	4
1014	128	152	2008-04-30 23:22:41	\N	f	5
1015	128	35	2008-04-30 23:22:45	\N	f	6
1018	129	138	2008-04-30 23:22:36	\N	f	1
1019	129	139	2008-04-30 23:22:38	\N	f	2
1020	129	140	2008-04-30 23:22:41	\N	f	3
1021	129	141	2008-04-30 23:22:43	\N	f	4
1022	129	142	2008-04-30 23:22:46	\N	f	5
1023	129	31	2008-04-30 23:22:53	\N	f	6
1026	130	146	2008-04-30 23:23:46	\N	f	1
1027	130	147	2008-04-30 23:23:48	\N	f	2
1028	130	148	2008-04-30 23:23:50	\N	f	3
1029	130	149	2008-04-30 23:23:51	\N	f	4
1030	130	151	2008-04-30 23:23:53	\N	f	5
1031	130	31	2008-04-30 23:23:58	\N	f	6
1034	131	149	2008-04-30 23:23:55	\N	f	1
1035	131	150	2008-04-30 23:23:57	\N	f	2
1036	131	151	2008-04-30 23:23:59	\N	f	3
1037	131	152	2008-04-30 23:24:02	\N	f	4
1038	131	153	2008-04-30 23:24:04	\N	f	5
1039	131	35	2008-04-30 23:24:07	\N	f	6
1042	132	138	2008-04-30 23:23:50	\N	f	1
1043	132	139	2008-04-30 23:23:54	\N	f	2
1044	132	140	2008-04-30 23:23:56	\N	f	3
1045	132	141	2008-04-30 23:23:59	\N	f	4
1046	132	142	2008-04-30 23:24:02	\N	f	5
1047	132	31	2008-04-30 23:24:07	\N	f	6
1050	133	146	2008-04-30 23:24:07	\N	f	1
1051	133	147	2008-04-30 23:24:09	\N	f	2
1052	133	148	2008-04-30 23:24:12	\N	f	3
1053	133	149	2008-04-30 23:24:15	\N	f	4
1054	133	150	2008-04-30 23:24:17	\N	f	5
1055	133	35	2008-04-30 23:24:19	\N	f	6
1058	134	141	2008-04-30 23:24:02	\N	f	1
1059	134	142	2008-04-30 23:24:03	\N	f	2
1060	134	143	2008-04-30 23:24:05	\N	f	3
1061	134	144	2008-04-30 23:24:07	\N	f	4
1062	134	145	2008-04-30 23:24:10	\N	f	5
1063	134	35	2008-04-30 23:24:14	\N	f	6
1066	135	146	2008-04-30 23:24:24	\N	f	1
1067	135	147	2008-04-30 23:24:26	\N	f	2
1068	135	148	2008-04-30 23:24:28	\N	f	3
1069	135	149	2008-04-30 23:24:31	\N	f	4
1070	135	151	2008-04-30 23:24:34	\N	f	5
1071	135	31	2008-04-30 23:24:36	\N	f	6
1074	136	150	2008-04-30 23:24:37	\N	f	1
1075	136	151	2008-04-30 23:24:40	\N	f	2
1076	136	152	2008-04-30 23:24:41	\N	f	3
1077	136	153	2008-04-30 23:24:44	\N	f	4
1078	136	154	2008-04-30 23:24:46	\N	f	5
1079	136	35	2008-04-30 23:24:48	\N	f	6
1082	137	137	2008-04-30 23:24:37	\N	f	1
1083	137	138	2008-04-30 23:24:39	\N	f	2
1084	137	139	2008-04-30 23:24:43	\N	f	3
1085	137	140	2008-04-30 23:24:46	\N	f	4
1086	137	141	2008-04-30 23:24:48	\N	f	5
1087	137	31	2008-04-30 23:24:53	\N	f	6
1186	149	154	2008-04-30 23:25:11	\N	f	2
1187	149	148	2008-04-30 23:25:16	\N	f	3
1188	149	142	2008-04-30 23:25:21	\N	f	4
1189	149	135	2008-04-30 23:25:27	\N	f	5
1190	149	31	2008-04-30 23:25:34	\N	f	6
1201	151	160	2008-04-30 23:25:50	\N	f	1
1202	151	159	2008-04-30 23:25:54	\N	f	2
1203	151	158	2008-04-30 23:25:56	\N	f	3
1204	151	157	2008-04-30 23:25:58	\N	f	4
1205	151	155	2008-04-30 23:26:02	\N	f	5
1206	151	31	2008-04-30 23:26:08	\N	f	6
1209	152	149	2008-04-30 23:27:36	\N	f	1
1122	142	147	2008-04-30 23:24:39	\N	f	1
1123	142	148	2008-04-30 23:24:41	\N	f	2
1124	142	135	2008-04-30 23:24:46	\N	f	3
1125	142	150	2008-04-30 23:24:50	\N	f	4
1126	142	151	2008-04-30 23:24:52	\N	f	5
1127	142	31	2008-04-30 23:24:55	\N	f	6
1130	143	146	2008-04-30 23:24:48	\N	f	1
1131	143	147	2008-04-30 23:24:51	\N	f	2
1132	143	148	2008-04-30 23:24:52	\N	f	3
1133	143	149	2008-04-30 23:24:54	\N	f	4
1134	143	151	2008-04-30 23:24:56	\N	f	5
1135	143	31	2008-04-30 23:24:58	\N	f	6
1138	144	156	2008-04-30 23:25:01	\N	f	1
1139	144	157	2008-04-30 23:25:03	\N	f	2
1140	144	158	2008-04-30 23:25:05	\N	f	3
1141	144	159	2008-04-30 23:25:07	\N	f	4
1142	144	160	2008-04-30 23:25:09	\N	f	5
1143	144	35	2008-04-30 23:25:12	\N	f	6
1210	152	150	2008-04-30 23:27:38	\N	f	2
1211	152	151	2008-04-30 23:27:40	\N	f	3
1212	152	152	2008-04-30 23:27:42	\N	f	4
1213	152	153	2008-04-30 23:27:43	\N	f	5
1214	152	35	2008-04-30 23:27:47	\N	f	6
1217	153	143	2008-04-30 23:27:39	\N	f	1
1218	153	144	2008-04-30 23:27:41	\N	f	2
1219	153	145	2008-04-30 23:27:44	\N	f	3
1220	153	148	2008-04-30 23:27:45	\N	f	4
1221	153	147	2008-04-30 23:27:48	\N	f	5
1158	146	147	2008-04-30 23:25:02	\N	f	1
1159	146	148	2008-04-30 23:25:04	\N	f	2
1160	146	149	2008-04-30 23:25:06	\N	f	3
1161	146	150	2008-04-30 23:25:09	\N	f	4
1162	146	151	2008-04-30 23:25:11	\N	f	5
1163	146	31	2008-04-30 23:25:14	\N	f	6
1222	153	31	2008-04-30 23:27:50	\N	f	6
1225	154	144	2008-04-30 23:27:46	\N	f	1
1226	154	145	2008-04-30 23:27:48	\N	f	2
1227	154	146	2008-04-30 23:27:50	\N	f	3
1228	154	147	2008-04-30 23:27:51	\N	f	4
1229	154	148	2008-04-30 23:27:53	\N	f	5
1230	154	31	2008-04-30 23:27:56	\N	f	6
1233	155	136	2008-04-30 23:30:32	\N	f	1
1234	155	137	2008-04-30 23:30:38	\N	f	2
1235	155	138	2008-04-30 23:30:42	\N	f	3
1236	155	139	2008-04-30 23:30:46	\N	f	4
1237	155	140	2008-04-30 23:30:48	\N	f	5
1238	155	35	2008-04-30 23:30:54	\N	f	6
1249	157	154	2008-04-30 23:31:39	\N	f	1
1250	157	155	2008-04-30 23:31:41	\N	f	2
1251	157	156	2008-04-30 23:31:43	\N	f	3
1252	157	157	2008-04-30 23:31:47	\N	f	4
1253	157	158	2008-04-30 23:31:49	\N	f	5
1254	157	35	2008-04-30 23:31:51	\N	f	6
1257	158	156	2008-04-30 23:32:00	\N	f	1
1258	158	152	2008-04-30 23:32:05	\N	f	2
1259	158	145	2008-04-30 23:32:11	\N	f	3
1260	158	136	2008-04-30 23:32:17	\N	f	4
1261	158	132	2008-04-30 23:32:21	\N	f	5
1262	158	35	2008-04-30 23:32:27	\N	f	6
1265	159	150	2008-04-30 23:32:56	\N	f	1
1266	159	151	2008-04-30 23:32:59	\N	f	2
1267	159	152	2008-04-30 23:33:01	\N	f	3
1268	159	153	2008-04-30 23:33:04	\N	f	4
1269	159	154	2008-04-30 23:33:06	\N	f	5
1270	159	35	2008-04-30 23:33:11	\N	f	6
1273	160	139	2008-04-30 23:33:10	\N	f	1
1274	160	140	2008-04-30 23:33:12	\N	f	2
1275	160	141	2008-04-30 23:33:14	\N	f	3
1276	160	142	2008-04-30 23:33:16	\N	f	4
1277	160	143	2008-04-30 23:33:18	\N	f	5
1278	160	35	2008-04-30 23:33:21	\N	f	6
1281	161	158	2008-04-30 23:33:04	\N	f	1
1282	161	156	2008-04-30 23:33:06	\N	f	2
1283	161	150	2008-04-30 23:33:10	\N	f	3
1284	161	147	2008-04-30 23:33:13	\N	f	4
1285	161	140	2008-04-30 23:33:20	\N	f	5
1286	161	35	2008-04-30 23:33:29	\N	f	6
1289	162	142	2008-04-30 23:33:18	\N	f	1
1290	162	143	2008-04-30 23:33:21	\N	f	2
1291	162	144	2008-04-30 23:33:23	\N	f	3
1292	162	145	2008-04-30 23:33:25	\N	f	4
1293	162	146	2008-04-30 23:33:27	\N	f	5
1294	162	35	2008-04-30 23:33:30	\N	f	6
1297	163	156	2008-04-30 23:33:31	\N	f	1
1298	163	157	2008-04-30 23:33:32	\N	f	2
1299	163	158	2008-04-30 23:33:34	\N	f	3
1300	163	159	2008-04-30 23:33:36	\N	f	4
1301	163	160	2008-04-30 23:33:38	\N	f	5
1302	163	35	2008-04-30 23:33:39	\N	f	6
1305	164	154	2008-04-30 23:33:28	\N	f	1
1306	164	155	2008-04-30 23:33:32	\N	f	2
1307	164	156	2008-04-30 23:33:34	\N	f	3
1308	164	157	2008-04-30 23:33:36	\N	f	4
1309	164	158	2008-04-30 23:33:38	\N	f	5
1310	164	35	2008-04-30 23:33:41	\N	f	6
1313	165	151	2008-04-30 23:33:51	\N	f	1
1314	165	152	2008-04-30 23:33:53	\N	f	2
1315	165	153	2008-04-30 23:33:55	\N	f	3
1316	165	154	2008-04-30 23:33:58	\N	f	4
1317	165	155	2008-04-30 23:34:00	\N	f	5
1318	165	31	2008-04-30 23:34:04	\N	f	6
1329	167	151	2008-04-30 23:33:57	\N	f	1
1330	167	152	2008-04-30 23:33:59	\N	f	2
1331	167	153	2008-04-30 23:34:01	\N	f	3
1332	167	154	2008-04-30 23:34:03	\N	f	4
1333	167	155	2008-04-30 23:34:05	\N	f	5
1334	167	31	2008-04-30 23:34:07	\N	f	6
1337	168	158	2008-04-30 23:33:44	\N	f	1
1338	168	152	2008-04-30 23:33:49	\N	f	2
1339	168	159	2008-04-30 23:33:53	\N	f	3
1340	168	153	2008-04-30 23:34:03	\N	f	4
1341	168	160	2008-04-30 23:34:09	\N	f	5
1342	168	31	2008-04-30 23:34:12	\N	f	6
1345	169	140	2008-04-30 23:34:07	\N	f	1
1346	169	141	2008-04-30 23:34:10	\N	f	2
1347	169	142	2008-04-30 23:34:11	\N	f	3
1348	169	143	2008-04-30 23:34:15	\N	f	4
1349	169	35	2008-04-30 23:34:18	\N	f	5
1352	170	138	2008-04-30 23:33:56	\N	f	1
1353	170	139	2008-04-30 23:34:02	\N	f	2
1354	170	140	2008-04-30 23:34:05	\N	f	3
1355	170	141	2008-04-30 23:34:08	\N	f	4
1356	170	142	2008-04-30 23:34:14	\N	f	5
1357	170	31	2008-04-30 23:34:25	\N	f	6
1360	171	139	2008-04-30 23:34:09	\N	f	1
1361	171	140	2008-04-30 23:34:11	\N	f	2
1362	171	141	2008-04-30 23:34:13	\N	f	3
1363	171	142	2008-04-30 23:34:16	\N	f	4
1364	171	143	2008-04-30 23:34:18	\N	f	5
1365	171	35	2008-04-30 23:34:23	\N	f	6
1368	172	157	2008-04-30 23:34:20	\N	f	1
1369	172	154	2008-04-30 23:34:22	\N	f	2
1370	172	148	2008-04-30 23:34:25	\N	f	3
1371	172	142	2008-04-30 23:34:29	\N	f	4
1374	173	142	2008-04-30 23:34:17	\N	f	1
1375	173	143	2008-04-30 23:34:20	\N	f	2
1376	173	144	2008-04-30 23:34:22	\N	f	3
1377	173	145	2008-04-30 23:34:24	\N	f	4
1378	173	146	2008-04-30 23:34:26	\N	f	5
1379	173	35	2008-04-30 23:34:30	\N	f	6
1382	174	154	2008-04-30 23:34:47	\N	f	1
1383	174	155	2008-04-30 23:34:49	\N	f	2
1384	174	156	2008-04-30 23:34:51	\N	f	3
1385	174	157	2008-04-30 23:34:53	\N	f	4
1386	174	158	2008-04-30 23:34:55	\N	f	5
1387	174	35	2008-04-30 23:35:00	\N	f	6
1390	175	147	2008-04-30 23:34:58	\N	f	1
1391	175	148	2008-04-30 23:35:00	\N	f	2
1392	175	149	2008-04-30 23:35:03	\N	f	3
1393	175	150	2008-04-30 23:35:05	\N	f	4
1394	175	151	2008-04-30 23:35:07	\N	f	5
1395	175	31	2008-04-30 23:35:10	\N	f	6
1398	176	154	2008-04-30 23:35:26	\N	f	1
1399	176	155	2008-04-30 23:35:28	\N	f	2
1400	176	156	2008-04-30 23:35:31	\N	f	3
1401	176	157	2008-04-30 23:35:34	\N	f	4
1402	176	158	2008-04-30 23:35:36	\N	f	5
1403	176	35	2008-04-30 23:35:38	\N	f	6
1406	177	148	2008-04-30 23:35:24	\N	f	1
1407	177	147	2008-04-30 23:35:28	\N	f	2
1408	177	146	2008-04-30 23:35:30	\N	f	3
1409	177	145	2008-04-30 23:35:37	\N	f	4
1410	177	143	2008-04-30 23:35:40	\N	f	5
1411	177	31	2008-04-30 23:35:50	\N	f	6
1414	178	156	2008-04-30 23:35:54	\N	f	1
1415	178	152	2008-04-30 23:35:58	\N	f	2
1416	178	145	2008-04-30 23:36:02	\N	f	3
1417	178	136	2008-04-30 23:36:06	\N	f	4
1418	178	132	2008-04-30 23:36:09	\N	f	5
1419	178	35	2008-04-30 23:36:13	\N	f	6
1422	179	150	2008-04-30 23:36:13	\N	f	1
1423	179	151	2008-04-30 23:36:15	\N	f	2
1424	179	152	2008-04-30 23:36:18	\N	f	3
1425	179	153	2008-04-30 23:36:20	\N	f	4
1426	179	154	2008-04-30 23:36:22	\N	f	5
1427	179	35	2008-04-30 23:36:26	\N	f	6
1430	180	156	2008-04-30 23:36:22	\N	f	1
1431	180	157	2008-04-30 23:36:26	\N	f	2
1432	180	158	2008-04-30 23:36:28	\N	f	3
1433	180	159	2008-04-30 23:36:30	\N	f	4
1434	180	160	2008-04-30 23:36:32	\N	f	5
1435	180	35	2008-04-30 23:36:34	\N	f	6
1438	181	157	2008-04-30 23:36:23	\N	f	1
1439	181	154	2008-04-30 23:36:26	\N	f	2
1440	181	148	2008-04-30 23:36:30	\N	f	3
1441	181	142	2008-04-30 23:36:34	\N	f	4
1442	181	135	2008-04-30 23:36:36	\N	f	5
1443	181	31	2008-04-30 23:36:40	\N	f	6
1446	182	156	2008-04-30 23:36:12	\N	f	1
1447	182	152	2008-04-30 23:36:16	\N	f	2
1448	182	145	2008-04-30 23:36:22	\N	f	3
1449	182	136	2008-04-30 23:36:27	\N	f	4
1450	182	132	2008-04-30 23:36:30	\N	f	5
1451	182	35	2008-04-30 23:36:39	\N	f	6
1454	183	140	2008-04-30 23:36:29	\N	f	1
1455	183	141	2008-04-30 23:36:33	\N	f	2
1456	183	142	2008-04-30 23:36:37	\N	f	3
1457	183	143	2008-04-30 23:36:39	\N	f	4
1458	183	144	2008-04-30 23:36:41	\N	f	5
1459	183	35	2008-04-30 23:36:45	\N	f	6
1462	184	155	2008-04-30 23:36:45	\N	f	1
1463	184	152	2008-04-30 23:36:48	\N	f	2
1464	184	145	2008-04-30 23:36:50	\N	f	3
1465	184	138	2008-04-30 23:36:53	\N	f	4
1466	184	134	2008-04-30 23:36:56	\N	f	5
1467	184	35	2008-04-30 23:37:00	\N	f	6
1470	185	154	2008-04-30 23:36:52	\N	f	1
1471	185	155	2008-04-30 23:36:53	\N	f	2
1472	185	156	2008-04-30 23:36:55	\N	f	3
1473	185	157	2008-04-30 23:36:57	\N	f	4
1474	185	158	2008-04-30 23:36:59	\N	f	5
1475	185	35	2008-04-30 23:37:01	\N	f	6
1478	186	135	2008-04-30 23:36:47	\N	f	1
1479	186	136	2008-04-30 23:36:50	\N	f	2
1480	186	137	2008-04-30 23:36:53	\N	f	3
1481	186	138	2008-04-30 23:36:55	\N	f	4
1482	186	139	2008-04-30 23:36:59	\N	f	5
1483	186	31	2008-04-30 23:37:03	\N	f	6
1486	187	135	2008-04-30 23:37:05	\N	f	1
1487	187	136	2008-04-30 23:37:08	\N	f	2
1488	187	137	2008-04-30 23:37:10	\N	f	3
1489	187	138	2008-04-30 23:37:12	\N	f	4
1490	187	139	2008-04-30 23:37:14	\N	f	5
1491	187	31	2008-04-30 23:37:17	\N	f	6
1494	188	158	2008-04-30 23:37:06	\N	f	1
1495	188	152	2008-04-30 23:37:09	\N	f	2
1496	188	159	2008-04-30 23:37:11	\N	f	3
1497	188	153	2008-04-30 23:37:14	\N	f	4
1498	188	160	2008-04-30 23:37:20	\N	f	5
1499	188	31	2008-04-30 23:37:22	\N	f	6
1502	189	153	2008-04-30 23:37:27	\N	f	1
1503	189	148	2008-04-30 23:37:29	\N	f	2
1504	189	146	2008-04-30 23:37:31	\N	f	3
1505	189	145	2008-04-30 23:37:34	\N	f	4
1506	189	144	2008-04-30 23:37:37	\N	f	5
1507	189	35	2008-04-30 23:37:40	\N	f	6
1518	191	144	2008-04-30 23:37:29	\N	f	1
1519	191	145	2008-04-30 23:37:31	\N	f	2
1520	191	146	2008-04-30 23:37:33	\N	f	3
1521	191	147	2008-04-30 23:37:36	\N	f	4
1522	191	148	2008-04-30 23:37:39	\N	f	5
1523	191	35	2008-04-30 23:37:43	\N	f	6
1526	192	142	2008-04-30 23:37:37	\N	f	1
1527	192	143	2008-04-30 23:37:39	\N	f	2
1528	192	144	2008-04-30 23:37:41	\N	f	3
1529	192	145	2008-04-30 23:37:43	\N	f	4
1530	192	146	2008-04-30 23:37:45	\N	f	5
1531	192	35	2008-04-30 23:37:48	\N	f	6
1534	193	137	2008-04-30 23:37:48	\N	f	1
1535	193	138	2008-04-30 23:37:51	\N	f	2
1536	193	139	2008-04-30 23:37:53	\N	f	3
1537	193	140	2008-04-30 23:37:55	\N	f	4
1538	193	141	2008-04-30 23:38:00	\N	f	5
1539	193	31	2008-04-30 23:38:04	\N	f	6
1542	194	157	2008-04-30 23:37:14	\N	f	1
1543	194	154	2008-04-30 23:37:21	\N	f	2
1544	194	148	2008-04-30 23:37:37	\N	f	3
1545	194	142	2008-04-30 23:37:47	\N	f	4
1546	194	135	2008-04-30 23:37:56	\N	f	5
1547	194	31	2008-04-30 23:38:06	\N	f	6
1550	195	136	2008-04-30 23:37:57	\N	f	1
1551	195	137	2008-04-30 23:37:58	\N	f	2
1552	195	138	2008-04-30 23:38:00	\N	f	3
1553	195	139	2008-04-30 23:38:02	\N	f	4
1554	195	140	2008-04-30 23:38:06	\N	f	5
1555	195	35	2008-04-30 23:38:10	\N	f	6
1558	196	140	2008-04-30 23:37:57	\N	f	1
1559	196	153	2008-04-30 23:38:00	\N	f	2
1560	196	149	2008-04-30 23:38:03	\N	f	3
1561	196	139	2008-04-30 23:38:05	\N	f	4
1562	196	152	2008-04-30 23:38:08	\N	f	5
1563	196	35	2008-04-30 23:38:12	\N	f	6
1566	197	135	2008-04-30 23:38:11	\N	f	1
1567	197	136	2008-04-30 23:38:12	\N	f	2
1568	197	137	2008-04-30 23:38:14	\N	f	3
1569	197	138	2008-04-30 23:38:16	\N	f	4
1570	197	139	2008-04-30 23:38:18	\N	f	5
1571	197	31	2008-04-30 23:38:21	\N	f	6
1574	198	139	2008-04-30 23:39:03	\N	f	1
1575	198	140	2008-04-30 23:39:06	\N	f	2
1576	198	141	2008-04-30 23:39:10	\N	f	3
1577	198	142	2008-04-30 23:39:17	\N	f	4
1578	198	143	2008-04-30 23:39:22	\N	f	5
1579	198	35	2008-04-30 23:39:30	\N	f	6
1582	199	153	2008-04-30 23:40:11	\N	f	1
1583	199	148	2008-04-30 23:40:14	\N	f	2
1584	199	146	2008-04-30 23:40:16	\N	f	3
1585	199	145	2008-04-30 23:40:18	\N	f	4
1586	199	144	2008-04-30 23:40:20	\N	f	5
1587	199	35	2008-04-30 23:40:23	\N	f	6
1590	200	159	2008-04-30 23:37:29	\N	f	1
1591	200	158	2008-04-30 23:37:31	\N	f	2
1592	200	156	2008-04-30 23:37:34	\N	f	3
1593	200	155	2008-04-30 23:37:37	\N	f	4
1594	200	154	2008-04-30 23:37:40	\N	f	5
1595	200	31	2008-04-30 23:37:44	\N	f	6
1598	201	131	2008-04-30 23:40:09	\N	f	1
1599	201	133	2008-04-30 23:40:12	\N	f	2
1600	201	135	2008-04-30 23:40:14	\N	f	3
1601	201	137	2008-04-30 23:40:17	\N	f	4
1602	201	139	2008-04-30 23:40:21	\N	f	5
1603	201	31	2008-04-30 23:40:28	\N	f	6
1606	202	136	2008-04-30 23:40:20	\N	f	1
1607	202	137	2008-04-30 23:40:21	\N	f	2
1608	202	138	2008-04-30 23:40:23	\N	f	3
1609	202	139	2008-04-30 23:40:25	\N	f	4
1610	202	140	2008-04-30 23:40:27	\N	f	5
1611	202	35	2008-04-30 23:40:30	\N	f	6
1622	204	151	2008-04-30 23:40:32	\N	f	1
1623	204	152	2008-04-30 23:40:35	\N	f	2
1624	204	153	2008-04-30 23:40:37	\N	f	3
1625	204	154	2008-04-30 23:40:41	\N	f	4
1626	204	155	2008-04-30 23:40:43	\N	f	5
1627	204	31	2008-04-30 23:40:48	\N	f	6
1630	205	156	2008-04-30 23:40:42	\N	f	1
1631	205	152	2008-04-30 23:40:50	\N	f	2
1632	205	145	2008-04-30 23:41:08	\N	f	3
1633	205	136	2008-04-30 23:41:17	\N	f	4
1634	205	132	2008-04-30 23:41:24	\N	f	5
1635	205	35	2008-04-30 23:41:31	\N	f	6
1638	206	138	2008-04-30 23:41:40	\N	f	1
1639	206	139	2008-04-30 23:41:42	\N	f	2
1640	206	140	2008-04-30 23:41:44	\N	f	3
1641	206	141	2008-04-30 23:41:46	\N	f	4
1642	206	142	2008-04-30 23:41:48	\N	f	5
1643	206	31	2008-04-30 23:41:53	\N	f	6
1646	207	153	2008-04-30 23:41:43	\N	f	1
1647	207	148	2008-04-30 23:41:47	\N	f	2
1648	207	146	2008-04-30 23:41:50	\N	f	3
1649	207	145	2008-04-30 23:41:52	\N	f	4
1650	207	144	2008-04-30 23:41:55	\N	f	5
1651	207	35	2008-04-30 23:41:58	\N	f	6
1654	208	138	2008-04-30 23:41:54	\N	f	1
1655	208	139	2008-04-30 23:41:55	\N	f	2
1656	208	140	2008-04-30 23:41:57	\N	f	3
1657	208	141	2008-04-30 23:42:00	\N	f	4
1658	208	142	2008-04-30 23:42:02	\N	f	5
1659	208	31	2008-04-30 23:42:05	\N	f	6
1662	209	141	2008-04-30 23:41:54	\N	f	1
1663	209	145	2008-04-30 23:41:58	\N	f	2
1664	209	153	2008-04-30 23:42:03	\N	f	3
1665	209	148	2008-04-30 23:42:08	\N	f	4
1666	209	149	2008-04-30 23:42:10	\N	f	5
1667	209	31	2008-04-30 23:42:14	\N	f	6
1670	210	135	2008-04-30 23:41:53	\N	f	1
1671	210	136	2008-04-30 23:41:56	\N	f	2
1672	210	137	2008-04-30 23:41:59	\N	f	3
1673	210	138	2008-04-30 23:42:02	\N	f	4
1674	210	139	2008-04-30 23:42:05	\N	f	5
1675	210	31	2008-04-30 23:42:11	\N	f	6
1678	211	156	2008-04-30 23:42:04	\N	f	1
1679	211	152	2008-04-30 23:42:08	\N	f	2
1680	211	145	2008-04-30 23:42:14	\N	f	3
1681	211	136	2008-04-30 23:42:18	\N	f	4
1682	211	132	2008-04-30 23:42:22	\N	f	5
1683	211	35	2008-04-30 23:42:29	\N	f	6
1686	212	137	2008-04-30 23:43:03	\N	f	1
1687	212	138	2008-04-30 23:43:05	\N	f	2
1688	212	139	2008-04-30 23:43:07	\N	f	3
1689	212	140	2008-04-30 23:43:09	\N	f	4
1690	212	141	2008-04-30 23:43:11	\N	f	5
1691	212	31	2008-04-30 23:43:17	\N	f	6
1694	213	158	2008-04-30 23:43:01	\N	f	1
1695	213	152	2008-04-30 23:43:07	\N	f	2
1696	213	159	2008-04-30 23:43:15	\N	f	3
1697	213	153	2008-04-30 23:43:23	\N	f	4
1698	213	160	2008-04-30 23:43:31	\N	f	5
1699	213	31	2008-04-30 23:43:38	\N	f	6
1704	215	137	2008-04-30 23:44:19	\N	f	1
1705	215	138	2008-04-30 23:44:20	\N	f	2
1706	215	139	2008-04-30 23:44:22	\N	f	3
1707	215	140	2008-04-30 23:44:24	\N	f	4
1708	215	141	2008-04-30 23:44:28	\N	f	5
1709	215	31	2008-04-30 23:44:32	\N	f	6
1712	216	155	2008-04-30 23:44:17	\N	f	1
1713	216	152	2008-04-30 23:44:20	\N	f	2
1714	216	145	2008-04-30 23:44:22	\N	f	3
1715	216	138	2008-04-30 23:44:25	\N	f	4
1716	216	134	2008-04-30 23:44:29	\N	f	5
1717	216	35	2008-04-30 23:44:35	\N	f	6
1720	217	160	2008-04-30 23:44:47	\N	f	1
1721	217	159	2008-04-30 23:44:50	\N	f	2
1722	217	158	2008-04-30 23:44:52	\N	f	3
1723	217	157	2008-04-30 23:44:54	\N	f	4
1724	217	156	2008-04-30 23:44:56	\N	f	5
1725	217	31	2008-04-30 23:44:59	\N	f	6
1728	218	136	2008-04-30 23:44:46	\N	f	1
1729	218	137	2008-04-30 23:44:48	\N	f	2
1730	218	138	2008-04-30 23:44:51	\N	f	3
1731	218	139	2008-04-30 23:44:55	\N	f	4
1732	218	140	2008-04-30 23:44:57	\N	f	5
1733	218	35	2008-04-30 23:45:05	\N	f	6
1736	219	160	2008-04-30 23:45:16	\N	f	1
1737	219	159	2008-04-30 23:45:18	\N	f	2
1738	219	158	2008-04-30 23:45:21	\N	f	3
1739	219	157	2008-04-30 23:45:23	\N	f	4
1740	219	156	2008-04-30 23:45:25	\N	f	5
1741	219	31	2008-04-30 23:45:30	\N	f	6
1752	221	148	2008-04-30 23:45:06	\N	f	1
1753	221	142	2008-04-30 23:45:13	\N	f	2
1754	221	146	2008-04-30 23:45:19	\N	f	3
1755	221	145	2008-04-30 23:45:23	\N	f	4
1756	221	143	2008-04-30 23:45:27	\N	f	5
1757	221	31	2008-04-30 23:45:38	\N	f	6
1768	223	156	2008-04-30 23:45:27	\N	f	1
1769	223	152	2008-04-30 23:45:30	\N	f	2
1770	223	145	2008-04-30 23:45:33	\N	f	3
1771	223	136	2008-04-30 23:45:36	\N	f	4
1772	223	132	2008-04-30 23:45:39	\N	f	5
1773	223	35	2008-04-30 23:45:43	\N	f	6
1776	224	160	2008-04-30 23:45:34	\N	f	1
1777	224	159	2008-04-30 23:45:36	\N	f	2
1778	224	158	2008-04-30 23:45:38	\N	f	3
1779	224	157	2008-04-30 23:45:40	\N	f	4
1780	224	156	2008-04-30 23:45:42	\N	f	5
1781	224	31	2008-04-30 23:45:44	\N	f	6
1784	225	136	2008-04-30 23:45:58	\N	f	1
1785	225	137	2008-04-30 23:46:00	\N	f	2
1786	225	138	2008-04-30 23:46:01	\N	f	3
1787	225	139	2008-04-30 23:46:04	\N	f	4
1788	225	140	2008-04-30 23:46:06	\N	f	5
1789	225	35	2008-04-30 23:46:10	\N	f	6
1792	226	137	2008-04-30 23:46:10	\N	f	1
1793	226	138	2008-04-30 23:46:13	\N	f	2
1794	226	139	2008-04-30 23:46:15	\N	f	3
1795	226	140	2008-04-30 23:46:18	\N	f	4
1796	226	141	2008-04-30 23:46:20	\N	f	5
1797	226	31	2008-04-30 23:46:25	\N	f	6
1800	227	159	2008-04-30 23:46:31	\N	f	1
1801	227	158	2008-04-30 23:46:33	\N	f	2
1802	227	156	2008-04-30 23:46:35	\N	f	3
1803	227	155	2008-04-30 23:46:37	\N	f	4
1804	227	154	2008-04-30 23:46:39	\N	f	5
1805	227	31	2008-04-30 23:46:42	\N	f	6
1808	228	140	2008-04-30 23:46:26	\N	f	1
1809	228	153	2008-04-30 23:46:32	\N	f	2
1810	228	149	2008-04-30 23:46:36	\N	f	3
1811	228	139	2008-04-30 23:46:42	\N	f	4
1812	228	152	2008-04-30 23:46:48	\N	f	5
1813	228	35	2008-04-30 23:46:55	\N	f	6
1816	229	135	2008-04-30 23:47:22	\N	f	1
1817	229	136	2008-04-30 23:47:25	\N	f	2
1818	229	137	2008-04-30 23:47:28	\N	f	3
1819	229	138	2008-04-30 23:47:32	\N	f	4
1820	229	139	2008-04-30 23:47:34	\N	f	5
1821	229	31	2008-04-30 23:47:41	\N	f	6
1824	230	160	2008-04-30 23:47:44	\N	f	1
1825	230	159	2008-04-30 23:47:46	\N	f	2
1826	230	158	2008-04-30 23:47:48	\N	f	3
1827	230	157	2008-04-30 23:47:50	\N	f	4
1828	230	156	2008-04-30 23:47:52	\N	f	5
1829	230	31	2008-04-30 23:47:55	\N	f	6
1832	231	138	2008-04-30 23:47:49	\N	f	1
1833	231	139	2008-04-30 23:47:51	\N	f	2
1834	231	140	2008-04-30 23:47:53	\N	f	3
1835	231	141	2008-04-30 23:47:55	\N	f	4
1836	231	142	2008-04-30 23:47:57	\N	f	5
1837	231	31	2008-04-30 23:48:00	\N	f	6
1840	232	159	2008-04-30 23:47:51	\N	f	1
1841	232	158	2008-04-30 23:47:54	\N	f	2
1842	232	156	2008-04-30 23:47:55	\N	f	3
1843	232	155	2008-04-30 23:47:57	\N	f	4
1844	232	154	2008-04-30 23:48:01	\N	f	5
1845	232	31	2008-04-30 23:48:06	\N	f	6
1848	233	159	2008-04-30 23:48:07	\N	f	1
1849	233	158	2008-04-30 23:48:09	\N	f	2
1850	233	156	2008-04-30 23:48:12	\N	f	3
1851	233	155	2008-04-30 23:48:14	\N	f	4
1852	233	154	2008-04-30 23:48:16	\N	f	5
1853	233	31	2008-04-30 23:48:20	\N	f	6
1856	234	137	2008-04-30 23:48:25	\N	f	1
1857	234	138	2008-04-30 23:48:27	\N	f	2
1858	234	139	2008-04-30 23:48:28	\N	f	3
1859	234	140	2008-04-30 23:48:30	\N	f	4
1860	234	141	2008-04-30 23:48:32	\N	f	5
1861	234	31	2008-04-30 23:48:36	\N	f	6
1864	235	153	2008-04-30 23:48:21	\N	f	1
1865	235	148	2008-04-30 23:48:25	\N	f	2
1866	235	146	2008-04-30 23:48:29	\N	f	3
1867	235	145	2008-04-30 23:48:32	\N	f	4
1868	235	144	2008-04-30 23:48:34	\N	f	5
1869	235	35	2008-04-30 23:48:39	\N	f	6
1872	236	158	2008-04-30 23:48:12	\N	f	1
1873	236	156	2008-04-30 23:48:15	\N	f	2
1874	236	150	2008-04-30 23:48:26	\N	f	3
1875	236	147	2008-04-30 23:48:30	\N	f	4
1876	236	140	2008-04-30 23:48:36	\N	f	5
1877	236	35	2008-04-30 23:48:42	\N	f	6
1880	237	156	2008-04-30 23:48:29	\N	f	1
1881	237	152	2008-04-30 23:48:32	\N	f	2
1882	237	145	2008-04-30 23:48:35	\N	f	3
1883	237	136	2008-04-30 23:48:38	\N	f	4
1884	237	132	2008-04-30 23:48:41	\N	f	5
1885	237	35	2008-04-30 23:48:45	\N	f	6
1888	238	158	2008-04-30 23:48:34	\N	f	1
1889	238	156	2008-04-30 23:48:36	\N	f	2
1890	238	150	2008-04-30 23:48:39	\N	f	3
1891	238	147	2008-04-30 23:48:42	\N	f	4
1892	238	140	2008-04-30 23:48:47	\N	f	5
1893	238	35	2008-04-30 23:48:50	\N	f	6
1896	239	137	2008-04-30 23:48:44	\N	f	1
1897	239	138	2008-04-30 23:48:47	\N	f	2
1898	239	139	2008-04-30 23:48:49	\N	f	3
1899	239	140	2008-04-30 23:48:51	\N	f	4
1900	239	141	2008-04-30 23:48:53	\N	f	5
1901	239	31	2008-04-30 23:49:00	\N	f	6
1904	240	159	2008-04-30 23:49:00	\N	f	1
1905	240	158	2008-04-30 23:49:01	\N	f	2
1906	240	156	2008-04-30 23:49:03	\N	f	3
1907	240	155	2008-04-30 23:49:05	\N	f	4
1908	240	154	2008-04-30 23:49:07	\N	f	5
1909	240	31	2008-04-30 23:49:08	\N	f	6
1912	241	148	2008-04-30 23:48:54	\N	f	1
1913	241	147	2008-04-30 23:48:57	\N	f	2
1914	241	146	2008-04-30 23:48:59	\N	f	3
1915	241	145	2008-04-30 23:49:02	\N	f	4
1916	241	143	2008-04-30 23:49:05	\N	f	5
1917	241	31	2008-04-30 23:49:11	\N	f	6
1920	242	160	2008-04-30 23:49:17	\N	f	1
1921	242	159	2008-04-30 23:49:18	\N	f	2
1922	242	158	2008-04-30 23:49:20	\N	f	3
1923	242	157	2008-04-30 23:49:22	\N	f	4
1924	242	156	2008-04-30 23:49:24	\N	f	5
1925	242	31	2008-04-30 23:49:26	\N	f	6
1928	243	157	2008-04-30 23:49:26	\N	f	1
1929	243	154	2008-04-30 23:49:28	\N	f	2
1930	243	148	2008-04-30 23:49:32	\N	f	3
1931	243	142	2008-04-30 23:49:35	\N	f	4
1932	243	135	2008-04-30 23:49:39	\N	f	5
1933	243	31	2008-04-30 23:49:45	\N	f	6
1945	245	157	2008-04-30 23:49:24	\N	f	1
1946	245	154	2008-04-30 23:49:27	\N	f	2
1947	245	148	2008-04-30 23:49:30	\N	f	3
1948	245	142	2008-04-30 23:49:37	\N	f	4
1949	245	135	2008-04-30 23:49:41	\N	f	5
1950	245	31	2008-04-30 23:49:50	\N	f	6
1953	246	148	2008-04-30 23:49:35	\N	f	1
1954	246	147	2008-04-30 23:49:38	\N	f	2
1955	246	146	2008-04-30 23:49:40	\N	f	3
1956	246	145	2008-04-30 23:49:43	\N	f	4
1957	246	143	2008-04-30 23:49:45	\N	f	5
1958	246	31	2008-04-30 23:49:49	\N	f	6
1961	247	137	2008-04-30 23:49:45	\N	f	1
1962	247	138	2008-04-30 23:49:47	\N	f	2
1963	247	139	2008-04-30 23:49:49	\N	f	3
1964	247	140	2008-04-30 23:49:51	\N	f	4
1965	247	141	2008-04-30 23:49:53	\N	f	5
1966	247	31	2008-04-30 23:49:56	\N	f	6
1969	248	157	2008-04-30 23:49:46	\N	f	1
1970	248	154	2008-04-30 23:49:50	\N	f	2
1971	248	148	2008-04-30 23:49:55	\N	f	3
1972	248	142	2008-04-30 23:49:58	\N	f	4
1973	248	135	2008-04-30 23:50:02	\N	f	5
1974	248	31	2008-04-30 23:50:08	\N	f	6
1977	249	148	2008-04-30 23:50:04	\N	f	1
1978	249	147	2008-04-30 23:50:06	\N	f	2
1979	249	146	2008-04-30 23:50:08	\N	f	3
1980	249	145	2008-04-30 23:50:10	\N	f	4
1981	249	143	2008-04-30 23:50:12	\N	f	5
1982	249	31	2008-04-30 23:50:16	\N	f	6
1985	250	140	2008-04-30 23:49:53	\N	f	1
1986	250	153	2008-04-30 23:50:02	\N	f	2
1987	250	149	2008-04-30 23:50:16	\N	f	3
1988	250	139	2008-04-30 23:50:26	\N	f	4
1989	250	152	2008-04-30 23:50:36	\N	f	5
1990	250	35	2008-04-30 23:50:40	\N	f	6
1993	251	140	2008-04-30 23:46:26	\N	f	1
1994	251	153	2008-04-30 23:46:32	\N	f	2
1995	251	149	2008-04-30 23:46:36	\N	f	3
1996	251	139	2008-04-30 23:46:42	\N	f	4
1997	251	152	2008-04-30 23:46:48	\N	f	5
1998	251	35	2008-04-30 23:46:55	\N	f	6
1999	251	148	2008-04-30 23:50:44	\N	f	7
2000	251	147	2008-04-30 23:50:47	\N	f	8
2001	251	146	2008-04-30 23:50:49	\N	f	9
2002	251	145	2008-04-30 23:50:52	\N	f	10
2003	251	143	2008-04-30 23:50:54	\N	f	11
2004	251	31	2008-04-30 23:51:01	\N	f	12
2007	252	157	2008-04-30 23:50:53	\N	f	1
2008	252	154	2008-04-30 23:50:55	\N	f	2
2009	252	148	2008-04-30 23:50:58	\N	f	3
2010	252	142	2008-04-30 23:51:01	\N	f	4
2011	252	135	2008-04-30 23:51:05	\N	f	5
2012	252	31	2008-04-30 23:51:10	\N	f	6
2015	253	159	2008-04-30 23:50:59	\N	f	1
2016	253	158	2008-04-30 23:51:01	\N	f	2
2017	253	156	2008-04-30 23:51:05	\N	f	3
2018	253	155	2008-04-30 23:51:07	\N	f	4
2019	253	154	2008-04-30 23:51:09	\N	f	5
2020	253	31	2008-04-30 23:51:11	\N	f	6
2023	254	140	2008-04-30 23:51:06	\N	f	1
2024	254	153	2008-04-30 23:51:09	\N	f	2
2025	254	149	2008-04-30 23:51:12	\N	f	3
2026	254	139	2008-04-30 23:51:16	\N	f	4
2027	254	152	2008-04-30 23:51:20	\N	f	5
2028	254	35	2008-04-30 23:51:22	\N	f	6
2031	255	156	2008-04-30 23:51:03	\N	f	1
2032	255	152	2008-04-30 23:51:07	\N	f	2
2033	255	145	2008-04-30 23:51:12	\N	f	3
2034	255	136	2008-04-30 23:51:15	\N	f	4
2035	255	132	2008-04-30 23:51:18	\N	f	5
2036	255	35	2008-04-30 23:51:23	\N	f	6
2039	256	158	2008-04-30 23:51:19	\N	f	1
2040	256	152	2008-04-30 23:51:23	\N	f	2
2041	256	159	2008-04-30 23:51:27	\N	f	3
2042	256	153	2008-04-30 23:51:30	\N	f	4
2043	256	160	2008-04-30 23:51:34	\N	f	5
2044	256	31	2008-04-30 23:51:37	\N	f	6
2047	257	158	2008-04-30 23:51:50	\N	f	1
2048	257	152	2008-04-30 23:51:52	\N	f	2
2049	257	159	2008-04-30 23:51:55	\N	f	3
2050	257	153	2008-04-30 23:51:57	\N	f	4
2051	257	160	2008-04-30 23:51:59	\N	f	5
2052	257	31	2008-04-30 23:52:01	\N	f	6
2055	258	148	2008-04-30 23:51:54	\N	f	1
2056	258	147	2008-04-30 23:51:57	\N	f	2
2057	258	146	2008-04-30 23:51:59	\N	f	3
2058	258	145	2008-04-30 23:52:02	\N	f	4
2059	258	143	2008-04-30 23:52:04	\N	f	5
2060	258	31	2008-04-30 23:52:06	\N	f	6
2063	259	131	2008-04-30 23:51:42	\N	f	1
2064	259	133	2008-04-30 23:51:46	\N	f	2
2065	259	135	2008-04-30 23:51:50	\N	f	3
2066	259	137	2008-04-30 23:51:56	\N	f	4
2067	259	139	2008-04-30 23:52:02	\N	f	5
2068	259	31	2008-04-30 23:52:09	\N	f	6
2071	260	158	2008-04-30 23:52:01	\N	f	1
2072	260	152	2008-04-30 23:52:04	\N	f	2
2073	260	159	2008-04-30 23:52:06	\N	f	3
2074	260	153	2008-04-30 23:52:09	\N	f	4
2075	260	160	2008-04-30 23:52:12	\N	f	5
2076	260	31	2008-04-30 23:52:14	\N	f	6
2085	262	155	2008-04-30 23:52:17	\N	f	1
2086	262	152	2008-04-30 23:52:19	\N	f	2
2087	262	145	2008-04-30 23:52:22	\N	f	3
2088	262	138	2008-04-30 23:52:26	\N	f	4
2089	262	134	2008-04-30 23:52:29	\N	f	5
2090	262	35	2008-04-30 23:52:34	\N	f	6
2093	263	138	2008-04-30 23:52:22	\N	f	1
2094	263	139	2008-04-30 23:52:27	\N	f	2
2095	263	140	2008-04-30 23:52:30	\N	f	3
2096	263	141	2008-04-30 23:52:34	\N	f	4
2097	263	142	2008-04-30 23:52:36	\N	f	5
2098	263	31	2008-04-30 23:52:41	\N	f	6
2101	264	131	2008-04-30 23:52:07	\N	f	1
2102	264	133	2008-04-30 23:52:10	\N	f	2
2103	264	135	2008-04-30 23:52:12	\N	f	3
2104	264	137	2008-04-30 23:52:15	\N	f	4
2105	264	139	2008-04-30 23:52:18	\N	f	5
2106	264	31	2008-04-30 23:52:25	\N	f	6
2109	265	158	2008-04-30 23:52:33	\N	f	1
2110	265	156	2008-04-30 23:52:35	\N	f	2
2111	265	150	2008-04-30 23:52:38	\N	f	3
2112	265	147	2008-04-30 23:52:40	\N	f	4
2113	265	140	2008-04-30 23:52:43	\N	f	5
2114	265	35	2008-04-30 23:52:46	\N	f	6
2125	267	140	2008-04-30 23:52:28	\N	f	1
2126	267	153	2008-04-30 23:52:32	\N	f	2
2127	267	149	2008-04-30 23:52:35	\N	f	3
2128	267	139	2008-04-30 23:52:39	\N	f	4
2129	267	152	2008-04-30 23:52:43	\N	f	5
2130	267	35	2008-04-30 23:52:47	\N	f	6
2149	270	131	2008-04-30 23:52:49	\N	f	1
2150	270	133	2008-04-30 23:52:50	\N	f	2
2151	270	135	2008-04-30 23:52:52	\N	f	3
2152	270	137	2008-04-30 23:52:55	\N	f	4
2153	270	139	2008-04-30 23:52:57	\N	f	5
2154	270	31	2008-04-30 23:53:00	\N	f	6
2157	271	153	2008-04-30 23:53:10	\N	f	1
2158	271	148	2008-04-30 23:53:15	\N	f	2
2159	271	146	2008-04-30 23:53:18	\N	f	3
2160	271	145	2008-04-30 23:53:20	\N	f	4
2161	271	144	2008-04-30 23:53:22	\N	f	5
2162	271	35	2008-04-30 23:53:28	\N	f	6
2165	272	141	2008-04-30 23:52:59	\N	f	1
2166	272	145	2008-04-30 23:53:03	\N	f	2
2167	272	153	2008-04-30 23:53:17	\N	f	3
2168	272	148	2008-04-30 23:53:29	\N	f	4
2169	272	149	2008-04-30 23:53:32	\N	f	5
2170	272	31	2008-04-30 23:53:40	\N	f	6
2173	273	131	2008-04-30 23:53:31	\N	f	1
2174	273	133	2008-04-30 23:53:33	\N	f	2
2175	273	135	2008-04-30 23:53:35	\N	f	3
2176	273	137	2008-04-30 23:53:37	\N	f	4
2177	273	139	2008-04-30 23:53:38	\N	f	5
2178	273	31	2008-04-30 23:53:41	\N	f	6
2181	274	158	2008-04-30 23:53:20	\N	f	1
2182	274	156	2008-04-30 23:53:28	\N	f	2
2183	274	150	2008-04-30 23:53:33	\N	f	3
2184	274	147	2008-04-30 23:53:37	\N	f	4
2185	274	140	2008-04-30 23:53:42	\N	f	5
2186	274	35	2008-04-30 23:53:47	\N	f	6
2189	275	153	2008-04-30 23:53:37	\N	f	1
2190	275	148	2008-04-30 23:53:40	\N	f	2
2191	275	146	2008-04-30 23:53:42	\N	f	3
2192	275	145	2008-04-30 23:53:44	\N	f	4
2193	275	144	2008-04-30 23:53:46	\N	f	5
2194	275	35	2008-04-30 23:53:49	\N	f	6
2197	276	141	2008-04-30 23:53:31	\N	f	1
2198	276	145	2008-04-30 23:53:34	\N	f	2
2199	276	153	2008-04-30 23:53:40	\N	f	3
2200	276	148	2008-04-30 23:53:44	\N	f	4
2201	276	149	2008-04-30 23:53:47	\N	f	5
2202	276	31	2008-04-30 23:53:51	\N	f	6
2205	277	141	2008-04-30 23:54:27	\N	f	1
2206	277	145	2008-04-30 23:54:29	\N	f	2
2207	277	153	2008-04-30 23:54:32	\N	f	3
2208	277	148	2008-04-30 23:54:34	\N	f	4
2209	277	149	2008-04-30 23:54:36	\N	f	5
2210	277	31	2008-04-30 23:54:39	\N	f	6
2227	279	158	2008-04-30 23:54:42	\N	f	1
2228	279	152	2008-04-30 23:54:45	\N	f	2
2229	279	159	2008-04-30 23:54:48	\N	f	3
2230	279	153	2008-04-30 23:54:54	\N	f	4
2231	279	160	2008-04-30 23:54:59	\N	f	5
2232	279	31	2008-04-30 23:55:04	\N	f	6
2235	280	135	2008-04-30 23:55:04	\N	f	1
2236	280	136	2008-04-30 23:55:07	\N	f	2
2237	280	137	2008-04-30 23:55:09	\N	f	3
2238	280	138	2008-04-30 23:55:12	\N	f	4
2239	280	139	2008-04-30 23:55:15	\N	f	5
2240	280	31	2008-04-30 23:55:20	\N	f	6
2243	281	155	2008-04-30 23:55:15	\N	f	1
2244	281	152	2008-04-30 23:55:18	\N	f	2
2245	281	145	2008-04-30 23:55:22	\N	f	3
2246	281	138	2008-04-30 23:55:25	\N	f	4
2247	281	134	2008-04-30 23:55:27	\N	f	5
2248	281	35	2008-04-30 23:55:32	\N	f	6
2251	282	137	2008-04-30 23:55:22	\N	f	1
2252	282	131	2008-04-30 23:55:24	\N	f	2
2253	282	156	2008-04-30 23:55:28	\N	f	3
2254	282	160	2008-04-30 23:55:30	\N	f	4
2255	282	147	2008-04-30 23:55:34	\N	f	5
2256	282	35	2008-04-30 23:55:38	\N	f	6
2259	283	137	2008-04-30 23:55:30	\N	f	1
2260	283	131	2008-04-30 23:55:34	\N	f	2
2261	283	156	2008-04-30 23:55:39	\N	f	3
2262	283	160	2008-04-30 23:55:43	\N	f	4
2263	283	147	2008-04-30 23:55:46	\N	f	5
2264	283	35	2008-04-30 23:55:48	\N	f	6
2267	284	148	2008-04-30 23:55:50	\N	f	1
2268	284	147	2008-04-30 23:55:51	\N	f	2
2269	284	146	2008-04-30 23:55:53	\N	f	3
2270	284	145	2008-04-30 23:55:55	\N	f	4
2271	284	143	2008-04-30 23:55:56	\N	f	5
2272	284	31	2008-04-30 23:56:01	\N	f	6
2275	285	148	2008-04-30 23:56:03	\N	f	1
2276	285	155	2008-04-30 23:56:05	\N	f	2
2277	285	147	2008-04-30 23:56:07	\N	f	3
2278	285	154	2008-04-30 23:56:10	\N	f	4
2279	285	146	2008-04-30 23:56:14	\N	f	5
2280	285	31	2008-04-30 23:56:16	\N	f	6
2283	286	148	2008-04-30 23:56:10	\N	f	1
2284	286	155	2008-04-30 23:56:14	\N	f	2
2285	286	147	2008-04-30 23:56:16	\N	f	3
2286	286	154	2008-04-30 23:56:19	\N	f	4
2287	286	146	2008-04-30 23:56:21	\N	f	5
2288	286	31	2008-04-30 23:56:25	\N	f	6
2291	287	140	2008-04-30 23:56:02	\N	f	1
2292	287	153	2008-04-30 23:56:10	\N	f	2
2293	287	149	2008-04-30 23:56:16	\N	f	3
2294	287	139	2008-04-30 23:56:22	\N	f	4
2295	287	152	2008-04-30 23:56:27	\N	f	5
2296	287	35	2008-04-30 23:56:30	\N	f	6
2299	288	140	2008-04-30 23:56:33	\N	f	1
2300	288	153	2008-04-30 23:56:38	\N	f	2
2301	288	149	2008-04-30 23:56:41	\N	f	3
2302	288	139	2008-04-30 23:56:45	\N	f	4
2303	288	152	2008-04-30 23:56:50	\N	f	5
2304	288	35	2008-04-30 23:56:53	\N	f	6
2307	289	136	2008-04-30 23:56:54	\N	f	1
2308	289	137	2008-04-30 23:56:56	\N	f	2
2309	289	138	2008-04-30 23:56:57	\N	f	3
2310	289	139	2008-04-30 23:56:59	\N	f	4
2311	289	140	2008-04-30 23:57:01	\N	f	5
2312	289	35	2008-04-30 23:57:04	\N	f	6
2315	290	153	2008-04-30 23:57:09	\N	f	1
2316	290	148	2008-04-30 23:57:15	\N	f	2
2317	290	146	2008-04-30 23:57:17	\N	f	3
2318	290	145	2008-04-30 23:57:20	\N	f	4
2319	290	144	2008-04-30 23:57:22	\N	f	5
2320	290	35	2008-04-30 23:57:25	\N	f	6
2323	291	153	2008-04-30 23:56:37	\N	f	1
2324	291	146	2008-04-30 23:56:39	\N	f	2
2325	291	154	2008-04-30 23:56:42	\N	f	3
2326	291	147	2008-04-30 23:56:45	\N	f	4
2327	291	155	2008-04-30 23:56:48	\N	f	5
2328	291	35	2008-04-30 23:56:50	\N	f	6
2331	292	153	2008-04-30 23:56:52	\N	f	1
2332	292	146	2008-04-30 23:56:54	\N	f	2
2333	292	154	2008-04-30 23:57:00	\N	f	3
2334	292	147	2008-04-30 23:57:03	\N	f	4
2335	292	155	2008-04-30 23:57:06	\N	f	5
2336	292	35	2008-04-30 23:57:08	\N	f	6
2339	293	131	2008-04-30 23:57:22	\N	f	1
2340	293	133	2008-04-30 23:57:24	\N	f	2
2341	293	135	2008-04-30 23:57:26	\N	f	3
2342	293	137	2008-04-30 23:57:28	\N	f	4
2343	293	139	2008-04-30 23:57:31	\N	f	5
2344	293	31	2008-04-30 23:57:37	\N	f	6
2347	294	138	2008-04-30 23:57:28	\N	f	1
2348	294	139	2008-04-30 23:57:30	\N	f	2
2349	294	140	2008-04-30 23:57:32	\N	f	3
2350	294	141	2008-04-30 23:57:34	\N	f	4
2351	294	142	2008-04-30 23:57:36	\N	f	5
2352	294	31	2008-04-30 23:57:39	\N	f	6
2367	297	159	2008-04-30 23:57:53	\N	f	1
2368	297	151	2008-04-30 23:57:56	\N	f	2
2369	297	157	2008-04-30 23:57:59	\N	f	3
2370	297	150	2008-04-30 23:58:03	\N	f	4
2371	297	158	2008-04-30 23:58:06	\N	f	5
2372	297	31	2008-04-30 23:58:08	\N	f	6
2375	298	158	2008-04-30 23:58:13	\N	f	1
2376	298	156	2008-04-30 23:58:16	\N	f	2
2377	298	150	2008-04-30 23:58:19	\N	f	3
2378	298	147	2008-04-30 23:58:21	\N	f	4
2379	298	140	2008-04-30 23:58:25	\N	f	5
2380	298	35	2008-04-30 23:58:28	\N	f	6
2383	299	155	2008-04-30 23:58:07	\N	f	1
2384	299	152	2008-04-30 23:58:11	\N	f	2
2385	299	145	2008-04-30 23:58:15	\N	f	3
2386	299	138	2008-04-30 23:58:21	\N	f	4
2387	299	134	2008-04-30 23:58:25	\N	f	5
2388	299	35	2008-04-30 23:58:31	\N	f	6
2391	300	141	2008-04-30 23:58:14	\N	f	1
2392	300	145	2008-04-30 23:58:18	\N	f	2
2393	300	153	2008-04-30 23:58:23	\N	f	3
2394	300	148	2008-04-30 23:58:27	\N	f	4
2395	300	149	2008-04-30 23:58:28	\N	f	5
2396	300	31	2008-04-30 23:58:32	\N	f	6
2399	301	159	2008-04-30 23:58:51	\N	f	1
2400	301	151	2008-04-30 23:58:53	\N	f	2
2401	301	157	2008-04-30 23:58:57	\N	f	3
2402	301	150	2008-04-30 23:59:00	\N	f	4
2403	301	158	2008-04-30 23:59:03	\N	f	5
2404	301	31	2008-04-30 23:59:05	\N	f	6
2407	302	135	2008-04-30 23:59:10	\N	f	1
2408	302	136	2008-04-30 23:59:11	\N	f	2
2409	302	137	2008-04-30 23:59:13	\N	f	3
2410	302	138	2008-04-30 23:59:14	\N	f	4
2411	302	139	2008-04-30 23:59:16	\N	f	5
2412	302	31	2008-04-30 23:59:19	\N	f	6
2415	303	136	2008-04-30 23:59:33	\N	f	1
2416	303	137	2008-04-30 23:59:35	\N	f	2
2417	303	138	2008-04-30 23:59:37	\N	f	3
2418	303	139	2008-04-30 23:59:39	\N	f	4
2419	303	140	2008-04-30 23:59:42	\N	f	5
2420	303	35	2008-04-30 23:59:46	\N	f	6
2423	304	137	2008-04-30 23:59:29	\N	f	1
2424	304	131	2008-04-30 23:59:32	\N	f	2
2425	304	156	2008-04-30 23:59:38	\N	f	3
2426	304	160	2008-04-30 23:59:42	\N	f	4
2427	304	147	2008-04-30 23:59:47	\N	f	5
2428	304	35	2008-04-30 23:59:54	\N	f	6
2431	305	131	2008-04-30 23:59:44	\N	f	1
2432	305	133	2008-04-30 23:59:46	\N	f	2
2433	305	135	2008-04-30 23:59:48	\N	f	3
2434	305	137	2008-04-30 23:59:50	\N	f	4
2435	305	139	2008-04-30 23:59:52	\N	f	5
2436	305	31	2008-04-30 23:59:56	\N	f	6
2439	306	131	2008-05-01 00:00:18	\N	f	1
2440	306	133	2008-05-01 00:00:20	\N	f	2
2441	306	135	2008-05-01 00:00:22	\N	f	3
2442	306	137	2008-05-01 00:00:24	\N	f	4
2443	306	139	2008-05-01 00:00:26	\N	f	5
2444	306	31	2008-05-01 00:00:31	\N	f	6
2453	308	141	2008-05-01 00:00:23	\N	f	1
2454	308	145	2008-05-01 00:00:26	\N	f	2
2455	308	153	2008-05-01 00:00:30	\N	f	3
2456	308	148	2008-05-01 00:00:33	\N	f	4
2457	308	149	2008-05-01 00:00:34	\N	f	5
2458	308	31	2008-05-01 00:00:37	\N	f	6
2461	309	148	2008-05-01 00:00:28	\N	f	1
2462	309	155	2008-05-01 00:00:31	\N	f	2
2463	309	147	2008-05-01 00:00:37	\N	f	3
2464	309	154	2008-05-01 00:00:41	\N	f	4
2465	309	146	2008-05-01 00:00:46	\N	f	5
2466	309	31	2008-05-01 00:00:52	\N	f	6
711	90	139	2008-04-30 23:13:46	\N	f	1
712	90	140	2008-04-30 23:13:49	\N	f	2
713	90	141	2008-04-30 23:13:52	\N	f	3
714	90	142	2008-04-30 23:13:54	\N	f	4
715	90	143	2008-04-30 23:13:57	\N	f	5
716	90	35	2008-04-30 23:14:00	\N	f	6
353	47	137	2008-04-30 14:50:29	\N	f	1
354	47	138	2008-04-30 14:53:56	\N	f	2
355	47	140	2008-04-30 14:57:27	\N	f	3
356	47	143	2008-04-30 15:01:03	\N	f	4
357	47	144	2008-04-30 15:04:07	\N	f	5
359	47	152	2008-04-30 15:18:05	\N	f	7
360	47	155	2008-04-30 15:22:09	\N	f	8
361	47	159	2008-04-30 15:27:07	\N	f	9
362	47	160	2008-04-30 15:32:43	\N	f	10
363	47	133	2008-04-30 22:58:32	\N	f	11
364	47	134	2008-04-30 22:58:35	\N	f	12
365	47	135	2008-04-30 22:58:39	\N	f	13
366	47	136	2008-04-30 22:58:43	\N	f	14
367	47	137	2008-04-30 22:58:46	\N	f	15
368	47	31	2008-04-30 22:58:54	\N	f	16
2473	223	1	\N	2008-04-30 23:43:50	f	\N
2475	214	2	\N	2008-04-30 23:43:00	f	\N
2476	315	2	\N	2008-04-30 23:25:01	f	\N
1935	244	4	2008-04-30 16:57:35	\N	f	\N
2477	244	156	2008-04-30 23:36:12	\N	f	1
2478	244	152	2008-04-30 23:36:16	\N	f	2
2479	244	145	2008-04-30 23:36:22	\N	f	3
2480	244	136	2008-04-30 23:36:27	\N	f	4
2481	244	132	2008-04-30 23:36:30	\N	f	5
2482	244	35	2008-04-30 23:36:39	\N	f	6
1936	244	158	2008-04-30 23:49:21	\N	f	7
1937	244	152	2008-04-30 23:49:29	\N	f	8
1938	244	159	2008-04-30 23:49:34	\N	f	9
1939	244	153	2008-04-30 23:49:38	\N	f	10
1940	244	160	2008-04-30 23:49:41	\N	f	11
1941	244	31	2008-04-30 23:49:44	\N	f	12
1942	244	31	2008-04-30 23:49:47	\N	f	13
\.


--
-- Data for Name: run; Type: TABLE DATA; Schema: public; Owner: gaudenz
--

COPY run (id, sicard, course, complete, override, readout_time) FROM stdin;
64	61624	14	t	\N	\N
40	61511	3	t	\N	\N
41	62755	1	t	\N	\N
33	61878	4	t	\N	\N
34	61586	1	t	\N	\N
35	61508	1	t	\N	\N
36	61764	4	t	\N	\N
37	61703	3	t	\N	\N
38	61555	1	t	\N	\N
39	61726	4	t	\N	\N
42	61706	2	t	\N	\N
65	61854	20	t	\N	\N
43	61679	3	t	\N	\N
44	60344	2	t	\N	\N
45	61530	2	t	\N	\N
56	61713	1	t	\N	\N
47	62705	3	t	\N	\N
49	61751	1	t	\N	\N
50	61647	4	t	\N	\N
51	62631	3	t	\N	\N
57	62679	10	t	\N	\N
58	61820	2	t	\N	\N
59	61583	13	t	\N	\N
74	61569	13	t	\N	\N
66	61515	4	t	\N	\N
54	61516	2	t	\N	\N
67	62741	11	t	\N	\N
68	62733	2	t	\N	\N
75	61878	15	t	\N	\N
55	61741	9	t	\N	\N
70	62755	11	t	\N	\N
76	61670	26	t	\N	\N
73	61519	1	t	\N	\N
84	61891	27	t	\N	\N
78	61508	24	t	\N	\N
83	61743	25	t	\N	\N
79	61706	12	t	\N	\N
80	61586	10	t	\N	\N
81	61555	11	t	\N	\N
82	61734	2	t	\N	\N
86	61679	13	t	\N	\N
87	60344	11	t	\N	\N
88	61726	24	t	\N	\N
89	61651	20	t	\N	\N
90	61703	9	t	\N	\N
102	61713	25	t	\N	\N
103	61583	16	t	\N	\N
93	60990	26	t	\N	\N
94	61648	30	t	\N	\N
95	62631	12	t	\N	\N
96	61855	15	t	\N	\N
97	62705	15	t	\N	\N
98	61530	22	t	\N	\N
99	61647	14	t	\N	\N
120	61515	18	t	\N	\N
121	60969	30	t	\N	\N
101	61536	2	t	\N	\N
105	61511	16	t	\N	\N
109	61741	15	t	\N	\N
106	62766	19	t	\N	\N
107	61516	16	t	\N	\N
108	61743	27	t	\N	\N
114	62741	20	t	\N	\N
115	61751	17	t	\N	\N
111	60969	1	t	\N	\N
112	61624	17	t	\N	\N
113	61670	32	t	\N	\N
116	60990	30	t	\N	\N
117	61878	18	t	\N	\N
118	62679	16	t	\N	\N
122	61508	15	t	\N	\N
147	61589	17	t	\N	\N
124	62755	17	t	\N	\N
125	61586	19	t	\N	\N
126	61891	6	t	\N	\N
127	61734	13	t	\N	\N
128	61764	16	t	\N	\N
129	61903	7	t	\N	\N
130	61706	18	t	\N	\N
131	60344	20	t	\N	\N
132	61648	7	t	\N	\N
133	61703	17	t	\N	\N
134	61651	11	t	\N	\N
135	61569	18	t	\N	\N
136	62631	21	t	\N	\N
137	61857	8	t	\N	\N
148	61583	22	t	\N	\N
142	61679	19	t	\N	\N
143	61530	18	t	\N	\N
144	61855	24	t	\N	\N
159	61741	21	t	\N	\N
160	61751	9	t	\N	\N
146	61555	19	t	\N	\N
149	61770	28	t	\N	\N
161	61707	27	t	\N	\N
162	62741	12	t	\N	\N
151	60969	25	t	\N	\N
152	61647	20	t	\N	\N
153	62766	13	t	\N	\N
154	61511	14	t	\N	\N
155	62640	6	t	\N	\N
156	61726	21	t	\N	\N
157	61624	23	t	\N	\N
158	62733	29	t	\N	\N
163	61878	24	t	\N	\N
164	62705	23	t	\N	\N
165	62679	22	t	\N	\N
181	61703	28	t	\N	\N
167	61515	22	t	\N	\N
168	61713	33	t	\N	\N
169	61508	10	t	\N	\N
171	61586	9	t	\N	\N
170	60990	7	t	\N	\N
172	61903	28	t	\N	\N
174	62755	23	t	\N	\N
175	61734	19	t	\N	\N
176	61764	23	t	\N	\N
173	61516	12	t	\N	\N
177	61670	34	t	\N	\N
178	60344	29	t	\N	\N
179	61651	21	t	\N	\N
180	61706	24	t	\N	\N
182	61536	29	t	\N	\N
183	61589	10	t	\N	\N
184	62631	30	t	\N	\N
185	61855	23	t	\N	\N
186	61891	5	t	\N	\N
187	61679	5	t	\N	\N
188	61530	33	t	\N	\N
189	61583	32	t	\N	\N
199	62741	32	t	\N	\N
191	61569	14	t	\N	\N
192	61511	12	t	\N	\N
193	61670	8	t	\N	\N
194	61820	28	t	\N	\N
195	61647	6	t	\N	\N
196	62766	35	t	\N	\N
197	61624	5	t	\N	\N
198	61555	9	t	\N	\N
200	61869	26	t	\N	\N
201	61713	36	t	\N	\N
202	61878	6	t	\N	\N
204	61726	22	t	\N	\N
205	61626	29	t	\N	\N
206	62679	7	t	\N	\N
207	61508	32	t	\N	\N
208	61586	7	t	\N	\N
209	61891	37	t	\N	\N
210	60969	5	t	\N	\N
211	62705	29	t	\N	\N
212	62755	8	t	\N	\N
213	61519	33	t	\N	\N
215	60344	8	t	\N	\N
216	61764	30	t	\N	\N
217	61516	25	t	\N	\N
218	61707	6	t	\N	\N
219	61706	25	t	\N	\N
243	61878	28	t	\N	\N
221	61626	34	t	\N	\N
244	61536	33	t	\N	\N
223	61515	29	t	\N	\N
224	62631	25	t	\N	\N
225	61703	6	t	\N	\N
226	61589	8	t	\N	\N
227	61679	26	t	\N	\N
228	60969	35	t	\N	\N
229	61820	5	t	\N	\N
230	61734	25	t	\N	\N
231	61530	7	t	\N	\N
232	61583	26	t	\N	\N
233	61569	26	t	\N	\N
234	61651	8	t	\N	\N
235	61857	32	t	\N	\N
236	61647	27	t	\N	\N
237	62766	29	t	\N	\N
238	61624	27	t	\N	\N
239	61519	8	t	\N	\N
240	61855	26	t	\N	\N
245	62755	28	t	\N	\N
241	61555	34	t	\N	\N
242	62741	25	t	\N	\N
246	61511	34	t	\N	\N
247	61508	8	t	\N	\N
248	61726	28	t	\N	\N
249	61586	34	t	\N	\N
250	61743	35	t	\N	\N
251	60969	34	t	\N	\N
253	61764	26	t	\N	\N
254	60344	35	t	\N	\N
252	61515	28	t	\N	\N
255	61706	29	t	\N	\N
257	61734	33	t	\N	\N
256	62705	33	t	\N	\N
258	61703	34	t	\N	\N
259	60990	36	t	\N	\N
260	62631	33	t	\N	\N
262	61679	30	t	\N	\N
263	61516	7	t	\N	\N
264	61707	36	t	\N	\N
265	61530	27	t	\N	\N
267	61651	35	t	\N	\N
289	61515	6	t	\N	\N
270	61583	36	t	\N	\N
271	61647	32	t	\N	\N
272	62640	37	t	\N	\N
273	62766	36	t	\N	\N
274	61589	27	t	\N	\N
275	61855	32	t	\N	\N
276	62721	37	t	\N	\N
277	61624	37	t	\N	\N
290	61726	32	t	\N	\N
279	62755	33	t	\N	\N
280	61569	5	t	\N	\N
281	61511	30	t	\N	\N
282	61878	38	t	\N	\N
283	61508	38	t	\N	\N
284	61706	34	t	\N	\N
286	61764	39	t	\N	\N
287	61555	35	t	\N	\N
285	61586	39	t	\N	\N
288	61679	35	t	\N	\N
291	60344	40	t	\N	\N
292	61703	40	t	\N	\N
293	61647	36	t	\N	\N
294	61734	7	t	\N	\N
297	62631	41	t	\N	\N
298	61651	27	t	\N	\N
299	62705	30	t	\N	\N
300	62755	37	t	\N	\N
301	62766	41	t	\N	\N
302	61855	5	t	\N	\N
303	61589	6	t	\N	\N
304	61706	38	t	\N	\N
305	61511	36	t	\N	\N
306	61569	36	t	\N	\N
308	61515	37	t	\N	\N
309	61679	39	t	\N	\N
214	61751	10	t	4	\N
85	61764	14	t	4	\N
315	-1	32	t	4	\N
\.


--
-- Data for Name: runner; Type: TABLE DATA; Schema: public; Owner: gaudenz
--

COPY runner (id, number, given_name, surname, dateofbirth, sex, nation, solvnr, startblock, starttime, category, club, address1, address2, zipcode, city, address_country_id, email, startfee, paid, comment, team) FROM stdin;
2	001A	Hans	Muster	1975-01-01	male	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	1
3	001B	Baster	Buster	2010-01-01	male	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	1
4	001C	Troxler	Roman	1985-01-01	male	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	1
5	001D	Marc	Eyer	1976-01-01	male	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	1
6	001E	Doris	Grüniger	1945-01-01	male	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	1
7	001F	Laurent	Baumgartner	1945-01-01	male	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	1
8	002A	Joseph	Doetsch	1981-01-01	male	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	2
9	002B	Franz	Doetsch	1985-01-01	male	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	2
10	002C	Radoslav	Dotchev	1963-01-01	male	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	2
11	002D	Esther	Doetsch	1988-01-01	female	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	2
12	002E	Jakob	Doetsch	1983-01-01	male	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	2
13	002F	Marie-Christine	Böhm	1989-01-01	female	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	2
14	003A	Christine	Rufer	1987-01-01	female	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	3
15	003B	Barbara	Hüsler	1981-01-01	female	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	3
16	003C	Martin	Widler	1971-01-01	male	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	3
17	003D	Daniel	Zwiker	1979-01-01	male	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	3
18	003E	Thomas	Häne	1980-01-01	male	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	3
19	003F	Raphael	Zwiker	1978-01-01	male	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	3
20	004A	Peter	Vitzthum	1964-01-01	male	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	4
21	004B	Mario	Gorecki	1963-01-01	male	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	4
22	004C	Anke	Zentgraf	1964-01-01	female	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	4
23	004D	Jürgen	Ehms	1957-01-01	male	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	4
24	004E	Marion	Friebe	1964-01-01	female	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	4
25	004F	Mirko	Hoppe	1970-01-01	male	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	4
26	005A	Torsten	Kaufmann	1971-01-01	male	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	5
27	005B	Fanny	Sembdner	1985-01-01	female	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	5
28	005C	Jan	Müller	1976-01-01	male	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	5
29	005D	Annegret	Fromke	1986-01-01	female	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	5
30	005E	Joachim	Gerhardt	1958-01-01	male	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	5
31	005F	Andrej	Olunczek	1984-01-01	male	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	5
32	101A	Heiko	Gossel	1965-01-01	male	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	6
33	101B	Wieland	Kundisch	1985-01-01	male	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	6
34	101C	Karsten	Leideck	1986-01-01	male	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	6
35	101D	Sonnhild	Knoblauch	1981-01-01	female	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	6
36	101E	Thomas	Wuttig	1965-01-01	male	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	6
37	101F	Cornelia	Eckardt	1969-01-01	female	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	6
38	102A	Kerstin	Hellmann	1963-01-01	female	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	7
39	102B	Rene	Hellmann	1963-01-01	male	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	7
40	102C	Norbert	Zenker	1958-01-01	male	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	7
41	102D	Lutz	Spranger	1967-01-01	male	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	7
42	102E	Nils	Eyer	1965-01-01	male	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	7
43	102F	Diethard	Kundisch	1954-01-01	male	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	7
44	103A	Peter	Winteler	1948-01-01	male	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	8
45	103B	Mister	Minit	1965-01-01	male	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	8
46	103C	Guggislav	Mandislav	1907-01-01	male	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	8
47	103D	Christian	Roggenmoser	1975-01-01	male	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	8
48	103E	Koni	Ehrbar	1981-01-01	male	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	8
49	103F	Lorenz	Eugster	1965-01-01	male	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	8
\.


--
-- Data for Name: sicard; Type: TABLE DATA; Schema: public; Owner: gaudenz
--

COPY sicard (id, runner) FROM stdin;
51555	2
61726	3
62705	4
61516	5
61854	6
61569	7
61878	8
61586	9
60344	10
62631	11
61583	12
61624	13
51508	14
61764	15
61703	16
61530	17
62766	18
62741	19
62755	20
61706	21
61679	22
61647	23
61741	24
62679	25
61511	26
61751	27
61515	28
61734	29
61651	30
61855	31
61713	32
62733	33
61670	34
61770	35
61891	36
61648	37
61820	38
61519	39
61743	40
61626	41
60990	42
62640	43
61536	44
60969	45
61707	46
62721	47
61903	48
61857	49
61508	14
61555	2
61589	6
61869	46
-1	39
\.


--
-- Data for Name: sistation; Type: TABLE DATA; Schema: public; Owner: gaudenz
--

COPY sistation (id, control) FROM stdin;
2	\N
131	3
132	4
133	5
134	6
135	7
136	8
137	9
138	10
139	11
140	12
141	13
142	14
143	15
144	16
145	17
146	18
147	19
148	20
149	21
150	22
151	23
152	24
153	25
154	26
155	27
156	28
157	29
158	30
159	31
160	32
199	33
200	34
35	34
31	33
4	\N
1	\N
\.


--
-- Data for Name: team; Type: TABLE DATA; Schema: public; Owner: gaudenz
--

COPY team (id, number, name, official, responsible, category, override) FROM stdin;
1	001	ol norska sélection	t	\N	1	\N
2	002	Die Wanderer	t	\N	1	\N
3	003	OLG Galgenen	t	\N	1	\N
4	004	Das Thüringer Original	t	\N	1	\N
5	005	Wie üblich, gemütlich!	t	\N	1	\N
6	101	Traditionell schnell	t	\N	2	\N
7	102	USV TU Dresden III	t	\N	2	\N
8	103	OLG Welsikon	t	\N	2	\N
\.


--
-- Name: pk_category; Type: CONSTRAINT; Schema: public; Owner: gaudenz; Tablespace: 
--

ALTER TABLE ONLY category
    ADD CONSTRAINT pk_category PRIMARY KEY (id);


--
-- Name: pk_control; Type: CONSTRAINT; Schema: public; Owner: gaudenz; Tablespace: 
--

ALTER TABLE ONLY control
    ADD CONSTRAINT pk_control PRIMARY KEY (id);


--
-- Name: pk_controlsequence; Type: CONSTRAINT; Schema: public; Owner: gaudenz; Tablespace: 
--

ALTER TABLE ONLY controlsequence
    ADD CONSTRAINT pk_controlsequence PRIMARY KEY (id);


--
-- Name: pk_course; Type: CONSTRAINT; Schema: public; Owner: gaudenz; Tablespace: 
--

ALTER TABLE ONLY course
    ADD CONSTRAINT pk_course PRIMARY KEY (id);


--
-- Name: pk_coursecontrol; Type: CONSTRAINT; Schema: public; Owner: gaudenz; Tablespace: 
--

ALTER TABLE ONLY coursecontrol
    ADD CONSTRAINT pk_coursecontrol PRIMARY KEY (courseid, controlid);


--
-- Name: pk_punch; Type: CONSTRAINT; Schema: public; Owner: gaudenz; Tablespace: 
--

ALTER TABLE ONLY punch
    ADD CONSTRAINT pk_punch PRIMARY KEY (id);


--
-- Name: pk_run; Type: CONSTRAINT; Schema: public; Owner: gaudenz; Tablespace: 
--

ALTER TABLE ONLY run
    ADD CONSTRAINT pk_run PRIMARY KEY (id);


--
-- Name: pk_runner; Type: CONSTRAINT; Schema: public; Owner: gaudenz; Tablespace: 
--

ALTER TABLE ONLY runner
    ADD CONSTRAINT pk_runner PRIMARY KEY (id);


--
-- Name: pk_sicard; Type: CONSTRAINT; Schema: public; Owner: gaudenz; Tablespace: 
--

ALTER TABLE ONLY sicard
    ADD CONSTRAINT pk_sicard PRIMARY KEY (id);


--
-- Name: pk_sistation; Type: CONSTRAINT; Schema: public; Owner: gaudenz; Tablespace: 
--

ALTER TABLE ONLY sistation
    ADD CONSTRAINT pk_sistation PRIMARY KEY (id);


--
-- Name: pk_team; Type: CONSTRAINT; Schema: public; Owner: gaudenz; Tablespace: 
--

ALTER TABLE ONLY team
    ADD CONSTRAINT pk_team PRIMARY KEY (id);


--
-- Name: idx_code_course; Type: INDEX; Schema: public; Owner: gaudenz; Tablespace: 
--

CREATE UNIQUE INDEX idx_code_course ON course USING btree (code);


--
-- Name: idx_name_category; Type: INDEX; Schema: public; Owner: gaudenz; Tablespace: 
--

CREATE UNIQUE INDEX idx_name_category ON category USING btree (name);


--
-- Name: idx_name_team; Type: INDEX; Schema: public; Owner: gaudenz; Tablespace: 
--

CREATE UNIQUE INDEX idx_name_team ON team USING btree (name);


--
-- Name: idx_number_runner; Type: INDEX; Schema: public; Owner: gaudenz; Tablespace: 
--

CREATE UNIQUE INDEX idx_number_runner ON runner USING btree (number);


--
-- Name: idx_number_team; Type: INDEX; Schema: public; Owner: gaudenz; Tablespace: 
--

CREATE UNIQUE INDEX idx_number_team ON team USING btree (number);


--
-- Name: idx_run_sistation_punchtime_punch; Type: INDEX; Schema: public; Owner: gaudenz; Tablespace: 
--

CREATE UNIQUE INDEX idx_run_sistation_punchtime_punch ON punch USING btree (run, sistation, card_punchtime);


--
-- Name: idx_runner_sicard; Type: INDEX; Schema: public; Owner: gaudenz; Tablespace: 
--

CREATE INDEX idx_runner_sicard ON sicard USING btree (runner);


--
-- Name: idx_sicard_course_run; Type: INDEX; Schema: public; Owner: gaudenz; Tablespace: 
--

CREATE UNIQUE INDEX idx_sicard_course_run ON run USING btree (sicard, course);


--
-- Name: idx_solvnr_runner; Type: INDEX; Schema: public; Owner: gaudenz; Tablespace: 
--

CREATE UNIQUE INDEX idx_solvnr_runner ON runner USING btree (solvnr);


--
-- Name: idx_team_runner; Type: INDEX; Schema: public; Owner: gaudenz; Tablespace: 
--

CREATE INDEX idx_team_runner ON runner USING btree (team);


--
-- Name: controlsequence_fk_control; Type: FK CONSTRAINT; Schema: public; Owner: gaudenz
--

ALTER TABLE ONLY controlsequence
    ADD CONSTRAINT controlsequence_fk_control FOREIGN KEY (control) REFERENCES control(id);


--
-- Name: controlsequence_fk_course; Type: FK CONSTRAINT; Schema: public; Owner: gaudenz
--

ALTER TABLE ONLY controlsequence
    ADD CONSTRAINT controlsequence_fk_course FOREIGN KEY (course) REFERENCES course(id);


--
-- Name: punch_fk_run; Type: FK CONSTRAINT; Schema: public; Owner: gaudenz
--

ALTER TABLE ONLY punch
    ADD CONSTRAINT punch_fk_run FOREIGN KEY (run) REFERENCES run(id);


--
-- Name: punch_fk_sistation; Type: FK CONSTRAINT; Schema: public; Owner: gaudenz
--

ALTER TABLE ONLY punch
    ADD CONSTRAINT punch_fk_sistation FOREIGN KEY (sistation) REFERENCES sistation(id);


--
-- Name: run_fk_course; Type: FK CONSTRAINT; Schema: public; Owner: gaudenz
--

ALTER TABLE ONLY run
    ADD CONSTRAINT run_fk_course FOREIGN KEY (course) REFERENCES course(id);


--
-- Name: run_fk_sicard; Type: FK CONSTRAINT; Schema: public; Owner: gaudenz
--

ALTER TABLE ONLY run
    ADD CONSTRAINT run_fk_sicard FOREIGN KEY (sicard) REFERENCES sicard(id);


--
-- Name: runner_fk_category; Type: FK CONSTRAINT; Schema: public; Owner: gaudenz
--

ALTER TABLE ONLY runner
    ADD CONSTRAINT runner_fk_category FOREIGN KEY (category) REFERENCES category(id);


--
-- Name: runner_fk_team; Type: FK CONSTRAINT; Schema: public; Owner: gaudenz
--

ALTER TABLE ONLY runner
    ADD CONSTRAINT runner_fk_team FOREIGN KEY (team) REFERENCES team(id);


--
-- Name: sicard_fk_runner; Type: FK CONSTRAINT; Schema: public; Owner: gaudenz
--

ALTER TABLE ONLY sicard
    ADD CONSTRAINT sicard_fk_runner FOREIGN KEY (runner) REFERENCES runner(id);


--
-- Name: sistation_fk_control; Type: FK CONSTRAINT; Schema: public; Owner: gaudenz
--

ALTER TABLE ONLY sistation
    ADD CONSTRAINT sistation_fk_control FOREIGN KEY (control) REFERENCES control(id);


--
-- Name: team_fk_category; Type: FK CONSTRAINT; Schema: public; Owner: gaudenz
--

ALTER TABLE ONLY team
    ADD CONSTRAINT team_fk_category FOREIGN KEY (category) REFERENCES category(id);


--
-- Name: team_fk_responsible; Type: FK CONSTRAINT; Schema: public; Owner: gaudenz
--

ALTER TABLE ONLY team
    ADD CONSTRAINT team_fk_responsible FOREIGN KEY (responsible) REFERENCES runner(id);


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- Name: category; Type: ACL; Schema: public; Owner: gaudenz
--

REVOKE ALL ON TABLE category FROM PUBLIC;
REVOKE ALL ON TABLE category FROM gaudenz;
GRANT ALL ON TABLE category TO gaudenz;
GRANT ALL ON TABLE category TO "24h";


--
-- Name: control; Type: ACL; Schema: public; Owner: gaudenz
--

REVOKE ALL ON TABLE control FROM PUBLIC;
REVOKE ALL ON TABLE control FROM gaudenz;
GRANT ALL ON TABLE control TO gaudenz;
GRANT ALL ON TABLE control TO "24h";


--
-- Name: controlsequence; Type: ACL; Schema: public; Owner: gaudenz
--

REVOKE ALL ON TABLE controlsequence FROM PUBLIC;
REVOKE ALL ON TABLE controlsequence FROM gaudenz;
GRANT ALL ON TABLE controlsequence TO gaudenz;
GRANT ALL ON TABLE controlsequence TO "24h";


--
-- Name: course; Type: ACL; Schema: public; Owner: gaudenz
--

REVOKE ALL ON TABLE course FROM PUBLIC;
REVOKE ALL ON TABLE course FROM gaudenz;
GRANT ALL ON TABLE course TO gaudenz;
GRANT ALL ON TABLE course TO "24h";


--
-- Name: coursecontrol; Type: ACL; Schema: public; Owner: gaudenz
--

REVOKE ALL ON TABLE coursecontrol FROM PUBLIC;
REVOKE ALL ON TABLE coursecontrol FROM gaudenz;
GRANT ALL ON TABLE coursecontrol TO gaudenz;
GRANT ALL ON TABLE coursecontrol TO "24h";


--
-- Name: punch; Type: ACL; Schema: public; Owner: gaudenz
--

REVOKE ALL ON TABLE punch FROM PUBLIC;
REVOKE ALL ON TABLE punch FROM gaudenz;
GRANT ALL ON TABLE punch TO gaudenz;
GRANT ALL ON TABLE punch TO "24h";


--
-- Name: run; Type: ACL; Schema: public; Owner: gaudenz
--

REVOKE ALL ON TABLE run FROM PUBLIC;
REVOKE ALL ON TABLE run FROM gaudenz;
GRANT ALL ON TABLE run TO gaudenz;
GRANT ALL ON TABLE run TO "24h";


--
-- Name: runner; Type: ACL; Schema: public; Owner: gaudenz
--

REVOKE ALL ON TABLE runner FROM PUBLIC;
REVOKE ALL ON TABLE runner FROM gaudenz;
GRANT ALL ON TABLE runner TO gaudenz;
GRANT ALL ON TABLE runner TO "24h";


--
-- Name: sicard; Type: ACL; Schema: public; Owner: gaudenz
--

REVOKE ALL ON TABLE sicard FROM PUBLIC;
REVOKE ALL ON TABLE sicard FROM gaudenz;
GRANT ALL ON TABLE sicard TO gaudenz;
GRANT ALL ON TABLE sicard TO "24h";


--
-- Name: sistation; Type: ACL; Schema: public; Owner: gaudenz
--

REVOKE ALL ON TABLE sistation FROM PUBLIC;
REVOKE ALL ON TABLE sistation FROM gaudenz;
GRANT ALL ON TABLE sistation TO gaudenz;
GRANT ALL ON TABLE sistation TO "24h";


--
-- Name: team; Type: ACL; Schema: public; Owner: gaudenz
--

REVOKE ALL ON TABLE team FROM PUBLIC;
REVOKE ALL ON TABLE team FROM gaudenz;
GRANT ALL ON TABLE team TO gaudenz;
GRANT ALL ON TABLE team TO "24h";


--
-- Name: category_id_seq; Type: ACL; Schema: public; Owner: gaudenz
--

REVOKE ALL ON SEQUENCE category_id_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE category_id_seq FROM gaudenz;
GRANT ALL ON SEQUENCE category_id_seq TO gaudenz;
GRANT ALL ON SEQUENCE category_id_seq TO "24h";


--
-- Name: control_id_seq; Type: ACL; Schema: public; Owner: gaudenz
--

REVOKE ALL ON SEQUENCE control_id_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE control_id_seq FROM gaudenz;
GRANT ALL ON SEQUENCE control_id_seq TO gaudenz;
GRANT ALL ON SEQUENCE control_id_seq TO "24h";


--
-- Name: controlsequence_id_seq; Type: ACL; Schema: public; Owner: gaudenz
--

REVOKE ALL ON SEQUENCE controlsequence_id_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE controlsequence_id_seq FROM gaudenz;
GRANT ALL ON SEQUENCE controlsequence_id_seq TO gaudenz;
GRANT ALL ON SEQUENCE controlsequence_id_seq TO "24h";


--
-- Name: course_id_seq; Type: ACL; Schema: public; Owner: gaudenz
--

REVOKE ALL ON SEQUENCE course_id_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE course_id_seq FROM gaudenz;
GRANT ALL ON SEQUENCE course_id_seq TO gaudenz;
GRANT ALL ON SEQUENCE course_id_seq TO "24h";


--
-- Name: punch_id_seq; Type: ACL; Schema: public; Owner: gaudenz
--

REVOKE ALL ON SEQUENCE punch_id_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE punch_id_seq FROM gaudenz;
GRANT ALL ON SEQUENCE punch_id_seq TO gaudenz;
GRANT ALL ON SEQUENCE punch_id_seq TO "24h";


--
-- Name: run_id_seq; Type: ACL; Schema: public; Owner: gaudenz
--

REVOKE ALL ON SEQUENCE run_id_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE run_id_seq FROM gaudenz;
GRANT ALL ON SEQUENCE run_id_seq TO gaudenz;
GRANT ALL ON SEQUENCE run_id_seq TO "24h";


--
-- Name: runner_id_seq; Type: ACL; Schema: public; Owner: gaudenz
--

REVOKE ALL ON SEQUENCE runner_id_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE runner_id_seq FROM gaudenz;
GRANT ALL ON SEQUENCE runner_id_seq TO gaudenz;
GRANT ALL ON SEQUENCE runner_id_seq TO "24h";


--
-- Name: team_id_seq; Type: ACL; Schema: public; Owner: gaudenz
--

REVOKE ALL ON SEQUENCE team_id_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE team_id_seq FROM gaudenz;
GRANT ALL ON SEQUENCE team_id_seq TO gaudenz;
GRANT ALL ON SEQUENCE team_id_seq TO "24h";


--
-- PostgreSQL database dump complete
--

