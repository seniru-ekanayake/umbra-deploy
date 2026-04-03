"""
UMBRA Coverage Engine
=====================
Computes the real coverage state for each technique × rule × source
combination per client.

Coverage States:
  BUILT   — rule deployed, healthy, all HARD deps present
  PARTIAL — rule deployed, HARD deps present, SOFT deps missing
  BROKEN  — rule deployed but HARD deps missing (COVERAGE ILLUSION!)
  GAP     — no rule deployed at all

Coverage Illusion:
  A rule shows as "deployed" in the deployment registry but
  one or more HARD source dependencies are missing or offline.
  The technique appears covered — it is NOT.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger("umbra.coverage_engine")


class CoverageState(str, Enum):
    BUILT = "BUILT"
    PARTIAL = "PARTIAL"
    BROKEN = "BROKEN"
    GAP = "GAP"


@dataclass
class SourcePresence:
    source_key: str
    source_id: str
    active: bool
    health: str  # healthy, degraded, offline, unknown


@dataclass
class RuleDependency:
    source_id: str
    source_key: str
    dependency_type: str  # HARD or SOFT


@dataclass
class RuleState:
    rule_id: str
    technique_id: str
    rule_type: str
    deployed: bool
    deployment_status: str
    rule_health: str
    dependencies: List[RuleDependency] = field(default_factory=list)


@dataclass
class CoverageResult:
    client_id: str
    technique_id: str
    rule_id: str
    source_id: Optional[str]
    coverage_state: CoverageState
    source_present: bool
    rule_deployed: bool
    rule_healthy: bool
    hard_deps_met: bool
    soft_deps_met: bool
    coverage_illusion: bool
    illusion_reason: Optional[str]
    missing_hard_sources: List[str] = field(default_factory=list)
    missing_soft_sources: List[str] = field(default_factory=list)


@dataclass
class TechniqueCoverageRollup:
    technique_id: str
    overall_state: CoverageState
    rule_states: List[CoverageResult]
    coverage_illusion: bool
    illusion_rules: List[str]
    missing_sources: List[str]
    gap_type: Optional[str]  # detection_gap, visibility_gap, broken_rule, partial_coverage
    gap_description: str


class CoverageEngine:
    """
    Stateless engine — call evaluate() with client data.
    """

    def evaluate_rule(
        self,
        client_id: str,
        rule: RuleState,
        client_sources: Dict[str, SourcePresence],
    ) -> List[CoverageResult]:
        """
        Evaluate a single rule's coverage for a client.
        Returns one CoverageResult per source dependency (for granular matrix storage).
        """
        results = []

        if not rule.deployed or rule.deployment_status in ("disabled", "pending"):
            # No deployment = GAP for every dependency
            for dep in rule.dependencies:
                results.append(CoverageResult(
                    client_id=client_id,
                    technique_id=rule.technique_id,
                    rule_id=rule.rule_id,
                    source_id=dep.source_id,
                    coverage_state=CoverageState.GAP,
                    source_present=dep.source_key in client_sources and client_sources[dep.source_key].active,
                    rule_deployed=False,
                    rule_healthy=False,
                    hard_deps_met=False,
                    soft_deps_met=False,
                    coverage_illusion=False,
                    illusion_reason=None,
                ))
            if not rule.dependencies:
                results.append(CoverageResult(
                    client_id=client_id,
                    technique_id=rule.technique_id,
                    rule_id=rule.rule_id,
                    source_id=None,
                    coverage_state=CoverageState.GAP,
                    source_present=False,
                    rule_deployed=False,
                    rule_healthy=False,
                    hard_deps_met=False,
                    soft_deps_met=False,
                    coverage_illusion=False,
                    illusion_reason=None,
                ))
            return results

        # Rule IS deployed — evaluate dependency resolution
        hard_deps = [d for d in rule.dependencies if d.dependency_type == "HARD"]
        soft_deps = [d for d in rule.dependencies if d.dependency_type == "SOFT"]

        hard_met = []
        hard_failed = []
        soft_met = []
        soft_failed = []

        for dep in hard_deps:
            presence = client_sources.get(dep.source_key)
            if presence and presence.active and presence.health not in ("offline",):
                hard_met.append(dep)
            else:
                hard_failed.append(dep)

        for dep in soft_deps:
            presence = client_sources.get(dep.source_key)
            if presence and presence.active and presence.health not in ("offline",):
                soft_met.append(dep)
            else:
                soft_failed.append(dep)

        all_hard_met = len(hard_failed) == 0
        all_soft_met = len(soft_failed) == 0
        rule_healthy = rule.rule_health in ("healthy",)

        # -------------------------------------------------------
        # Determine coverage state
        # -------------------------------------------------------
        if not all_hard_met:
            # COVERAGE ILLUSION — rule is deployed but cannot fire
            state = CoverageState.BROKEN
            illusion = True
            illusion_reasons = []
            for dep in hard_failed:
                presence = client_sources.get(dep.source_key)
                if presence and not presence.active:
                    illusion_reasons.append(
                        f"Required source '{dep.source_key}' is inactive/offline"
                    )
                else:
                    illusion_reasons.append(
                        f"Required source '{dep.source_key}' is not ingested"
                    )
            illusion_reason = "; ".join(illusion_reasons)
        elif all_hard_met and not all_soft_met:
            state = CoverageState.PARTIAL
            illusion = False
            illusion_reason = None
        elif all_hard_met and all_soft_met and rule_healthy:
            state = CoverageState.BUILT
            illusion = False
            illusion_reason = None
        elif all_hard_met and all_soft_met and not rule_healthy:
            # All sources present but rule itself is degraded
            state = CoverageState.PARTIAL
            illusion = True
            illusion_reason = f"All sources present but rule health is '{rule.rule_health}'"
        else:
            state = CoverageState.GAP
            illusion = False
            illusion_reason = None

        # Emit one result per dependency for matrix granularity
        for dep in rule.dependencies:
            presence = client_sources.get(dep.source_key)
            results.append(CoverageResult(
                client_id=client_id,
                technique_id=rule.technique_id,
                rule_id=rule.rule_id,
                source_id=dep.source_id,
                coverage_state=state,
                source_present=bool(presence and presence.active),
                rule_deployed=True,
                rule_healthy=rule_healthy,
                hard_deps_met=all_hard_met,
                soft_deps_met=all_soft_met,
                coverage_illusion=illusion,
                illusion_reason=illusion_reason,
                missing_hard_sources=[d.source_key for d in hard_failed],
                missing_soft_sources=[d.source_key for d in soft_failed],
            ))

        return results

    def rollup_technique(
        self,
        technique_id: str,
        rule_results: List[CoverageResult],
    ) -> TechniqueCoverageRollup:
        """
        Roll up multiple rule results into a single technique-level verdict.
        
        Logic:
          - If ANY rule is BUILT → technique is covered (BUILT)
          - If no BUILT but PARTIAL exists → PARTIAL
          - If all BROKEN → BROKEN (maximum coverage illusion)
          - If no rules at all → GAP
        """
        if not rule_results:
            return TechniqueCoverageRollup(
                technique_id=technique_id,
                overall_state=CoverageState.GAP,
                rule_states=[],
                coverage_illusion=False,
                illusion_rules=[],
                missing_sources=[],
                gap_type="detection_gap",
                gap_description="No rules exist for this technique.",
            )

        states = {r.coverage_state for r in rule_results}
        illusion_rules = [r.rule_id for r in rule_results if r.coverage_illusion]
        all_missing = list(set(
            s for r in rule_results for s in r.missing_hard_sources
        ))

        if CoverageState.BUILT in states:
            overall = CoverageState.BUILT
            gap_type = None
            desc = "Technique has at least one fully operational detection rule."
        elif CoverageState.PARTIAL in states:
            overall = CoverageState.PARTIAL
            gap_type = "partial_coverage"
            desc = "Rules exist but enrichment/soft dependencies are missing."
        elif all(s == CoverageState.BROKEN for s in states):
            overall = CoverageState.BROKEN
            gap_type = "broken_rule"
            desc = (
                "ALL rules for this technique are broken due to missing required "
                "log sources. Technique appears covered but CANNOT be detected."
            )
        elif CoverageState.BROKEN in states:
            overall = CoverageState.BROKEN
            gap_type = "broken_rule"
            desc = "Some rules are broken; effective coverage is degraded."
        else:
            overall = CoverageState.GAP
            gap_type = "detection_gap"
            desc = "No operational detection rules for this technique."

        # Distinguish detection gap vs visibility gap
        if overall == CoverageState.GAP:
            if all_missing:
                gap_type = "visibility_gap"
                desc = "No rules and no required log sources present."

        return TechniqueCoverageRollup(
            technique_id=technique_id,
            overall_state=overall,
            rule_states=rule_results,
            coverage_illusion=len(illusion_rules) > 0,
            illusion_rules=illusion_rules,
            missing_sources=all_missing,
            gap_type=gap_type,
            gap_description=desc,
        )

    def compute_coverage_score(self, rollups: List[TechniqueCoverageRollup]) -> Dict:
        """
        Compute aggregate coverage metrics for a client.
        """
        total = len(rollups)
        if total == 0:
            return {"coverage_score": 0, "breakdown": {}}

        counts = {
            "BUILT": 0, "PARTIAL": 0, "BROKEN": 0, "GAP": 0,
        }
        illusion_count = 0

        for r in rollups:
            counts[r.overall_state.value] += 1
            if r.coverage_illusion:
                illusion_count += 1

        # Score: BUILT=1.0, PARTIAL=0.5, BROKEN=0.0 (it LOOKS covered), GAP=0.0
        # Illusion penalty: broken rules LOOK covered but score 0
        real_coverage = (
            counts["BUILT"] * 1.0 +
            counts["PARTIAL"] * 0.5
        ) / total * 100

        apparent_coverage = (
            counts["BUILT"] * 1.0 +
            counts["PARTIAL"] * 0.5 +
            counts["BROKEN"] * 0.5  # broken rules appear partially covered
        ) / total * 100

        return {
            "total_techniques": total,
            "real_coverage_score": round(real_coverage, 1),
            "apparent_coverage_score": round(apparent_coverage, 1),
            "illusion_gap": round(apparent_coverage - real_coverage, 1),
            "illusion_count": illusion_count,
            "breakdown": {k: {"count": v, "pct": round(v / total * 100, 1)} for k, v in counts.items()},
        }

    def prioritise_gaps(
        self,
        rollups: List[TechniqueCoverageRollup],
        technique_scores: Dict[str, float],
    ) -> List[Dict]:
        """
        Rank gaps by: severity * technique priority score.
        """
        gap_severity = {
            "BROKEN": 3,
            "GAP": 2,
            "PARTIAL": 1,
        }

        gaps = []
        for r in rollups:
            if r.overall_state == CoverageState.BUILT:
                continue
            severity_weight = gap_severity.get(r.overall_state.value, 1)
            priority = technique_scores.get(r.technique_id, 50) * severity_weight
            gaps.append({
                "technique_id": r.technique_id,
                "coverage_state": r.overall_state.value,
                "gap_type": r.gap_type,
                "gap_description": r.gap_description,
                "coverage_illusion": r.coverage_illusion,
                "illusion_rules": r.illusion_rules,
                "missing_sources": r.missing_sources,
                "priority_score": round(min(priority, 100), 2),
                "severity": self._score_to_severity(priority),
            })

        gaps.sort(key=lambda g: g["priority_score"], reverse=True)
        return gaps

    def _score_to_severity(self, score: float) -> str:
        if score >= 240:
            return "critical"
        elif score >= 160:
            return "high"
        elif score >= 80:
            return "medium"
        return "low"

    def recommend_log_sources(
        self,
        gaps: List[Dict],
        available_sources: Dict,  # source_key → source metadata
        client_sources: Dict[str, SourcePresence],
        technique_scores: Dict[str, float],
    ) -> List[Dict]:
        """
        Rank missing log sources by:
        - How many gaps they resolve
        - Total priority weight of affected techniques
        - Estimated cost
        """
        source_impact: Dict[str, Dict] = {}

        for gap in gaps:
            for source_key in gap["missing_sources"]:
                if source_key in client_sources:
                    continue  # already ingested
                if source_key not in source_impact:
                    src_meta = available_sources.get(source_key, {})
                    source_impact[source_key] = {
                        "source_key": source_key,
                        "source_name": src_meta.get("name", source_key),
                        "techniques_unlocked": set(),
                        "total_priority": 0,
                        "gaps_resolved": 0,
                        "cost_per_gb": src_meta.get("cost_per_gb", 0.5),
                        "avg_daily_gb": src_meta.get("avg_daily_gb", 10),
                        "setup_complexity": src_meta.get("setup_complexity", "medium"),
                    }
                source_impact[source_key]["techniques_unlocked"].add(gap["technique_id"])
                source_impact[source_key]["total_priority"] += gap["priority_score"]
                source_impact[source_key]["gaps_resolved"] += 1

        recommendations = []
        for sk, impact in source_impact.items():
            monthly_cost = impact["cost_per_gb"] * impact["avg_daily_gb"] * 30
            roi = (float(impact.get("total_priority", 0)) / float(max(monthly_cost or 0, 1))) * 10
            recommendations.append({
                "source_key": sk,
                "source_name": impact["source_name"],
                "techniques_unlocked": len(impact["techniques_unlocked"]),
                "technique_ids": list(impact["techniques_unlocked"]),
                "gaps_resolved": impact["gaps_resolved"],
                "detection_improvement": min(round(impact["total_priority"] / 10, 1), 100),
                "estimated_monthly_cost": round(monthly_cost, 2),
                "estimated_annual_cost": round(monthly_cost * 12, 2),
                "roi_score": round(min(roi, 100), 1),
                "setup_complexity": impact["setup_complexity"],
            })

        recommendations.sort(key=lambda r: r["roi_score"], reverse=True)
        for i, rec in enumerate(recommendations):
            rec["priority_rank"] = i + 1

        return recommendations
