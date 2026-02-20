"""Generate Hugo Boss quality documentation PDFs and upload to UC volume.

Creates 5 realistic quality management documents and uploads them to
innovation_factory_catalog.hb_product_center volume.
"""

import io
import textwrap
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.catalog import VolumeType
from fpdf import FPDF

CATALOG = "innovation_factory_catalog"
SCHEMA = "hb_product_center"
VOLUME = "quality_documents"
VOLUME_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}"


class HBDocument(FPDF):
    """Hugo Boss branded PDF document."""

    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(0, 0, 0)
        self.cell(0, 8, "HUGO BOSS AG  |  CONFIDENTIAL", align="R")
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def title_page(self, title: str, subtitle: str, doc_id: str):
        self.add_page()
        self.ln(50)
        self.set_font("Helvetica", "B", 28)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 14, title, align="C")
        self.ln(8)
        self.set_font("Helvetica", "", 14)
        self.set_text_color(100, 100, 100)
        self.multi_cell(0, 8, subtitle, align="C")
        self.ln(20)
        self.set_font("Helvetica", "", 10)
        self.cell(0, 6, f"Document ID: {doc_id}", align="C")
        self.ln(6)
        self.cell(0, 6, "Classification: Internal / Quality Management", align="C")
        self.ln(6)
        self.cell(0, 6, "Effective Date: January 2026", align="C")

    def section(self, title: str):
        self.add_page()
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(0, 0, 0)
        self.cell(0, 12, title)
        self.ln(16)

    def subsection(self, title: str):
        self.ln(4)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(40, 40, 40)
        self.cell(0, 10, title)
        self.ln(12)

    def body(self, text: str):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(50, 50, 50)
        for paragraph in text.strip().split("\n\n"):
            cleaned = " ".join(paragraph.split())
            self.multi_cell(0, 5, cleaned)
            self.ln(3)

    def bullet_list(self, items: list[str]):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(50, 50, 50)
        for item in items:
            cleaned = " ".join(item.split())
            x = self.get_x()
            self.cell(8, 5, "-")
            self.multi_cell(0, 5, cleaned)
            self.set_x(x)
        self.ln(3)

    def table(self, headers: list[str], rows: list[list[str]], col_widths: list[int] | None = None):
        if col_widths is None:
            w = int((self.w - 20) / len(headers))
            col_widths = [w] * len(headers)
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(230, 230, 230)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, h, border=1, fill=True)
        self.ln()
        self.set_font("Helvetica", "", 9)
        self.set_fill_color(255, 255, 255)
        for row in rows:
            max_h = 7
            for i, cell in enumerate(row):
                self.cell(col_widths[i], max_h, cell[:40], border=1)
            self.ln()
        self.ln(4)


DOCUMENTS: dict[str, dict] = {}


