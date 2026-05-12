"""P5 placeholder — yard-pro dealer Genie space provisioning.

The yard-pro dealer panel (UC6) hangs off a Genie space that queries
``yard_pro_gold.dealer_customer_summary`` (plan §5 + §11). Provisioning
that Genie space is P5 work; for P0 the demo is a static screenshot —
no engineered fallback (plan §12 Q9 explicit).

This module ships in P0 as a placeholder so the deploy-script slot is
recognizable from day one and so the script registry in
``scripts/yard_pro/`` reflects the plan's surface area. Re-running
``python -m scripts.yard_pro.deploy_genie_space`` prints a clear
"P5 placeholder" message and exits 0.

When P5 lands, this file's body will create the Genie space against
the gold table, register canary rows in the SQL filter, and write
``YARD_PRO_DEALER_GENIE_SPACE_ID`` to the deploy state.
"""
from __future__ import annotations

import sys


def main() -> int:
    print("================================================================")
    print(" yard-pro: Dealer Genie space provisioning")
    print("================================================================")
    print()
    print(" This is a P5 placeholder. Per plan §12 (Open question Q9),")
    print(" the dealer panel demo at end-of-P0 is a static screenshot;")
    print(" no engineered fallback. The Genie space itself ships in P5")
    print(" once the consent state machine and the anonymization pipeline")
    print(" are production-grade.")
    print()
    print(" When P5 lands, this script will:")
    print("   1. Create a Genie space against")
    print("      yard_pro_gold.dealer_customer_summary in the target")
    print("      catalog (lessons §28 catalog-parameterized).")
    print("   2. Register canary rows in the underlying SQL filter to")
    print("      detect leakage (plan §8 AI security row — Genie / RT-004).")
    print("   3. Print the YARD_PRO_DEALER_GENIE_SPACE_ID env var to")
    print("      paste into app.yml.")
    print()
    print(" For now: no-op exit 0.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
