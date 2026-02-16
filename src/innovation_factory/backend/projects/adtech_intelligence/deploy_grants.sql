-- AdTech Intelligence: Lakebase PostgreSQL Grants
-- Run this script BEFORE deploying the app to grant the service principal
-- access to all at_ tables in the public schema.
--
-- Replace <DATABRICKS_CLIENT_ID> with the actual service principal client ID
-- from your Databricks App deployment configuration.
--
-- You can find the client ID in:
--   Databricks Workspace > Compute > Apps > [Your App] > Settings > Service Principal

GRANT SELECT, INSERT, UPDATE, DELETE ON at_advertisers TO "<DATABRICKS_CLIENT_ID>";
GRANT SELECT, INSERT, UPDATE, DELETE ON at_campaigns TO "<DATABRICKS_CLIENT_ID>";
GRANT SELECT, INSERT, UPDATE, DELETE ON at_ad_inventory TO "<DATABRICKS_CLIENT_ID>";
GRANT SELECT, INSERT, UPDATE, DELETE ON at_placements TO "<DATABRICKS_CLIENT_ID>";
GRANT SELECT, INSERT, UPDATE, DELETE ON at_performance_metrics TO "<DATABRICKS_CLIENT_ID>";
GRANT SELECT, INSERT, UPDATE, DELETE ON at_anomaly_rules TO "<DATABRICKS_CLIENT_ID>";
GRANT SELECT, INSERT, UPDATE, DELETE ON at_anomalies TO "<DATABRICKS_CLIENT_ID>";
GRANT SELECT, INSERT, UPDATE, DELETE ON at_issues TO "<DATABRICKS_CLIENT_ID>";
GRANT SELECT, INSERT, UPDATE, DELETE ON at_customer_contracts TO "<DATABRICKS_CLIENT_ID>";
GRANT SELECT, INSERT, UPDATE, DELETE ON at_chat_sessions TO "<DATABRICKS_CLIENT_ID>";
GRANT SELECT, INSERT, UPDATE, DELETE ON at_chat_messages TO "<DATABRICKS_CLIENT_ID>";

-- Grant USAGE on sequences (needed for auto-increment IDs)
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO "<DATABRICKS_CLIENT_ID>";