def build_quality_inspection_manual() -> bytes:
    pdf = HBDocument()
    pdf.alias_nb_pages()
    pdf.title_page(
        "Quality Inspection Manual",
        "Standard Operating Procedures for Product Quality Assessment",
        "HB-QIM-2026-001",
    )

    pdf.section("1. Fabric Inspection Standards")
    pdf.body("""
All incoming fabrics must be inspected using the 4-point inspection system before entering
the production line. The 4-point system assigns penalty points based on defect size: defects
up to 3 inches receive 1 point, defects 3-6 inches receive 2 points, defects 6-9 inches
receive 3 points, and defects over 9 inches receive 4 points.

Acceptance criteria: A lot is accepted if total penalty points per 100 linear yards is 28 or
fewer. Lots exceeding this threshold must be quarantined and the supplier notified within
24 hours. For premium BOSS collection fabrics, the threshold is reduced to 20 points per
100 linear yards.
    """)

    pdf.subsection("1.1 Color Consistency Testing")
    pdf.body("""
Color consistency is evaluated using a spectrophotometer against approved lab dip standards.
Acceptable Delta E (CIE LAB) values are: Delta E <= 0.8 for solid colors, Delta E <= 1.0
for prints and patterns, and Delta E <= 0.5 for black fabrics (critical for BOSS suits).

Mitigation for color deviation: If Delta E exceeds acceptable limits, segregate the lot
and request a re-dye from the supplier. For minor deviations (Delta E 0.8-1.2), the fabric
may be used for secondary product lines with QC manager approval. For deviations greater
than 1.5, the lot must be rejected and returned.
    """)

    pdf.subsection("1.2 Fabric Weight and Hand Feel")
    pdf.body("""
Fabric weight tolerance is +/- 5% of the specification. For wool suiting (typically 240-280 g/m2),
variation beyond this range compromises garment drape and structure. Lightweight summer
fabrics (120-180 g/m2) have a tighter tolerance of +/- 3%.

Mitigation for weight deviation: Adjust pattern cutting parameters to compensate for minor
weight variations. For heavier fabrics (+5-8%), increase pressing temperature by 5 degrees C and
extend pressing time by 2 seconds. For underweight fabrics, add interlining reinforcement at
key structural points (shoulders, collar, lapels).
    """)

    pdf.section("2. Stitching and Construction Standards")
    pdf.body("""
All garments must meet Hugo Boss stitching standards. Stitch density requirements vary by
garment area: seam construction requires 10-12 stitches per inch (SPI) for woven garments
and 8-10 SPI for knitwear. Topstitching requires 6-8 SPI with consistent spacing.

Critical construction checkpoints include: shoulder seam alignment (tolerance +/- 3mm),
collar symmetry (tolerance +/- 2mm), button spacing uniformity (tolerance +/- 1mm),
and sleeve pitch angle (consistent with pattern specification +/- 2 degrees).
    """)

    pdf.subsection("2.1 Seam Strength Requirements")
    pdf.body("""
Minimum seam strength values (tested per ISO 13935-1): Main body seams 150N,
side seams 180N, armhole seams 200N, crotch seams 220N, and pocket attachment 120N.

Mitigation for weak seams: If seam strength falls below minimum, increase stitch density
by 2 SPI and verify thread tension settings. For repeated failures, audit the sewing machine
calibration schedule and operator training records. Replace thread lot if breakage rate exceeds
2% during production.
    """)

    pdf.subsection("2.2 Button and Fastener Attachment")
    pdf.body("""
Button pull strength minimum: 80N for coat buttons, 60N for shirt buttons, 50N for trouser
buttons. Snap fasteners require 20N minimum. All buttons must be cross-stitched with
minimum 4 thread passes. BOSS-branded buttons must have logo facing upward when garment
is buttoned.

Mitigation for button attachment failure: Re-train operators on cross-stitch technique.
Increase thread passes from 4 to 6 for heavy coat buttons. Replace button machines
if failure rate exceeds 1% per shift. For branded button misalignment, implement a
go/no-go gauge at the button attachment station.
    """)

    pdf.section("3. Measurement and Fit Standards")
    pdf.body("""
All garments must be measured flat against the approved measurement specification sheet.
Critical measurements include: chest width, waist width, hip width, body length, sleeve
length, and shoulder width. Tolerance for BOSS collection: +/- 0.5 cm for critical points,
+/- 1.0 cm for non-critical points. HUGO collection allows +/- 1.0 cm for critical points.

Each production lot must have a minimum of 5 garments measured per size. If any measurement
falls outside tolerance, the entire lot for that size must be 100% measured.

Mitigation for measurement deviation: If systematic drift is detected (all pieces
trending in one direction), adjust the spreading/cutting parameters. For random variation,
review marker placement and fabric relaxation procedures. For consistent oversizing,
recalibrate cutting equipment and verify pattern grading.
    """)

    pdf.section("4. Labeling and Packaging")
    pdf.body("""
All labels must be correctly positioned, legible, and comply with local market regulations.
Care labels must include: fiber composition, care symbols (ISO 3758), country of origin,
and size designation. Brand labels must be centered within 2mm tolerance.

Packaging must use approved Hugo Boss tissue paper, hangers, and garment bags.
Each garment must have a unique barcode/RFID tag matching the style-color-size combination.

Mitigation for labeling errors: Immediately quarantine affected garments. For minor label
positioning errors, re-attach labels at the finishing station. For incorrect content (wrong
fiber composition or care instructions), escalate to compliance team within 4 hours as this
may constitute a regulatory violation.
    """)

    return pdf.output()


