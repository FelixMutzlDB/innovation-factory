"""Create UC function for product ID and Multi-Agent Supervisor."""
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

SC_GENIE_ID = "01f10dce917e158093ef87c43e5f66f3"
AQ_GENIE_ID = "01f10dcf2ecd1b26a5dd22b98cff8a73"

# Step 1: Create UC function for product identification
print("=== Creating UC Function for Product Identification ===")
create_func_sql = """
CREATE OR REPLACE FUNCTION innovation_factory_catalog.hb_product_center.identify_product(
  image_description STRING COMMENT 'A textual description of the product to identify, including visual features like color, style, material, category'
)
RETURNS TABLE (
  product_id BIGINT,
  sku STRING,
  style_name STRING,
  color STRING,
  category STRING,
  collection STRING,
  material STRING,
  price DOUBLE,
  confidence STRING
)
COMMENT 'Identifies Hugo Boss products based on visual description. Returns matching products from the catalog with confidence levels.'
RETURN
  SELECT
    id as product_id,
    sku,
    style_name,
    color,
    category,
    collection,
    material,
    price,
    CASE
      WHEN LOWER(image_description) LIKE CONCAT('%', LOWER(style_name), '%')
        OR LOWER(image_description) LIKE CONCAT('%', LOWER(category), '%')
      THEN 'high'
      WHEN LOWER(image_description) LIKE CONCAT('%', LOWER(color), '%')
        OR LOWER(image_description) LIKE CONCAT('%', LOWER(material), '%')
      THEN 'medium'
      ELSE 'low'
    END as confidence
  FROM innovation_factory_catalog.hb_product_center.hb_products
  WHERE
    LOWER(image_description) LIKE CONCAT('%', LOWER(style_name), '%')
    OR LOWER(image_description) LIKE CONCAT('%', LOWER(category), '%')
    OR LOWER(image_description) LIKE CONCAT('%', LOWER(color), '%')
    OR LOWER(image_description) LIKE CONCAT('%', LOWER(material), '%')
    OR LOWER(image_description) LIKE CONCAT('%', LOWER(collection), '%')
  ORDER BY
    CASE
      WHEN LOWER(image_description) LIKE CONCAT('%', LOWER(style_name), '%') THEN 1
      WHEN LOWER(image_description) LIKE CONCAT('%', LOWER(category), '%') THEN 2
      WHEN LOWER(image_description) LIKE CONCAT('%', LOWER(color), '%') THEN 3
      ELSE 4
    END
  LIMIT 5
"""

stmt_resp = requests.post(
    f"{HOST}/api/2.0/sql/statements",
    headers=HEADERS,
    json={
        "warehouse_id": WAREHOUSE_ID,
        "statement": create_func_sql,
        "wait_timeout": "30s",
    },
)
print(f"UC Function: {stmt_resp.status_code}")
r = stmt_resp.json()
print(f"  Status: {r.get('status', {}).get('state', 'unknown')}")
if r.get('status', {}).get('state') == 'FAILED':
    print(f"  Error: {r.get('status', {}).get('error', {}).get('message', 'unknown')}")

# Test the function
print("\n=== Testing UC Function ===")
test_resp = requests.post(
    f"{HOST}/api/2.0/sql/statements",
    headers=HEADERS,
    json={
        "warehouse_id": WAREHOUSE_ID,
        "statement": "SELECT * FROM innovation_factory_catalog.hb_product_center.identify_product('dark blue wool suit')",
        "wait_timeout": "30s",
    },
)
test_data = test_resp.json()
print(f"  Test status: {test_data.get('status', {}).get('state', 'unknown')}")
if test_data.get('result', {}).get('data_array'):
    for row in test_data['result']['data_array'][:3]:
        print(f"  -> {row}")

# Step 2: Create the MAS
print("\n=== Creating Multi-Agent Supervisor ===")
mas_body = {
    "display_name": "HB Product Center Intelligence",
    "description": "Hugo Boss Product Center Intelligence Agent - orchestrates supply chain analytics, authenticity & quality insights, and product identification capabilities.",
    "agents": [
        {
            "display_name": "Supply Chain Analyst",
            "description": "Answers questions about supply chain events, logistics, product journeys from manufacturing to retail, sustainability metrics, carbon footprint, water usage, recycled content, compliance status, and partner performance. Use this agent for any supply chain or sustainability related question.",
            "genie_space_id": SC_GENIE_ID,
        },
        {
            "display_name": "Quality & Auth Analyst",
            "description": "Answers questions about product authenticity verifications, counterfeit detection alerts, quality control inspections, defect analysis, manufacturing partner quality scores, verification methods, and brand protection. Use this agent for any quality control or authenticity related question.",
            "genie_space_id": AQ_GENIE_ID,
        },
        {
            "display_name": "Product Identifier",
            "description": "Identifies Hugo Boss products from visual descriptions. Given a description of a product (color, style, material, category), searches the product catalog and returns matching products with confidence levels. Use this agent when the user wants to identify a product or find products matching certain visual features.",
            "uc_function_name": "innovation_factory_catalog.hb_product_center.identify_product",
        },
    ],
    "instructions": "You are the Hugo Boss Product Center Intelligence Assistant. Route supply chain, logistics, and sustainability questions to the Supply Chain Analyst. Route quality control, defect, inspection, and authenticity questions to the Quality & Auth Analyst. Route product identification requests to the Product Identifier. For general questions, use your best judgment on which agent to route to. Always provide clear, professional responses.",
}

mas_resp = requests.post(
    f"{HOST}/api/2.0/agent-bricks/agents",
    headers=HEADERS,
    json=mas_body,
)
if mas_resp.status_code in (200, 201):
    mas_data = mas_resp.json()
    print(f"MAS Created: {mas_data}")
    tile_id = mas_data.get("tile_id", mas_data.get("id", "unknown"))
    endpoint = mas_data.get("endpoint_name", "unknown")
    print(f"  Tile ID: {tile_id}")
    print(f"  Endpoint: {endpoint}")
else:
    print(f"MAS creation via agent-bricks API: {mas_resp.status_code}")
    print(f"  Response: {mas_resp.text[:500]}")
    print("\nTrying alternative endpoint...")
    # Try manage_mas format
    mas_resp2 = requests.post(
        f"{HOST}/api/2.0/serving-endpoints/agent-bricks/supervisors",
        headers=HEADERS,
        json=mas_body,
    )
    print(f"Alternative: {mas_resp2.status_code} {mas_resp2.text[:500]}")
