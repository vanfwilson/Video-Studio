--
-- PostgreSQL database dump
--

\restrict mY4wsZeM0moTfIiR4ECe7sxYdujcYT5kbOCithvgmDei7eaDqrn8fA0ZhvjKTYb

-- Dumped from database version 16.11
-- Dumped by pg_dump version 16.11

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

--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: video_studio
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_updated_at_column() OWNER TO video_studio;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: confidentiality_checks; Type: TABLE; Schema: public; Owner: video_studio
--

CREATE TABLE public.confidentiality_checks (
    id integer NOT NULL,
    video_id integer NOT NULL,
    user_id character varying(255) NOT NULL,
    overall_status character varying(50) NOT NULL,
    summary text,
    counts jsonb DEFAULT '{"low": 0, "high": 0, "medium": 0}'::jsonb,
    segments jsonb DEFAULT '[]'::jsonb,
    model_used character varying(255),
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.confidentiality_checks OWNER TO video_studio;

--
-- Name: confidentiality_checks_id_seq; Type: SEQUENCE; Schema: public; Owner: video_studio
--

CREATE SEQUENCE public.confidentiality_checks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.confidentiality_checks_id_seq OWNER TO video_studio;

--
-- Name: confidentiality_checks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: video_studio
--

ALTER SEQUENCE public.confidentiality_checks_id_seq OWNED BY public.confidentiality_checks.id;


--
-- Name: oauth_states; Type: TABLE; Schema: public; Owner: video_studio
--

CREATE TABLE public.oauth_states (
    id integer NOT NULL,
    provider character varying(50) NOT NULL,
    user_id character varying(255) NOT NULL,
    state character varying(255) NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.oauth_states OWNER TO video_studio;

--
-- Name: oauth_states_id_seq; Type: SEQUENCE; Schema: public; Owner: video_studio
--

CREATE SEQUENCE public.oauth_states_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.oauth_states_id_seq OWNER TO video_studio;

--
-- Name: oauth_states_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: video_studio
--

ALTER SEQUENCE public.oauth_states_id_seq OWNED BY public.oauth_states.id;


--
-- Name: publish_transactions; Type: TABLE; Schema: public; Owner: video_studio
--

CREATE TABLE public.publish_transactions (
    id integer NOT NULL,
    video_id integer NOT NULL,
    user_id character varying(255) NOT NULL,
    action character varying(50) NOT NULL,
    request_payload jsonb NOT NULL,
    status character varying(50) DEFAULT 'pending'::character varying,
    response_payload jsonb,
    error_message text,
    created_at timestamp with time zone DEFAULT now(),
    completed_at timestamp with time zone,
    CONSTRAINT publish_transactions_action_check CHECK (((action)::text = ANY ((ARRAY['transcribe'::character varying, 'metadata'::character varying, 'confidentiality'::character varying, 'publish'::character varying])::text[]))),
    CONSTRAINT publish_transactions_status_check CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'success'::character varying, 'failed'::character varying])::text[])))
);


ALTER TABLE public.publish_transactions OWNER TO video_studio;

--
-- Name: publish_transactions_id_seq; Type: SEQUENCE; Schema: public; Owner: video_studio
--

CREATE SEQUENCE public.publish_transactions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.publish_transactions_id_seq OWNER TO video_studio;

--
-- Name: publish_transactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: video_studio
--

ALTER SEQUENCE public.publish_transactions_id_seq OWNED BY public.publish_transactions.id;


--
-- Name: user_social_accounts; Type: TABLE; Schema: public; Owner: video_studio
--