def build_defect_classification_guide() -> bytes:
    pdf = HBDocument()
    pdf.alias_nb_pages()
    pdf.title_page(
        "Defect Classification\n& Severity Guide",
        "Standard Reference for Quality Inspection Teams",
        "HB-DCG-2026-002",
    )

    pdf.section("1. Defect Severity Classification")
    pdf.body("""
All defects are classified into four severity levels that determine the appropriate response
and mitigation actions. This standardized classification ensures consistent quality decisions
across all Hugo Boss manufacturing facilities worldwide.
    """)

    pdf.table(
        ["Severity", "Description", "Action Required", "Escalation"],
        [
            ["Critical", "Safety hazard or brand damage", "Reject lot, stop line", "VP Quality <1hr"],
            ["Major", "Visible defect, affects function", "Quarantine, sort 100%", "QC Manager <4hr"],
            ["Minor", "Slight visual defect", "Accept with deviation", "QC Supervisor <8hr"],
            ["Cosmetic", "Barely visible, no function impact", "Accept, log for trend", "Weekly report"],
        ],
        [35, 45, 45, 45],
    )

    pdf.section("2. Fabric Defects")
    pdf.subsection("2.1 Weaving Defects")
    pdf.body("""
Broken picks (missing weft threads): Severity depends on visibility. Single broken pick
in non-visible area is Minor. Multiple broken picks or in visible area is Major.

Mitigation: For isolated broken picks, hand-repair using matching yarn if defect is less
than 5mm. For larger areas, cut around defect if fabric yield allows. Request replacement
fabric from supplier for systematic issues.
    """)

    pdf.body("""
Slubs (thick places in yarn): Single slub less than 3mm is Cosmetic. Multiple slubs or
slubs greater than 3mm in visible area is Minor to Major depending on garment positioning.

Reed marks (vertical lines from loom): If visible under normal lighting at 1 meter distance,
classify as Major. Intermittent marks visible only on close inspection are Minor.

Mitigation for reed marks: Reject the roll if marks appear in more than 10% of the length.
For isolated areas, mark and avoid during cutting. Report to supplier for loom maintenance.
    """)

    pdf.subsection("2.2 Dyeing and Finishing Defects")
    pdf.body("""
Shade variation (lot-to-lot or within roll): Center-to-selvedge variation exceeding Delta E 1.0
is Major. End-to-end variation exceeding Delta E 0.5 is Major for BOSS, Minor for HUGO.

Staining or spotting: Any visible stain is Major in finished garment. In fabric, stains that
can be removed by standard cleaning are Minor. Permanent stains are Major.

Mitigation for shade variation: Segregate fabric by shade group and cut single garments from
same shade group only. For lot-to-lot variation, adjust cutting plan to use similar shades
for the same order. Implement shade sorting at fabric receiving.

Mitigation for staining: Attempt spot cleaning with approved solvents (test on hidden area
first). For oil-based stains, use dry cleaning process. If stain persists after two cleaning
attempts, classify garment as second quality or reject.
    """)

    pdf.section("3. Construction Defects")
    pdf.subsection("3.1 Stitching Defects")
    pdf.body("""
Skipped stitches: More than 2 skipped stitches in any 10cm section is Major.
Single skipped stitch in non-stress area is Minor.

Puckering (fabric gathering along seam): Visible puckering on front, collar, or cuffs is Major.
Light puckering on inner seams is Minor.

Mitigation for skipped stitches: Replace needle immediately (worn needle is most common cause).
Verify thread path and tension. Check needle-to-hook timing on the machine. If issue persists
across multiple machines, test thread lot for consistency.

Mitigation for puckering: Reduce presser foot pressure by 10-15%. Verify thread tension balance
(bobbin vs. needle thread). For differential feed machines, adjust feed ratio. For lightweight
fabrics, use tissue paper backing during sewing, removing after completion.
    """)

    pdf.subsection("3.2 Pressing and Finishing Defects")
    pdf.body("""
Shine marks (glazing from excessive heat/pressure): Any visible shine on dark fabrics is Major.
This is particularly critical for BOSS dark wool suits.

Mitigation for shine marks: Immediately reduce pressing temperature by 10 degrees C and pressure
by 15%. Use pressing cloth between iron and fabric surface. For existing shine marks, attempt
steam restoration. If shine persists, apply light brushing with garment brush in direction of
fabric nap. Prevent recurrence by calibrating press equipment daily.

Wrinkles or creasing: Wrinkles that do not hang out within 24 hours on a hanger are Minor.
Permanent creasing (heat-set) is Major.

Mitigation for permanent creasing: Attempt re-pressing with increased steam and lower
temperature. For stubborn creases, use a steam tunnel. If crease remains visible, downgrade
to second quality. Investigate root cause in handling and storage procedures.
    """)

    pdf.section("4. Defect Trend Analysis")
    pdf.body("""
Quality teams must track defect rates weekly and conduct monthly trend analysis. Key metrics:
Defect rate per 100 units (target: <2.0 for BOSS, <3.0 for HUGO), First Pass Yield (target: >97%),
and Return rate (target: <0.5%).

When defect rates exceed targets for two consecutive weeks, initiate a Corrective Action
Request (CAR) per document HB-CAP-2026-003. Persistent issues (>4 weeks above target)
require a formal supplier audit per the Supplier Quality Requirements manual.
    """)

    return pdf.output()


