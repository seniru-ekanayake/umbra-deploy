"""
UMBRA Analysis Pipeline — Free-tier optimised
- Demo mode: 1 client per run, max 5 reasoning calls
- Upsert everywhere (idempotent — safe to re-run)
- Logging on all major steps
"""
import logging
from typing import Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.coverage_engine import (
    CoverageEngine, CoverageResult, CoverageState,
    RuleDependency, RuleState, SourcePresence, TechniqueCoverageRollup,
)
from app.services.reasoning import generate_gap_reasoning

logger = logging.getLogger("umbra.analysis")
engine = CoverageEngine()


async def run_client_analysis(db: AsyncSession, client_id: str) -> Dict:
    logger.info(f"[Analysis] Starting for client {client_id}")

    client = await _load_client(db, client_id)
    if not client:
        raise ValueError(f"Client {client_id} not found")

    client_sources = await _load_client_sources(db, client_id)
    rules          = await _load_rules_with_deps(db)
    technique_scores = await _load_technique_scores(db, client_id)
    all_sources    = await _load_all_sources(db)
    deployments    = await _load_deployments(db, client_id)
    techniques     = await _load_techniques(db)

    logger.info(f"[Analysis] Loaded {len(rules)} rules, {len(client_sources)} sources, {len(techniques)} techniques")

    # ── Run coverage engine ─────────────────────────────
    all_results: List[CoverageResult] = []
    rollups_by_technique: Dict[str, List[CoverageResult]] = {}

    for rule_id, rule_data in rules.items():
        dep = deployments.get(rule_id, {})
        rule_state = RuleState(
            rule_id=rule_id,
            technique_id=rule_data["technique_id"],
            rule_type=rule_data["rule_type"],
            deployed=dep.get("status") in ("deployed", "broken"),
            deployment_status=dep.get("status", "pending"),
            rule_health=dep.get("health", "untested"),
            dependencies=rule_data["dependencies"],
        )
        results = engine.evaluate_rule(client_id, rule_state, client_sources)
        all_results.extend(results)
        rollups_by_technique.setdefault(rule_data["technique_id"], []).extend(results)

    rollups: List[TechniqueCoverageRollup] = []
    for tid, results in rollups_by_technique.items():
        rollups.append(engine.rollup_technique(tid, results))

    # Techniques with no rules → pure GAP
    for tid in techniques:
        if tid not in rollups_by_technique:
            rollups.append(engine.rollup_technique(tid, []))

    coverage_metrics = engine.compute_coverage_score(rollups)
    gaps             = engine.prioritise_gaps(rollups, technique_scores)
    recommendations  = engine.recommend_log_sources(gaps, all_sources, client_sources, technique_scores)

    logger.info(f"[Analysis] {len(gaps)} gaps, {len(recommendations)} recs, "
                f"real={coverage_metrics['real_coverage_score']}%, "
                f"illusions={coverage_metrics['illusion_count']}")

    # ── Persist ─────────────────────────────────────────
    await _persist_coverage_matrix(db, client_id, all_results)
    await _persist_gaps(db, client_id, gaps, techniques)
    await _persist_recommendations(db, client_id, recommendations, all_sources)

    # ── Claude reasoning (capped by DEMO_MODE limit) ────
    reasoning_cap = settings.MAX_REASONING_GAPS if settings.DEMO_MODE else 20
    top_gaps = [g for g in gaps if g.get("coverage_state") in ("BROKEN", "GAP")][:reasoning_cap]

    for gap in top_gaps:
        tid   = gap["technique_id"]
        tech  = techniques.get(tid, {})
        rule_list = [
            {"rule_id": rid, "name": rules.get(rid, {}).get("rule_type", ""),
             "rule_type": rules.get(rid, {}).get("rule_type", ""),
             "deployment_status": deployments.get(rid, {}).get("status", "unknown"),
             "rule_health": deployments.get(rid, {}).get("health", "unknown")}
            for rid in _rules_for_technique(rules, tid)
        ]
        reasoning = await generate_gap_reasoning(
            gap_data=gap,
            client_data={
                "name": client["name"],
                "industry": client["industry"],
                "tier": client["tier"],
                "geography": client["geography"],
                "active_source_keys": list(client_sources.keys()),
            },
            technique_data=tech,
            rule_data=rule_list,
            source_data=all_sources,
        )
        if reasoning:
            await _persist_gap_reasoning(db, client_id, tid, reasoning)

    await db.commit()
    logger.info(f"[Analysis] Complete for {client['name']}")

    return {
        "client_id": client_id,
        "client_name": client["name"],
        "coverage_metrics": coverage_metrics,
        "gaps_count": len(gaps),
        "recommendations_count": len(recommendations),
        "top_gaps": gaps[:10],
        "top_recommendations": recommendations[:5],
    }


