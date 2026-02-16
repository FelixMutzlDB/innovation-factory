# Billing & Reporting Issues — Troubleshooting Runbook

## Overview
This runbook covers billing discrepancies and reporting delays commonly reported by advertisers and internal finance teams.

## Issue: Billing Discrepancy — Overcharge

### Symptoms
- Invoice amount exceeds the agreed campaign budget
- Advertiser reports charges for impressions/clicks not aligned with reporting
- Discrepancy between internal reporting and billing system

### Root Cause Analysis
1. **Rate Card Mismatch**: CPM/CPC rate applied differs from the contract rate
2. **Pacing Overshoot**: Daily spend exceeded budget caps due to aggressive pacing
3. **Duplicate Billing**: Same impressions billed twice due to reconciliation error
4. **Currency Conversion**: Exchange rate differences for international campaigns
5. **Makegood Credits Not Applied**: Previous makegood credits were not deducted

### Resolution Steps
1. Pull the detailed billing report for the campaign period
2. Compare line items against the signed contract/IO (insertion order)
3. Verify the CPM/CPC rates match the agreed rates
4. Check if any pacing overrides were applied
5. Look for duplicate entries in the billing system
6. If discrepancy is confirmed:
   - Issue a credit note for the overage amount
   - Apply the credit to the next invoice or refund
   - Document the root cause for future prevention
7. Notify the account manager and advertiser with the resolution

### SLA
- Billing inquiries must be acknowledged within 1 business day
- Resolution and credit note issued within 5 business days

---

## Issue: Reporting Delay — Metrics Missing

### Symptoms
- Performance dashboard shows gaps in data
- Metrics not updated for 24+ hours
- Advertiser cannot access campaign reports

### Root Cause Analysis
1. **Data Pipeline Failure**: ETL pipeline for aggregating metrics has failed
2. **Publisher Reporting Delay**: Third-party publisher has not sent data
3. **Time Zone Misalignment**: Data for certain time zones not yet processed
4. **System Maintenance**: Scheduled maintenance window caused processing delay
5. **Data Quality Issue**: Invalid data rejected by validation rules

### Resolution Steps
1. Check the data pipeline monitoring dashboard for failures
2. Verify the last successful data refresh timestamp
3. If pipeline failure:
   - Restart the failed pipeline job
   - Monitor for successful completion
   - Backfill any missing data
4. If publisher delay:
   - Contact the publisher's ad ops team
   - Request expedited data delivery
5. Communicate expected resolution time to the advertiser
6. Once data is available, verify completeness by spot-checking key metrics

---

## Issue: Campaign Pacing — Over/Under Delivery

### Symptoms
- Campaign spending significantly faster or slower than planned
- Budget utilization is >110% or <60% of expected at the current date
- Advertiser concerned about budget management

### Root Cause Analysis
1. **Pacing Algorithm Misconfigured**: Even/ASAP pacing not set correctly
2. **Bid Too High/Low**: Bid prices causing over/under win rate
3. **Audience Pool Too Small/Large**: Targeting is too narrow or too broad
4. **Seasonal Traffic Fluctuation**: Organic traffic patterns affect delivery
5. **Competition**: Other campaigns competing for the same inventory

### Resolution Steps
1. Review the pacing settings — switch to "Even" pacing if set to "ASAP"
2. Adjust bid prices:
   - Over-delivery: Lower the bid by 15-20%
   - Under-delivery: Increase the bid by 15-20%
3. Review audience size estimates — expand or narrow targeting
4. Check historical traffic patterns for the current period
5. Set daily budget caps to prevent runaway spending
6. Monitor for 48 hours after adjustments

### Best Practices
- Set up automated pacing alerts at 80% and 110% of expected pace
- Review pacing weekly for campaigns >30 days
- Communicate pacing adjustments to the advertiser proactively