def build_corrective_action_procedures() -> bytes:
    pdf = HBDocument()
    pdf.alias_nb_pages()
    pdf.title_page(
        "Corrective & Preventive\nAction Procedures (CAPA)",
        "Root Cause Analysis and Mitigation Framework",
        "HB-CAP-2026-003",
    )

    pdf.section("1. CAPA Process Overview")
    pdf.body("""
The Hugo Boss Corrective and Preventive Action (CAPA) process follows an 8-step methodology
(8D) adapted for garment manufacturing. Every quality issue that exceeds acceptable thresholds
triggers this process to identify root causes, implement corrective actions, and prevent recurrence.

The CAPA process is mandatory for: Critical defects (any occurrence), Major defects exceeding
2% per lot, Minor defects exceeding 5% per lot, customer complaints related to product quality,
and any safety-related concern.
    """)

    pdf.subsection("1.1 CAPA Workflow Steps")
    pdf.bullet_list([
        "Step 1: Problem Identification - Document the issue with photos, measurements, lot info",
        "Step 2: Containment - Quarantine affected product, stop production if critical",
        "Step 3: Root Cause Analysis - Use 5-Why or Fishbone (Ishikawa) diagram",
        "Step 4: Corrective Action Plan - Define specific, measurable actions with deadlines",
        "Step 5: Implementation - Execute the corrective actions, document changes",
        "Step 6: Verification - Confirm effectiveness through re-inspection",
        "Step 7: Preventive Action - Update SOPs, training, or processes to prevent recurrence",
        "Step 8: Closure - Sign off by QC Manager, archive in quality database",
    ])

    pdf.section("2. Root Cause Analysis Methods")
    pdf.subsection("2.1 Five-Why Analysis for Common Quality Issues")
    pdf.body("""
Example: Thread breakage during production

Why 1: Thread breaks frequently during sewing.
Why 2: Thread tension is inconsistent.
Why 3: Tension disc is worn unevenly.
Why 4: Tension disc was not replaced during last maintenance cycle.
Why 5: Preventive maintenance schedule was not followed.

Root Cause: Failure to adhere to preventive maintenance schedule.
Corrective Action: Implement automated maintenance alerts in MES system.
Preventive Action: Monthly audit of maintenance compliance with accountability to shift supervisor.
    """)

    pdf.subsection("2.2 Fishbone Diagram Categories")
    pdf.body("""
For systematic quality issues, use the 6M framework:

Machine: Equipment calibration, maintenance, age, capability
Method: SOP compliance, process design, work instructions
Material: Fabric quality, thread quality, trims, interlining
Manpower: Training, skill level, experience, workload
Measurement: Gauge accuracy, inspection frequency, sampling plan
Milieu (Environment): Temperature, humidity, lighting, workspace layout

Each category should be investigated when performing root cause analysis for defects
that cannot be attributed to a single obvious cause.
    """)

    pdf.section("3. Mitigation Action Templates")
    pdf.subsection("3.1 Fabric Quality Issues")
    pdf.body("""
Issue: Fabric shrinkage exceeds tolerance after washing
Immediate Action: Quarantine remaining fabric from the same lot
Short-term Mitigation: Adjust pattern to include additional shrinkage allowance (+2%)
Long-term Solution: Require pre-shrinkage testing certificate from supplier for every lot
Verification: Test 3 samples from next 5 lots to confirm compliance
Timeline: Immediate quarantine, pattern adjustment within 24 hours, supplier requirement within 1 week

Issue: Pilling on knitwear after 3 wash cycles
Immediate Action: Hold shipment of affected styles
Short-term Mitigation: Add anti-pilling finish treatment to production process
Long-term Solution: Change yarn specification to higher twist count or blended fiber
Verification: Martindale pilling test (minimum 3000 cycles, rating 3.5 or better)
Timeline: Shipment hold immediately, finishing treatment within 48 hours, yarn spec change for next season
    """)

    pdf.subsection("3.2 Construction Quality Issues")
    pdf.body("""
Issue: Systematic collar roll inconsistency in suit jackets
Immediate Action: 100% inspection of collar area for current production
Short-term Mitigation: Add collar-specific pressing jig to standardize the pressing angle
Long-term Solution: Update collar construction method to include stay tape at roll line
Verification: Measure collar roll angle on 20 garments after corrective action
Timeline: 100% inspection immediately, jig within 3 days, pattern update within 2 weeks

Issue: Button hole fraying on shirts after 5 washes
Immediate Action: Recall affected batch if already shipped to retail
Short-term Mitigation: Apply fray-check sealant to all buttonholes before shipping
Long-term Solution: Switch to bar-tack buttonhole finish with increased stitch density
Verification: Wash test 10 garments for 10 cycles, zero buttonhole defects
Timeline: Recall decision within 4 hours, sealant application within 24 hours, process change within 1 week
    """)

    pdf.section("4. Escalation and Communication")
    pdf.body("""
Quality issues must be communicated to the appropriate level based on severity:

Cosmetic defects: Logged in Quality Management System, reviewed in weekly team meeting
Minor defects: QC Supervisor notified within 8 hours, included in shift report
Major defects: QC Manager notified within 4 hours, supplier notified within 24 hours
Critical defects: VP Quality notified within 1 hour, production line halted, CEO office briefed

For supplier-related issues, the Supplier Quality Engineer must issue a formal Non-Conformance
Report (NCR) within 48 hours. Suppliers have 10 business days to respond with their CAPA plan.
Failure to respond or implement corrective actions may result in supplier scorecard downgrade
and potential removal from the approved vendor list.
    """)

    return pdf.output()


