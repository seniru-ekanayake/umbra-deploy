-- ============================================================
-- UMBRA — Supabase Migration Script
-- Run this in: Supabase Dashboard → SQL Editor → New Query
-- ============================================================

-- Extensions (already available in Supabase)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- ENUMS
-- ============================================================
DO $$ BEGIN
  CREATE TYPE rule_type AS ENUM ('single','correlation','enrichment','chain');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE source_dependency AS ENUM ('HARD','SOFT');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE deployment_status AS ENUM ('deployed','disabled','pending','broken');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE rule_health AS ENUM ('healthy','degraded','broken','untested');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE coverage_state AS ENUM ('BUILT','PARTIAL','BROKEN','GAP');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE gap_type AS ENUM ('detection_gap','visibility_gap','broken_rule','partial_coverage');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE decision_action AS ENUM ('approved','rejected','deferred','escalated');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE recommendation_type AS ENUM ('ingest_source','deploy_rule','fix_rule','tune_rule');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- ============================================================
-- TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS clients (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name         TEXT NOT NULL,
    industry     TEXT NOT NULL,
    geography    TEXT NOT NULL,
    tier         TEXT NOT NULL DEFAULT 'standard',
    onboarded_at TIMESTAMPTZ DEFAULT NOW(),
    active       BOOLEAN DEFAULT TRUE,
    metadata     JSONB DEFAULT '{}'::jsonb,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    updated_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS assets (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id   UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    asset_type  TEXT NOT NULL,
    criticality INTEGER NOT NULL CHECK (criticality BETWEEN 1 AND 5),
    os_family   TEXT,
    environment TEXT,
    tags        TEXT[] DEFAULT '{}',
    metadata    JSONB DEFAULT '{}'::jsonb,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS mitre_techniques (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    technique_id    TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    tactic          TEXT NOT NULL,
    parent_id       TEXT,
    description     TEXT,
    data_sources    TEXT[] DEFAULT '{}',
    platforms       TEXT[] DEFAULT '{}',
    detection_notes TEXT,
    url             TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS technique_scores (
    id                   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id            UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    technique_id         TEXT NOT NULL REFERENCES mitre_techniques(technique_id),
    priority_score       NUMERIC(5,2) NOT NULL DEFAULT 0,
    threat_intel_score   NUMERIC(5,2) DEFAULT 0,
    asset_exposure_score NUMERIC(5,2) DEFAULT 0,
    industry_score       NUMERIC(5,2) DEFAULT 0,
    geo_score            NUMERIC(5,2) DEFAULT 0,
    rationale            TEXT,
    computed_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(client_id, technique_id)
);

CREATE TABLE IF NOT EXISTS log_sources (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_key       TEXT NOT NULL UNIQUE,
    name             TEXT NOT NULL,
    category         TEXT NOT NULL,
    vendor           TEXT,
    description      TEXT,
    data_types       TEXT[] DEFAULT '{}',
    cost_per_gb      NUMERIC(8,4),
    avg_daily_gb     NUMERIC(8,4),
    setup_complexity TEXT DEFAULT 'medium',
    documentation_url TEXT,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS client_log_sources (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id        UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    source_id        UUID NOT NULL REFERENCES log_sources(id),
    active           BOOLEAN DEFAULT TRUE,
    ingestion_rate_gb NUMERIC(8,4),
    first_seen       TIMESTAMPTZ,
    last_event       TIMESTAMPTZ,
    health           TEXT DEFAULT 'unknown',
    notes            TEXT,
    UNIQUE(client_id, source_id)
);

CREATE TABLE IF NOT EXISTS rule_inventory (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_id          TEXT NOT NULL UNIQUE,
    name             TEXT NOT NULL,
    description      TEXT,
    technique_id     TEXT NOT NULL REFERENCES mitre_techniques(technique_id),
    rule_type        rule_type NOT NULL,
    logic_summary    TEXT,
    query_platform   TEXT,
    query_raw        TEXT,
    false_positive_rate TEXT DEFAULT 'medium',
    severity         TEXT DEFAULT 'medium',
    author           TEXT,
    version          TEXT DEFAULT '1.0.0',
    tags             TEXT[] DEFAULT '{}',
    active           BOOLEAN DEFAULT TRUE,
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    updated_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rule_dependencies (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_id         TEXT NOT NULL REFERENCES rule_inventory(rule_id) ON DELETE CASCADE,
    source_id       UUID NOT NULL REFERENCES log_sources(id),
    dependency_type source_dependency NOT NULL,
    field_requirements TEXT[],
    notes           TEXT,
    UNIQUE(rule_id, source_id)
);

CREATE TABLE IF NOT EXISTS rule_deployments (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id    UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    rule_id      TEXT NOT NULL REFERENCES rule_inventory(rule_id),
    status       deployment_status NOT NULL DEFAULT 'pending',
    health       rule_health NOT NULL DEFAULT 'untested',
    deployed_at  TIMESTAMPTZ,
    last_fired   TIMESTAMPTZ,
    alert_count_7d INTEGER DEFAULT 0,
    tuning_notes TEXT,
    UNIQUE(client_id, rule_id)
);

CREATE TABLE IF NOT EXISTS coverage_matrix (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id        UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    technique_id     TEXT NOT NULL REFERENCES mitre_techniques(technique_id),
    rule_id          TEXT NOT NULL REFERENCES rule_inventory(rule_id),
    source_id        UUID REFERENCES log_sources(id),
    coverage_state   coverage_state NOT NULL,
    source_present   BOOLEAN DEFAULT FALSE,
    rule_deployed    BOOLEAN DEFAULT FALSE,
    rule_healthy     BOOLEAN DEFAULT FALSE,
    hard_deps_met    BOOLEAN DEFAULT FALSE,
    soft_deps_met    BOOLEAN DEFAULT FALSE,
    coverage_illusion BOOLEAN DEFAULT FALSE,
    illusion_reason  TEXT,
    computed_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(client_id, technique_id, rule_id, source_id)
);

CREATE TABLE IF NOT EXISTS gaps (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id        UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    technique_id     TEXT NOT NULL REFERENCES mitre_techniques(technique_id),
    gap_type         gap_type NOT NULL,
    severity         TEXT NOT NULL DEFAULT 'medium',
    title            TEXT NOT NULL,
    description      TEXT,
    affected_rules   TEXT[] DEFAULT '{}',
    missing_sources  TEXT[] DEFAULT '{}',
    priority_score   NUMERIC(5,2) DEFAULT 0,
    -- Claude reasoning
    attacker_path       TEXT,
    detection_failure   TEXT,
    estimated_dwell_time TEXT,
    business_impact     TEXT,
    -- Status
    resolved         BOOLEAN DEFAULT FALSE,
    resolved_at      TIMESTAMPTZ,
    resolution_notes TEXT,
    first_detected   TIMESTAMPTZ DEFAULT NOW(),
    last_updated     TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(client_id, technique_id, gap_type)
);

CREATE TABLE IF NOT EXISTS recommendations (
    id                     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id              UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    recommendation_type    recommendation_type NOT NULL,
    title                  TEXT NOT NULL,
    description            TEXT,
    source_id              UUID REFERENCES log_sources(id),
    rule_ids               TEXT[] DEFAULT '{}',
    technique_ids          TEXT[] DEFAULT '{}',
    techniques_unlocked    INTEGER DEFAULT 0,
    rules_activated        INTEGER DEFAULT 0,
    detection_improvement  NUMERIC(5,2) DEFAULT 0,
    estimated_cost_monthly NUMERIC(10,2),
    estimated_cost_annually NUMERIC(10,2),
    roi_score              NUMERIC(5,2),
    priority_rank          INTEGER,
    status                 TEXT DEFAULT 'pending',
    created_at             TIMESTAMPTZ DEFAULT NOW(),
    updated_at             TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS decisions (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id    UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    entity_type  TEXT NOT NULL,
    entity_id    UUID NOT NULL,
    title        TEXT NOT NULL,
    description  TEXT,
    context_json JSONB DEFAULT '{}'::jsonb,
    action       decision_action,
    decided_by   TEXT,
    decided_at   TIMESTAMPTZ,
    rationale    TEXT,
    priority     INTEGER DEFAULT 50,
    due_by       TIMESTAMPTZ,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_log (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id   UUID REFERENCES clients(id),
    actor       TEXT NOT NULL,
    action      TEXT NOT NULL,
    entity_type TEXT,
    entity_id   UUID,
    before_json JSONB,
    after_json  JSONB,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS analysis_runs (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id    UUID REFERENCES clients(id),
    run_type     TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'pending',
    triggered_by TEXT DEFAULT 'scheduler',
    started_at   TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    stats_json   JSONB DEFAULT '{}'::jsonb,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_assets_client        ON assets(client_id);
CREATE INDEX IF NOT EXISTS idx_ts_client            ON technique_scores(client_id);
CREATE INDEX IF NOT EXISTS idx_ts_priority          ON technique_scores(priority_score DESC);
CREATE INDEX IF NOT EXISTS idx_cls_client           ON client_log_sources(client_id);
CREATE INDEX IF NOT EXISTS idx_rule_technique       ON rule_inventory(technique_id);
CREATE INDEX IF NOT EXISTS idx_rule_dep_rule        ON rule_dependencies(rule_id);
CREATE INDEX IF NOT EXISTS idx_rule_dep_source      ON rule_dependencies(source_id);
CREATE INDEX IF NOT EXISTS idx_rd_client            ON rule_deployments(client_id);
CREATE INDEX IF NOT EXISTS idx_cm_client            ON coverage_matrix(client_id);
CREATE INDEX IF NOT EXISTS idx_cm_technique         ON coverage_matrix(technique_id);
CREATE INDEX IF NOT EXISTS idx_cm_state             ON coverage_matrix(coverage_state);
CREATE INDEX IF NOT EXISTS idx_gaps_client          ON gaps(client_id);
CREATE INDEX IF NOT EXISTS idx_gaps_severity        ON gaps(severity);
CREATE INDEX IF NOT EXISTS idx_gaps_resolved        ON gaps(resolved);
CREATE INDEX IF NOT EXISTS idx_rec_client           ON recommendations(client_id);
CREATE INDEX IF NOT EXISTS idx_decisions_client     ON decisions(client_id);
CREATE INDEX IF NOT EXISTS idx_audit_created        ON audit_log(created_at DESC);

-- ============================================================
-- VIEWS
-- ============================================================
CREATE OR REPLACE VIEW v_coverage_summary AS
SELECT
    c.id AS client_id, c.name AS client_name, mt.tactic,
    COUNT(DISTINCT mt.technique_id) AS total_techniques,
    COUNT(DISTINCT CASE WHEN cm.coverage_state = 'BUILT'   THEN cm.technique_id END) AS fully_covered,
    COUNT(DISTINCT CASE WHEN cm.coverage_state = 'PARTIAL' THEN cm.technique_id END) AS partially_covered,
    COUNT(DISTINCT CASE WHEN cm.coverage_state = 'BROKEN'  THEN cm.technique_id END) AS broken_coverage,
    COUNT(DISTINCT CASE WHEN cm.coverage_state = 'GAP'     THEN cm.technique_id END) AS no_coverage,
    COUNT(DISTINCT CASE WHEN cm.coverage_illusion           THEN cm.technique_id END) AS illusion_count
FROM clients c
CROSS JOIN mitre_techniques mt
LEFT JOIN coverage_matrix cm
    ON cm.client_id = c.id AND cm.technique_id = mt.technique_id
GROUP BY c.id, c.name, mt.tactic;

-- ============================================================
-- TRIGGERS — updated_at
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_clients_updated        ON clients;
DROP TRIGGER IF EXISTS tr_rule_inventory_updated ON rule_inventory;
DROP TRIGGER IF EXISTS tr_recommendations_updated ON recommendations;
DROP TRIGGER IF EXISTS tr_gaps_updated           ON gaps;

CREATE TRIGGER tr_clients_updated        BEFORE UPDATE ON clients        FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER tr_rule_inventory_updated BEFORE UPDATE ON rule_inventory  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER tr_recommendations_updated BEFORE UPDATE ON recommendations FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER tr_gaps_updated           BEFORE UPDATE ON gaps            FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- DONE
-- ============================================================
SELECT 'UMBRA schema installed successfully ✓' AS status;
