"""
UMBRA Reasoning Layer — Claude (demo-safe)
- Works with OR without ANTHROPIC_API_KEY
- Capped at MAX_REASONING_GAPS per run (free-tier cost control)
- Structured mock reasoning matches real output schema exactly
"""
import json
import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger("umbra.reasoning")

SYSTEM_PROMPT = """You are a senior detection engineer at an MDR provider.
Analyse a specific detection gap and respond ONLY with a JSON object — no preamble, no markdown fences.

Rules:
- Reference the SPECIFIC technique, missing sources, and client industry
- Think like an attacker exploiting THIS exact gap
- Be technical and precise
- Dwell time must be realistic

Output schema:
{
  "attacker_path": "<step-by-step technical attacker narrative for this specific gap>",
  "detection_failure": "<why detection fails for this exact rule/source combination>",
  "estimated_dwell_time": "<realistic range with rationale>",
  "business_impact": "<impact specific to this industry>"
}"""

USER_TEMPLATE = """Analyse this detection gap:

CLIENT: {client_name} | Industry: {industry} | Tier: {tier}
TECHNIQUE: {technique_id} — {technique_name} ({tactic})
COVERAGE STATE: {coverage_state} | ILLUSION: {coverage_illusion}
GAP: {gap_description}
MISSING SOURCES: {missing_sources}
ACTIVE SOURCES: {active_sources}
AFFECTED RULES: {affected_rules}
PRIORITY SCORE: {priority_score}/100

Generate the attacker path analysis."""


async def generate_gap_reasoning(
    gap_data: dict,
    client_data: dict,
    technique_data: dict,
    rule_data: list,
    source_data: dict,
) -> Optional[dict]:
    if not settings.ANTHROPIC_API_KEY:
        logger.info("No API key — using mock reasoning")
        return _mock_reasoning(gap_data, client_data, technique_data)

    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

        prompt = USER_TEMPLATE.format(
            client_name=client_data.get("name", "Unknown"),
            industry=client_data.get("industry", "Unknown"),
            tier=client_data.get("tier", "standard"),
            technique_id=technique_data.get("technique_id", ""),
            technique_name=technique_data.get("name", ""),
            tactic=technique_data.get("tactic", ""),
            coverage_state=gap_data.get("coverage_state", ""),
            coverage_illusion=gap_data.get("coverage_illusion", False),
            gap_description=gap_data.get("gap_description", ""),
            missing_sources=", ".join(gap_data.get("missing_sources", [])) or "None",
            active_sources=", ".join(client_data.get("active_source_keys", [])[:8]) or "None",
            affected_rules=", ".join(r.get("rule_id", "") for r in rule_data) or "None",
            priority_score=gap_data.get("priority_score", 0),
        )

        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]

        return json.loads(text.strip())

    except Exception as e:
        logger.error(f"Claude API error: {e} — falling back to mock")
        return _mock_reasoning(gap_data, client_data, technique_data)