# ── Loaders ────────────────────────────────────────────────

async def _load_client(db, client_id):
    r = await db.execute(
        text("SELECT id, name, industry, geography, tier FROM clients WHERE id = :id"),
        {"id": client_id},
    )
    row = r.fetchone()
    return dict(row._mapping) if row else None


async def _load_client_sources(db, client_id) -> Dict[str, SourcePresence]:
    r = await db.execute(text("""
        SELECT ls.source_key, ls.id::text AS source_id, cls.active, cls.health
        FROM client_log_sources cls
        JOIN log_sources ls ON ls.id = cls.source_id
        WHERE cls.client_id = :cid
    """), {"cid": client_id})
    return {
        row["source_key"]: SourcePresence(row["source_key"], row["source_id"],
                                           row["active"], row["health"] or "unknown")
        for row in (dict(r._mapping) for r in r.fetchall())
    }


async def _load_rules_with_deps(db) -> Dict[str, Dict]:
    r = await db.execute(text("""
        SELECT ri.rule_id, ri.technique_id, ri.rule_type,
               rd.source_id::text, rd.dependency_type, ls.source_key
        FROM rule_inventory ri
        LEFT JOIN rule_dependencies rd ON rd.rule_id = ri.rule_id
        LEFT JOIN log_sources ls ON ls.id = rd.source_id
        WHERE ri.active = TRUE
    """))
    rules: Dict[str, Dict] = {}
    for row in (dict(r._mapping) for r in r.fetchall()):
        rid = row["rule_id"]
        if rid not in rules:
            rules[rid] = {"rule_id": rid, "technique_id": row["technique_id"],
                          "rule_type": row["rule_type"], "dependencies": []}
        if row["source_id"]:
            rules[rid]["dependencies"].append(
                RuleDependency(row["source_id"], row["source_key"], row["dependency_type"])
            )
    return rules


async def _load_technique_scores(db, client_id) -> Dict[str, float]:
    r = await db.execute(text("""
        SELECT technique_id, priority_score FROM technique_scores WHERE client_id = :cid
    """), {"cid": client_id})
    return {row["technique_id"]: float(row["priority_score"])
            for row in (dict(r._mapping) for r in r.fetchall())}


async def _load_all_sources(db) -> Dict[str, Dict]:
    r = await db.execute(text("""
        SELECT source_key, id::text, name, category,
               cost_per_gb, avg_daily_gb, setup_complexity
        FROM log_sources
    """))
    return {row["source_key"]: row
            for row in (dict(r._mapping) for r in r.fetchall())}


async def _load_deployments(db, client_id) -> Dict[str, Dict]:
    r = await db.execute(text("""
        SELECT rule_id, status, health FROM rule_deployments WHERE client_id = :cid
    """), {"cid": client_id})
    return {row["rule_id"]: row
            for row in (dict(r._mapping) for r in r.fetchall())}


async def _load_techniques(db) -> Dict[str, Dict]:
    r = await db.execute(text("""
        SELECT technique_id, name, tactic, parent_id, description FROM mitre_techniques
    """))
    return {row["technique_id"]: row
            for row in (dict(r._mapping) for r in r.fetchall())}


# ── Persistence ────────────────────────────────────────────

