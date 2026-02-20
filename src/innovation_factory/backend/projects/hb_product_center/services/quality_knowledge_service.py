"""Quality Knowledge Assistant service.

Proposes mitigations for quality issues in product lots using Hugo Boss
quality documentation stored in the UC volume as context. The service
loads document knowledge and augments LLM responses with relevant
procedures, standards, and corrective actions.
"""

import json
import logging
from typing import Any, AsyncIterator, Optional

from databricks.sdk import WorkspaceClient
from sqlmodel import Session, select

from ..databricks_config import LLM_ENDPOINT_NAME
from ..models import HbChatMessage, HbChatSession

logger = logging.getLogger(__name__)

QUALITY_KNOWLEDGE = """
=== HB-QIM-2026-001: Quality Inspection Manual ===

FABRIC INSPECTION (4-Point System):
- Acceptance: <=28 penalty points per 100 linear yards. Premium BOSS: <=20 points.
- Color consistency (spectrophotometer): Delta E <=0.8 solid, <=1.0 prints, <=0.5 black.
- Fabric weight tolerance: +/-5% standard, +/-3% for lightweight summer fabrics.

COLOR DEVIATION MITIGATION:
- Delta E 0.8-1.2: May use for secondary lines with QC manager approval.
- Delta E >1.5: Reject and return lot. Segregate and request re-dye from supplier.

WEIGHT DEVIATION MITIGATION:
- Heavier (+5-8%): Increase pressing temp by 5C, extend pressing time by 2s.
- Underweight: Add interlining reinforcement at shoulders, collar, lapels.

STITCHING STANDARDS:
- Woven: 10-12 SPI. Knitwear: 8-10 SPI. Topstitching: 6-8 SPI.
- Shoulder seam alignment: +/-3mm. Collar symmetry: +/-2mm. Button spacing: +/-1mm.
- Seam strength minimums: Body 150N, Side 180N, Armhole 200N, Crotch 220N.

WEAK SEAM MITIGATION:
- Increase stitch density by 2 SPI. Verify thread tension. Audit machine calibration.
- If breakage rate >2%, replace thread lot.

BUTTON ATTACHMENT:
- Pull strength: Coat 80N, Shirt 60N, Trouser 50N. Minimum 4 thread passes.
- Failure mitigation: Re-train operators, increase to 6 passes for heavy coats.
- If failure rate >1% per shift, replace button machines.

MEASUREMENT TOLERANCES:
- BOSS: +/-0.5cm critical, +/-1.0cm non-critical.
- HUGO: +/-1.0cm critical. Min 5 garments per size per lot.
- Drift mitigation: Adjust spreading/cutting. For oversizing, recalibrate cutting equipment.

LABELING:
- Care labels: fiber composition, care symbols (ISO 3758), origin, size.
- Positioning error: Re-attach at finishing station.
- Content error: Escalate to compliance team within 4 hours (regulatory violation risk).

=== HB-DCG-2026-002: Defect Classification & Severity Guide ===

SEVERITY LEVELS:
- Critical: Safety hazard/brand damage → Reject lot, stop line, VP Quality <1hr
- Major: Visible, affects function → Quarantine, 100% sort, QC Manager <4hr
- Minor: Slight visual → Accept with deviation, QC Supervisor <8hr
- Cosmetic: Barely visible → Accept, log for trend analysis

FABRIC DEFECTS:
- Broken picks: Hand-repair if <5mm. Cut around if fabric yield allows.
- Slubs <3mm: Cosmetic. >3mm visible: Minor-Major.
- Reed marks >10% of roll: Reject. Isolated: Mark and avoid in cutting.
- Shade variation >Delta E 1.0 center-to-selvedge: Major. Segregate by shade group.
- Staining: Spot clean with approved solvents. Oil-based: dry clean. 2 failed attempts: reject.

CONSTRUCTION DEFECTS:
- Skipped stitches >2 per 10cm: Major. Replace needle, verify thread tension.
- Puckering on front/collar/cuffs: Major. Reduce presser foot pressure 10-15%.
- For lightweight fabrics: Use tissue paper backing during sewing.

PRESSING DEFECTS:
- Shine marks on dark fabrics: Major (critical for BOSS dark wool suits).
- Mitigation: Reduce temp 10C, pressure 15%. Use pressing cloth. Steam restoration.
- Light brushing in direction of nap. Calibrate press equipment daily.
- Permanent creasing: Re-press with increased steam, lower temp. Steam tunnel for stubborn.

TREND ANALYSIS TARGETS:
- Defect rate: <2.0 per 100 (BOSS), <3.0 per 100 (HUGO).
- First Pass Yield: >97%. Return rate: <0.5%.
- Exceeding targets 2 consecutive weeks: Initiate Corrective Action Request.

=== HB-CAP-2026-003: Corrective & Preventive Action Procedures ===

8D CAPA PROCESS:
1. Problem Identification (photos, measurements, lot info)
2. Containment (quarantine, stop production if critical)
3. Root Cause Analysis (5-Why or Fishbone/Ishikawa)
4. Corrective Action Plan (specific, measurable, deadlines)
5. Implementation (execute, document changes)
6. Verification (re-inspection to confirm effectiveness)
7. Preventive Action (update SOPs, training, processes)
8. Closure (QC Manager sign-off, archive)

ROOT CAUSE ANALYSIS - 6M Framework:
- Machine: calibration, maintenance, age
- Method: SOP compliance, process design
- Material: fabric, thread, trims quality
- Manpower: training, skill, workload
- Measurement: gauge accuracy, sampling plan
- Milieu: temperature, humidity, lighting

FABRIC MITIGATION TEMPLATES:
- Shrinkage: Quarantine lot → Adjust pattern +2% allowance → Require pre-shrinkage cert
- Pilling: Hold shipment → Anti-pilling finish → Change yarn to higher twist/blended fiber
  Verify: Martindale 3000 cycles, rating >=3.5

CONSTRUCTION MITIGATION TEMPLATES:
- Collar roll inconsistency: 100% inspect → Add pressing jig → Update pattern with stay tape
- Buttonhole fraying: Recall if shipped → Fray-check sealant → Bar-tack with increased density
  Verify: 10 garments, 10 wash cycles, zero defects

ESCALATION:
- Cosmetic: Weekly team meeting
- Minor: QC Supervisor <8hr
- Major: QC Manager <4hr, supplier <24hr
- Critical: VP Quality <1hr, line halt, CEO briefing

NCR PROCESS: Issue within 48hr. Supplier responds in 10 business days.
Failure to respond → scorecard downgrade → potential vendor removal.

=== HB-MTS-2026-004: Material Testing Standards ===

TENSILE STRENGTH (ISO 13934-1):
- Suiting: Warp 400N, Weft 300N. Shirting: Warp 300N, Weft 250N.
- Denim: Warp 500N, Weft 350N. Outerwear: Warp 600N, Weft 400N.
- Within 10% of min: accept with deviation. Below 90%: reject.
- Mitigation: Request 5% weight increase. Restrict to non-stress areas.

TEAR STRENGTH (ISO 13937-2):
- Suiting: Warp 15N, Weft 12N. Sportswear: Warp 20N, Weft 15N.
- Mitigation: Seam reinforcement tape. Fusible interlining at stress points.

COLORFASTNESS TO WASHING (ISO 105-C06):
- Color change: Grade 4 min. Staining: Grade 3-4 min.
- Mitigation: After-treatment fixative. Switch to pre-metallized/vat dyes.

COLORFASTNESS TO LIGHT (ISO 105-B02):
- Dark: Grade 5. Medium: Grade 4. Light/pastel: Grade 4.
- Mitigation: UV absorbers in finish. Retail display rotation max 2 weeks.

COLORFASTNESS TO RUBBING (ISO 105-X12):
- Dry: Grade 4. Wet: Grade 3. Below Grade 2-3 wet: reject.

DIMENSIONAL STABILITY (ISO 6330/5077):
- Woven: max 3% warp, 2% weft. Knitwear: max 5%/5%.
- Mitigation: Increase pre-shrinkage treatment. Add shrinkage allowance to pattern.
- >2x max allowance: reject lot.

BOSS SPECIAL TESTS:
- Pilling: Grade 4 after 5000 cycles. Mitigation: anti-pilling enzyme, increase polyamide 5-10%.
- Seam slippage: max 6mm at 180N. Abrasion: min 20,000 cycles.

=== HB-SQR-2026-005: Supplier Quality Requirements ===

SUPPLIER SCORECARD (Quarterly):
- Quality 40%, Delivery 25%, Cost 20%, Sustainability 15%.
- <70/100 for 2 quarters: formal improvement plan.
- <60/100: potential vendor removal.

INCOMING MATERIAL:
- Fabric: 100% 4-point inspection. Trims: AQL 1.5 level II.
- Thread: tensile test every lot. Labels: 100% visual.

IN-PROCESS CONTROLS:
- Cutting: verify direction, shade grouping, pattern matching.
- Assembly: in-line inspection every 30 min.
- Pressing: temp/pressure verification every 2 hr.
- Finishing: 100% final inspection.
- If defect rate >3%: stop, root cause, 100% sort.

AQL SAMPLING (ISO 2859-1):
- BOSS: Critical 1.5, Major 2.5, Minor 4.0.
- HUGO: Critical 2.5, Major 4.0, Minor 6.5.
- AQL fail: 100% sort at supplier cost. 2nd fail: reject + replacement at supplier cost.

NON-CONFORMANCE ESCALATION:
- 1st: Warning + CAPA
- 2nd: Tightened inspection (10 lots) + scorecard impact
- 3rd: On-site audit (supplier pays) + improvement plan
- 4th: Probation / contract termination

RSL COMPLIANCE:
- Formaldehyde: max 75ppm (skin contact), 300ppm (outerwear).
- Azo dyes: zero tolerance. Heavy metals: per REACH. PFAS: zero tolerance (2026).
- RSL failure: No shipment. Identify source, replace, re-test. 2 failures in 12 months: suspension.
"""