def build_material_testing_standards() -> bytes:
    pdf = HBDocument()
    pdf.alias_nb_pages()
    pdf.title_page(
        "Material Testing Standards",
        "Laboratory Test Methods and Acceptance Criteria",
        "HB-MTS-2026-004",
    )

    pdf.section("1. Physical Testing Requirements")
    pdf.subsection("1.1 Tensile Strength (ISO 13934-1)")
    pdf.body("""
Minimum tensile strength requirements for woven fabrics:

Suiting (wool/wool blend): Warp 400N, Weft 300N
Shirting (cotton/cotton blend): Warp 300N, Weft 250N
Denim: Warp 500N, Weft 350N
Outerwear: Warp 600N, Weft 400N
Lining: Warp 200N, Weft 150N

Mitigation for tensile failure: Request fabric weight increase from supplier (minimum 5%).
For existing stock, restrict use to non-stress areas or lower-stress garment types.
If tensile strength is within 10% of minimum, accept with deviation for non-safety-critical
applications. Below 90% of minimum: reject the lot.
    """)

    pdf.subsection("1.2 Tear Strength (ISO 13937-2)")
    pdf.body("""
Minimum tear strength (Elmendorf method):

Suiting: Warp 15N, Weft 12N
Shirting: Warp 10N, Weft 8N
Sportswear: Warp 20N, Weft 15N
Outerwear: Warp 25N, Weft 20N

Mitigation for low tear strength: Add seam reinforcement tape at stress points.
For lightweight fabrics, consider fusible interlining in high-stress areas.
Recommend yarn density increase to supplier for future production.
    """)

    pdf.section("2. Colorfastness Testing")
    pdf.subsection("2.1 Colorfastness to Washing (ISO 105-C06)")
    pdf.body("""
Minimum rating requirements (Grey Scale 1-5):

Color change: Grade 4 minimum (Grade 4-5 for white and light colors)
Color staining on multifiber strip: Grade 3-4 minimum

Test conditions: C2S method (40 degrees C, 30 minutes, with steel balls)
For premium suiting: A1S method (additional test at 60 degrees C)

Mitigation for poor wash fastness: Apply after-treatment fixative to improve fastness.
For reactive dyes showing poor washfastness, switch to pre-metallized or vat dyes.
Retest after treatment; if still below Grade 4, reject the lot and request re-dyeing
from the supplier.
    """)

    pdf.subsection("2.2 Colorfastness to Light (ISO 105-B02)")
    pdf.body("""
Minimum Blue Wool Scale ratings:

Dark colors: Grade 5 minimum
Medium colors: Grade 4 minimum
Light and pastel colors: Grade 4 minimum
Fluorescent colors: Grade 3 minimum (these inherently fade faster)

Mitigation for poor lightfastness: Add UV absorbers to finish treatment. For display
garments (retail floor), implement rotation policy (maximum 2 weeks in direct light).
For outdoor advertising samples, require Grade 6 minimum.
    """)

    pdf.subsection("2.3 Colorfastness to Rubbing (ISO 105-X12)")
    pdf.body("""
Minimum rating:
Dry rubbing: Grade 4 minimum
Wet rubbing: Grade 3 minimum (Grade 3-4 for dark denim)

Mitigation for poor rubbing fastness: For denim, this is partially expected and managed
through consumer care instructions. For non-denim, apply fixing agent. If wet rubbing
is below Grade 2-3, the fabric is not suitable for Hugo Boss products and must be rejected.
    """)

    pdf.section("3. Dimensional Stability (ISO 6330 / ISO 5077)")
    pdf.body("""
Maximum shrinkage/growth after washing and drying:

Woven garments: Shrinkage max 3% (warp), 2% (weft)
Knitwear: Shrinkage max 5% (length), 5% (width)
Denim (raw): Shrinkage max 10% (preshrunk must meet woven spec)
Stretch fabrics: Maximum growth 5% after 5 wash cycles

Mitigation for excessive shrinkage: Increase pre-shrinkage treatment in finishing.
Adjust garment dimensions to compensate (add shrinkage allowance to pattern).
For knitwear, implement tumble dry relaxation step in production.
If shrinkage exceeds 2x the maximum allowance, reject the lot.
    """)

    pdf.section("4. Special Tests for BOSS Collection")
    pdf.body("""
The BOSS mainline collection requires additional testing beyond standard requirements:

Pilling resistance (ISO 12945-2): Minimum Grade 4 after 5000 cycles (Martindale)
Seam slippage (ISO 13936-1): Maximum 6mm at 180N for woven fabrics
Abrasion resistance (ISO 12947-2): Minimum 20,000 cycles (Martindale) for seating areas
Drape coefficient: Must match approved sample within 10% tolerance

Mitigation for pilling failure: Apply anti-pilling enzyme treatment. For wool blends,
increase polyamide content by 5-10% in the blend. For cotton knits, use compact yarn
or combed ring-spun yarn instead of open-end yarn.
    """)

    return pdf.output()


