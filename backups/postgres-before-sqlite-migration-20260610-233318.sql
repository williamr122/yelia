--
-- PostgreSQL database dump
--

\restrict TmM39PTbMjr5gUk7mgfk9oiBbBaQidET0Ycgri7Or75wC7u0O0L9RZ2wGMmUMMO

-- Dumped from database version 15.18
-- Dumped by pg_dump version 15.18

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

ALTER TABLE IF EXISTS ONLY public.structured_quizzes DROP CONSTRAINT IF EXISTS structured_quizzes_source_message_id_fkey;
ALTER TABLE IF EXISTS ONLY public.structured_quizzes DROP CONSTRAINT IF EXISTS structured_quizzes_conv_id_fkey;
ALTER TABLE IF EXISTS ONLY public.metrics_events DROP CONSTRAINT IF EXISTS metrics_events_mensaje_id_fkey;
ALTER TABLE IF EXISTS ONLY public.metrics_events DROP CONSTRAINT IF EXISTS metrics_events_conv_id_fkey;
ALTER TABLE IF EXISTS ONLY public.messages DROP CONSTRAINT IF EXISTS messages_conv_id_fkey;
ALTER TABLE IF EXISTS ONLY public.interacciones DROP CONSTRAINT IF EXISTS interacciones_usuario_id_fkey;
ALTER TABLE IF EXISTS ONLY public.attachments DROP CONSTRAINT IF EXISTS attachments_message_id_fkey;
ALTER TABLE IF EXISTS ONLY public.attachments DROP CONSTRAINT IF EXISTS attachments_conv_id_fkey;
DROP INDEX IF EXISTS public.idx_student_profiles_updated;
DROP INDEX IF EXISTS public.idx_structured_quizzes_usuario;
DROP INDEX IF EXISTS public.idx_structured_quizzes_status;
DROP INDEX IF EXISTS public.idx_structured_quizzes_conv;
DROP INDEX IF EXISTS public.idx_progreso_usuario;
DROP INDEX IF EXISTS public.idx_metrics_usuario_created;
DROP INDEX IF EXISTS public.idx_metrics_conv;
DROP INDEX IF EXISTS public.idx_messages_usuario_created;
DROP INDEX IF EXISTS public.idx_messages_tema_remitente;
DROP INDEX IF EXISTS public.idx_messages_tema;
DROP INDEX IF EXISTS public.idx_messages_remitente;
DROP INDEX IF EXISTS public.idx_messages_conv_created;
DROP INDEX IF EXISTS public.idx_messages_conv;
DROP INDEX IF EXISTS public.idx_interacciones_usuario;
DROP INDEX IF EXISTS public.idx_conversaciones_usuario;
DROP INDEX IF EXISTS public.idx_attachments_usuario;
DROP INDEX IF EXISTS public.idx_attachments_uploaded;
DROP INDEX IF EXISTS public.idx_attachments_original_name;
DROP INDEX IF EXISTS public.idx_attachments_created;
DROP INDEX IF EXISTS public.idx_attachments_conv;
ALTER TABLE IF EXISTS ONLY public.usuarios DROP CONSTRAINT IF EXISTS usuarios_pkey;
ALTER TABLE IF EXISTS ONLY public.usuarios DROP CONSTRAINT IF EXISTS usuarios_alias_key;
ALTER TABLE IF EXISTS ONLY public.student_profiles DROP CONSTRAINT IF EXISTS student_profiles_pkey;
ALTER TABLE IF EXISTS ONLY public.structured_quizzes DROP CONSTRAINT IF EXISTS structured_quizzes_pkey;
ALTER TABLE IF EXISTS ONLY public.progreso DROP CONSTRAINT IF EXISTS progreso_usuario_key;
ALTER TABLE IF EXISTS ONLY public.progreso DROP CONSTRAINT IF EXISTS progreso_pkey;
ALTER TABLE IF EXISTS ONLY public.metrics_recommendations DROP CONSTRAINT IF EXISTS metrics_recommendations_pkey;
ALTER TABLE IF EXISTS ONLY public.metrics_perf DROP CONSTRAINT IF EXISTS metrics_perf_pkey;
ALTER TABLE IF EXISTS ONLY public.metrics_feedback DROP CONSTRAINT IF EXISTS metrics_feedback_pkey;
ALTER TABLE IF EXISTS ONLY public.metrics_events DROP CONSTRAINT IF EXISTS metrics_events_pkey;
ALTER TABLE IF EXISTS ONLY public.metrics_adaptive_feedback DROP CONSTRAINT IF EXISTS metrics_adaptive_feedback_pkey;
ALTER TABLE IF EXISTS ONLY public.messages DROP CONSTRAINT IF EXISTS messages_pkey;
ALTER TABLE IF EXISTS ONLY public.interacciones DROP CONSTRAINT IF EXISTS interacciones_pkey;
ALTER TABLE IF EXISTS ONLY public.conversaciones DROP CONSTRAINT IF EXISTS conversaciones_pkey;
ALTER TABLE IF EXISTS ONLY public.audit_logs DROP CONSTRAINT IF EXISTS audit_logs_pkey;
ALTER TABLE IF EXISTS ONLY public.attachments DROP CONSTRAINT IF EXISTS attachments_pkey;
ALTER TABLE IF EXISTS ONLY public.accounts DROP CONSTRAINT IF EXISTS accounts_username_key;
ALTER TABLE IF EXISTS ONLY public.accounts DROP CONSTRAINT IF EXISTS accounts_pkey;
ALTER TABLE IF EXISTS public.usuarios ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.structured_quizzes ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.progreso ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.metrics_recommendations ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.metrics_perf ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.metrics_feedback ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.metrics_events ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.metrics_adaptive_feedback ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.messages ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.interacciones ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.conversaciones ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.audit_logs ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.attachments ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.accounts ALTER COLUMN id DROP DEFAULT;
DROP SEQUENCE IF EXISTS public.usuarios_id_seq;
DROP TABLE IF EXISTS public.usuarios;
DROP TABLE IF EXISTS public.student_profiles;
DROP SEQUENCE IF EXISTS public.structured_quizzes_id_seq;
DROP TABLE IF EXISTS public.structured_quizzes;
DROP SEQUENCE IF EXISTS public.progreso_id_seq;
DROP TABLE IF EXISTS public.progreso;
DROP SEQUENCE IF EXISTS public.metrics_recommendations_id_seq;
DROP TABLE IF EXISTS public.metrics_recommendations;
DROP SEQUENCE IF EXISTS public.metrics_perf_id_seq;
DROP TABLE IF EXISTS public.metrics_perf;
DROP SEQUENCE IF EXISTS public.metrics_feedback_id_seq;
DROP TABLE IF EXISTS public.metrics_feedback;
DROP SEQUENCE IF EXISTS public.metrics_events_id_seq;
DROP TABLE IF EXISTS public.metrics_events;
DROP SEQUENCE IF EXISTS public.metrics_adaptive_feedback_id_seq;
DROP TABLE IF EXISTS public.metrics_adaptive_feedback;
DROP SEQUENCE IF EXISTS public.messages_id_seq;
DROP TABLE IF EXISTS public.messages;
DROP SEQUENCE IF EXISTS public.interacciones_id_seq;
DROP TABLE IF EXISTS public.interacciones;
DROP SEQUENCE IF EXISTS public.conversaciones_id_seq;
DROP TABLE IF EXISTS public.conversaciones;
DROP SEQUENCE IF EXISTS public.audit_logs_id_seq;
DROP TABLE IF EXISTS public.audit_logs;
DROP SEQUENCE IF EXISTS public.attachments_id_seq;
DROP TABLE IF EXISTS public.attachments;
DROP SEQUENCE IF EXISTS public.accounts_id_seq;
DROP TABLE IF EXISTS public.accounts;
SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: accounts; Type: TABLE; Schema: public; Owner: yelia
--

