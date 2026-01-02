--
-- PostgreSQL database dump
--

\restrict ZKoPvRdm0x8JXR0sXZfcZpfPwIghaWZbID9TE33R8IcDyoen1XILtqpaWnpsPB9

-- Dumped from database version 16.11 (Debian 16.11-1.pgdg12+1)
-- Dumped by pg_dump version 16.11 (Debian 16.11-1.pgdg12+1)

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
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- Name: auth_reason; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.auth_reason AS ENUM (
    'ok',
    'low_similarity',
    'spoof',
    'bad_phrase',
    'expired_challenge',
    'error'
);


--
-- Name: purge_expired_data(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.purge_expired_data() RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
  -- Borrar audio crudo pasado el período de retención definido por cada usuario
  DELETE FROM audio_blob ab
  USING auth_attempt a, user_policy up
  WHERE a.audio_id = ab.id
    AND a.user_id = up.user_id
    AND a.created_at < now() - (up.retention_days || ' days')::interval;

  -- Borrar challenges viejos (ya usados o expirados hace rato)
  DELETE FROM challenge
  WHERE (used_at IS NOT NULL OR expires_at < now())
    AND created_at < now() - interval '14 days';
END; $$;


--
-- Name: trg_auth_attempt_consistency(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.trg_auth_attempt_consistency() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE ch_user UUID;
BEGIN
  -- Si marcamos decidido y no hay timestamp, lo sellamos
  IF NEW.decided = TRUE AND NEW.decided_at IS NULL THEN
    NEW.decided_at := now();
  END IF;

  -- Validar que el challenge pertenezca al mismo user
  IF NEW.challenge_id IS NOT NULL AND NEW.user_id IS NOT NULL THEN
    SELECT user_id INTO ch_user FROM challenge WHERE id = NEW.challenge_id;
    IF ch_user IS NOT NULL AND NEW.user_id IS DISTINCT FROM ch_user THEN
      RAISE EXCEPTION 'challenge % no pertenece al user %', NEW.challenge_id, NEW.user_id;
    END IF;
  END IF;

  -- Si se decidió, marcamos el challenge como usado (si no lo estaba)
  IF NEW.decided = TRUE AND NEW.challenge_id IS NOT NULL THEN
    UPDATE challenge
      SET used_at = COALESCE(used_at, now())
      WHERE id = NEW.challenge_id;
  END IF;

  RETURN NEW;
END; $$;


--
-- Name: update_phrase_quality_rules_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_phrase_quality_rules_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: api_key; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.api_key (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    client_id uuid NOT NULL,
    key_hash text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    revoked_at timestamp with time zone,
    CONSTRAINT ck_api_key_not_revoked CHECK (((revoked_at IS NULL) OR (revoked_at > created_at)))
);


--
-- Name: audio_blob; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audio_blob (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    content bytea NOT NULL,
    mime text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: audit_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audit_log (
    id bigint NOT NULL,
    "timestamp" timestamp with time zone DEFAULT now() NOT NULL,
    actor text NOT NULL,
    action text NOT NULL,
    entity_type text,
    entity_id text,
    metadata jsonb,
    success boolean DEFAULT true,
    error_message text
);


--
-- Name: audit_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.audit_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: audit_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.audit_log_id_seq OWNED BY public.audit_log.id;


--
-- Name: auth_attempt; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auth_attempt (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid,
    client_id uuid,
    challenge_id uuid,
    audio_id uuid,
    decided boolean DEFAULT false NOT NULL,
    accept boolean,
    reason public.auth_reason,
    policy_id text,
    total_latency_ms integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    decided_at timestamp with time zone,
    CONSTRAINT ck_accept_consistency CHECK ((((decided = false) AND (accept IS NULL)) OR ((decided = true) AND (accept IS NOT NULL))))
);


--
-- Name: books; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.books (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    title text NOT NULL,
    author text,
    filename text NOT NULL,
    language text DEFAULT 'es'::text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: challenge; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.challenge (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid,
    phrase text NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    used_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    phrase_id uuid,
    CONSTRAINT ck_challenge_time CHECK (((expires_at > created_at) AND ((used_at IS NULL) OR (used_at >= created_at))))
);


--
-- Name: client_app; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.client_app (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL,
    contact_email text
);


--
-- Name: enrollment_sample; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.enrollment_sample (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    embedding bytea NOT NULL,
    snr_db real,
    duration_sec real,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: model_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.model_version (
    id integer NOT NULL,
    kind text NOT NULL,
    name text NOT NULL,
    version text NOT NULL,
    CONSTRAINT model_version_kind_check CHECK ((kind = ANY (ARRAY['speaker'::text, 'antispoof'::text, 'asr'::text])))
);


--
-- Name: model_version_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.model_version_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: model_version_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.model_version_id_seq OWNED BY public.model_version.id;


--
-- Name: phrase; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.phrase (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    text text NOT NULL,
    source text,
    word_count integer NOT NULL,
    char_count integer NOT NULL,
    language text DEFAULT 'es'::text NOT NULL,
    difficulty text,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    book_id uuid,
    CONSTRAINT ck_phrase_length CHECK (((char_count >= 20) AND (char_count <= 500))),
    CONSTRAINT phrase_difficulty_check CHECK ((difficulty = ANY (ARRAY['easy'::text, 'medium'::text, 'hard'::text])))
);


--
-- Name: phrase_quality_rules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.phrase_quality_rules (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    rule_name text NOT NULL,
    rule_type text NOT NULL,
    rule_value jsonb NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by uuid,
    CONSTRAINT ck_rule_value_has_description CHECK ((rule_value ? 'description'::text)),
    CONSTRAINT ck_rule_value_has_value CHECK ((rule_value ? 'value'::text)),
    CONSTRAINT phrase_quality_rules_rule_type_check CHECK ((rule_type = ANY (ARRAY['threshold'::text, 'rate_limit'::text, 'cleanup'::text])))
);


--
-- Name: phrase_usage; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.phrase_usage (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    phrase_id uuid NOT NULL,
    user_id uuid NOT NULL,
    used_for text NOT NULL,
    used_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT phrase_usage_used_for_check CHECK ((used_for = ANY (ARRAY['enrollment'::text, 'verification'::text, 'challenge'::text])))
);


--
-- Name: scores; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.scores (
    attempt_id uuid NOT NULL,
    similarity real NOT NULL,
    spoof_prob real NOT NULL,
    phrase_match real NOT NULL,
    phrase_ok boolean,
    inference_ms integer,
    speaker_model_id integer,
    antispoof_model_id integer,
    asr_model_id integer
);


--
-- Name: user; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."user" (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    external_ref text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    deleted_at timestamp with time zone,
    failed_auth_attempts integer DEFAULT 0 NOT NULL,
    locked_until timestamp with time zone,
    email text,
    password text,
    first_name text,
    last_name text,
    role text DEFAULT 'user'::text,
    company text,
    last_login timestamp with time zone,
    settings jsonb DEFAULT '{}'::jsonb,
    rut character varying(12),
    CONSTRAINT user_role_check CHECK ((role = ANY (ARRAY['user'::text, 'admin'::text, 'superadmin'::text])))
);


--
-- Name: user_policy; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_policy (
    user_id uuid NOT NULL,
    keep_audio boolean DEFAULT false NOT NULL,
    retention_days integer DEFAULT 7 NOT NULL,
    consent_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: v_attempt_metrics; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_attempt_metrics AS
 SELECT a.id AS attempt_id,
    a.created_at,
    a.decided_at,
    a.accept,
    a.reason,
    a.policy_id,
    a.total_latency_ms,
    s.similarity,
    s.spoof_prob,
    s.phrase_match,
    s.phrase_ok,
    s.inference_ms,
    a.user_id,
    a.client_id,
    a.challenge_id
   FROM (public.auth_attempt a
     JOIN public.scores s ON ((s.attempt_id = a.id)));


--
-- Name: voiceprint; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.voiceprint (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    embedding bytea NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: voiceprint_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.voiceprint_history (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    embedding bytea NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    speaker_model_id integer
);


--
-- Name: audit_log id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_log ALTER COLUMN id SET DEFAULT nextval('public.audit_log_id_seq'::regclass);


--
-- Name: model_version id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_version ALTER COLUMN id SET DEFAULT nextval('public.model_version_id_seq'::regclass);


--
-- Name: api_key api_key_key_hash_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_key
    ADD CONSTRAINT api_key_key_hash_key UNIQUE (key_hash);


--
-- Name: api_key api_key_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_key
    ADD CONSTRAINT api_key_pkey PRIMARY KEY (id);


--
-- Name: audio_blob audio_blob_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audio_blob
    ADD CONSTRAINT audio_blob_pkey PRIMARY KEY (id);


--
-- Name: audit_log audit_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_log
    ADD CONSTRAINT audit_log_pkey PRIMARY KEY (id);


--
-- Name: auth_attempt auth_attempt_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_attempt
    ADD CONSTRAINT auth_attempt_pkey PRIMARY KEY (id);


--
-- Name: books books_filename_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.books
    ADD CONSTRAINT books_filename_key UNIQUE (filename);


--
-- Name: books books_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.books
    ADD CONSTRAINT books_pkey PRIMARY KEY (id);


--
-- Name: challenge challenge_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.challenge
    ADD CONSTRAINT challenge_pkey PRIMARY KEY (id);


--
-- Name: client_app client_app_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.client_app
    ADD CONSTRAINT client_app_name_key UNIQUE (name);


--
-- Name: client_app client_app_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.client_app
    ADD CONSTRAINT client_app_pkey PRIMARY KEY (id);


--
-- Name: enrollment_sample enrollment_sample_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.enrollment_sample
    ADD CONSTRAINT enrollment_sample_pkey PRIMARY KEY (id);


--
-- Name: model_version model_version_kind_name_version_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_version
    ADD CONSTRAINT model_version_kind_name_version_key UNIQUE (kind, name, version);


--
-- Name: model_version model_version_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.model_version
    ADD CONSTRAINT model_version_pkey PRIMARY KEY (id);


--
-- Name: phrase phrase_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.phrase
    ADD CONSTRAINT phrase_pkey PRIMARY KEY (id);


--
-- Name: phrase_quality_rules phrase_quality_rules_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.phrase_quality_rules
    ADD CONSTRAINT phrase_quality_rules_pkey PRIMARY KEY (id);


--
-- Name: phrase_quality_rules phrase_quality_rules_rule_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.phrase_quality_rules
    ADD CONSTRAINT phrase_quality_rules_rule_name_key UNIQUE (rule_name);


--
-- Name: phrase_usage phrase_usage_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.phrase_usage
    ADD CONSTRAINT phrase_usage_pkey PRIMARY KEY (id);


--
-- Name: scores scores_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scores
    ADD CONSTRAINT scores_pkey PRIMARY KEY (attempt_id);


--
-- Name: voiceprint uq_voiceprint_user; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.voiceprint
    ADD CONSTRAINT uq_voiceprint_user UNIQUE (user_id);


--
-- Name: user user_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_email_key UNIQUE (email);


--
-- Name: user user_external_ref_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_external_ref_key UNIQUE (external_ref);


--
-- Name: user user_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);


--
-- Name: user_policy user_policy_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_policy
    ADD CONSTRAINT user_policy_pkey PRIMARY KEY (user_id);


--
-- Name: voiceprint_history voiceprint_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.voiceprint_history
    ADD CONSTRAINT voiceprint_history_pkey PRIMARY KEY (id);


--
-- Name: voiceprint voiceprint_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.voiceprint
    ADD CONSTRAINT voiceprint_pkey PRIMARY KEY (id);


--
-- Name: idx_audit_actor; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_actor ON public.audit_log USING btree (actor);


--
-- Name: idx_audit_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_time ON public.audit_log USING btree ("timestamp");


--
-- Name: idx_auth_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_auth_created ON public.auth_attempt USING btree (created_at);


--
-- Name: idx_auth_reason; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_auth_reason ON public.auth_attempt USING btree (reason);


--
-- Name: idx_auth_user_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_auth_user_time ON public.auth_attempt USING btree (user_id, created_at DESC);


--
-- Name: idx_books_filename; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_books_filename ON public.books USING btree (filename);


--
-- Name: idx_challenge_expires; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_challenge_expires ON public.challenge USING btree (expires_at);


--
-- Name: idx_challenge_phrase; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_challenge_phrase ON public.challenge USING btree (phrase_id);


--
-- Name: idx_challenge_used; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_challenge_used ON public.challenge USING btree (used_at);


--
-- Name: idx_challenge_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_challenge_user ON public.challenge USING btree (user_id);


--
-- Name: idx_enrollment_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_enrollment_user ON public.enrollment_sample USING btree (user_id);


--
-- Name: idx_phrase_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_phrase_active ON public.phrase USING btree (is_active);


--
-- Name: idx_phrase_book_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_phrase_book_id ON public.phrase USING btree (book_id);


--
-- Name: idx_phrase_difficulty; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_phrase_difficulty ON public.phrase USING btree (difficulty);


--
-- Name: idx_phrase_quality_rules_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_phrase_quality_rules_active ON public.phrase_quality_rules USING btree (is_active) WHERE (is_active = true);


--
-- Name: idx_phrase_quality_rules_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_phrase_quality_rules_type ON public.phrase_quality_rules USING btree (rule_type);


--
-- Name: idx_phrase_source; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_phrase_source ON public.phrase USING btree (source);


--
-- Name: idx_phrase_usage_phrase; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_phrase_usage_phrase ON public.phrase_usage USING btree (phrase_id);


--
-- Name: idx_phrase_usage_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_phrase_usage_user ON public.phrase_usage USING btree (user_id, used_at DESC);


--
-- Name: idx_scores_phrase_ok; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scores_phrase_ok ON public.scores USING btree (phrase_ok);


--
-- Name: idx_scores_similarity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scores_similarity ON public.scores USING btree (similarity);


--
-- Name: idx_scores_spoof; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scores_spoof ON public.scores USING btree (spoof_prob);


--
-- Name: idx_user_company; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_company ON public."user" USING btree (company) WHERE (company IS NOT NULL);


--
-- Name: idx_user_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_email ON public."user" USING btree (email) WHERE (email IS NOT NULL);


--
-- Name: idx_user_role; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_role ON public."user" USING btree (role);


--
-- Name: idx_voiceprint_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_voiceprint_user ON public.voiceprint USING btree (user_id);


--
-- Name: auth_attempt trg_auth_attempt_consistency; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_auth_attempt_consistency BEFORE INSERT OR UPDATE OF decided ON public.auth_attempt FOR EACH ROW EXECUTE FUNCTION public.trg_auth_attempt_consistency();


--
-- Name: phrase_quality_rules trg_phrase_quality_rules_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_phrase_quality_rules_updated_at BEFORE UPDATE ON public.phrase_quality_rules FOR EACH ROW EXECUTE FUNCTION public.update_phrase_quality_rules_updated_at();


--
-- Name: api_key api_key_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.api_key
    ADD CONSTRAINT api_key_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.client_app(id) ON DELETE CASCADE;


--
-- Name: auth_attempt auth_attempt_audio_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_attempt
    ADD CONSTRAINT auth_attempt_audio_id_fkey FOREIGN KEY (audio_id) REFERENCES public.audio_blob(id) ON DELETE SET NULL;


--
-- Name: auth_attempt auth_attempt_challenge_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_attempt
    ADD CONSTRAINT auth_attempt_challenge_id_fkey FOREIGN KEY (challenge_id) REFERENCES public.challenge(id) ON DELETE SET NULL;


--
-- Name: auth_attempt auth_attempt_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_attempt
    ADD CONSTRAINT auth_attempt_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.client_app(id) ON DELETE SET NULL;


--
-- Name: auth_attempt auth_attempt_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_attempt
    ADD CONSTRAINT auth_attempt_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id) ON DELETE SET NULL;


--
-- Name: challenge challenge_phrase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.challenge
    ADD CONSTRAINT challenge_phrase_id_fkey FOREIGN KEY (phrase_id) REFERENCES public.phrase(id) ON DELETE SET NULL;


--
-- Name: challenge challenge_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.challenge
    ADD CONSTRAINT challenge_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id) ON DELETE CASCADE;


--
-- Name: enrollment_sample enrollment_sample_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.enrollment_sample
    ADD CONSTRAINT enrollment_sample_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id) ON DELETE CASCADE;


--
-- Name: phrase phrase_book_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.phrase
    ADD CONSTRAINT phrase_book_id_fkey FOREIGN KEY (book_id) REFERENCES public.books(id) ON DELETE SET NULL;


--
-- Name: phrase_quality_rules phrase_quality_rules_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.phrase_quality_rules
    ADD CONSTRAINT phrase_quality_rules_created_by_fkey FOREIGN KEY (created_by) REFERENCES public."user"(id) ON DELETE SET NULL;


--
-- Name: phrase_usage phrase_usage_phrase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.phrase_usage
    ADD CONSTRAINT phrase_usage_phrase_id_fkey FOREIGN KEY (phrase_id) REFERENCES public.phrase(id) ON DELETE CASCADE;


--
-- Name: phrase_usage phrase_usage_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.phrase_usage
    ADD CONSTRAINT phrase_usage_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id) ON DELETE CASCADE;


--
-- Name: scores scores_antispoof_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scores
    ADD CONSTRAINT scores_antispoof_model_id_fkey FOREIGN KEY (antispoof_model_id) REFERENCES public.model_version(id);


--
-- Name: scores scores_asr_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scores
    ADD CONSTRAINT scores_asr_model_id_fkey FOREIGN KEY (asr_model_id) REFERENCES public.model_version(id);


--
-- Name: scores scores_attempt_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scores
    ADD CONSTRAINT scores_attempt_id_fkey FOREIGN KEY (attempt_id) REFERENCES public.auth_attempt(id) ON DELETE CASCADE;


--
-- Name: scores scores_speaker_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scores
    ADD CONSTRAINT scores_speaker_model_id_fkey FOREIGN KEY (speaker_model_id) REFERENCES public.model_version(id);


--
-- Name: user_policy user_policy_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_policy
    ADD CONSTRAINT user_policy_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id) ON DELETE CASCADE;


--
-- Name: voiceprint_history voiceprint_history_speaker_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.voiceprint_history
    ADD CONSTRAINT voiceprint_history_speaker_model_id_fkey FOREIGN KEY (speaker_model_id) REFERENCES public.model_version(id);


--
-- Name: voiceprint_history voiceprint_history_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.voiceprint_history
    ADD CONSTRAINT voiceprint_history_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id) ON DELETE CASCADE;


--
-- Name: voiceprint voiceprint_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.voiceprint
    ADD CONSTRAINT voiceprint_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict ZKoPvRdm0x8JXR0sXZfcZpfPwIghaWZbID9TE33R8IcDyoen1XILtqpaWnpsPB9

