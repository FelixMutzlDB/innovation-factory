"""Create AI/BI Dashboards for HB Product Center."""
import json
import subprocess
import requests


def get_token():
    result = subprocess.run(
        ["databricks", "auth", "token", "--profile", "e2-demo-field-eng"],
        capture_output=True, text=True,
    )
    return json.loads(result.stdout)["access_token"]


HOST = "https://e2-demo-field-eng.cloud.databricks.com"
TOKEN = get_token()
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
WAREHOUSE_ID = "862f1d757f0424f7"
PARENT = "/Workspace/Users/felix.mutzl@databricks.com"


def counter(name, dataset, expr, display, title, x, y, w=2, h=3):
    return {
        "widget": {
            "name": name,
            "queries": [{"name": "main_query", "query": {"datasetName": dataset, "fields": [{"name": expr, "expression": expr}], "disaggregated": False}}],
            "spec": {"version": 2, "widgetType": "counter", "encodings": {"value": {"fieldName": expr, "displayName": display}}},
        },
        "position": {"x": x, "y": y, "width": w, "height": h},
    }


def bar(name, dataset, x_field, x_expr, y_field, y_expr, title, x, y, w=3, h=5):
    return {
        "widget": {
            "name": name,
            "queries": [{"name": "main_query", "query": {"datasetName": dataset, "fields": [{"name": x_field, "expression": x_expr}, {"name": y_field, "expression": y_expr}], "disaggregated": False}}],
            "spec": {"version": 3, "widgetType": "bar", "encodings": {"x": {"fieldName": x_field, "scale": {"type": "categorical"}, "displayName": title.split(" by ")[-1] if " by " in title else x_field}, "y": {"fieldName": y_field, "scale": {"type": "quantitative"}, "displayName": "Count"}}},
        },
        "position": {"x": x, "y": y, "width": w, "height": h},
    }


def pie(name, dataset, color_field, color_expr, angle_field, angle_expr, title, x, y, w=3, h=5):
    return {
        "widget": {
            "name": name,
            "queries": [{"name": "main_query", "query": {"datasetName": dataset, "fields": [{"name": color_field, "expression": color_expr}, {"name": angle_field, "expression": angle_expr}], "disaggregated": False}}],
            "spec": {"version": 3, "widgetType": "pie", "encodings": {"angle": {"fieldName": angle_field, "displayName": "Count"}, "color": {"fieldName": color_field, "scale": {"type": "categorical"}, "displayName": title}}},
        },
        "position": {"x": x, "y": y, "width": w, "height": h},
    }


def table_w(name, dataset, columns, x, y, w=6, h=6):
    fields = [{"name": c[0], "expression": f"`{c[0]}`"} for c in columns]
    cols = [{"fieldName": c[0], "displayName": c[1]} for c in columns]
    return {
        "widget": {
            "name": name,
            "queries": [{"name": "main_query", "query": {"datasetName": dataset, "fields": fields, "disaggregated": True}}],
            "spec": {"version": 2, "widgetType": "table", "encodings": {"columns": cols}},
        },
        "position": {"x": x, "y": y, "width": w, "height": h},
    }


SC = "innovation_factory_catalog.hb_product_center"

SUPPLY_CHAIN_DASHBOARD = {
    "pages": [
        {
            "name": "sc_overview",
            "displayName": "Supply Chain Overview",
            "layout": [
                counter("ctr-events", "ds_sc_events", "COUNT(`id`)", "Total Events", "Total Events", 0, 0),
                counter("ctr-countries", "ds_sc_events", "COUNT(DISTINCT `country`)", "Countries", "Countries", 2, 0),
                counter("ctr-partners", "ds_sc_events", "COUNT(DISTINCT `partner_name`)", "Partners", "Partners", 4, 0),
                bar("bar-by-type", "ds_sc_events", "event_type", "`event_type`", "COUNT(id)", "COUNT(`id`)", "Events by Type", 0, 3),
                bar("bar-by-country", "ds_sc_events", "country", "`country`", "COUNT(id)", "COUNT(`id`)", "Events by Country", 3, 3),
                bar("bar-timeline", "ds_sc_events", "month", "DATE_TRUNC(\"MONTH\", `event_date`)", "COUNT(id)", "COUNT(`id`)", "Events Over Time", 0, 8, w=6),
                table_w("tbl-partners", "ds_top_partners", [("partner_name", "Partner"), ("event_count", "Events"), ("countries", "Countries")], 0, 13),
            ],
        },
        {
            "name": "sustainability",
            "displayName": "Sustainability",
            "layout": [
                counter("ctr-carbon", "ds_sustainability", "AVG(`carbon_footprint_kg`)", "Avg Carbon (kg)", "Avg Carbon", 0, 0),
                counter("ctr-recycled", "ds_sustainability", "AVG(`recycled_content_pct`)", "Avg Recycled %", "Avg Recycled", 2, 0),
                counter("ctr-compliant", "ds_sustainability", "SUM(CASE WHEN `compliance_status` = 'compliant' THEN 1 ELSE 0 END)", "Compliant", "Compliant", 4, 0),
                bar("bar-carbon-cat", "ds_sustainability", "category", "`category`", "AVG(carbon_footprint_kg)", "AVG(`carbon_footprint_kg`)", "Carbon by Category", 0, 3),
                pie("pie-compliance", "ds_sustainability", "compliance_status", "`compliance_status`", "COUNT(id)", "COUNT(`id`)", "Compliance Status", 3, 3),
            ],
        },
    ],
    "datasets": [
        {"name": "ds_sc_events", "displayName": "Supply Chain Events", "query": f"SELECT * FROM {SC}.hb_supply_chain_events"},
        {"name": "ds_sustainability", "displayName": "Sustainability", "query": f"SELECT s.*, p.category, p.style_name FROM {SC}.hb_sustainability_metrics s JOIN {SC}.hb_products p ON s.product_id = p.id"},
        {"name": "ds_top_partners", "displayName": "Top Partners", "query": f"SELECT partner_name, COUNT(*) as event_count, COUNT(DISTINCT country) as countries FROM {SC}.hb_supply_chain_events GROUP BY partner_name ORDER BY event_count DESC LIMIT 15"},
    ],
}