CREATE TABLE public.accounts (
    id integer NOT NULL,
    username text NOT NULL,
    email text,
    password_hash text NOT NULL,
    role text DEFAULT 'teacher'::text NOT NULL,
    status text DEFAULT 'active'::text NOT NULL,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    last_seen text,
    updated_at text DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.accounts OWNER TO yelia;

--
-- Name: accounts_id_seq; Type: SEQUENCE; Schema: public; Owner: yelia
--

CREATE SEQUENCE public.accounts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.accounts_id_seq OWNER TO yelia;

--
-- Name: accounts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: yelia
--

ALTER SEQUENCE public.accounts_id_seq OWNED BY public.accounts.id;


--
-- Name: attachments; Type: TABLE; Schema: public; Owner: yelia
--

CREATE TABLE public.attachments (
    id integer NOT NULL,
    conv_id integer,
    message_id integer,
    usuario text NOT NULL,
    original_name text NOT NULL,
    stored_name text NOT NULL,
    filename text NOT NULL,
    file_path text NOT NULL,
    mime text,
    size_bytes integer,
    sha256 text,
    url text,
    status text DEFAULT 'active'::text,
    uploaded_at text DEFAULT CURRENT_TIMESTAMP,
    created_at text DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.attachments OWNER TO yelia;

--
-- Name: attachments_id_seq; Type: SEQUENCE; Schema: public; Owner: yelia
--

CREATE SEQUENCE public.attachments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.attachments_id_seq OWNER TO yelia;

--
-- Name: attachments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: yelia
--

ALTER SEQUENCE public.attachments_id_seq OWNED BY public.attachments.id;


--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: yelia
--

CREATE TABLE public.audit_logs (
    id integer NOT NULL,
    actor text NOT NULL,
    action text NOT NULL,
    target text,
    meta_json text,
    created_at text DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.audit_logs OWNER TO yelia;

--
-- Name: audit_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: yelia
--

CREATE SEQUENCE public.audit_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.audit_logs_id_seq OWNER TO yelia;

--
-- Name: audit_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: yelia
--

ALTER SEQUENCE public.audit_logs_id_seq OWNED BY public.audit_logs.id;


--
-- Name: conversaciones; Type: TABLE; Schema: public; Owner: yelia
--

CREATE TABLE public.conversaciones (
    id integer NOT NULL,
    usuario text NOT NULL,
    titulo text,
    focus_topic text,
    focus_attachment_ids text,
    focus_updated_at text,
    memory_summary text,
    memory_msg_count integer,
    memory_updated_at text,
    created_at text DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.conversaciones OWNER TO yelia;

--
-- Name: conversaciones_id_seq; Type: SEQUENCE; Schema: public; Owner: yelia
--

CREATE SEQUENCE public.conversaciones_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.conversaciones_id_seq OWNER TO yelia;

--
-- Name: conversaciones_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: yelia
--

ALTER SEQUENCE public.conversaciones_id_seq OWNED BY public.conversaciones.id;


--
-- Name: interacciones; Type: TABLE; Schema: public; Owner: yelia
--

CREATE TABLE public.interacciones (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    pregunta text NOT NULL,
    respuesta text NOT NULL,
    tema text,
    created_at text DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.interacciones OWNER TO yelia;

--
-- Name: interacciones_id_seq; Type: SEQUENCE; Schema: public; Owner: yelia
--

CREATE SEQUENCE public.interacciones_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.interacciones_id_seq OWNER TO yelia;

--
-- Name: interacciones_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: yelia
--

ALTER SEQUENCE public.interacciones_id_seq OWNED BY public.interacciones.id;


--
-- Name: messages; Type: TABLE; Schema: public; Owner: yelia
--

CREATE TABLE public.messages (
    id integer NOT NULL,
    conv_id integer NOT NULL,
    usuario text NOT NULL,
    remitente text NOT NULL,
    contenido text NOT NULL,
    tema text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    proveedor text,
    response_ms integer
);


ALTER TABLE public.messages OWNER TO yelia;

--
-- Name: messages_id_seq; Type: SEQUENCE; Schema: public; Owner: yelia
--

CREATE SEQUENCE public.messages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.messages_id_seq OWNER TO yelia;

--
-- Name: messages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: yelia
--

ALTER SEQUENCE public.messages_id_seq OWNED BY public.messages.id;


--
-- Name: metrics_adaptive_feedback; Type: TABLE; Schema: public; Owner: yelia
--

CREATE TABLE public.metrics_adaptive_feedback (
    id integer NOT NULL,
    created_at text NOT NULL,
    usuario text,
    conversation_id integer,
    kind text,
    status text,
    topic text,
    level_used text,
    emotion_used text,
    next_action text,
    score_delta integer DEFAULT 0,
    recommendation text
);


ALTER TABLE public.metrics_adaptive_feedback OWNER TO yelia;

--
-- Name: metrics_adaptive_feedback_id_seq; Type: SEQUENCE; Schema: public; Owner: yelia
--

CREATE SEQUENCE public.metrics_adaptive_feedback_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.metrics_adaptive_feedback_id_seq OWNER TO yelia;

--
-- Name: metrics_adaptive_feedback_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: yelia
--

ALTER SEQUENCE public.metrics_adaptive_feedback_id_seq OWNED BY public.metrics_adaptive_feedback.id;


--
-- Name: metrics_events; Type: TABLE; Schema: public; Owner: yelia
--

CREATE TABLE public.metrics_events (
    id integer NOT NULL,
    conv_id integer,
    usuario text,
    mensaje_id integer,
    nivel_detectado text,
    quality_score double precision,
    motivo text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    event_type text,
    path text,
    meta_json text
);


ALTER TABLE public.metrics_events OWNER TO yelia;

--
-- Name: metrics_events_id_seq; Type: SEQUENCE; Schema: public; Owner: yelia
--

CREATE SEQUENCE public.metrics_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.metrics_events_id_seq OWNER TO yelia;

--
-- Name: metrics_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: yelia
--

ALTER SEQUENCE public.metrics_events_id_seq OWNED BY public.metrics_events.id;


--
-- Name: metrics_feedback; Type: TABLE; Schema: public; Owner: yelia
--

CREATE TABLE public.metrics_feedback (
    id integer NOT NULL,
    created_at text NOT NULL,
    usuario text NOT NULL,
    conversation_id integer,
    rating text NOT NULL,
    note text
);


ALTER TABLE public.metrics_feedback OWNER TO yelia;

--
-- Name: metrics_feedback_id_seq; Type: SEQUENCE; Schema: public; Owner: yelia
--

CREATE SEQUENCE public.metrics_feedback_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.metrics_feedback_id_seq OWNER TO yelia;

--
-- Name: metrics_feedback_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: yelia
--

ALTER SEQUENCE public.metrics_feedback_id_seq OWNED BY public.metrics_feedback.id;


--
-- Name: metrics_perf; Type: TABLE; Schema: public; Owner: yelia
--

CREATE TABLE public.metrics_perf (
    id integer NOT NULL,
    created_at text NOT NULL,
    usuario text,
    conversation_id integer,
    endpoint text NOT NULL,
    latency_ms double precision
);


ALTER TABLE public.metrics_perf OWNER TO yelia;

--
-- Name: metrics_perf_id_seq; Type: SEQUENCE; Schema: public; Owner: yelia
--

CREATE SEQUENCE public.metrics_perf_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.metrics_perf_id_seq OWNER TO yelia;

--
-- Name: metrics_perf_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: yelia
--

ALTER SEQUENCE public.metrics_perf_id_seq OWNED BY public.metrics_perf.id;


--
-- Name: metrics_recommendations; Type: TABLE; Schema: public; Owner: yelia
--

CREATE TABLE public.metrics_recommendations (
    id integer NOT NULL,
    created_at text NOT NULL,
    usuario text,
    conversation_id integer,
    recommendation_type text NOT NULL,
    title text,
    topic text,
    level_used text,
    emotion_used text,
    priority text,
    history_based integer DEFAULT 0,
    history_reason text,
    source text,
    url text,
    reason text
);


ALTER TABLE public.metrics_recommendations OWNER TO yelia;

--
-- Name: metrics_recommendations_id_seq; Type: SEQUENCE; Schema: public; Owner: yelia
--

CREATE SEQUENCE public.metrics_recommendations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.metrics_recommendations_id_seq OWNER TO yelia;

--
-- Name: metrics_recommendations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: yelia
--

ALTER SEQUENCE public.metrics_recommendations_id_seq OWNED BY public.metrics_recommendations.id;


--
-- Name: progreso; Type: TABLE; Schema: public; Owner: yelia
--

CREATE TABLE public.progreso (
    id integer NOT NULL,
    usuario text NOT NULL,
    puntos integer DEFAULT 0,
    temas_aprendidos text,
    ciclo_academico text,
    estado_materia text,
    nivel_materia text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.progreso OWNER TO yelia;

--
-- Name: progreso_id_seq; Type: SEQUENCE; Schema: public; Owner: yelia
--

CREATE SEQUENCE public.progreso_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.progreso_id_seq OWNER TO yelia;

--
-- Name: progreso_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: yelia
--

ALTER SEQUENCE public.progreso_id_seq OWNED BY public.progreso.id;


--
-- Name: structured_quizzes; Type: TABLE; Schema: public; Owner: yelia
--

CREATE TABLE public.structured_quizzes (
    id integer NOT NULL,
    conv_id integer,
    usuario text NOT NULL,
    tema text,
    source_message_id integer,
    quiz_json text NOT NULL,
    status text DEFAULT 'active'::text,
    last_score integer,
    total_questions integer,
    answered_at text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.structured_quizzes OWNER TO yelia;

--
-- Name: structured_quizzes_id_seq; Type: SEQUENCE; Schema: public; Owner: yelia
--

CREATE SEQUENCE public.structured_quizzes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.structured_quizzes_id_seq OWNER TO yelia;

--
-- Name: structured_quizzes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: yelia
--

ALTER SEQUENCE public.structured_quizzes_id_seq OWNED BY public.structured_quizzes.id;


--
-- Name: student_profiles; Type: TABLE; Schema: public; Owner: yelia
--

CREATE TABLE public.student_profiles (
    student_id text NOT NULL,
    profile_json text NOT NULL,
    updated_at text DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.student_profiles OWNER TO yelia;

--
-- Name: usuarios; Type: TABLE; Schema: public; Owner: yelia
--

CREATE TABLE public.usuarios (
    id integer NOT NULL,
    alias text NOT NULL,
    email text,
    role text DEFAULT 'student'::text,
    status text DEFAULT 'active'::text,
    last_seen text,
    updated_at text DEFAULT CURRENT_TIMESTAMP,
    created_at text DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.usuarios OWNER TO yelia;

--
-- Name: usuarios_id_seq; Type: SEQUENCE; Schema: public; Owner: yelia
--

CREATE SEQUENCE public.usuarios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.usuarios_id_seq OWNER TO yelia;

--
-- Name: usuarios_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: yelia
--

ALTER SEQUENCE public.usuarios_id_seq OWNED BY public.usuarios.id;


--
-- Name: accounts id; Type: DEFAULT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.accounts ALTER COLUMN id SET DEFAULT nextval('public.accounts_id_seq'::regclass);


--
-- Name: attachments id; Type: DEFAULT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.attachments ALTER COLUMN id SET DEFAULT nextval('public.attachments_id_seq'::regclass);


--
-- Name: audit_logs id; Type: DEFAULT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.audit_logs ALTER COLUMN id SET DEFAULT nextval('public.audit_logs_id_seq'::regclass);


--
-- Name: conversaciones id; Type: DEFAULT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.conversaciones ALTER COLUMN id SET DEFAULT nextval('public.conversaciones_id_seq'::regclass);


--
-- Name: interacciones id; Type: DEFAULT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.interacciones ALTER COLUMN id SET DEFAULT nextval('public.interacciones_id_seq'::regclass);


--
-- Name: messages id; Type: DEFAULT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.messages ALTER COLUMN id SET DEFAULT nextval('public.messages_id_seq'::regclass);


--
-- Name: metrics_adaptive_feedback id; Type: DEFAULT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.metrics_adaptive_feedback ALTER COLUMN id SET DEFAULT nextval('public.metrics_adaptive_feedback_id_seq'::regclass);


--
-- Name: metrics_events id; Type: DEFAULT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.metrics_events ALTER COLUMN id SET DEFAULT nextval('public.metrics_events_id_seq'::regclass);


--
-- Name: metrics_feedback id; Type: DEFAULT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.metrics_feedback ALTER COLUMN id SET DEFAULT nextval('public.metrics_feedback_id_seq'::regclass);


--
-- Name: metrics_perf id; Type: DEFAULT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.metrics_perf ALTER COLUMN id SET DEFAULT nextval('public.metrics_perf_id_seq'::regclass);


--
-- Name: metrics_recommendations id; Type: DEFAULT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.metrics_recommendations ALTER COLUMN id SET DEFAULT nextval('public.metrics_recommendations_id_seq'::regclass);


--
-- Name: progreso id; Type: DEFAULT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.progreso ALTER COLUMN id SET DEFAULT nextval('public.progreso_id_seq'::regclass);


--
-- Name: structured_quizzes id; Type: DEFAULT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.structured_quizzes ALTER COLUMN id SET DEFAULT nextval('public.structured_quizzes_id_seq'::regclass);


--
-- Name: usuarios id; Type: DEFAULT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.usuarios ALTER COLUMN id SET DEFAULT nextval('public.usuarios_id_seq'::regclass);


--
-- Data for Name: accounts; Type: TABLE DATA; Schema: public; Owner: yelia
--

COPY public.accounts (id, username, email, password_hash, role, status, created_at, last_seen, updated_at) FROM stdin;
1	admin	admin@yelia.local	pbkdf2:sha256:1000000$QvnAxl7aXC5alDV3$026494966a8c8a934278f9566bc7fec5a68fe75ded8ce750827f2fcd492a9204	admin	active	2026-06-09 01:47:12.712903+00	2026-06-09 03:00:02.204504+00	2026-06-09 02:59:43.946202+00
\.


--
-- Data for Name: attachments; Type: TABLE DATA; Schema: public; Owner: yelia
--

COPY public.attachments (id, conv_id, message_id, usuario, original_name, stored_name, filename, file_path, mime, size_bytes, sha256, url, status, uploaded_at, created_at) FROM stdin;
\.


--
-- Data for Name: audit_logs; Type: TABLE DATA; Schema: public; Owner: yelia
--

COPY public.audit_logs (id, actor, action, target, meta_json, created_at) FROM stdin;
1	admin	auth.login	admin	{"role": "admin"}	2026-06-09 02:59:43.958864+00
2	admin	student.update	2	{"fields": ["email", "role", "status"]}	2026-06-09 22:01:18.504854+00
\.


--
-- Data for Name: conversaciones; Type: TABLE DATA; Schema: public; Owner: yelia
--

COPY public.conversaciones (id, usuario, titulo, focus_topic, focus_attachment_ids, focus_updated_at, memory_summary, memory_msg_count, memory_updated_at, created_at) FROM stdin;
1	GUEST-4261ad10-61c0-471f-a3a4-7539b894cbc3	hola	Introducción a la Programación Orientada a Objetos	\N	2026-06-09 01:55:52.113056+00	\N	\N	\N	2026-06-09 01:55:52.043204+00
2	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	No entiendo clases y objetos, explícame más simple y recomié	Clases y Objetos	\N	2026-06-09 19:48:49.968088+00	\N	\N	\N	2026-06-09 19:48:49.889821+00
3	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	No entiendo clases y objetos, explícame más simple y recomié	Clases y Objetos	\N	2026-06-09 20:08:49.238714+00	\N	\N	\N	2026-06-09 20:08:49.174406+00
4	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	No entiendo clases y objetos, explícame más simple y recomié	Clases y Objetos	\N	2026-06-09 20:33:20.244593+00	\N	\N	\N	2026-06-09 20:31:02.106054+00
5	Anon-94ab2a702b	que es clase de forma cortita	Bases de Datos y ORM	\N	2026-06-10 02:43:49.948548+00	\N	\N	\N	2026-06-10 02:43:49.87776+00
6	Anon-94ab2a702b	que es clase	Clases y Objetos	\N	2026-06-10 14:59:35.832249+00	\N	\N	\N	2026-06-10 14:59:35.741171+00
\.


--
-- Data for Name: interacciones; Type: TABLE DATA; Schema: public; Owner: yelia
--

COPY public.interacciones (id, usuario_id, pregunta, respuesta, tema, created_at) FROM stdin;
1	1	hola	¡Hola! Me alegra verte en este espacio de aprendizaje de Programación Avanzada. Soy Yelia, tu tutor virtual especializado en esta materia. Estoy aquí para ayudarte a entender y dominar los conceptos más complejos de la programación.\n\n¿En qué puedo ayudarte hoy? ¿Quieres profundizar en un tema específico o explorar nuevos conceptos?	Introducción a la Programación Orientada a Objetos	2026-06-09 01:55:52.086841+00
2	2	No entiendo clases y objetos, explícame más simple y recomiéndame recursos	**Clases y Objetos: una explicación simple**\n\nImagina que estás diseñando una casa. Una casa tiene varias partes, como una cocina, un baño, una habitación y un jardín. Cada una de estas partes tiene características propias, como la cocina tiene un fogón y un refrigerador, el baño tiene un inodoro y una ducha, etc.\n\nEn programación, una **clase** es como una planta de construcción que define la estructura y las características de una casa. Una **objeto** es como una casa real que se construye a partir de la planta.\n\nPor ejemplo, si creamos una clase llamada "Casa", podríamos definir que tiene características como:\n\n* Un número de habitaciones\n* Un tamaño en metros cuadrados\n* Un color de paredes\n* Un número de puertas\n\nLuego, podemos crear objetos de la clase "Casa" que representen casas reales, como:\n\n* Una casa con 3 habitaciones, 100 metros cuadrados y paredes de color azul\n* Otra casa con 2 habitaciones, 80 metros cuadrados y paredes de color blanco\n\n**Ejemplo de código**\n\n```java\npublic class Casa {\n  private int numeroHabitaciones;\n  private int tamaño;\n  private String colorParedes;\n\n  public Casa(int numeroHabitaciones, int tamaño, String colorParedes) {\n    this.numeroHabitaciones = numeroHabitaciones;\n    this.tamaño = tamaño;\n    this.colorParedes = colorParedes;\n  }\n\n  public void mostrarCaracteristicas() {\n    System.out.println("Número de habitaciones: " + numeroHabitaciones);\n    System.out.println("Tamaño: " + tamaño + " metros cuadrados");\n    System.out.println("Color de paredes: " + colorParedes);\n  }\n}\n\n// Creamos un objeto de la clase Casa\nCasa miCasa = new Casa(3, 100, "azul");\nmiCasa.mostrarCaracteristicas();\n```\n\n**Recomendaciones**\n\n* Recomiendo que veas el tutorial de YouTube "Clases y Objetos en Java" de la canal de programación de Platzi.\n* También puedes leer el capítulo 3 del libro "Programación Orientada a Objetos" de la editorial McGraw-Hill.\n* Si quieres practicar, puedes intentar crear tus propias clases y objetos en Java, utilizando el ejemplo que te proporcioné anteriormente.\n\n¿Quieres que te explique más sobre la herencia o la polimorfismo?\n\nRecursos web recomendados:\n- **Oracle Java Tutorials: Classes and Objects**\n  Enlace directo: https://docs.oracle.com/javase/tutorial/java/javaOO/\n  Por que te sirve: Documentacion oficial para reforzar clases, objetos, metodos y constructores en Java.\n  Nivel usado: basico | Emocion detectada: neutral | Tema: Clases y Objetos\n\nRetroalimentacion personalizada:\n- Estado: necesitas refuerzo en Clases y Objetos.\n- Accion: lo explicare mas simple y con un ejemplo corto.\n- Nivel usado: basico | Emocion detectada: neutral.	Clases y Objetos	2026-06-09 19:48:49.947774+00
3	2	No entiendo clases y objetos, explícame más simple y recomiéndame recursos	**Clases y Objetos: Un Enfoque Simple**\n\nEntiendo que estás luchando un poco con las clases y objetos. Vamos a empezar desde cero y hacerlo más simple.\n\n**¿Qué son las Clases?**\n\nUna clase es como un molde para crear objetos. Es una forma de definir una estructura de datos y comportamiento para que puedas crear objetos que tengan propiedades y acciones específicas.\n\n**¿Qué son los Objetos?**\n\nUn objeto es una instancia de una clase. Es un ente que tiene propiedades y acciones específicas, basadas en la clase a la que pertenece.\n\n**Ejemplo Simple**\n\nImagina que estás creando un juego de cartas. Una clase podría ser "Carta" y un objeto podría ser una carta específica, como la "Reina de Corazones".\n\nLa clase "Carta" podría tener propiedades como:\n\n* Valor (As, 2, 3, etc.)\n* Símbolo (Corazones, Diamantes, etc.)\n* Color (Rojo, Negro, etc.)\n\nUn objeto "Reina de Corazones" podría tener propiedades específicas, como:\n\n* Valor: Reina\n* Símbolo: Corazones\n* Color: Rojo\n\n**Recursos Recomendados**\n\n* Oracle Java Tutorials: Classes and Objects (es un recurso excelente para aprender sobre clases y objetos en Java)\n* Clase y objeto básicos (un recurso simple y fácil de entender)\n\n**Práctica**\n\n* Crea un ejemplo simple de una clase y un objeto en un lenguaje de programación que conozcas (como Java o Python).\n* Experimenta con diferentes propiedades y acciones para ver cómo funcionan.\n\n**Retroalimentación**\n\n* ¿Te parece que esto te ayudó a entender mejor las clases y objetos?\n* ¿Tienes alguna pregunta o inquietud sobre este tema?\n\nRecuerda que la práctica y la experimentación son clave para aprender sobre clases y objetos. ¡No dudes en preguntar si necesitas ayuda adicional!\n\nRecomendacion por historial:\n- **Repaso adaptativo de Clases y Objetos**\n  Motivo: El historial marca este tema como debil; conviene reforzarlo antes de avanzar.\n  Accion sugerida: Repasemos Clases y Objetos desde la base, con un ejemplo minimo y una pregunta de comprobacion.\n- **Practica guiada por historial: Clases y Objetos**\n  Motivo: El estudiante ha trabajado este tema varias veces; la practica guiada ayuda a consolidar.\n  Accion sugerida: Dame una practica guiada de Clases y Objetos, paso a paso, y luego revisa mi respuesta.\n\nRecursos web recomendados:\n- **Oracle Java Tutorials: Classes and Objects**\n  Enlace directo: https://docs.oracle.com/javase/tutorial/java/javaOO/\n  Por que te sirve: Documentacion oficial para reforzar clases, objetos, metodos y constructores en Java.\n  Nivel usado: basico | Emocion detectada: neutral | Tema: Clases y Objetos\n\nRetroalimentacion personalizada:\n- Estado: necesitas refuerzo en Clases y Objetos.\n- Accion: lo explicare mas simple y con un ejemplo corto.\n- Nivel usado: basico | Emocion detectada: neutral.	Clases y Objetos	2026-06-09 20:08:49.218291+00
4	2	No entiendo clases y objetos, explícame más simple y recomiéndame recursos del pensum	**Clases y Objetos: una explicación más simple**\n\nImagina que estás creando un programa para gestionar una biblioteca. Quieres que cada libro tenga un título, autor y cantidad de ejemplares. En lugar de crear variables separadas para cada libro, como `titulo1`, `autor1`, `ejemplares1`, etc., puedes crear una estructura llamada **clase** que tenga todos estos atributos.\n\n**Clase**: es como un molde que define la estructura de un objeto. En este caso, la clase `Libro` tendría los atributos `titulo`, `autor` y `ejemplares`.\n\n**Objeto**: es una instancia de una clase. En este caso, cada libro en la biblioteca sería un objeto de la clase `Libro`.\n\n**Ejemplo**:\n\n```java\npublic class Libro {\n    private String titulo;\n    private String autor;\n    private int ejemplares;\n\n    public Libro(String titulo, String autor, int ejemplares) {\n        this.titulo = titulo;\n        this.autor = autor;\n        this.ejemplares = ejemplares;\n    }\n\n    public String getTitulo() {\n        return titulo;\n    }\n\n    public void setTitulo(String titulo) {\n        this.titulo = titulo;\n    }\n\n    public String getAutor() {\n        return autor;\n    }\n\n    public void setAutor(String autor) {\n        this.autor = autor;\n    }\n\n    public int getEjemplares() {\n        return ejemplares;\n    }\n\n    public void setEjemplares(int ejemplares) {\n        this.ejemplares = ejemplares;\n    }\n}\n```\n\n**Práctica guiada**:\n\n1. Crea una clase `Persona` con atributos `nombre`, `edad` y `direccion`.\n2. Crea un objeto `persona1` de la clase `Persona` y asigna valores a sus atributos.\n3. Imprime los valores de los atributos de `persona1`.\n\n**Recursos del pensum**:\n\n* El libro "Programación Orientada a Objetos" de la Universidad de Guayaquil.\n* El curso en línea "POO para principiantes" en la plataforma de la universidad.\n* El tutorial "Clases y Objetos en Java" en la página web de Oracle.\n\n**Recomendaciones**:\n\n* Repasa los conceptos de clases y objetos en el libro y en el curso en línea.\n* Practica creando clases y objetos en Java utilizando el tutorial de Oracle.\n* Si tienes alguna duda, no dudes en preguntar.\n\n¿Quieres que explique más sobre clases y objetos o prefieres seguir adelante con otro tema?\n\nRecomendacion por historial:\n- **Repaso adaptativo de Clases y Objetos**\n  Motivo: El historial marca este tema como debil; conviene reforzarlo antes de avanzar.\n  Accion sugerida: Repasemos Clases y Objetos desde la base, con un ejemplo minimo y una pregunta de comprobacion.\n- **Practica guiada por historial: Clases y Objetos**\n  Motivo: El estudiante ha trabajado este tema varias veces; la practica guiada ayuda a consolidar.\n  Accion sugerida: Dame una practica guiada de Clases y Objetos, paso a paso, y luego revisa mi respuesta.\n\nRecursos web recomendados:\n- **Oracle Java Tutorials: Classes and Objects**\n  Enlace directo: https://docs.oracle.com/javase/tutorial/java/javaOO/\n  Por que te sirve: Unidad 1 del pensum: clases, objetos, atributos, metodos y constructores en Java.\n  Nivel usado: basico | Emocion detectada: neutral | Tema: Clases y Objetos\n- **Ejercicios de POO con Java y UML**\n  Enlace directo: http://www.fadmon.unal.edu.co/fileadmin/user_upload/investigacion/centro_editorial/libros/ejercicios%20de%20programacion.pdf\n  Por que te sirve: Libro de ejercicios citado en el silabo para practicar POO, Java y UML.\n  Nivel usado: basico | Emocion detectada: neutral | Tema: Clases y Objetos\n- **Java 17: programacion avanzada**\n  Enlace directo: https://elibro.net/es/lc/uguayaquil/titulos/222668\n  Por que te sirve: Texto base del plan analitico para reforzar Programacion Avanzada.\n  Nivel usado: basico | Emocion detectada: neutral | Tema: Clases y Objetos\n\nRetroalimentacion personalizada:\n- Estado: necesitas refuerzo en Clases y Objetos.\n- Accion: lo explicare mas simple y con un ejemplo corto.\n- Nivel usado: basico | Emocion detectada: neutral.	Clases y Objetos	2026-06-09 20:31:02.148119+00
5	2	Repaso adaptativo de Clases y Objetos	**Repaso adaptativo de Clases y Objetos**\n\n¡Hola! Me alegra que estés dispuesto a repasar Clases y Objetos. Como sabes, esta es una parte fundamental de la programación orientada a objetos (POO). Vamos a empezar con algo simple y luego iremos profundizando.\n\n**¿Qué son Clases y Objetos?**\n\nUna **clase** es como un molde que define la estructura de un objeto. En este caso, la clase `Libro` tendría los atributos `titulo`, `autor` y `ejemplares`.\n\nUn **objeto** es una instancia de una clase. En este caso, cada libro en la biblioteca sería un objeto de la clase `Libro`.\n\n**Ejemplo sencillo**\n\nImagina que estás creando un programa para gestionar una biblioteca. Quieres que cada libro tenga un título, autor y cantidad de ejemplares. En lugar de crear variables separadas para cada libro, como `titulo1`, `autor1`, `ejemplares1`, etc., puedes crear una estructura llamada **clase** que tenga todos estos atributos.\n\n**Clase Libro**\n\n```java\npublic class Libro {\n    private String titulo;\n    private String autor;\n    private int ejemplares;\n\n    public Libro(String titulo, String autor, int ejemplares) {\n        this.titulo = titulo;\n        this.autor = autor;\n        this.ejemplares = ejemplares;\n    }\n\n    public String getTitulo() {\n        return titulo;\n    }\n\n    public void setTitulo(String titulo) {\n        this.titulo = titulo;\n    }\n\n    public String getAutor() {\n        return autor;\n    }\n\n    public void setAutor(String autor) {\n        this.autor = autor;\n    }\n\n    public int getEjemplares() {\n        return ejemplares;\n    }\n\n    public void setEjemplares(int ejemplares) {\n        this.ejemplares = ejemplares;\n    }\n}\n```\n\n**Práctica guiada**\n\n1. Crea una clase `Persona` con atributos `nombre`, `edad` y `direccion`.\n2. Crea un objeto `persona1` de la clase `Persona` y asigna valores a sus atributos.\n3. Imprime los valores de los atributos de `persona1`.\n\n**Preguntas de comprobación**\n\n1. ¿Qué es una clase?\n2. ¿Qué es un objeto?\n3. ¿Cómo se define una clase en Java?\n\n**Retroalimentación**\n\n¡Excelente! Has repasado Clases y Objetos de manera efectiva. Recuerda que la práctica es la mejor manera de consolidar tus conocimientos. ¡Sigue adelante y no dudes en preguntar si tienes alguna duda!\n\n¿Quieres seguir adelante con otro tema o prefieres seguir repasando Clases y Objetos?\n\nRecomendacion por historial:\n- **Repaso adaptativo de Clases y Objetos**\n  Motivo: El historial marca este tema como debil; conviene reforzarlo antes de avanzar.\n  Accion sugerida: Repasemos Clases y Objetos desde la base, con un ejemplo minimo y una pregunta de comprobacion.\n- **Practica guiada por historial: Clases y Objetos**\n  Motivo: El estudiante ha trabajado este tema varias veces; la practica guiada ayuda a consolidar.\n  Accion sugerida: Dame una practica guiada de Clases y Objetos, paso a paso, y luego revisa mi respuesta.	Clases y Objetos	2026-06-09 20:33:20.229741+00
6	3	que es clase de forma cortita	**Clase: Un Concepto Fundamental en Programación Avanzada**\n\nUna clase es un molde que define una estructura de datos y comportamientos para crear objetos en una aplicación. Puedes pensar en una clase como un plan de construcción para crear diferentes tipos de casas.\n\n**Ejemplo Paso a Paso:**\n\n1. Una clase define propiedades (atributos) y métodos (acciones) que se pueden realizar con esos atributos.\n2. Los objetos creados a partir de una clase heredan esas propiedades y métodos.\n3. Puedes crear múltiples objetos a partir de una clase, cada uno con sus propias características.\n\n**Ejemplo de Código:**\n```java\npublic class Casa {\n  private String color;\n  private int numeroPuertas;\n\n  public Casa(String color, int numeroPuertas) {\n    this.color = color;\n    this.numeroPuertas = numeroPuertas;\n  }\n\n  public void pintar() {\n    System.out.println("La casa se está pintando de " + color);\n  }\n}\n```\n**Resumen Final:**\nUna clase es un molde que define una estructura de datos y comportamientos para crear objetos en una aplicación. Puedes pensar en una clase como un plan de construcción para crear diferentes tipos de casas.\n\n¿Quieres ver un ejemplo de cómo crear objetos a partir de una clase?	Bases de Datos y ORM	2026-06-10 02:43:49.926184+00
7	3	que es clase	**Bienvenido, Anon-94ab2a702b.**\n\n**Clases y Objetos** es un tema fundamental en Programación Avanzada. Te voy a explicar qué es una **clase** de manera clara y concisa.\n\n### Definición\n\nUna **clase** es una plantilla o molde que define una estructura de datos y comportamiento para objetos que pertenecen a un tipo específico. En otras palabras, una clase es una forma de crear objetos que comparten características y acciones similares.\n\n### Ejemplo\n\nImagina que estás diseñando un sistema de gestión de libros en una biblioteca. Una clase podría ser `Libro`, que tiene propiedades como `titulo`, `autor`, `editorial` y `añoPublicacion`. Además, la clase `Libro` podría tener métodos como `mostrarInformacion()` y `prestarLibro()`.\n\n### Código de ejemplo\n\n```java\npublic class Libro {\n    private String titulo;\n    private String autor;\n    private String editorial;\n    private int añoPublicacion;\n\n    public Libro(String titulo, String autor, String editorial, int añoPublicacion) {\n        this.titulo = titulo;\n        this.autor = autor;\n        this.editorial = editorial;\n        this.añoPublicacion = añoPublicacion;\n    }\n\n    public void mostrarInformacion() {\n        System.out.println("Título: " + titulo);\n        System.out.println("Autor: " + autor);\n        System.out.println("Editorial: " + editorial);\n        System.out.println("Año de publicación: " + añoPublicacion);\n    }\n\n    public void prestarLibro() {\n        System.out.println("El libro ha sido prestado.");\n    }\n}\n```\n\n### Práctica\n\n* Crea una clase `Persona` con propiedades como `nombre`, `edad` y `direccion`. Agrega métodos como `mostrarInformacion()` y `cumplirAños()`.\n* Crea un objeto `persona` de la clase `Persona` y llama a los métodos `mostrarInformacion()` y `cumplirAños()`.\n\n¿Quieres ver un ejemplo de cómo crear un objeto `Persona` y llamar a los métodos?	Clases y Objetos	2026-06-10 14:59:35.801379+00
\.


--
-- Data for Name: messages; Type: TABLE DATA; Schema: public; Owner: yelia
--

COPY public.messages (id, conv_id, usuario, remitente, contenido, tema, created_at, proveedor, response_ms) FROM stdin;
1	1	GUEST-4261ad10-61c0-471f-a3a4-7539b894cbc3	user	hola	Introducción a la Programación Orientada a Objetos	2026-06-09 01:55:52.043204+00	\N	\N
2	1	GUEST-4261ad10-61c0-471f-a3a4-7539b894cbc3	bot	¡Hola! Me alegra verte en este espacio de aprendizaje de Programación Avanzada. Soy Yelia, tu tutor virtual especializado en esta materia. Estoy aquí para ayudarte a entender y dominar los conceptos más complejos de la programación.\n\n¿En qué puedo ayudarte hoy? ¿Quieres profundizar en un tema específico o explorar nuevos conceptos?	Introducción a la Programación Orientada a Objetos	2026-06-09 01:55:52.043204+00	groq	1395
3	2	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	user	No entiendo clases y objetos, explícame más simple y recomiéndame recursos	Clases y Objetos	2026-06-09 19:48:49.889821+00	\N	\N
4	2	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	bot	**Clases y Objetos: una explicación simple**\n\nImagina que estás diseñando una casa. Una casa tiene varias partes, como una cocina, un baño, una habitación y un jardín. Cada una de estas partes tiene características propias, como la cocina tiene un fogón y un refrigerador, el baño tiene un inodoro y una ducha, etc.\n\nEn programación, una **clase** es como una planta de construcción que define la estructura y las características de una casa. Una **objeto** es como una casa real que se construye a partir de la planta.\n\nPor ejemplo, si creamos una clase llamada "Casa", podríamos definir que tiene características como:\n\n* Un número de habitaciones\n* Un tamaño en metros cuadrados\n* Un color de paredes\n* Un número de puertas\n\nLuego, podemos crear objetos de la clase "Casa" que representen casas reales, como:\n\n* Una casa con 3 habitaciones, 100 metros cuadrados y paredes de color azul\n* Otra casa con 2 habitaciones, 80 metros cuadrados y paredes de color blanco\n\n**Ejemplo de código**\n\n```java\npublic class Casa {\n  private int numeroHabitaciones;\n  private int tamaño;\n  private String colorParedes;\n\n  public Casa(int numeroHabitaciones, int tamaño, String colorParedes) {\n    this.numeroHabitaciones = numeroHabitaciones;\n    this.tamaño = tamaño;\n    this.colorParedes = colorParedes;\n  }\n\n  public void mostrarCaracteristicas() {\n    System.out.println("Número de habitaciones: " + numeroHabitaciones);\n    System.out.println("Tamaño: " + tamaño + " metros cuadrados");\n    System.out.println("Color de paredes: " + colorParedes);\n  }\n}\n\n// Creamos un objeto de la clase Casa\nCasa miCasa = new Casa(3, 100, "azul");\nmiCasa.mostrarCaracteristicas();\n```\n\n**Recomendaciones**\n\n* Recomiendo que veas el tutorial de YouTube "Clases y Objetos en Java" de la canal de programación de Platzi.\n* También puedes leer el capítulo 3 del libro "Programación Orientada a Objetos" de la editorial McGraw-Hill.\n* Si quieres practicar, puedes intentar crear tus propias clases y objetos en Java, utilizando el ejemplo que te proporcioné anteriormente.\n\n¿Quieres que te explique más sobre la herencia o la polimorfismo?\n\nRecursos web recomendados:\n- **Oracle Java Tutorials: Classes and Objects**\n  Enlace directo: https://docs.oracle.com/javase/tutorial/java/javaOO/\n  Por que te sirve: Documentacion oficial para reforzar clases, objetos, metodos y constructores en Java.\n  Nivel usado: basico | Emocion detectada: neutral | Tema: Clases y Objetos\n\nRetroalimentacion personalizada:\n- Estado: necesitas refuerzo en Clases y Objetos.\n- Accion: lo explicare mas simple y con un ejemplo corto.\n- Nivel usado: basico | Emocion detectada: neutral.	Clases y Objetos	2026-06-09 19:48:49.889821+00	groq	2676
5	3	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	user	No entiendo clases y objetos, explícame más simple y recomiéndame recursos	Clases y Objetos	2026-06-09 20:08:49.174406+00	\N	\N
6	3	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	bot	**Clases y Objetos: Un Enfoque Simple**\n\nEntiendo que estás luchando un poco con las clases y objetos. Vamos a empezar desde cero y hacerlo más simple.\n\n**¿Qué son las Clases?**\n\nUna clase es como un molde para crear objetos. Es una forma de definir una estructura de datos y comportamiento para que puedas crear objetos que tengan propiedades y acciones específicas.\n\n**¿Qué son los Objetos?**\n\nUn objeto es una instancia de una clase. Es un ente que tiene propiedades y acciones específicas, basadas en la clase a la que pertenece.\n\n**Ejemplo Simple**\n\nImagina que estás creando un juego de cartas. Una clase podría ser "Carta" y un objeto podría ser una carta específica, como la "Reina de Corazones".\n\nLa clase "Carta" podría tener propiedades como:\n\n* Valor (As, 2, 3, etc.)\n* Símbolo (Corazones, Diamantes, etc.)\n* Color (Rojo, Negro, etc.)\n\nUn objeto "Reina de Corazones" podría tener propiedades específicas, como:\n\n* Valor: Reina\n* Símbolo: Corazones\n* Color: Rojo\n\n**Recursos Recomendados**\n\n* Oracle Java Tutorials: Classes and Objects (es un recurso excelente para aprender sobre clases y objetos en Java)\n* Clase y objeto básicos (un recurso simple y fácil de entender)\n\n**Práctica**\n\n* Crea un ejemplo simple de una clase y un objeto en un lenguaje de programación que conozcas (como Java o Python).\n* Experimenta con diferentes propiedades y acciones para ver cómo funcionan.\n\n**Retroalimentación**\n\n* ¿Te parece que esto te ayudó a entender mejor las clases y objetos?\n* ¿Tienes alguna pregunta o inquietud sobre este tema?\n\nRecuerda que la práctica y la experimentación son clave para aprender sobre clases y objetos. ¡No dudes en preguntar si necesitas ayuda adicional!\n\nRecomendacion por historial:\n- **Repaso adaptativo de Clases y Objetos**\n  Motivo: El historial marca este tema como debil; conviene reforzarlo antes de avanzar.\n  Accion sugerida: Repasemos Clases y Objetos desde la base, con un ejemplo minimo y una pregunta de comprobacion.\n- **Practica guiada por historial: Clases y Objetos**\n  Motivo: El estudiante ha trabajado este tema varias veces; la practica guiada ayuda a consolidar.\n  Accion sugerida: Dame una practica guiada de Clases y Objetos, paso a paso, y luego revisa mi respuesta.\n\nRecursos web recomendados:\n- **Oracle Java Tutorials: Classes and Objects**\n  Enlace directo: https://docs.oracle.com/javase/tutorial/java/javaOO/\n  Por que te sirve: Documentacion oficial para reforzar clases, objetos, metodos y constructores en Java.\n  Nivel usado: basico | Emocion detectada: neutral | Tema: Clases y Objetos\n\nRetroalimentacion personalizada:\n- Estado: necesitas refuerzo en Clases y Objetos.\n- Accion: lo explicare mas simple y con un ejemplo corto.\n- Nivel usado: basico | Emocion detectada: neutral.	Clases y Objetos	2026-06-09 20:08:49.174406+00	groq	3228
7	4	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	user	No entiendo clases y objetos, explícame más simple y recomiéndame recursos del pensum	Clases y Objetos	2026-06-09 20:31:02.106054+00	\N	\N
8	4	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	bot	**Clases y Objetos: una explicación más simple**\n\nImagina que estás creando un programa para gestionar una biblioteca. Quieres que cada libro tenga un título, autor y cantidad de ejemplares. En lugar de crear variables separadas para cada libro, como `titulo1`, `autor1`, `ejemplares1`, etc., puedes crear una estructura llamada **clase** que tenga todos estos atributos.\n\n**Clase**: es como un molde que define la estructura de un objeto. En este caso, la clase `Libro` tendría los atributos `titulo`, `autor` y `ejemplares`.\n\n**Objeto**: es una instancia de una clase. En este caso, cada libro en la biblioteca sería un objeto de la clase `Libro`.\n\n**Ejemplo**:\n\n```java\npublic class Libro {\n    private String titulo;\n    private String autor;\n    private int ejemplares;\n\n    public Libro(String titulo, String autor, int ejemplares) {\n        this.titulo = titulo;\n        this.autor = autor;\n        this.ejemplares = ejemplares;\n    }\n\n    public String getTitulo() {\n        return titulo;\n    }\n\n    public void setTitulo(String titulo) {\n        this.titulo = titulo;\n    }\n\n    public String getAutor() {\n        return autor;\n    }\n\n    public void setAutor(String autor) {\n        this.autor = autor;\n    }\n\n    public int getEjemplares() {\n        return ejemplares;\n    }\n\n    public void setEjemplares(int ejemplares) {\n        this.ejemplares = ejemplares;\n    }\n}\n```\n\n**Práctica guiada**:\n\n1. Crea una clase `Persona` con atributos `nombre`, `edad` y `direccion`.\n2. Crea un objeto `persona1` de la clase `Persona` y asigna valores a sus atributos.\n3. Imprime los valores de los atributos de `persona1`.\n\n**Recursos del pensum**:\n\n* El libro "Programación Orientada a Objetos" de la Universidad de Guayaquil.\n* El curso en línea "POO para principiantes" en la plataforma de la universidad.\n* El tutorial "Clases y Objetos en Java" en la página web de Oracle.\n\n**Recomendaciones**:\n\n* Repasa los conceptos de clases y objetos en el libro y en el curso en línea.\n* Practica creando clases y objetos en Java utilizando el tutorial de Oracle.\n* Si tienes alguna duda, no dudes en preguntar.\n\n¿Quieres que explique más sobre clases y objetos o prefieres seguir adelante con otro tema?\n\nRecomendacion por historial:\n- **Repaso adaptativo de Clases y Objetos**\n  Motivo: El historial marca este tema como debil; conviene reforzarlo antes de avanzar.\n  Accion sugerida: Repasemos Clases y Objetos desde la base, con un ejemplo minimo y una pregunta de comprobacion.\n- **Practica guiada por historial: Clases y Objetos**\n  Motivo: El estudiante ha trabajado este tema varias veces; la practica guiada ayuda a consolidar.\n  Accion sugerida: Dame una practica guiada de Clases y Objetos, paso a paso, y luego revisa mi respuesta.\n\nRecursos web recomendados:\n- **Oracle Java Tutorials: Classes and Objects**\n  Enlace directo: https://docs.oracle.com/javase/tutorial/java/javaOO/\n  Por que te sirve: Unidad 1 del pensum: clases, objetos, atributos, metodos y constructores en Java.\n  Nivel usado: basico | Emocion detectada: neutral | Tema: Clases y Objetos\n- **Ejercicios de POO con Java y UML**\n  Enlace directo: http://www.fadmon.unal.edu.co/fileadmin/user_upload/investigacion/centro_editorial/libros/ejercicios%20de%20programacion.pdf\n  Por que te sirve: Libro de ejercicios citado en el silabo para practicar POO, Java y UML.\n  Nivel usado: basico | Emocion detectada: neutral | Tema: Clases y Objetos\n- **Java 17: programacion avanzada**\n  Enlace directo: https://elibro.net/es/lc/uguayaquil/titulos/222668\n  Por que te sirve: Texto base del plan analitico para reforzar Programacion Avanzada.\n  Nivel usado: basico | Emocion detectada: neutral | Tema: Clases y Objetos\n\nRetroalimentacion personalizada:\n- Estado: necesitas refuerzo en Clases y Objetos.\n- Accion: lo explicare mas simple y con un ejemplo corto.\n- Nivel usado: basico | Emocion detectada: neutral.	Clases y Objetos	2026-06-09 20:31:02.106054+00	groq	2494
9	4	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	user	Repaso adaptativo de Clases y Objetos	Clases y Objetos	2026-06-09 20:33:20.206392+00	\N	\N
10	4	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	bot	**Repaso adaptativo de Clases y Objetos**\n\n¡Hola! Me alegra que estés dispuesto a repasar Clases y Objetos. Como sabes, esta es una parte fundamental de la programación orientada a objetos (POO). Vamos a empezar con algo simple y luego iremos profundizando.\n\n**¿Qué son Clases y Objetos?**\n\nUna **clase** es como un molde que define la estructura de un objeto. En este caso, la clase `Libro` tendría los atributos `titulo`, `autor` y `ejemplares`.\n\nUn **objeto** es una instancia de una clase. En este caso, cada libro en la biblioteca sería un objeto de la clase `Libro`.\n\n**Ejemplo sencillo**\n\nImagina que estás creando un programa para gestionar una biblioteca. Quieres que cada libro tenga un título, autor y cantidad de ejemplares. En lugar de crear variables separadas para cada libro, como `titulo1`, `autor1`, `ejemplares1`, etc., puedes crear una estructura llamada **clase** que tenga todos estos atributos.\n\n**Clase Libro**\n\n```java\npublic class Libro {\n    private String titulo;\n    private String autor;\n    private int ejemplares;\n\n    public Libro(String titulo, String autor, int ejemplares) {\n        this.titulo = titulo;\n        this.autor = autor;\n        this.ejemplares = ejemplares;\n    }\n\n    public String getTitulo() {\n        return titulo;\n    }\n\n    public void setTitulo(String titulo) {\n        this.titulo = titulo;\n    }\n\n    public String getAutor() {\n        return autor;\n    }\n\n    public void setAutor(String autor) {\n        this.autor = autor;\n    }\n\n    public int getEjemplares() {\n        return ejemplares;\n    }\n\n    public void setEjemplares(int ejemplares) {\n        this.ejemplares = ejemplares;\n    }\n}\n```\n\n**Práctica guiada**\n\n1. Crea una clase `Persona` con atributos `nombre`, `edad` y `direccion`.\n2. Crea un objeto `persona1` de la clase `Persona` y asigna valores a sus atributos.\n3. Imprime los valores de los atributos de `persona1`.\n\n**Preguntas de comprobación**\n\n1. ¿Qué es una clase?\n2. ¿Qué es un objeto?\n3. ¿Cómo se define una clase en Java?\n\n**Retroalimentación**\n\n¡Excelente! Has repasado Clases y Objetos de manera efectiva. Recuerda que la práctica es la mejor manera de consolidar tus conocimientos. ¡Sigue adelante y no dudes en preguntar si tienes alguna duda!\n\n¿Quieres seguir adelante con otro tema o prefieres seguir repasando Clases y Objetos?\n\nRecomendacion por historial:\n- **Repaso adaptativo de Clases y Objetos**\n  Motivo: El historial marca este tema como debil; conviene reforzarlo antes de avanzar.\n  Accion sugerida: Repasemos Clases y Objetos desde la base, con un ejemplo minimo y una pregunta de comprobacion.\n- **Practica guiada por historial: Clases y Objetos**\n  Motivo: El estudiante ha trabajado este tema varias veces; la practica guiada ayuda a consolidar.\n  Accion sugerida: Dame una practica guiada de Clases y Objetos, paso a paso, y luego revisa mi respuesta.	Clases y Objetos	2026-06-09 20:33:20.206392+00	groq	1955
11	5	Anon-94ab2a702b	user	que es clase de forma cortita	Bases de Datos y ORM	2026-06-10 02:43:49.87776+00	\N	\N
12	5	Anon-94ab2a702b	bot	**Clase: Un Concepto Fundamental en Programación Avanzada**\n\nUna clase es un molde que define una estructura de datos y comportamientos para crear objetos en una aplicación. Puedes pensar en una clase como un plan de construcción para crear diferentes tipos de casas.\n\n**Ejemplo Paso a Paso:**\n\n1. Una clase define propiedades (atributos) y métodos (acciones) que se pueden realizar con esos atributos.\n2. Los objetos creados a partir de una clase heredan esas propiedades y métodos.\n3. Puedes crear múltiples objetos a partir de una clase, cada uno con sus propias características.\n\n**Ejemplo de Código:**\n```java\npublic class Casa {\n  private String color;\n  private int numeroPuertas;\n\n  public Casa(String color, int numeroPuertas) {\n    this.color = color;\n    this.numeroPuertas = numeroPuertas;\n  }\n\n  public void pintar() {\n    System.out.println("La casa se está pintando de " + color);\n  }\n}\n```\n**Resumen Final:**\nUna clase es un molde que define una estructura de datos y comportamientos para crear objetos en una aplicación. Puedes pensar en una clase como un plan de construcción para crear diferentes tipos de casas.\n\n¿Quieres ver un ejemplo de cómo crear objetos a partir de una clase?	Bases de Datos y ORM	2026-06-10 02:43:49.87776+00	groq	2376
13	6	Anon-94ab2a702b	user	que es clase	Clases y Objetos	2026-06-10 14:59:35.741171+00	\N	\N
14	6	Anon-94ab2a702b	bot	**Bienvenido, Anon-94ab2a702b.**\n\n**Clases y Objetos** es un tema fundamental en Programación Avanzada. Te voy a explicar qué es una **clase** de manera clara y concisa.\n\n### Definición\n\nUna **clase** es una plantilla o molde que define una estructura de datos y comportamiento para objetos que pertenecen a un tipo específico. En otras palabras, una clase es una forma de crear objetos que comparten características y acciones similares.\n\n### Ejemplo\n\nImagina que estás diseñando un sistema de gestión de libros en una biblioteca. Una clase podría ser `Libro`, que tiene propiedades como `titulo`, `autor`, `editorial` y `añoPublicacion`. Además, la clase `Libro` podría tener métodos como `mostrarInformacion()` y `prestarLibro()`.\n\n### Código de ejemplo\n\n```java\npublic class Libro {\n    private String titulo;\n    private String autor;\n    private String editorial;\n    private int añoPublicacion;\n\n    public Libro(String titulo, String autor, String editorial, int añoPublicacion) {\n        this.titulo = titulo;\n        this.autor = autor;\n        this.editorial = editorial;\n        this.añoPublicacion = añoPublicacion;\n    }\n\n    public void mostrarInformacion() {\n        System.out.println("Título: " + titulo);\n        System.out.println("Autor: " + autor);\n        System.out.println("Editorial: " + editorial);\n        System.out.println("Año de publicación: " + añoPublicacion);\n    }\n\n    public void prestarLibro() {\n        System.out.println("El libro ha sido prestado.");\n    }\n}\n```\n\n### Práctica\n\n* Crea una clase `Persona` con propiedades como `nombre`, `edad` y `direccion`. Agrega métodos como `mostrarInformacion()` y `cumplirAños()`.\n* Crea un objeto `persona` de la clase `Persona` y llama a los métodos `mostrarInformacion()` y `cumplirAños()`.\n\n¿Quieres ver un ejemplo de cómo crear un objeto `Persona` y llamar a los métodos?	Clases y Objetos	2026-06-10 14:59:35.741171+00	groq	2379
\.


--
-- Data for Name: metrics_adaptive_feedback; Type: TABLE DATA; Schema: public; Owner: yelia
--

COPY public.metrics_adaptive_feedback (id, created_at, usuario, conversation_id, kind, status, topic, level_used, emotion_used, next_action, score_delta, recommendation) FROM stdin;
1	2026-06-09T19:48:50	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	2	needs_reinforcement	needs_help	Clases y Objetos	basico	neutral	explain_simpler	-1	Bajar la dificultad, usar analogia y cerrar con una pregunta de comprobacion.
2	2026-06-09T20:08:49	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	3	needs_reinforcement	needs_help	Clases y Objetos	basico	neutral	explain_simpler	-1	Bajar la dificultad, usar analogia y cerrar con una pregunta de comprobacion.
3	2026-06-09T20:31:02	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	4	needs_reinforcement	needs_help	Clases y Objetos	basico	neutral	explain_simpler	-1	Bajar la dificultad, usar analogia y cerrar con una pregunta de comprobacion.
\.


--
-- Data for Name: metrics_events; Type: TABLE DATA; Schema: public; Owner: yelia
--

COPY public.metrics_events (id, conv_id, usuario, mensaje_id, nivel_detectado, quality_score, motivo, created_at, event_type, path, meta_json) FROM stdin;
1	\N	admin	\N	\N	\N	\N	2026-06-09 02:59:43.971546+00	auth.login	/api/admin/auth/login	{"role":"admin"}
\.


--
-- Data for Name: metrics_feedback; Type: TABLE DATA; Schema: public; Owner: yelia
--

COPY public.metrics_feedback (id, created_at, usuario, conversation_id, rating, note) FROM stdin;
\.


--
-- Data for Name: metrics_perf; Type: TABLE DATA; Schema: public; Owner: yelia
--

COPY public.metrics_perf (id, created_at, usuario, conversation_id, endpoint, latency_ms) FROM stdin;
1	2026-06-09T01:55:52	GUEST-4261ad10-61c0-471f-a3a4-7539b894cbc3	1	/api/chat	1524.6
2	2026-06-09T19:48:50	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	2	/api/chat	2930.2
3	2026-06-09T20:08:49	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	3	/api/chat	3418.6
4	2026-06-09T20:31:02	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	4	/api/chat	2663.8
5	2026-06-09T20:33:20	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	4	/api/chat	2053.2
6	2026-06-10T02:43:50	Anon-94ab2a702b	5	/api/chat	2506.3
7	2026-06-10T14:59:35	Anon-94ab2a702b	6	/api/chat	2584
\.


--
-- Data for Name: metrics_recommendations; Type: TABLE DATA; Schema: public; Owner: yelia
--

COPY public.metrics_recommendations (id, created_at, usuario, conversation_id, recommendation_type, title, topic, level_used, emotion_used, priority, history_based, history_reason, source, url, reason) FROM stdin;
1	2026-06-09T01:55:52	GUEST-4261ad10-61c0-471f-a3a4-7539b894cbc3	1	practice	Modelado de clases	Introducción a la Programación Orientada a Objetos	intermedio	neutral	media	0	\N	\N	\N	La practica ayuda a consolidar el tema actual.
2	2026-06-09T01:55:52	GUEST-4261ad10-61c0-471f-a3a4-7539b894cbc3	1	quiz	Mini quiz	Introducción a la Programación Orientada a Objetos	intermedio	neutral	media	0	\N	\N	\N	Un quiz corto confirma si el estudiante ya puede reconocer el concepto.
3	2026-06-09T01:55:52	GUEST-4261ad10-61c0-471f-a3a4-7539b894cbc3	1	glossary	Glosario breve	Introducción a la Programación Orientada a Objetos	intermedio	neutral	media	0	\N	\N	\N	El tema contiene vocabulario tecnico que puede bloquear el aprendizaje.
4	2026-06-09T01:55:52	GUEST-4261ad10-61c0-471f-a3a4-7539b894cbc3	1	web_resource	Oracle Java Tutorials: Classes and Objects	Introducción a la Programación Orientada a Objetos	intermedio	neutral	baja	0	\N	Oracle	https://docs.oracle.com/javase/tutorial/java/javaOO/	El estudiante pidio recursos web; se recomienda una fuente externa confiable para complementar la explicacion.
5	2026-06-09T19:48:50	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	2	foundation	Refuerzo de bases	Clases y Objetos	basico	neutral	alta	0	\N	\N	\N	El nivel detectado requiere fundamentos antes de ejercicios extensos.
6	2026-06-09T19:48:50	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	2	web_resource	Oracle Java Tutorials: Classes and Objects	Clases y Objetos	basico	neutral	alta	0	\N	Oracle	https://docs.oracle.com/javase/tutorial/java/javaOO/	El estudiante pidio recursos web; se recomienda una fuente externa confiable para complementar la explicacion.
7	2026-06-09T19:48:50	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	2	practice	Clase y objeto básicos	Clases y Objetos	basico	neutral	media	0	\N	\N	\N	La practica ayuda a consolidar el tema actual.
8	2026-06-09T19:48:50	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	2	quiz	Mini quiz	Clases y Objetos	basico	neutral	media	0	\N	\N	\N	Un quiz corto confirma si el estudiante ya puede reconocer el concepto.
9	2026-06-09T19:48:50	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	2	glossary	Glosario breve	Clases y Objetos	basico	neutral	media	0	\N	\N	\N	El tema contiene vocabulario tecnico que puede bloquear el aprendizaje.
10	2026-06-09T20:08:49	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	3	history_review	Repaso adaptativo de Clases y Objetos	Clases y Objetos	basico	neutral	alta	1	topic_in_weak_topics	\N	\N	Recomendacion generada por historial adaptativo del estudiante.
11	2026-06-09T20:08:49	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	3	foundation	Refuerzo de bases	Clases y Objetos	basico	neutral	alta	0	\N	\N	\N	El nivel detectado requiere fundamentos antes de ejercicios extensos.
12	2026-06-09T20:08:49	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	3	history_practice	Practica guiada por historial: Clases y Objetos	Clases y Objetos	basico	neutral	alta	1	repeated_topic_or_reinforcement	\N	\N	Recomendacion generada por frecuencia de consultas y necesidades previas de refuerzo.
13	2026-06-09T20:08:49	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	3	web_resource	Oracle Java Tutorials: Classes and Objects	Clases y Objetos	basico	neutral	alta	0	\N	Oracle	https://docs.oracle.com/javase/tutorial/java/javaOO/	El estudiante pidio recursos web; se recomienda una fuente externa confiable para complementar la explicacion.
14	2026-06-09T20:08:49	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	3	practice	Clase y objeto básicos	Clases y Objetos	basico	neutral	media	0	\N	\N	\N	La practica ayuda a consolidar el tema actual.
15	2026-06-09T20:08:49	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	3	quiz	Mini quiz	Clases y Objetos	basico	neutral	media	0	\N	\N	\N	Un quiz corto confirma si el estudiante ya puede reconocer el concepto.
16	2026-06-09T20:31:02	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	4	history_review	Repaso adaptativo de Clases y Objetos	Clases y Objetos	basico	neutral	alta	1	topic_in_weak_topics	\N	\N	Recomendacion generada por historial adaptativo del estudiante.
17	2026-06-09T20:31:02	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	4	foundation	Refuerzo de bases	Clases y Objetos	basico	neutral	alta	0	\N	\N	\N	El nivel detectado requiere fundamentos antes de ejercicios extensos.
18	2026-06-09T20:31:02	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	4	history_practice	Practica guiada por historial: Clases y Objetos	Clases y Objetos	basico	neutral	alta	1	repeated_topic_or_reinforcement	\N	\N	Recomendacion generada por frecuencia de consultas y necesidades previas de refuerzo.
19	2026-06-09T20:31:02	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	4	web_resource	Oracle Java Tutorials: Classes and Objects	Clases y Objetos	basico	neutral	alta	0	\N	Oracle	https://docs.oracle.com/javase/tutorial/java/javaOO/	El estudiante pidio recursos web; se recomienda una fuente externa confiable para complementar la explicacion.
20	2026-06-09T20:31:02	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	4	web_resource	Ejercicios de POO con Java y UML	Clases y Objetos	basico	neutral	alta	0	\N	Bibliografia complementaria del silabo	http://www.fadmon.unal.edu.co/fileadmin/user_upload/investigacion/centro_editorial/libros/ejercicios%20de%20programacion.pdf	El estudiante pidio recursos web; se recomienda una fuente externa confiable para complementar la explicacion.
21	2026-06-09T20:31:02	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	4	web_resource	Java 17: programacion avanzada	Clases y Objetos	basico	neutral	alta	0	\N	Bibliografia basica UG	https://elibro.net/es/lc/uguayaquil/titulos/222668	El estudiante pidio recursos web; se recomienda una fuente externa confiable para complementar la explicacion.
22	2026-06-09T20:33:20	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	4	history_review	Repaso adaptativo de Clases y Objetos	Clases y Objetos	intermedio	neutral	alta	1	topic_in_weak_topics	\N	\N	Recomendacion generada por historial adaptativo del estudiante.
23	2026-06-09T20:33:20	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	4	history_practice	Practica guiada por historial: Clases y Objetos	Clases y Objetos	intermedio	neutral	alta	1	repeated_topic_or_reinforcement	\N	\N	Recomendacion generada por frecuencia de consultas y necesidades previas de refuerzo.
24	2026-06-09T20:33:20	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	4	practice	Modelado de clases	Clases y Objetos	intermedio	neutral	media	0	\N	\N	\N	La practica ayuda a consolidar el tema actual.
25	2026-06-09T20:33:20	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	4	quiz	Mini quiz	Clases y Objetos	intermedio	neutral	media	0	\N	\N	\N	Un quiz corto confirma si el estudiante ya puede reconocer el concepto.
26	2026-06-09T20:33:20	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	4	glossary	Glosario breve	Clases y Objetos	intermedio	neutral	media	0	\N	\N	\N	El tema contiene vocabulario tecnico que puede bloquear el aprendizaje.
27	2026-06-09T20:33:20	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	4	web_resource	Oracle Java Tutorials: Classes and Objects	Clases y Objetos	intermedio	neutral	baja	0	\N	Oracle	https://docs.oracle.com/javase/tutorial/java/javaOO/	El estudiante pidio recursos web; se recomienda una fuente externa confiable para complementar la explicacion.
28	2026-06-10T02:43:50	Anon-94ab2a702b	5	practice	ORM y buenas prácticas	Bases de Datos y ORM	intermedio	neutral	media	0	\N	\N	\N	La practica ayuda a consolidar el tema actual.
29	2026-06-10T02:43:50	Anon-94ab2a702b	5	quiz	Mini quiz	Bases de Datos y ORM	intermedio	neutral	media	0	\N	\N	\N	Un quiz corto confirma si el estudiante ya puede reconocer el concepto.
30	2026-06-10T02:43:50	Anon-94ab2a702b	5	glossary	Glosario breve	Bases de Datos y ORM	intermedio	neutral	media	0	\N	\N	\N	El tema contiene vocabulario tecnico que puede bloquear el aprendizaje.
31	2026-06-10T02:43:50	Anon-94ab2a702b	5	web_resource	Oracle Java Tutorials: JDBC Basics	Bases de Datos y ORM	intermedio	neutral	baja	0	\N	Oracle	https://docs.oracle.com/javase/tutorial/jdbc/basics/	El estudiante pidio recursos web; se recomienda una fuente externa confiable para complementar la explicacion.
32	2026-06-10T14:59:35	Anon-94ab2a702b	6	practice	Modelado de clases	Clases y Objetos	intermedio	neutral	media	0	\N	\N	\N	La practica ayuda a consolidar el tema actual.
33	2026-06-10T14:59:35	Anon-94ab2a702b	6	quiz	Mini quiz	Clases y Objetos	intermedio	neutral	media	0	\N	\N	\N	Un quiz corto confirma si el estudiante ya puede reconocer el concepto.
34	2026-06-10T14:59:35	Anon-94ab2a702b	6	glossary	Glosario breve	Clases y Objetos	intermedio	neutral	media	0	\N	\N	\N	El tema contiene vocabulario tecnico que puede bloquear el aprendizaje.
35	2026-06-10T14:59:35	Anon-94ab2a702b	6	web_resource	Oracle Java Tutorials: Classes and Objects	Clases y Objetos	intermedio	neutral	baja	0	\N	Oracle	https://docs.oracle.com/javase/tutorial/java/javaOO/	El estudiante pidio recursos web; se recomienda una fuente externa confiable para complementar la explicacion.
\.


--
-- Data for Name: progreso; Type: TABLE DATA; Schema: public; Owner: yelia
--

COPY public.progreso (id, usuario, puntos, temas_aprendidos, ciclo_academico, estado_materia, nivel_materia, created_at, updated_at) FROM stdin;
1	GUEST-4261ad10-61c0-471f-a3a4-7539b894cbc3	1	["Introducción a la Programación Orientada a Objetos"]	\N	\N	\N	2026-06-09 01:55:52.14946+00	2026-06-09 01:55:52.14946+00
2	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	1	["Clases y Objetos"]	\N	\N	\N	2026-06-09 19:48:50.020841+00	2026-06-09 20:33:20.278819+00
3	Anon-94ab2a702b	2	["Bases de Datos y ORM", "Clases y Objetos"]	\N	\N	\N	2026-06-10 02:43:49.980414+00	2026-06-10 14:59:35.895348+00
\.


--
-- Data for Name: structured_quizzes; Type: TABLE DATA; Schema: public; Owner: yelia
--

COPY public.structured_quizzes (id, conv_id, usuario, tema, source_message_id, quiz_json, status, last_score, total_questions, answered_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: student_profiles; Type: TABLE DATA; Schema: public; Owner: yelia
--

COPY public.student_profiles (student_id, profile_json, updated_at) FROM stdin;
GUEST-4261ad10-61c0-471f-a3a4-7539b894cbc3	{"student_id": "GUEST-4261ad10-61c0-471f-a3a4-7539b894cbc3", "nickname": null, "level_current": "intermedio", "level_confidence": 0.55, "course": null, "tags": [], "notes": "", "skills": {}, "mistakes": [], "goals": [], "stats": {"messages": 1, "quizzes": 0, "exercises": 0}, "last_topic": "Introducción a la Programación Orientada a Objetos", "updated_at": "2026-06-09T01:55:52", "metrics": {"messages_total": 2, "emotions": {"neutral": 2}, "intents": {"saludo": 2}, "topics": {"Introducción a la Programación Orientada a Objetos": 2}, "feedback": {}}, "adaptive": {"last_emotion": "neutral", "last_emotion_label": "neutral", "last_intent": "saludo", "last_topic": "Introducción a la Programación Orientada a Objetos", "last_level": "intermedio", "support_mode": false, "next_best_action": "recommend_next_resource", "recent_recommendations": [{"type": "practice", "title": "Modelado de clases", "source": null, "url": null, "topic": "Introducción a la Programación Orientada a Objetos", "reason": "La practica ayuda a consolidar el tema actual."}, {"type": "quiz", "title": "Mini quiz", "source": null, "url": null, "topic": "Introducción a la Programación Orientada a Objetos", "reason": "Un quiz corto confirma si el estudiante ya puede reconocer el concepto."}, {"type": "glossary", "title": "Glosario breve", "source": null, "url": null, "topic": "Introducción a la Programación Orientada a Objetos", "reason": "El tema contiene vocabulario tecnico que puede bloquear el aprendizaje."}, {"type": "web_resource", "title": "Oracle Java Tutorials: Classes and Objects", "source": "Oracle", "url": "https://docs.oracle.com/javase/tutorial/java/javaOO/", "topic": "Introducción a la Programación Orientada a Objetos", "reason": "El estudiante pidio recursos web; se recomienda una fuente externa confiable para complementar la explicacion."}], "updated_at": "2026-06-09T01:55:52", "weak_topics": [], "mastered_topics": [], "learning_state": "active"}, "adaptive_summary": {"learning_state": "active", "next_best_action": "recommend_next_resource", "weak_topics": [], "mastered_topics": [], "last_topic": "Introducción a la Programación Orientada a Objetos", "last_level": "intermedio", "last_emotion": "neutral"}}	2026-06-09T01:55:52
Anon-cff67bcbe5	{"student_id": "Anon-cff67bcbe5", "nickname": null, "level_current": "basico", "level_confidence": 0.5, "course": null, "tags": [], "notes": "", "skills": {}, "mistakes": [], "goals": [], "stats": {"messages": 0, "quizzes": 0, "exercises": 0}, "last_topic": null, "updated_at": "2026-06-09T19:52:13", "adaptive": {"last_plan": {"contract_version": "adaptive_personalization.v1", "topic": "Clases y Objetos", "selected_level": "basico", "strategy": "reinforce_foundations", "next_best_action": "explain_simpler", "updated_at": "2026-06-09T19:52:13"}}, "adaptive_summary": {"last_adaptive_strategy": "reinforce_foundations", "last_selected_level": "basico"}}	2026-06-09T19:52:13
GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	{"student_id": "GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028", "nickname": null, "level_current": "intermedio", "level_confidence": 0.55, "course": null, "tags": [], "notes": "", "skills": {}, "mistakes": [], "goals": [], "stats": {"messages": 4, "quizzes": 0, "exercises": 0}, "last_topic": "Clases y Objetos", "updated_at": "2026-06-09T20:33:20", "metrics": {"messages_total": 8, "emotions": {"neutral": 8}, "intents": {"teoria": 6, "otro": 2}, "topics": {"Clases y Objetos": 8}, "feedback": {"needs_reinforcement": 3}}, "adaptive": {"last_emotion": "neutral", "last_emotion_label": "neutral", "last_intent": "otro", "last_topic": "Clases y Objetos", "last_level": "intermedio", "support_mode": false, "next_best_action": "recommend_next_resource", "recent_recommendations": [{"type": "history_review", "title": "Repaso adaptativo de Clases y Objetos", "source": null, "url": null, "topic": "Clases y Objetos", "reason": "Recomendacion generada por historial adaptativo del estudiante."}, {"type": "history_practice", "title": "Practica guiada por historial: Clases y Objetos", "source": null, "url": null, "topic": "Clases y Objetos", "reason": "Recomendacion generada por frecuencia de consultas y necesidades previas de refuerzo."}, {"type": "practice", "title": "Modelado de clases", "source": null, "url": null, "topic": "Clases y Objetos", "reason": "La practica ayuda a consolidar el tema actual."}, {"type": "quiz", "title": "Mini quiz", "source": null, "url": null, "topic": "Clases y Objetos", "reason": "Un quiz corto confirma si el estudiante ya puede reconocer el concepto."}, {"type": "glossary", "title": "Glosario breve", "source": null, "url": null, "topic": "Clases y Objetos", "reason": "El tema contiene vocabulario tecnico que puede bloquear el aprendizaje."}], "updated_at": "2026-06-09T20:33:20", "weak_topics": ["Clases y Objetos"], "mastered_topics": [], "learning_state": "needs_reinforcement", "last_plan": {"contract_version": "adaptive_personalization.v1", "topic": "Clases y Objetos", "selected_level": "basico", "strategy": "reinforce_foundations", "next_best_action": "explain_simpler", "updated_at": "2026-06-09T20:33:20"}}, "adaptive_summary": {"learning_state": "needs_reinforcement", "next_best_action": "recommend_next_resource", "weak_topics": ["Clases y Objetos"], "mastered_topics": [], "last_topic": "Clases y Objetos", "last_level": "intermedio", "last_emotion": "neutral", "last_adaptive_strategy": "reinforce_foundations", "last_selected_level": "basico"}}	2026-06-09T20:33:20
Anon-94ab2a702b	{"student_id": "Anon-94ab2a702b", "nickname": null, "level_current": "intermedio", "level_confidence": 0.55, "course": null, "tags": [], "notes": "", "skills": {}, "mistakes": [], "goals": [], "stats": {"messages": 2, "quizzes": 0, "exercises": 0}, "last_topic": "Clases y Objetos", "updated_at": "2026-06-10T14:59:35", "metrics": {"messages_total": 4, "emotions": {"neutral": 4}, "intents": {"teoria": 2, "saludo": 2}, "topics": {"Bases de Datos y ORM": 2, "Clases y Objetos": 2}, "feedback": {}}, "adaptive": {"last_emotion": "neutral", "last_emotion_label": "neutral", "last_intent": "saludo", "last_topic": "Clases y Objetos", "last_level": "intermedio", "support_mode": false, "next_best_action": "recommend_next_resource", "recent_recommendations": [{"type": "practice", "title": "Modelado de clases", "source": null, "url": null, "topic": "Clases y Objetos", "reason": "La practica ayuda a consolidar el tema actual."}, {"type": "quiz", "title": "Mini quiz", "source": null, "url": null, "topic": "Clases y Objetos", "reason": "Un quiz corto confirma si el estudiante ya puede reconocer el concepto."}, {"type": "glossary", "title": "Glosario breve", "source": null, "url": null, "topic": "Clases y Objetos", "reason": "El tema contiene vocabulario tecnico que puede bloquear el aprendizaje."}, {"type": "web_resource", "title": "Oracle Java Tutorials: Classes and Objects", "source": "Oracle", "url": "https://docs.oracle.com/javase/tutorial/java/javaOO/", "topic": "Clases y Objetos", "reason": "El estudiante pidio recursos web; se recomienda una fuente externa confiable para complementar la explicacion."}], "updated_at": "2026-06-10T14:59:35", "weak_topics": [], "mastered_topics": [], "learning_state": "active", "last_plan": {"contract_version": "adaptive_personalization.v1", "topic": "Clases y Objetos", "selected_level": "intermedio", "strategy": "continue_learning", "next_best_action": "recommend_next_resource", "updated_at": "2026-06-10T14:59:35"}}, "adaptive_summary": {"learning_state": "active", "next_best_action": "recommend_next_resource", "weak_topics": [], "mastered_topics": [], "last_topic": "Clases y Objetos", "last_level": "intermedio", "last_emotion": "neutral", "last_adaptive_strategy": "continue_learning", "last_selected_level": "intermedio"}}	2026-06-10T14:59:35
\.


--
-- Data for Name: usuarios; Type: TABLE DATA; Schema: public; Owner: yelia
--

COPY public.usuarios (id, alias, email, role, status, last_seen, updated_at, created_at) FROM stdin;
1	GUEST-4261ad10-61c0-471f-a3a4-7539b894cbc3	\N	student	active	\N	2026-06-09 01:55:41.059621+00	2026-06-09 01:55:41.059621+00
2	GUEST-424246c0-1afd-41b6-a07b-0f9200bbc028	\N	student	active	\N	2026-06-09 22:01:18.484599+00	2026-06-09 19:48:41.55503+00
3	Anon-94ab2a702b	\N	student	active	\N	2026-06-10 02:43:49.900131+00	2026-06-10 02:43:49.900131+00
\.


--
-- Name: accounts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: yelia
--

SELECT pg_catalog.setval('public.accounts_id_seq', 1, true);


--
-- Name: attachments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: yelia
--

SELECT pg_catalog.setval('public.attachments_id_seq', 1, false);


--
-- Name: audit_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: yelia
--

SELECT pg_catalog.setval('public.audit_logs_id_seq', 2, true);


--
-- Name: conversaciones_id_seq; Type: SEQUENCE SET; Schema: public; Owner: yelia
--

SELECT pg_catalog.setval('public.conversaciones_id_seq', 6, true);


--
-- Name: interacciones_id_seq; Type: SEQUENCE SET; Schema: public; Owner: yelia
--

SELECT pg_catalog.setval('public.interacciones_id_seq', 7, true);


--
-- Name: messages_id_seq; Type: SEQUENCE SET; Schema: public; Owner: yelia
--

SELECT pg_catalog.setval('public.messages_id_seq', 14, true);


--
-- Name: metrics_adaptive_feedback_id_seq; Type: SEQUENCE SET; Schema: public; Owner: yelia
--

SELECT pg_catalog.setval('public.metrics_adaptive_feedback_id_seq', 3, true);


--
-- Name: metrics_events_id_seq; Type: SEQUENCE SET; Schema: public; Owner: yelia
--

SELECT pg_catalog.setval('public.metrics_events_id_seq', 1, true);


--
-- Name: metrics_feedback_id_seq; Type: SEQUENCE SET; Schema: public; Owner: yelia
--

SELECT pg_catalog.setval('public.metrics_feedback_id_seq', 1, false);


--
-- Name: metrics_perf_id_seq; Type: SEQUENCE SET; Schema: public; Owner: yelia
--

SELECT pg_catalog.setval('public.metrics_perf_id_seq', 7, true);


--
-- Name: metrics_recommendations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: yelia
--

SELECT pg_catalog.setval('public.metrics_recommendations_id_seq', 35, true);


--
-- Name: progreso_id_seq; Type: SEQUENCE SET; Schema: public; Owner: yelia
--

SELECT pg_catalog.setval('public.progreso_id_seq', 3, true);


--
-- Name: structured_quizzes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: yelia
--

SELECT pg_catalog.setval('public.structured_quizzes_id_seq', 1, false);


--
-- Name: usuarios_id_seq; Type: SEQUENCE SET; Schema: public; Owner: yelia
--

SELECT pg_catalog.setval('public.usuarios_id_seq', 3, true);


--
-- Name: accounts accounts_pkey; Type: CONSTRAINT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.accounts
    ADD CONSTRAINT accounts_pkey PRIMARY KEY (id);


--
-- Name: accounts accounts_username_key; Type: CONSTRAINT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.accounts
    ADD CONSTRAINT accounts_username_key UNIQUE (username);


--
-- Name: attachments attachments_pkey; Type: CONSTRAINT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.attachments
    ADD CONSTRAINT attachments_pkey PRIMARY KEY (id);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Name: conversaciones conversaciones_pkey; Type: CONSTRAINT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.conversaciones
    ADD CONSTRAINT conversaciones_pkey PRIMARY KEY (id);


--
-- Name: interacciones interacciones_pkey; Type: CONSTRAINT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.interacciones
    ADD CONSTRAINT interacciones_pkey PRIMARY KEY (id);


--
-- Name: messages messages_pkey; Type: CONSTRAINT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_pkey PRIMARY KEY (id);


--
-- Name: metrics_adaptive_feedback metrics_adaptive_feedback_pkey; Type: CONSTRAINT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.metrics_adaptive_feedback
    ADD CONSTRAINT metrics_adaptive_feedback_pkey PRIMARY KEY (id);


--
-- Name: metrics_events metrics_events_pkey; Type: CONSTRAINT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.metrics_events
    ADD CONSTRAINT metrics_events_pkey PRIMARY KEY (id);


--
-- Name: metrics_feedback metrics_feedback_pkey; Type: CONSTRAINT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.metrics_feedback
    ADD CONSTRAINT metrics_feedback_pkey PRIMARY KEY (id);


--
-- Name: metrics_perf metrics_perf_pkey; Type: CONSTRAINT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.metrics_perf
    ADD CONSTRAINT metrics_perf_pkey PRIMARY KEY (id);


--
-- Name: metrics_recommendations metrics_recommendations_pkey; Type: CONSTRAINT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.metrics_recommendations
    ADD CONSTRAINT metrics_recommendations_pkey PRIMARY KEY (id);


--
-- Name: progreso progreso_pkey; Type: CONSTRAINT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.progreso
    ADD CONSTRAINT progreso_pkey PRIMARY KEY (id);


--
-- Name: progreso progreso_usuario_key; Type: CONSTRAINT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.progreso
    ADD CONSTRAINT progreso_usuario_key UNIQUE (usuario);


--
-- Name: structured_quizzes structured_quizzes_pkey; Type: CONSTRAINT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.structured_quizzes
    ADD CONSTRAINT structured_quizzes_pkey PRIMARY KEY (id);


--
-- Name: student_profiles student_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.student_profiles
    ADD CONSTRAINT student_profiles_pkey PRIMARY KEY (student_id);


--
-- Name: usuarios usuarios_alias_key; Type: CONSTRAINT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_alias_key UNIQUE (alias);


--
-- Name: usuarios usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_pkey PRIMARY KEY (id);


--
-- Name: idx_attachments_conv; Type: INDEX; Schema: public; Owner: yelia
--

CREATE INDEX idx_attachments_conv ON public.attachments USING btree (conv_id);


--
-- Name: idx_attachments_created; Type: INDEX; Schema: public; Owner: yelia
--

CREATE INDEX idx_attachments_created ON public.attachments USING btree (created_at DESC);


--
-- Name: idx_attachments_original_name; Type: INDEX; Schema: public; Owner: yelia
--

CREATE INDEX idx_attachments_original_name ON public.attachments USING btree (original_name);


--
-- Name: idx_attachments_uploaded; Type: INDEX; Schema: public; Owner: yelia
--

CREATE INDEX idx_attachments_uploaded ON public.attachments USING btree (uploaded_at DESC);


--
-- Name: idx_attachments_usuario; Type: INDEX; Schema: public; Owner: yelia
--

CREATE INDEX idx_attachments_usuario ON public.attachments USING btree (usuario);


--
-- Name: idx_conversaciones_usuario; Type: INDEX; Schema: public; Owner: yelia
--

CREATE INDEX idx_conversaciones_usuario ON public.conversaciones USING btree (usuario);


--
-- Name: idx_interacciones_usuario; Type: INDEX; Schema: public; Owner: yelia
--

CREATE INDEX idx_interacciones_usuario ON public.interacciones USING btree (usuario_id);


--
-- Name: idx_messages_conv; Type: INDEX; Schema: public; Owner: yelia
--

CREATE INDEX idx_messages_conv ON public.messages USING btree (conv_id);


--
-- Name: idx_messages_conv_created; Type: INDEX; Schema: public; Owner: yelia
--

CREATE INDEX idx_messages_conv_created ON public.messages USING btree (conv_id, created_at);


--
-- Name: idx_messages_remitente; Type: INDEX; Schema: public; Owner: yelia
--

CREATE INDEX idx_messages_remitente ON public.messages USING btree (remitente);


--
-- Name: idx_messages_tema; Type: INDEX; Schema: public; Owner: yelia
--

CREATE INDEX idx_messages_tema ON public.messages USING btree (tema);


--
-- Name: idx_messages_tema_remitente; Type: INDEX; Schema: public; Owner: yelia
--

CREATE INDEX idx_messages_tema_remitente ON public.messages USING btree (tema, remitente);


--
-- Name: idx_messages_usuario_created; Type: INDEX; Schema: public; Owner: yelia
--

CREATE INDEX idx_messages_usuario_created ON public.messages USING btree (usuario, created_at);


--
-- Name: idx_metrics_conv; Type: INDEX; Schema: public; Owner: yelia
--

CREATE INDEX idx_metrics_conv ON public.metrics_events USING btree (conv_id);


--
-- Name: idx_metrics_usuario_created; Type: INDEX; Schema: public; Owner: yelia
--

CREATE INDEX idx_metrics_usuario_created ON public.metrics_events USING btree (usuario, created_at);


--
-- Name: idx_progreso_usuario; Type: INDEX; Schema: public; Owner: yelia
--

CREATE INDEX idx_progreso_usuario ON public.progreso USING btree (usuario);


--
-- Name: idx_structured_quizzes_conv; Type: INDEX; Schema: public; Owner: yelia
--

CREATE INDEX idx_structured_quizzes_conv ON public.structured_quizzes USING btree (conv_id);


--
-- Name: idx_structured_quizzes_status; Type: INDEX; Schema: public; Owner: yelia
--

CREATE INDEX idx_structured_quizzes_status ON public.structured_quizzes USING btree (status);


--
-- Name: idx_structured_quizzes_usuario; Type: INDEX; Schema: public; Owner: yelia
--

CREATE INDEX idx_structured_quizzes_usuario ON public.structured_quizzes USING btree (usuario);


--
-- Name: idx_student_profiles_updated; Type: INDEX; Schema: public; Owner: yelia
--

CREATE INDEX idx_student_profiles_updated ON public.student_profiles USING btree (updated_at);


--
-- Name: attachments attachments_conv_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.attachments
    ADD CONSTRAINT attachments_conv_id_fkey FOREIGN KEY (conv_id) REFERENCES public.conversaciones(id) ON DELETE CASCADE;


--
-- Name: attachments attachments_message_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.attachments
    ADD CONSTRAINT attachments_message_id_fkey FOREIGN KEY (message_id) REFERENCES public.messages(id) ON DELETE SET NULL;


--
-- Name: interacciones interacciones_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.interacciones
    ADD CONSTRAINT interacciones_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id);


--
-- Name: messages messages_conv_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_conv_id_fkey FOREIGN KEY (conv_id) REFERENCES public.conversaciones(id) ON DELETE CASCADE;


--
-- Name: metrics_events metrics_events_conv_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.metrics_events
    ADD CONSTRAINT metrics_events_conv_id_fkey FOREIGN KEY (conv_id) REFERENCES public.conversaciones(id);


--
-- Name: metrics_events metrics_events_mensaje_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.metrics_events
    ADD CONSTRAINT metrics_events_mensaje_id_fkey FOREIGN KEY (mensaje_id) REFERENCES public.messages(id);


--
-- Name: structured_quizzes structured_quizzes_conv_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.structured_quizzes
    ADD CONSTRAINT structured_quizzes_conv_id_fkey FOREIGN KEY (conv_id) REFERENCES public.conversaciones(id) ON DELETE CASCADE;


--
-- Name: structured_quizzes structured_quizzes_source_message_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: yelia
--

ALTER TABLE ONLY public.structured_quizzes
    ADD CONSTRAINT structured_quizzes_source_message_id_fkey FOREIGN KEY (source_message_id) REFERENCES public.messages(id) ON DELETE SET NULL;


--
-- PostgreSQL database dump complete
--

\unrestrict TmM39PTbMjr5gUk7mgfk9oiBbBaQidET0Ycgri7Or75wC7u0O0L9RZ2wGMmUMMO

