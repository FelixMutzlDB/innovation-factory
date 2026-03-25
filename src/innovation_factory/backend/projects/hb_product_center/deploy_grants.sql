-- Hugo Boss Product Center: Lakebase PostgreSQL Grants
-- Run this script BEFORE deploying the app to grant the service principal
-- access to all hb_ tables in the public schema.
--
-- Replace <DATABRICKS_CLIENT_ID> with the actual service principal client ID
-- from your Databricks App deployment configuration.
--
-- You can find the client ID in:
--   Databricks Workspace > Compute > Apps > [Your App] > Settings > Service Principal

GRANT SELECT, INSERT, UPDATE, DELETE ON hb_products TO "<DATABRICKS_CLIENT_ID>";
GRANT SELECT, INSERT, UPDATE, DELETE ON hb_product_images TO "<DATABRICKS_CLIENT_ID>";
GRANT SELECT, INSERT, UPDATE, DELETE ON hb_recognition_jobs TO "<DATABRICKS_CLIENT_ID>";
GRANT SELECT, INSERT, UPDATE, DELETE ON hb_recognition_results TO "<DATABRICKS_CLIENT_ID>";
GRANT SELECT, INSERT, UPDATE, DELETE ON hb_quality_inspections TO "<DATABRICKS_CLIENT_ID>";
GRANT SELECT, INSERT, UPDATE, DELETE ON hb_quality_defects TO "<DATABRICKS_CLIENT_ID>";
GRANT SELECT, INSERT, UPDATE, DELETE ON hb_auth_verifications TO "<DATABRICKS_CLIENT_ID>";
GRANT SELECT, INSERT, UPDATE, DELETE ON hb_auth_alerts TO "<DATABRICKS_CLIENT_ID>";
GRANT SELECT, INSERT, UPDATE, DELETE ON hb_supply_chain_events TO "<DATABRICKS_CLIENT_ID>";
GRANT SELECT, INSERT, UPDATE, DELETE ON hb_sustainability_metrics TO "<DATABRICKS_CLIENT_ID>";
GRANT SELECT, INSERT, UPDATE, DELETE ON hb_chat_sessions TO "<DATABRICKS_CLIENT_ID>";
GRANT SELECT, INSERT, UPDATE, DELETE ON hb_chat_messages TO "<DATABRICKS_CLIENT_ID>";

-- Grant USAGE on sequences (needed for auto-increment IDs)
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO "<DATABRICKS_CLIENT_ID>";