AUTH_QUALITY_DASHBOARD = {
    "pages": [
        {
            "name": "authenticity",
            "displayName": "Authenticity",
            "layout": [
                counter("ctr-verifications", "ds_auth", "COUNT(`id`)", "Total Verifications", "Verifications", 0, 0),
                counter("ctr-verified", "ds_auth", "SUM(CASE WHEN `status` = 'verified' THEN 1 ELSE 0 END)", "Verified", "Verified", 2, 0),
                counter("ctr-alerts", "ds_alerts", "COUNT(`id`)", "Alerts", "Alerts", 4, 0),
                pie("pie-auth-status", "ds_auth", "status", "`status`", "COUNT(id)", "COUNT(`id`)", "Verification Status", 0, 3),
                bar("bar-auth-region", "ds_auth", "region", "`region`", "COUNT(id)", "COUNT(`id`)", "Verifications by Region", 3, 3),
                bar("bar-auth-method", "ds_auth", "verification_method", "`verification_method`", "COUNT(id)", "COUNT(`id`)", "Verification Methods", 0, 8, w=6),
            ],
        },
        {
            "name": "quality",
            "displayName": "Quality Control",
            "layout": [
                counter("ctr-inspections", "ds_inspections", "COUNT(`id`)", "Inspections", "Inspections", 0, 0),
                counter("ctr-avg-score", "ds_inspections", "AVG(`overall_score`)", "Avg Score", "Avg Score", 2, 0),
                counter("ctr-defects", "ds_defects", "COUNT(`id`)", "Defects", "Defects", 4, 0),
                pie("pie-insp-status", "ds_inspections", "status", "`status`", "COUNT(id)", "COUNT(`id`)", "Inspection Status", 0, 3),
                bar("bar-defect-type", "ds_defects", "defect_type", "`defect_type`", "COUNT(id)", "COUNT(`id`)", "Defects by Type", 3, 3),
                bar("bar-partner-quality", "ds_inspections", "manufacturing_partner", "`manufacturing_partner`", "AVG(overall_score)", "AVG(`overall_score`)", "Quality by Partner", 0, 8),
                pie("pie-defect-severity", "ds_defects", "severity", "`severity`", "COUNT(id)", "COUNT(`id`)", "Defect Severity", 3, 8),
            ],
        },
    ],
    "datasets": [
        {"name": "ds_auth", "displayName": "Auth Verifications", "query": f"SELECT * FROM {SC}.hb_auth_verifications"},
        {"name": "ds_alerts", "displayName": "Auth Alerts", "query": f"SELECT * FROM {SC}.hb_auth_alerts"},
        {"name": "ds_inspections", "displayName": "Quality Inspections", "query": f"SELECT * FROM {SC}.hb_quality_inspections"},
        {"name": "ds_defects", "displayName": "Quality Defects", "query": f"SELECT * FROM {SC}.hb_quality_defects"},
    ],
}


def create_and_publish(name, dashboard_json):
    serialized = json.dumps(dashboard_json)
    body = {"display_name": name, "parent_path": PARENT, "serialized_dashboard": serialized, "warehouse_id": WAREHOUSE_ID}
    resp = requests.post(f"{HOST}/api/2.0/lakeview/dashboards", headers=HEADERS, json=body)
    if resp.status_code != 200:
        print(f"FAIL {name}: {resp.status_code} {resp.text[:500]}")
        return None
    did = resp.json()["dashboard_id"]
    print(f"Created: {name} -> {did}")
    pub = requests.post(f"{HOST}/api/2.0/lakeview/dashboards/{did}/published", headers=HEADERS, json={"warehouse_id": WAREHOUSE_ID, "embed_credentials": True})
    if pub.status_code in (200, 201):
        print(f"Published: {did}")
    else:
        print(f"Publish warning: {pub.status_code} {pub.text[:200]}")
    return did


if __name__ == "__main__":
    sc_id = create_and_publish("HB Supply Chain Intelligence", SUPPLY_CHAIN_DASHBOARD)
    aq_id = create_and_publish("HB Authenticity & Quality Control", AUTH_QUALITY_DASHBOARD)
    print(f"\n=== RESULTS ===")
    print(f"HB_SC_DASHBOARD_ID={sc_id}")
    print(f"HB_AQ_DASHBOARD_ID={aq_id}")
    print(f"SC embed: {HOST}/embed/dashboardsv3/{sc_id}")
    print(f"AQ embed: {HOST}/embed/dashboardsv3/{aq_id}")