QUALITY_SYSTEM_PROMPT = f"""You are the Hugo Boss Quality Knowledge Assistant. You help quality \
engineers and inspectors propose suitable mitigations for quality issues in product lots.

You have access to the following Hugo Boss quality documentation stored in the \
innovation_factory_catalog.hb_product_center.quality_documents volume:
1. Quality Inspection Manual (HB-QIM-2026-001)
2. Defect Classification & Severity Guide (HB-DCG-2026-002)
3. Corrective & Preventive Action Procedures (HB-CAP-2026-003)
4. Material Testing Standards (HB-MTS-2026-004)
5. Supplier Quality Requirements (HB-SQR-2026-005)

Here is the relevant documentation content:

{QUALITY_KNOWLEDGE}

When responding to quality issues:
1. First classify the issue severity (Critical/Major/Minor/Cosmetic)
2. Reference the specific document and section number
3. Propose immediate containment actions
4. Suggest short-term corrective actions with timelines
5. Recommend long-term preventive measures
6. Specify verification steps to confirm effectiveness
7. Note escalation requirements based on severity

Always cite the document ID (e.g., HB-QIM-2026-001) when referencing procedures.
Be specific, actionable, and professional. Use markdown formatting for clarity."""


class QualityKnowledgeService:
    """RAG-style quality knowledge assistant backed by document context."""

    async def stream_response(
        self,
        ws: WorkspaceClient,
        db: Session,
        user_message: str,
        session_id: Optional[int] = None,
    ) -> AsyncIterator[str]:
        session = self._get_or_create_session(db, session_id)
        assert session.id is not None
        self._save_user_message(db, session.id, user_message)

        history = self._get_message_history(db, session.id, limit=6)
        messages: list[dict[str, str]] = [
            {"role": "system", "content": QUALITY_SYSTEM_PROMPT},
        ]
        messages.extend({"role": m["role"], "content": m["content"]} for m in history)

        try:
            result = ws.api_client.do(
                "POST",
                f"/serving-endpoints/{LLM_ENDPOINT_NAME}/invocations",
                body={"messages": messages, "max_tokens": 2048},
            )
            content = self._extract_text(result)
            sources = [
                {"type": "document", "source": "HB Quality Documentation (UC Volume)"},
            ]
        except Exception as e:
            logger.error(f"Quality assistant error: {type(e).__name__}: {e}", exc_info=True)
            content = (
                "I'm sorry, I couldn't process your quality query right now. "
                "Please check the serving endpoint is online and try again."
            )
            sources = [{"type": "error", "source": "System"}]

        self._save_assistant_message(db, session.id, content, sources)

        yield json.dumps({
            "session_id": session.id,
            "content": content,
            "sources": sources,
            "done": False,
        })
        yield json.dumps({"content": "", "done": True})

    def _extract_text(self, response: Any) -> str:
        if isinstance(response, dict):
            resp: dict[str, Any] = response
            choices = resp.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
            output = resp.get("output")
            if isinstance(output, str):
                return output
        return str(response)

    def _get_or_create_session(self, db: Session, session_id: Optional[int]) -> HbChatSession:
        if session_id:
            session = db.get(HbChatSession, session_id)
            if session:
                return session
        session = HbChatSession(context="quality_asst")
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def _save_user_message(self, db: Session, session_id: int, content: str) -> None:
        msg = HbChatMessage(session_id=session_id, role="user", content=content)
        db.add(msg)
        db.commit()

    def _save_assistant_message(
        self, db: Session, session_id: int, content: str, sources: list[dict]
    ) -> None:
        msg = HbChatMessage(session_id=session_id, role="assistant", content=content)
        db.add(msg)
        db.commit()

    def _get_message_history(self, db: Session, session_id: int, limit: int = 6) -> list[dict]:
        messages = db.exec(
            select(HbChatMessage)
            .where(HbChatMessage.session_id == session_id)
            .order_by(HbChatMessage.created_at.asc())  # type: ignore[union-attr]
        ).all()
        recent = messages[-limit:] if len(messages) > limit else messages
        return [{"role": m.role, "content": m.content} for m in recent]
