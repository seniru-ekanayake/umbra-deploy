"""UMBRA — coverage.py"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db

router = APIRouter()


@router.get("")
async def get_coverage(
    client_id: str = Query(...),
    tactic: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    GET /coverage?client_id=...
    Returns technique-level coverage summary per tactic.
    """
    tactic_filter = "AND mt.tactic = :tactic" if tactic else ""
    params = {"client_id": client_id}
    if tactic:
        params["tactic"] = tactic

    result = await db.execute(
        text(f"""
            SELECT
                mt.technique_id,
                mt.name,
                mt.tactic,
                mt.parent_id,
                mt.platforms,
                ts.priority_score,
                COALESCE(cm_agg.best_state, 'GAP') AS coverage_state,
                COALESCE(cm_agg.has_illusion, FALSE) AS coverage_illusion,
                cm_agg.illusion_reason,
                cm_agg.rule_count
            FROM mitre_techniques mt
            LEFT JOIN technique_scores ts
                ON ts.technique_id = mt.technique_id AND ts.client_id = :client_id
            LEFT JOIN (
                SELECT
                    technique_id,
                    CASE
                        WHEN bool_or(coverage_state = 'BUILT') THEN 'BUILT'
                        WHEN bool_or(coverage_state = 'PARTIAL') THEN 'PARTIAL'
                        WHEN bool_or(coverage_state = 'BROKEN') THEN 'BROKEN'
                        ELSE 'GAP'
                    END AS best_state,
                    bool_or(coverage_illusion) AS has_illusion,
                    string_agg(DISTINCT illusion_reason, '; ') FILTER (WHERE illusion_reason IS NOT NULL) AS illusion_reason,
                    COUNT(DISTINCT rule_id) AS rule_count
                FROM coverage_matrix
                WHERE client_id = :client_id
                GROUP BY technique_id
            ) cm_agg ON cm_agg.technique_id = mt.technique_id
            {tactic_filter}
            ORDER BY mt.tactic, mt.technique_id
        """),
        params,
    )
    return [dict(r._mapping) for r in result.fetchall()]


@router.get("/summary")
async def get_coverage_summary(
    client_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Coverage summary metrics per tactic.
    """
    result = await db.execute(
        text("""
            SELECT
                mt.tactic,
                COUNT(DISTINCT mt.technique_id) AS total,
                COUNT(DISTINCT CASE WHEN COALESCE(cm.best_state,'GAP')='BUILT' THEN mt.technique_id END) AS built,
                COUNT(DISTINCT CASE WHEN COALESCE(cm.best_state,'GAP')='PARTIAL' THEN mt.technique_id END) AS partial,
                COUNT(DISTINCT CASE WHEN COALESCE(cm.best_state,'GAP')='BROKEN' THEN mt.technique_id END) AS broken,
                COUNT(DISTINCT CASE WHEN COALESCE(cm.best_state,'GAP')='GAP' THEN mt.technique_id END) AS gap,
                COUNT(DISTINCT CASE WHEN cm.has_illusion THEN mt.technique_id END) AS illusion_count
            FROM mitre_techniques mt
            LEFT JOIN (
                SELECT technique_id,
                    CASE
                        WHEN bool_or(coverage_state='BUILT') THEN 'BUILT'
                        WHEN bool_or(coverage_state='PARTIAL') THEN 'PARTIAL'
                        WHEN bool_or(coverage_state='BROKEN') THEN 'BROKEN'
                        ELSE 'GAP'
                    END AS best_state,
                    bool_or(coverage_illusion) AS has_illusion
                FROM coverage_matrix
                WHERE client_id = :client_id
                GROUP BY technique_id
            ) cm ON cm.technique_id = mt.technique_id
            GROUP BY mt.tactic
            ORDER BY mt.tactic
        """),
        {"client_id": client_id},
    )
    rows = [dict(r._mapping) for r in result.fetchall()]

    # Overall metrics
    totals = {
        "total": sum(r["total"] for r in rows),
        "built": sum(r["built"] for r in rows),
        "partial": sum(r["partial"] for r in rows),
        "broken": sum(r["broken"] for r in rows),
        "gap": sum(r["gap"] for r in rows),
        "illusion_count": sum(r["illusion_count"] for r in rows),
    }
    total = totals["total"] or 1
    totals["real_coverage_pct"] = round(
        (totals["built"] + totals["partial"] * 0.5) / total * 100, 1
    )
    totals["apparent_coverage_pct"] = round(
        (totals["built"] + totals["partial"] * 0.5 + totals["broken"] * 0.5) / total * 100, 1
    )
    totals["illusion_gap_pct"] = round(
        totals["apparent_coverage_pct"] - totals["real_coverage_pct"], 1
    )

    return {"by_tactic": rows, "totals": totals}


@router.get("/matrix")
async def get_coverage_matrix(
    client_id: str = Query(...),
    technique_id: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Detailed rule × source × state matrix for a technique.
    """
    filters = "WHERE cm.client_id = :client_id"
    params = {"client_id": client_id}
    if technique_id:
        filters += " AND cm.technique_id = :technique_id"
        params["technique_id"] = technique_id

    result = await db.execute(
        text(f"""
            SELECT
                cm.technique_id,
                cm.rule_id,
                ri.name AS rule_name,
                ri.rule_type,
                ls.source_key,
                ls.name AS source_name,
                cm.coverage_state,
                cm.source_present,
                cm.rule_deployed,
                cm.rule_healthy,
                cm.hard_deps_met,
                cm.soft_deps_met,
                cm.coverage_illusion,
                cm.illusion_reason,
                rd_dep.dependency_type,
                cm.computed_at
            FROM coverage_matrix cm
            JOIN rule_inventory ri ON ri.rule_id = cm.rule_id
            LEFT JOIN log_sources ls ON ls.id = cm.source_id
            LEFT JOIN rule_dependencies rd_dep
                ON rd_dep.rule_id = cm.rule_id AND rd_dep.source_id = cm.source_id
            {filters}
            ORDER BY cm.technique_id, cm.rule_id, ls.source_key
        """),
        params,
    )
    return [dict(r._mapping) for r in result.fetchall()]