async def _persist_coverage_matrix(db, client_id, results: List[CoverageResult]):
    for r in results:
        await db.execute(text("""
            INSERT INTO coverage_matrix
              (client_id,technique_id,rule_id,source_id,coverage_state,
               source_present,rule_deployed,rule_healthy,
               hard_deps_met,soft_deps_met,coverage_illusion,illusion_reason,computed_at)
            VALUES
              (:cid,:tid,:gt,:sev,:title,:desc,
               CAST(:ar AS text[]),CAST(:ms AS text[]),:ps,NOW(),NOW())
            ON CONFLICT (client_id,technique_id,rule_id,source_id)
            DO UPDATE SET
              coverage_state=EXCLUDED.coverage_state,
              source_present=EXCLUDED.source_present,
              rule_deployed=EXCLUDED.rule_deployed,
              rule_healthy=EXCLUDED.rule_healthy,
              hard_deps_met=EXCLUDED.hard_deps_met,
              soft_deps_met=EXCLUDED.soft_deps_met,
              coverage_illusion=EXCLUDED.coverage_illusion,
              illusion_reason=EXCLUDED.illusion_reason,
              computed_at=NOW()
        """), {
            "cid": client_id, "tid": r.technique_id,
            "rid": r.rule_id, "sid": r.source_id,
            "state": r.coverage_state.value, "sp": r.source_present,
            "rd": r.rule_deployed, "rh": r.rule_healthy,
            "hd": r.hard_deps_met, "sd": r.soft_deps_met,
            "ci": r.coverage_illusion, "ir": r.illusion_reason,
        })


async def _persist_gaps(db, client_id, gaps, techniques):
    for g in gaps:
        tid  = g["technique_id"]
        tech = techniques.get(tid, {})
        title = f"{tid} — {tech.get('name', tid)}: {g['gap_type'].replace('_',' ').title()}"
        await db.execute(text("""
            INSERT INTO gaps
              (client_id,technique_id,gap_type,severity,title,description,
               affected_rules,missing_sources,priority_score,first_detected,last_updated)
            VALUES
              (:cid,:tid,:gt,:sev,:title,:desc,
               :ar,:ms,:ps,NOW(),NOW())
            ON CONFLICT (client_id,technique_id,gap_type)
            DO UPDATE SET
              severity=EXCLUDED.severity, title=EXCLUDED.title,
              description=EXCLUDED.description,
              affected_rules=EXCLUDED.affected_rules,
              missing_sources=EXCLUDED.missing_sources,
              priority_score=EXCLUDED.priority_score,
              last_updated=NOW()
        """), {
            "cid": client_id, "tid": tid, "gt": g["gap_type"],
            "sev": g["severity"], "title": title,
            "desc": g.get("gap_description", ""),
            "ar": g.get("illusion_rules") or [],
            "ms": g.get("missing_sources") or [],
            "ps": g["priority_score"],
        })


async def _persist_recommendations(db, client_id, recs, all_sources):
    for rec in recs:
        src = await db.execute(
            text("SELECT id FROM log_sources WHERE source_key = :sk"),
            {"sk": rec["source_key"]}
        )
        src_row = src.fetchone()
        src_id  = str(src_row[0]) if src_row else None
        await db.execute(text("""
            INSERT INTO recommendations
              (client_id,recommendation_type,title,description,source_id,
               technique_ids,techniques_unlocked,rules_activated,
               detection_improvement,estimated_cost_monthly,estimated_cost_annually,
               roi_score,priority_rank)
            VALUES
              (:cid,'ingest_source',:title,:desc,:sid,
               CAST(:tids AS text[]),:tu,:ra,:di,:cm,:ca,:roi,:rank)
            ON CONFLICT DO NOTHING
        """), {
            "cid": client_id,
            "title": f"Ingest: {rec['source_name']}",
            "desc": f"Unlocks {rec['techniques_unlocked']} techniques. ROI: {rec['roi_score']}",
            "sid": src_id, "tids": rec.get("technique_ids") or [],
            "tu": rec["techniques_unlocked"], "ra": rec["gaps_resolved"],
            "di": rec["detection_improvement"],
            "cm": rec["estimated_monthly_cost"], "ca": rec["estimated_annual_cost"],
            "roi": rec["roi_score"], "rank": rec["priority_rank"],
        })


async def _persist_gap_reasoning(db, client_id, technique_id, reasoning):
    await db.execute(text("""
        UPDATE gaps SET
          attacker_path=:ap, detection_failure=:df,
          estimated_dwell_time=:dw, business_impact=:bi,
          last_updated=NOW()
        WHERE client_id=:cid AND technique_id=:tid AND resolved=FALSE
    """), {
        "cid": client_id, "tid": technique_id,
        "ap": reasoning.get("attacker_path"),
        "df": reasoning.get("detection_failure"),
        "dw": reasoning.get("estimated_dwell_time"),
        "bi": reasoning.get("business_impact"),
    })


def _rules_for_technique(rules: Dict, technique_id: str) -> List[str]:
    return [rid for rid, r in rules.items() if r["technique_id"] == technique_id]