def build_supplier_quality_requirements() -> bytes:
    pdf = HBDocument()
    pdf.alias_nb_pages()
    pdf.title_page(
        "Supplier Quality\nRequirements Manual",
        "Standards for Approved Manufacturing Partners",
        "HB-SQR-2026-005",
    )

    pdf.section("1. Supplier Quality Expectations")
    pdf.body("""
Hugo Boss requires all manufacturing partners to maintain quality management systems
certified to ISO 9001:2015 or equivalent. Suppliers must demonstrate a minimum First Pass
Yield of 95% for HUGO products and 97% for BOSS products.

Suppliers are evaluated quarterly on a scorecard system covering: Quality (40% weight),
Delivery (25% weight), Cost (20% weight), and Sustainability (15% weight). A score below
70/100 for two consecutive quarters triggers a formal improvement plan. A score below 60/100
may result in removal from the approved vendor list.
    """)

    pdf.subsection("1.1 Incoming Material Quality")
    pdf.body("""
Suppliers must implement incoming material inspection for all raw materials:

Fabric: 4-point inspection on 100% of rolls received
Trims: AQL 1.5 inspection level II for critical trims (buttons, zippers)
Thread: Tensile strength test on every incoming lot
Labels: 100% visual inspection for content accuracy

Mitigation for incoming material failures: Supplier must segregate non-conforming material
immediately. Replacement material must be sourced within the agreed lead time. Costs for
replacement, re-inspection, and production delays are borne by the material supplier.
The manufacturing partner must notify Hugo Boss QC within 24 hours of any material rejection.
    """)

    pdf.section("2. In-Process Quality Controls")
    pdf.body("""
Suppliers must implement quality checkpoints at critical production stages:

Cutting: Verify fabric direction, shade grouping, and pattern matching
Assembly: In-line inspection at minimum every 30 minutes per line
Pressing: Temperature and pressure verification every 2 hours
Finishing: 100% final inspection before packing

Statistical Process Control (SPC) is required for critical measurements. Suppliers must
maintain control charts for key garment dimensions and demonstrate process capability
(Cpk >= 1.33) for critical quality characteristics.

Mitigation for in-process failures: When in-line inspection detects defect rate above 3%,
production must be stopped and root cause identified before restart. The affected batch
must be 100% sorted. Production restart requires QC supervisor sign-off.
    """)

    pdf.section("3. Final Inspection and AQL")
    pdf.body("""
Final inspection follows the AQL (Acceptable Quality Level) sampling plan per ISO 2859-1:

BOSS Collection: AQL 1.5 for Critical, AQL 2.5 for Major, AQL 4.0 for Minor
HUGO Collection: AQL 2.5 for Critical, AQL 4.0 for Major, AQL 6.5 for Minor
Accessories: AQL 1.0 for Critical, AQL 2.5 for Major, AQL 4.0 for Minor

Normal inspection level II applies unless the supplier is on tightened inspection
(triggered by 2 lot rejections in 5 consecutive lots).

Mitigation for AQL failure: Entire lot must be 100% sorted by supplier at their cost.
After sorting, lot is re-submitted for inspection. If second inspection also fails,
the lot is rejected and supplier must produce replacement at their cost.
Hugo Boss reserves the right to charge penalty of 5% of lot value for each failed
inspection after the first.
    """)

    pdf.section("4. Non-Conformance Management")
    pdf.body("""
When non-conforming product is identified, suppliers must:

1. Immediately quarantine affected product
2. Notify Hugo Boss quality representative within 4 hours
3. Submit initial investigation report within 24 hours
4. Provide root cause analysis and CAPA plan within 5 business days
5. Implement corrective actions per agreed timeline
6. Submit verification evidence of corrective action effectiveness

Recurring non-conformances (same defect type, 3 occurrences in 6 months) trigger a
mandatory on-site audit by Hugo Boss quality engineering team. The supplier bears travel
and audit costs. Audit findings must be addressed within 30 days.

Mitigation framework for recurring issues:
First occurrence: Documented warning and CAPA requirement
Second occurrence: Tightened inspection (next 10 lots) and supplier scorecard impact
Third occurrence: On-site audit and formal improvement plan with weekly progress reviews
Fourth occurrence: Probationary status with potential for contract termination
    """)

    pdf.section("5. Sustainability and Compliance")
    pdf.body("""
All suppliers must comply with Hugo Boss restricted substances list (RSL), which aligns
with REACH regulations and AFIRM Group RSL. Testing must be performed by an accredited
third-party laboratory.

Key restricted substance requirements:
Formaldehyde: Max 75 ppm (direct skin contact), Max 300 ppm (outerwear)
Azo dyes: Zero tolerance for listed amines (EU Regulation 1907/2006 Annex XVII)
Heavy metals: Per REACH limits (Lead <90 ppm, Cadmium <40 ppm, etc.)
PFAS: Zero tolerance effective 2026 for all product categories

Mitigation for RSL failures: Product must not be shipped under any circumstances.
Supplier must identify the source of contamination, replace the material, and re-test
before production can resume. All costs including re-testing, material replacement,
and production delays are borne by the supplier. Repeated RSL failures (2 in 12 months)
result in immediate suspension from the approved vendor list.
    """)

    return pdf.output()