CREATE TABLE public.user_social_accounts (
    id integer NOT NULL,
    user_id character varying(255) NOT NULL,
    platform character varying(50) DEFAULT 'youtube'::character varying NOT NULL,
    account_id character varying(255),
    account_name character varying(255),
    account_email character varying(255),
    channel_id character varying(255),
    profile_image_url text,
    access_token text,
    refresh_token text,
    token_expires_at timestamp with time zone,
    is_active boolean DEFAULT true,
    metadata jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.user_social_accounts OWNER TO video_studio;

--
-- Name: user_social_accounts_id_seq; Type: SEQUENCE; Schema: public; Owner: video_studio
--

CREATE SEQUENCE public.user_social_accounts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_social_accounts_id_seq OWNER TO video_studio;

--
-- Name: user_social_accounts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: video_studio
--

ALTER SEQUENCE public.user_social_accounts_id_seq OWNED BY public.user_social_accounts.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: video_studio
--

CREATE TABLE public.users (
    id character varying(255) NOT NULL,
    email character varying(255),
    first_name character varying(255),
    last_name character varying(255),
    profile_image_url text,
    role character varying(50) DEFAULT 'user'::character varying,
    default_channel_id character varying(255),
    notes text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.users OWNER TO video_studio;

--
-- Name: video_ingest_requests; Type: TABLE; Schema: public; Owner: video_studio
--

CREATE TABLE public.video_ingest_requests (
    id integer NOT NULL,
    user_id character varying(255) NOT NULL,
    video_id integer,
    provider character varying(50) NOT NULL,
    source_path text NOT NULL,
    source_file_name text NOT NULL,
    source_file_size bigint,
    status character varying(50) DEFAULT 'queued'::character varying,
    progress jsonb,
    error_message text,
    downloaded_path text,
    started_at timestamp with time zone,
    completed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT video_ingest_requests_status_check CHECK (((status)::text = ANY ((ARRAY['queued'::character varying, 'downloading'::character varying, 'processing'::character varying, 'done'::character varying, 'error'::character varying])::text[])))
);


ALTER TABLE public.video_ingest_requests OWNER TO video_studio;

--
-- Name: video_ingest_requests_id_seq; Type: SEQUENCE; Schema: public; Owner: video_studio
--

CREATE SEQUENCE public.video_ingest_requests_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.video_ingest_requests_id_seq OWNER TO video_studio;

--
-- Name: video_ingest_requests_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: video_studio
--

ALTER SEQUENCE public.video_ingest_requests_id_seq OWNED BY public.video_ingest_requests.id;


--
-- Name: videos; Type: TABLE; Schema: public; Owner: video_studio
--

CREATE TABLE public.videos (
    id integer NOT NULL,
    user_id character varying(255) NOT NULL,
    original_filename text NOT NULL,
    storage_path text NOT NULL,
    file_size bigint,
    mime_type character varying(100) DEFAULT 'video/mp4'::character varying,
    duration_ms integer,
    status character varying(50) DEFAULT 'uploading'::character varying,
    error_message text,
    transcript text,
    captions jsonb,
    language character varying(10) DEFAULT 'en'::character varying,
    ai_summary text,
    title character varying(500),
    description text,
    tags text,
    hashtags text,
    thumbnail_prompt text,
    thumbnail_url text,
    privacy_status character varying(20) DEFAULT 'private'::character varying,
    category character varying(50) DEFAULT '22'::character varying,
    youtube_id character varying(100),
    youtube_url text,
    youtube_channel_id character varying(100),
    youtube_response jsonb,
    published_at timestamp with time zone,
    confidentiality_status character varying(50) DEFAULT 'pending'::character varying,
    confidentiality_issues jsonb DEFAULT '[]'::jsonb,
    last_confidentiality_check_at timestamp with time zone,
    parent_video_id integer,
    trim_start_ms integer,
    trim_end_ms integer,
    speaker_image_url text,
    sentiment text,
    categories text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT videos_confidentiality_status_check CHECK (((confidentiality_status)::text = ANY ((ARRAY['pending'::character varying, 'pass'::character varying, 'warn'::character varying, 'fail'::character varying])::text[]))),
    CONSTRAINT videos_privacy_status_check CHECK (((privacy_status)::text = ANY ((ARRAY['private'::character varying, 'unlisted'::character varying, 'public'::character varying])::text[]))),
    CONSTRAINT videos_status_check CHECK (((status)::text = ANY ((ARRAY['uploading'::character varying, 'ready'::character varying, 'captioning'::character varying, 'metadata_ready'::character varying, 'publishing'::character varying, 'published'::character varying, 'error'::character varying])::text[])))
);


ALTER TABLE public.videos OWNER TO video_studio;

--
-- Name: videos_id_seq; Type: SEQUENCE; Schema: public; Owner: video_studio
--

CREATE SEQUENCE public.videos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.videos_id_seq OWNER TO video_studio;

--
-- Name: videos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: video_studio
--

ALTER SEQUENCE public.videos_id_seq OWNED BY public.videos.id;


--
-- Name: confidentiality_checks id; Type: DEFAULT; Schema: public; Owner: video_studio
--

ALTER TABLE ONLY public.confidentiality_checks ALTER COLUMN id SET DEFAULT nextval('public.confidentiality_checks_id_seq'::regclass);


--
-- Name: oauth_states id; Type: DEFAULT; Schema: public; Owner: video_studio
--

ALTER TABLE ONLY public.oauth_states ALTER COLUMN id SET DEFAULT nextval('public.oauth_states_id_seq'::regclass);


--
-- Name: publish_transactions id; Type: DEFAULT; Schema: public; Owner: video_studio
--

ALTER TABLE ONLY public.publish_transactions ALTER COLUMN id SET DEFAULT nextval('public.publish_transactions_id_seq'::regclass);


--
-- Name: user_social_accounts id; Type: DEFAULT; Schema: public; Owner: video_studio
--

ALTER TABLE ONLY public.user_social_accounts ALTER COLUMN id SET DEFAULT nextval('public.user_social_accounts_id_seq'::regclass);


--
-- Name: video_ingest_requests id; Type: DEFAULT; Schema: public; Owner: video_studio
--

ALTER TABLE ONLY public.video_ingest_requests ALTER COLUMN id SET DEFAULT nextval('public.video_ingest_requests_id_seq'::regclass);


--
-- Name: videos id; Type: DEFAULT; Schema: public; Owner: video_studio
--

ALTER TABLE ONLY public.videos ALTER COLUMN id SET DEFAULT nextval('public.videos_id_seq'::regclass);


--
-- Data for Name: confidentiality_checks; Type: TABLE DATA; Schema: public; Owner: video_studio
--



--
-- Data for Name: oauth_states; Type: TABLE DATA; Schema: public; Owner: video_studio
--

INSERT INTO public.oauth_states VALUES (1, 'youtube', 'user_enioz99mn56', 'DiNF0sUklgIAcuegRnPYW5BKbF3F9ad9foYXF_E9aJE', '2026-01-16 19:17:23.430019+00');


--
-- Data for Name: publish_transactions; Type: TABLE DATA; Schema: public; Owner: video_studio
--



--
-- Data for Name: user_social_accounts; Type: TABLE DATA; Schema: public; Owner: video_studio
--



--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: video_studio
--

INSERT INTO public.users VALUES ('user_37semyevj01', NULL, NULL, NULL, NULL, 'user', NULL, NULL, '2026-01-16 02:14:18.91393+00', '2026-01-16 02:14:18.91393+00');
INSERT INTO public.users VALUES ('user_lc1wulf9n9k', NULL, NULL, NULL, NULL, 'user', NULL, NULL, '2026-01-16 02:14:27.140696+00', '2026-01-16 02:14:27.140696+00');
INSERT INTO public.users VALUES ('user_kiijup8luy', NULL, NULL, NULL, NULL, 'user', NULL, NULL, '2026-01-16 02:15:02.250497+00', '2026-01-16 02:15:02.250497+00');
INSERT INTO public.users VALUES ('user_gclzk14xpum', NULL, NULL, NULL, NULL, 'user', NULL, NULL, '2026-01-16 02:16:19.850369+00', '2026-01-16 02:16:19.850369+00');
INSERT INTO public.users VALUES ('user_9prj8teqa99', NULL, NULL, NULL, NULL, 'user', NULL, NULL, '2026-01-16 02:17:00.318274+00', '2026-01-16 02:17:00.318274+00');
INSERT INTO public.users VALUES ('user_168jgptp7qv', NULL, NULL, NULL, NULL, 'user', NULL, NULL, '2026-01-16 03:43:54.528162+00', '2026-01-16 03:43:54.528162+00');
INSERT INTO public.users VALUES ('user_0kp084cdydz', NULL, NULL, NULL, NULL, 'user', NULL, NULL, '2026-01-16 03:54:57.840815+00', '2026-01-16 03:54:57.840815+00');
INSERT INTO public.users VALUES ('user_fw11x1peosi', NULL, NULL, NULL, NULL, 'user', NULL, NULL, '2026-01-16 03:55:15.933244+00', '2026-01-16 03:55:15.933244+00');
INSERT INTO public.users VALUES ('user_r1sc5mj5i7', NULL, NULL, NULL, NULL, 'user', NULL, NULL, '2026-01-16 04:39:32.298733+00', '2026-01-16 04:39:32.298733+00');
INSERT INTO public.users VALUES ('user_me69fyxjy3', NULL, NULL, NULL, NULL, 'user', NULL, NULL, '2026-01-16 05:07:59.054321+00', '2026-01-16 05:07:59.054321+00');
INSERT INTO public.users VALUES ('user_494qdiv9vha', NULL, NULL, NULL, NULL, 'user', NULL, NULL, '2026-01-16 12:06:53.844091+00', '2026-01-16 12:06:53.844091+00');
INSERT INTO public.users VALUES ('user_enioz99mn56', NULL, NULL, NULL, NULL, 'user', NULL, NULL, '2026-01-16 15:50:38.81877+00', '2026-01-16 15:50:38.81877+00');


--
-- Data for Name: video_ingest_requests; Type: TABLE DATA; Schema: public; Owner: video_studio
--



--
-- Data for Name: videos; Type: TABLE DATA; Schema: public; Owner: video_studio
--



--
-- Name: confidentiality_checks_id_seq; Type: SEQUENCE SET; Schema: public; Owner: video_studio
--

SELECT pg_catalog.setval('public.confidentiality_checks_id_seq', 1, false);


--
-- Name: oauth_states_id_seq; Type: SEQUENCE SET; Schema: public; Owner: video_studio
--

SELECT pg_catalog.setval('public.oauth_states_id_seq', 1, true);


--
-- Name: publish_transactions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: video_studio
--

SELECT pg_catalog.setval('public.publish_transactions_id_seq', 1, false);


--
-- Name: user_social_accounts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: video_studio
--

SELECT pg_catalog.setval('public.user_social_accounts_id_seq', 1, false);


--
-- Name: video_ingest_requests_id_seq; Type: SEQUENCE SET; Schema: public; Owner: video_studio
--

SELECT pg_catalog.setval('public.video_ingest_requests_id_seq', 1, false);


--
-- Name: videos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: video_studio
--

SELECT pg_catalog.setval('public.videos_id_seq', 1, false);


--
-- Name: confidentiality_checks confidentiality_checks_pkey; Type: CONSTRAINT; Schema: public; Owner: video_studio
--

ALTER TABLE ONLY public.confidentiality_checks
    ADD CONSTRAINT confidentiality_checks_pkey PRIMARY KEY (id);


--
-- Name: oauth_states oauth_states_pkey; Type: CONSTRAINT; Schema: public; Owner: video_studio
--

ALTER TABLE ONLY public.oauth_states
    ADD CONSTRAINT oauth_states_pkey PRIMARY KEY (id);


--
-- Name: oauth_states oauth_states_state_key; Type: CONSTRAINT; Schema: public; Owner: video_studio
--

ALTER TABLE ONLY public.oauth_states
    ADD CONSTRAINT oauth_states_state_key UNIQUE (state);


--
-- Name: publish_transactions publish_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: video_studio
--

ALTER TABLE ONLY public.publish_transactions
    ADD CONSTRAINT publish_transactions_pkey PRIMARY KEY (id);


--
-- Name: user_social_accounts user_social_accounts_pkey; Type: CONSTRAINT; Schema: public; Owner: video_studio
--

ALTER TABLE ONLY public.user_social_accounts
    ADD CONSTRAINT user_social_accounts_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: video_studio
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: video_studio
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: video_ingest_requests video_ingest_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: video_studio
--

ALTER TABLE ONLY public.video_ingest_requests
    ADD CONSTRAINT video_ingest_requests_pkey PRIMARY KEY (id);


--
-- Name: videos videos_pkey; Type: CONSTRAINT; Schema: public; Owner: video_studio
--

ALTER TABLE ONLY public.videos
    ADD CONSTRAINT videos_pkey PRIMARY KEY (id);


--
-- Name: idx_confidentiality_video; Type: INDEX; Schema: public; Owner: video_studio
--

CREATE INDEX idx_confidentiality_video ON public.confidentiality_checks USING btree (video_id);


--
-- Name: idx_ingest_user; Type: INDEX; Schema: public; Owner: video_studio
--

CREATE INDEX idx_ingest_user ON public.video_ingest_requests USING btree (user_id);


--
-- Name: idx_oauth_states_state; Type: INDEX; Schema: public; Owner: video_studio
--

CREATE INDEX idx_oauth_states_state ON public.oauth_states USING btree (state);


--
-- Name: idx_social_accounts_user; Type: INDEX; Schema: public; Owner: video_studio
--

CREATE INDEX idx_social_accounts_user ON public.user_social_accounts USING btree (user_id, platform);


--
-- Name: idx_transactions_video; Type: INDEX; Schema: public; Owner: video_studio
--

CREATE INDEX idx_transactions_video ON public.publish_transactions USING btree (video_id);


--
-- Name: idx_users_email; Type: INDEX; Schema: public; Owner: video_studio
--

CREATE INDEX idx_users_email ON public.users USING btree (email);


--
-- Name: idx_videos_created_at; Type: INDEX; Schema: public; Owner: video_studio
--

CREATE INDEX idx_videos_created_at ON public.videos USING btree (created_at DESC);


--
-- Name: idx_videos_status; Type: INDEX; Schema: public; Owner: video_studio
--

CREATE INDEX idx_videos_status ON public.videos USING btree (status);


--
-- Name: idx_videos_user_id; Type: INDEX; Schema: public; Owner: video_studio
--

CREATE INDEX idx_videos_user_id ON public.videos USING btree (user_id);


--
-- Name: video_ingest_requests update_ingest_updated_at; Type: TRIGGER; Schema: public; Owner: video_studio
--

CREATE TRIGGER update_ingest_updated_at BEFORE UPDATE ON public.video_ingest_requests FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: user_social_accounts update_social_accounts_updated_at; Type: TRIGGER; Schema: public; Owner: video_studio
--

CREATE TRIGGER update_social_accounts_updated_at BEFORE UPDATE ON public.user_social_accounts FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: users update_users_updated_at; Type: TRIGGER; Schema: public; Owner: video_studio
--

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: videos update_videos_updated_at; Type: TRIGGER; Schema: public; Owner: video_studio
--

CREATE TRIGGER update_videos_updated_at BEFORE UPDATE ON public.videos FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: confidentiality_checks confidentiality_checks_video_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: video_studio
--

ALTER TABLE ONLY public.confidentiality_checks
    ADD CONSTRAINT confidentiality_checks_video_id_fkey FOREIGN KEY (video_id) REFERENCES public.videos(id) ON DELETE CASCADE;


--
-- Name: oauth_states oauth_states_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: video_studio
--

ALTER TABLE ONLY public.oauth_states
    ADD CONSTRAINT oauth_states_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: publish_transactions publish_transactions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: video_studio
--

ALTER TABLE ONLY public.publish_transactions
    ADD CONSTRAINT publish_transactions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: publish_transactions publish_transactions_video_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: video_studio
--

ALTER TABLE ONLY public.publish_transactions
    ADD CONSTRAINT publish_transactions_video_id_fkey FOREIGN KEY (video_id) REFERENCES public.videos(id) ON DELETE CASCADE;


--
-- Name: user_social_accounts user_social_accounts_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: video_studio
--

ALTER TABLE ONLY public.user_social_accounts
    ADD CONSTRAINT user_social_accounts_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: video_ingest_requests video_ingest_requests_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: video_studio
--

ALTER TABLE ONLY public.video_ingest_requests
    ADD CONSTRAINT video_ingest_requests_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: video_ingest_requests video_ingest_requests_video_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: video_studio
--

ALTER TABLE ONLY public.video_ingest_requests
    ADD CONSTRAINT video_ingest_requests_video_id_fkey FOREIGN KEY (video_id) REFERENCES public.videos(id) ON DELETE SET NULL;


--
-- Name: videos videos_parent_video_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: video_studio
--

ALTER TABLE ONLY public.videos
    ADD CONSTRAINT videos_parent_video_id_fkey FOREIGN KEY (parent_video_id) REFERENCES public.videos(id);


--
-- Name: videos videos_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: video_studio
--

ALTER TABLE ONLY public.videos
    ADD CONSTRAINT videos_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict mY4wsZeM0moTfIiR4ECe7sxYdujcYT5kbOCithvgmDei7eaDqrn8fA0ZhvjKTYb

