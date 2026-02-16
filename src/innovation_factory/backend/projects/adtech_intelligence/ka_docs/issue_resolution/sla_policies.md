# Service Level Agreements & Operational Policies

## SLA Tiers by Advertiser Budget Level

### Enterprise (Budget > €500K/year)
- **Dedicated Account Manager**: Assigned point of contact
- **Issue Response Time**: 2 hours during business hours, 4 hours off-hours
- **Resolution Time**: 24 hours for critical, 48 hours for high, 5 days for medium/low
- **Reporting**: Daily automated reports + weekly review call
- **Makegood Policy**: 120% of lost impressions credited
- **Campaign Launch SLA**: Campaign goes live within 24 hours of creative approval

### Premium (Budget €150K–€500K/year)
- **Dedicated Account Manager**: Shared across 3-5 accounts
- **Issue Response Time**: 4 hours during business hours
- **Resolution Time**: 48 hours for critical, 72 hours for high, 7 days for medium/low
- **Reporting**: Weekly automated reports + bi-weekly review call
- **Makegood Policy**: 110% of lost impressions credited
- **Campaign Launch SLA**: Campaign goes live within 48 hours of creative approval

### Standard (Budget < €150K/year)
- **Account Management**: Pool-based support
- **Issue Response Time**: 8 hours during business hours
- **Resolution Time**: 72 hours for critical, 5 days for high, 10 days for medium/low
- **Reporting**: Weekly automated reports
- **Makegood Policy**: 100% of lost impressions credited
- **Campaign Launch SLA**: Campaign goes live within 72 hours of creative approval

---

## Escalation Matrix

| Level | Trigger | Responder | Time to Escalate |
|-------|---------|-----------|------------------|
| L1 | Initial ticket | Ad Ops Associate | N/A (starts here) |
| L2 | No resolution in SLA | Senior Ad Ops | After SLA breach |
| L3 | Revenue impact > €5K | Ad Ops Manager | After 4 hours at L2 |
| L4 | Revenue impact > €50K or client escalation | VP of Ad Operations | After 2 hours at L3 |
| L5 | Systemic outage | CTO + VP Ad Ops | Immediately for critical outages |

---

## Makegood Calculation Policy

### Formula
```
Makegood Credits = Lost Impressions × CPM Rate × Makegood Multiplier
```

### Makegood Multiplier by Cause
| Cause | Multiplier |
|-------|-----------|
| Our System Failure | 1.2x |
| Publisher Issue | 1.0x |
| Third-Party Issue | 0.8x |
| Force Majeure | 0.5x |

### Process
1. Calculate lost impressions from the reporting system
2. Apply the appropriate multiplier based on root cause
3. Generate makegood order in the ad server
4. Notify the advertiser with breakdown
5. Track delivery of makegood impressions
6. Close the makegood case when fully delivered

---

## Creative Specifications

### Online Formats
| Format | Dimensions | Max File Size | Accepted Types | Animation |
|--------|-----------|---------------|----------------|-----------|
| Display Banner (Standard) | 300×250, 728×90, 160×600 | 150 KB | JPG, PNG, GIF, HTML5 | Max 30s |
| Display Banner (Large) | 300×600, 970×250 | 200 KB | JPG, PNG, GIF, HTML5 | Max 30s |
| Video Pre-Roll | 16:9, min 640×360 | 20 MB | MP4, WebM | 15s or 30s |
| Native Content | Varies by publisher | 5 MB | JPG, PNG + Text | Static |
| High Impact | Publisher-specific | 500 KB | HTML5, Video | Max 30s |

### OOH Formats
| Format | Resolution | Aspect Ratio | File Type | Duration |
|--------|-----------|-------------|-----------|----------|
| DOOH Screen (Landscape) | 1920×1080 | 16:9 | MP4, JPG | 10s or 15s |
| DOOH Screen (Portrait) | 1080×1920 | 9:16 | MP4, JPG | 10s or 15s |
| City Light Poster | 1195×1750 mm | 4:5.86 | PDF, TIFF | Static |
| Mega Poster | Custom | Custom | PDF, TIFF | Static |
| Billboard | 4×3 m standard | 4:3 | PDF, TIFF | Static |

---

## Data Retention Policy

| Data Type | Retention Period | Archive Policy |
|-----------|-----------------|----------------|
| Campaign Performance Metrics | 2 years (hot) | 5 years (cold storage) |
| Ad Server Logs | 90 days (hot) | 1 year (cold storage) |
| Billing Records | 7 years | Per German tax law |
| Support Tickets | 3 years | Per DSGVO requirements |
| Creative Assets | 1 year after campaign end | Purged after 1 year |
| User Behavioral Data | 30 days | Deleted per DSGVO |