# Collect all document builders
DOCUMENT_BUILDERS = {
    "HB_Quality_Inspection_Manual.pdf": build_quality_inspection_manual,
    "HB_Defect_Classification_Guide.pdf": build_defect_classification_guide,
    "HB_Corrective_Action_Procedures_CAPA.pdf": build_corrective_action_procedures,
    "HB_Material_Testing_Standards.pdf": build_material_testing_standards,
    "HB_Supplier_Quality_Requirements.pdf": build_supplier_quality_requirements,
}


def main():
    w = WorkspaceClient()
    print(f"Connected to workspace: {w.config.host}")

    # Ensure volume exists
    print(f"\nCreating volume {CATALOG}.{SCHEMA}.{VOLUME} ...")
    try:
        w.volumes.create(
            catalog_name=CATALOG,
            schema_name=SCHEMA,
            name=VOLUME,
            volume_type=VolumeType.MANAGED,
        )
        print("  Volume created.")
    except Exception as e:
        if "ALREADY_EXISTS" in str(e):
            print("  Volume already exists.")
        else:
            print(f"  Warning: {e}")

    # Generate and upload each document
    for filename, builder in DOCUMENT_BUILDERS.items():
        print(f"\nGenerating {filename} ...")
        pdf_bytes = builder()
        print(f"  Generated {len(pdf_bytes)} bytes")

        file_path = f"{VOLUME_PATH}/{filename}"
        print(f"  Uploading to {file_path} ...")
        w.files.upload(file_path=file_path, contents=io.BytesIO(pdf_bytes), overwrite=True)
        print(f"  Uploaded successfully.")

    # Verify uploads
    print(f"\nFiles in {VOLUME_PATH}:")
    for entry in w.files.list_directory_contents(VOLUME_PATH):
        print(f"  {entry.name} ({entry.file_size} bytes)")

    print("\nDone! All quality documents generated and uploaded.")


if __name__ == "__main__":
    main()