def _mock_reasoning(gap_data: dict, client_data: dict, technique_data: dict) -> dict:
    """
    Deterministic mock reasoning — same structure as real Claude output.
    Used when: no API key, API error, or demo mode.
    """
    tid = technique_data.get("technique_id", "unknown")
    industry = client_data.get("industry", "enterprise")
    client = client_data.get("name", "the client")
    missing = gap_data.get("missing_sources", [])
    state = gap_data.get("coverage_state", "BROKEN")
    tactic = technique_data.get("tactic", "unknown")

    paths = {
        "T1059.001": f"Adversary targeting {client} executes a Base64-encoded PowerShell download cradle "
                     f"using -EncodedCommand. Without Script Block Logging (powershell_logs), no execution "
                     f"content is captured. Process creation events show only powershell.exe — indistinguishable "
                     f"from legitimate use. Attacker stages Cobalt Strike beacon via Invoke-Expression with "
                     f"string concatenation, bypassing all keyword-based detection.",
        "T1003.001": f"Post-compromise, attacker runs a custom LSASS dumper against {client}'s domain controllers. "
                     f"Sysmon EventID 10 (ProcessAccess) is configured but the source is offline — zero events "
                     f"reach the SIEM. NTLM hashes and Kerberos tickets extracted within 4 minutes. "
                     f"Pass-the-hash enables domain-wide lateral movement before any alert fires.",
        "T1021.001": f"Using harvested domain credentials, attacker initiates RDP sessions to jump servers "
                     f"and domain controllers at {client}. Detection relies on network flow for the chain rule — "
                     f"absent. Only Windows Security Event 4624 is visible, but attacker uses admin credentials "
                     f"that bypass the non-admin-source heuristic. Each RDP hop is invisible.",
        "T1041":     f"Attacker exfiltrates data from {client} via chunked HTTPS POST requests to a CDN-fronted "
                     f"C2 server. Without proxy_logs or network_flow, there is zero visibility into outbound "
                     f"data volume or destination reputation. Large transfers blend into normal business traffic.",
        "T1071.004": f"DNS C2 channel established against {client} using subdomain encoding. "
                     f"Without DNS query logs, query volume and encoded payloads are invisible. "
                     f"Attacker maintains persistent comms channel through corporate DNS resolvers, "
                     f"bypassing all proxy and web filtering controls.",
    }

    failures = {
        "T1059.001": "RULE-T1059-001-B and C require powershell_logs (HARD dependency). "
                     "Source not ingested — both rules show 'deployed' in the registry but cannot fire. "
                     "RULE-T1059-001-A (process_creation only) misses encoded and in-memory execution entirely.",
        "T1003.001": "process_access source is configured in client_log_sources but health=offline. "
                     "The coverage matrix marks LSASS rules as BUILT — this is the Coverage Illusion. "
                     "Zero LSASS access events reach the SIEM. Attacker has unrestricted credential dumping.",
        "T1021.001": "RULE-T1021-001-B (chain rule) requires network_flow (HARD). "
                     "Without network-layer visibility, the credential-access → lateral-movement chain "
                     "cannot be correlated. Single-source RDP detection misses privileged account usage.",
        "T1041":     "No rules deployed. Neither network_flow nor proxy_logs are ingested. "
                     "This is a complete visibility gap — no telemetry, no rules, no detection possible. "
                     "Forensic reconstruction after incident is impossible without historical network data.",
        "T1071.004": "No DNS query logs ingested. RULE-T1071-004-A cannot evaluate query frequency "
                     "or encoded subdomain patterns. DNS traffic passes through infrastructure entirely unmonitored.",
    }

    dwell_times = {
        "execution":         "21–60 days — Encoded execution without script logging is effectively silent.",
        "credential_access": "7–21 days — Credential compromise enables rapid lateral movement to domain admin.",
        "lateral_movement":  "3–14 days — Lateral movement phase spans days before ransomware/exfil stage.",
        "exfiltration":      "Indeterminate — Exfiltration may have started before detection engagement.",
        "command_and_control": "30–90 days — Persistent C2 channels can maintain access for months undetected.",
        "persistence":       "30–90 days — Valid account abuse has the highest mean dwell time of any technique.",
    }

    impacts = {
        "Financial Services": f"Credential compromise at {client} threatens trading system access, SWIFT "
                              f"infrastructure, and customer PII. Full domain compromise → $15M–$50M IR cost "
                              f"+ PCI-DSS/SOX regulatory penalties + mandatory breach notification.",
        "Healthcare":         f"Undetected access at {client} risks PHI exfiltration (HIPAA breach), "
                              f"ransomware targeting clinical systems, and patient safety if OT/medical devices "
                              f"are reachable from compromised endpoints.",
        "Energy & Utilities": f"Lateral movement at {client} from IT into OT networks risks operational "
                              f"disruption, safety system compromise, and regulatory action under NERC-CIP. "
                              f"Grid disruption events have cascading infrastructure impact.",
    }

    return {
        "attacker_path": paths.get(tid,
            f"Adversary targeting {client} exploits {tid} ({tactic}) leveraging the absence of "
            f"{', '.join(missing[:2]) if missing else 'required telemetry'}. "
            f"With coverage state '{state}', the technique operates below the detection threshold "
            f"of the current rule stack."
        ),
        "detection_failure": failures.get(tid,
            f"Detection fails because {', '.join(missing) if missing else 'required sources are unavailable'}. "
            f"Deployed rules cannot fire without this telemetry, creating a coverage illusion."
        ),
        "estimated_dwell_time": dwell_times.get(tactic, "14–45 days — standard dwell when telemetry is absent."),
        "business_impact": impacts.get(industry,
            f"In the {industry} sector, exploitation of this gap risks credential compromise, "
            f"lateral movement, and data exfiltration against critical assets."
        ),
    }
