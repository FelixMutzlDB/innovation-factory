# Ad Delivery Issues — Troubleshooting Runbook

## Overview
This runbook covers the most common ad delivery issues and their resolution steps. It is intended for Ad Operations teams handling support tickets.

## Issue: Ad Not Displaying (Blank Slot)

### Symptoms
- Ad slot appears blank or shows a default fallback
- Impression count is zero for the affected placement
- Advertiser reports missing ad on specific publisher

### Root Cause Analysis
1. **Ad Tag Malformation**: Check if the ad tag (JavaScript/iframe) is correctly formatted
2. **Creative Not Approved**: Verify the creative has passed platform review
3. **Targeting Mismatch**: The user viewing the page may not match targeting criteria
4. **Frequency Cap Reached**: The user may have already seen the ad the maximum number of times
5. **Budget Exhausted**: Daily or lifetime budget may have been consumed

### Resolution Steps
1. Open the campaign in the ad server and verify the creative status
2. Check the ad tag implementation on the publisher's page (use browser developer tools)
3. Review targeting settings — ensure geographic and demographic parameters are correct
4. Inspect frequency capping rules
5. Verify budget allocation and pacing settings
6. If the issue persists, regenerate the ad tag and ask the publisher to update

### Prevention
- Always validate ad tags in a staging environment before going live
- Set up automated alerts for zero-impression placements
- Maintain a creative approval checklist

---

## Issue: DOOH Screen Offline

### Symptoms
- Physical digital out-of-home screen is not displaying ads
- Screen shows error message, blank screen, or is powered off
- No impression data being recorded for the location

### Root Cause Analysis
1. **Hardware Failure**: Screen, media player, or power supply malfunction
2. **Network Connectivity**: Internet connection to the screen is down
3. **Content Management System (CMS) Error**: CMS cannot push content to the screen
4. **Scheduled Maintenance**: Screen may be undergoing planned maintenance
5. **Weather Damage**: Outdoor screens may be affected by extreme weather

### Resolution Steps
1. Check the screen management dashboard for device status
2. Contact the local maintenance team for physical inspection
3. Verify network connectivity at the location
4. Restart the media player remotely if possible
5. Check if content is queued in the CMS
6. If hardware replacement is needed, estimate downtime and notify affected campaigns
7. Allocate makegoods to compensate for lost impressions

### SLA Requirements
- Critical locations (Hauptbahnhof, airports): 4-hour response time
- Standard locations: 24-hour response time
- Makegoods must be processed within 5 business days

---

## Issue: Click Tracking Not Working

### Symptoms
- Click count is zero despite visible ad impressions
- CTR appears as 0.00% for placements that historically have clicks
- Advertiser's analytics show traffic but our system does not

### Root Cause Analysis
1. **Tracking Pixel Broken**: The click-tracking URL returns 404 or 500
2. **HTTPS/HTTP Mismatch**: Click tracker is HTTP but the page is HTTPS (mixed content blocked)
3. **Ad Blocker**: User's browser is blocking the tracking call
4. **Redirect Chain Too Long**: Too many redirects before reaching the landing page
5. **Domain Blocklisted**: Click tracking domain is on a browser blocklist

### Resolution Steps
1. Test the click-tracking URL manually in a browser
2. Verify SSL certificates on the tracking domain
3. Check for redirect chains — consolidate to a single redirect
4. Update the tracking URL to use HTTPS
5. Validate that the landing page is accessible
6. Re-deploy the tracking pixel and verify in QA

---

## Issue: Low Viewability

### Symptoms
- Viewability rate consistently below 50% (industry standard target)
- Advertiser complaints about ad quality
- High impression count but low engagement

### Root Cause Analysis
1. **Below-the-Fold Placement**: Ad is placed too low on the page
2. **Fast Scroll Behavior**: Users scroll past the ad before it loads
3. **Small Ad Size**: Smaller formats have inherently lower viewability
4. **Page Load Speed**: Slow page load means the ad is never seen
5. **Bot Traffic**: Automated traffic inflates impressions without views

### Resolution Steps
1. Move the placement to above-the-fold position
2. Switch to viewability-optimized bidding strategy
3. Consider larger ad formats (300x600 instead of 300x250)
4. Blacklist domains with consistently low viewability (<30%)
5. Enable IVT (Invalid Traffic) filtering
6. Test lazy loading — only load the ad when the slot is in viewport

---

## Issue: Incorrect Targeting

### Symptoms
- Ads appearing in unintended geographic regions
- Audience demographics don't match campaign settings
- Advertiser receives complaints from users who shouldn't see the ad

### Root Cause Analysis
1. **IP Geolocation Inaccuracy**: VPN or proxy usage masks the user's true location
2. **Misconfigured Region Settings**: Incorrect region codes or city names in campaign setup
3. **Inherited Settings**: Campaign inherited targeting from a template incorrectly
4. **Publisher Data Pass-Through**: Publisher sends incorrect user metadata

### Resolution Steps
1. Review and verify all targeting parameters in the campaign settings
2. Cross-reference region codes with the official geolocation database
3. Check if the campaign was cloned from another — reset inherited settings
4. Contact the publisher to verify metadata pass-through
5. Add negative targeting to explicitly exclude unintended regions
6. Monitor for 24 hours after the fix to confirm correct delivery
