# Past Incident Reports — Ad Operations

## Incident INC-2025-089: Major DOOH Network Outage — Berlin Region
**Date**: 2025-11-15
**Severity**: Critical
**Duration**: 6 hours
**Affected Campaigns**: 12 campaigns across 8 advertisers

### Summary
A firmware update pushed to all Berlin-region DOOH screens caused a boot loop, rendering 47 screens non-functional. Affected locations included Berlin Hbf, Alexanderplatz Mall, and 15 U-Bahn stations.

### Root Cause
The firmware update (v3.2.1) had an incompatibility with the older media player hardware (Model X200) deployed at Berlin locations. The update was pushed without hardware compatibility verification.

### Resolution
1. Rolled back firmware to v3.1.8 on all affected screens
2. Implemented staged rollout policy — test on 5% of screens before full deployment
3. Created hardware compatibility matrix for all firmware versions

### Makegoods Issued
- Total makegood value: €42,500
- Impressions credited: 2.1M across affected campaigns
- All makegoods processed by 2025-11-22

### Lessons Learned
- Always test firmware updates on a subset of devices first
- Maintain a rollback plan for all infrastructure changes
- Notify affected advertisers within 2 hours of any critical outage

---

## Incident INC-2025-112: Click Fraud Attack — sport1.de Placements
**Date**: 2025-12-03
**Severity**: High
**Duration**: 3 days (until detection)
**Affected Campaigns**: 4 campaigns

### Summary
Automated bot traffic inflated click counts by 800% on sport1.de placements over a weekend. The attack was detected on Monday during routine anomaly review.

### Root Cause
A botnet targeted sport1.de's ad slots, generating fraudulent clicks. The IVT (Invalid Traffic) filter was not configured for the new sport1.de integration.

### Resolution
1. Immediately paused all affected placements
2. Enabled IVT filtering for sport1.de placements
3. Credited advertisers for all fraudulent clicks (€18,200 total)
4. Implemented real-time CTR anomaly alerts (>3x baseline = auto-pause)

### Prevention Measures Implemented
- IVT filtering enabled by default on all new publisher integrations
- Real-time anomaly detection for CTR spikes >200% above baseline
- Weekly review of click patterns across all publishers

---

## Incident INC-2026-015: Billing System Reconciliation Error
**Date**: 2026-01-10
**Severity**: Medium
**Duration**: 5 business days
**Affected Campaigns**: 23 campaigns across 11 advertisers

### Summary
January invoices contained incorrect amounts due to a timezone handling bug in the billing reconciliation pipeline. European campaigns were billed for an extra day (January 1 counted twice).

### Root Cause
A recent code change to handle New Year's Day timezone transitions introduced a bug where UTC+1 dates were processed twice — once as December 31 UTC and once as January 1 CET.

### Resolution
1. Fixed the timezone handling in the reconciliation pipeline
2. Regenerated all January invoices
3. Sent corrected invoices to all affected advertisers with an explanation
4. Added timezone-aware unit tests to the billing pipeline

### Financial Impact
- Total overbilling: €67,400 across 23 campaigns
- All credits issued by January 15
- No advertiser churn resulted from this incident

---

## Incident INC-2026-028: Creative Serving Wrong Version
**Date**: 2026-01-28
**Severity**: Medium
**Duration**: 12 hours
**Affected Campaigns**: 2 campaigns (StyleHaus Mode, DigiMedia Verlag)

### Summary
Two campaigns were serving outdated creative versions after a CDN cache purge failure. Advertisers noticed their old branding was being displayed.

### Root Cause
The CDN cache purge for creative assets was timing out silently. The system reported success but the old assets remained cached at edge nodes.

### Resolution
1. Manually purged CDN caches for affected creative assets
2. Verified correct creative serving on all target publishers
3. Implemented CDN purge verification — check asset hash after purge
4. Added monitoring for CDN purge success/failure rates

---

## Incident INC-2026-041: Performance Data Loss — 4 Hour Window
**Date**: 2026-02-06
**Severity**: High
**Duration**: 4 hours of data loss
**Affected Campaigns**: All active campaigns

### Summary
The real-time metrics pipeline lost 4 hours of performance data (06:00-10:00 CET) due to a Kafka consumer group rebalancing storm triggered by a deployment.

### Root Cause
A rolling deployment of the metrics consumer service triggered excessive consumer group rebalances, causing messages to expire from the Kafka retention window before being processed.

### Resolution
1. Backfilled missing data from publisher raw logs
2. Extended Kafka retention from 6 hours to 24 hours
3. Implemented graceful shutdown for consumer service during deployments
4. Added Kafka consumer lag monitoring with alerts at >1 hour lag

### Data Recovery
- 97% of data recovered from publisher raw logs
- 3% estimated from interpolation of surrounding time periods
- All campaign reports updated by 2026-02-07
