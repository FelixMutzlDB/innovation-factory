"""Deploy / verify the yard-pro Mosaic AI Vision endpoint.

In P0 the Vision endpoint itself is out of scope to train — a baseline
plant / lawn / pest classifier needs a real dataset and an MLflow
training run that lives in P3+ engineering. This script is the
deploy / verification shell:

  * If an existing Mosaic AI Model Serving endpoint named
    ``yard-pro-vision-v1`` (or the env-var override) is found and
    READY, print its status + a sample curl so the demo can be
    re-tested.
  * If absent, print an explicit setup-instructions block describing
    the required steps:
      1. Train and register the model in MLflow under
         ``models:/yard_pro_vision``.
      2. Create a CPU or GPU model-serving endpoint using
         ``ws.serving_endpoints.create(...)``.
      3. Re-run this script.

The yard-pro diagnose service (``services/diagnose_service.py``) reads
the endpoint name from ``YARD_PRO_VISION_ENDPOINT``; missing the env
var renders the "Snap-and-diagnose requires configuration" card per
lessons §18 — never a 500.

Apx MCP skill used when available: ``databricks-model-serving``.

CLI:

  python -m scripts.yard_pro.deploy_vision \\
      --workspace-url https://fevm-felix-demo.cloud.databricks.com \\
      --endpoint-name yard-pro-vision-v1
"""
from __future__ import annotations

import argparse
import os
import sys

DEFAULT_ENDPOINT_NAME = os.getenv("YARD_PRO_VISION_ENDPOINT", "yard-pro-vision-v1")


SETUP_INSTRUCTIONS = """
================================================================
yard-pro Vision endpoint NOT FOUND.

This script is a deploy/verification shell — the model itself ships
in the P3+ engineering work, not P0. To stand it up:

  1. Train a baseline plant / lawn / pest classifier offline (any
     framework that MLflow supports — PyTorch, TensorFlow, scikit).
     Recommended starting point: a fine-tuned EfficientNet-B0 on a
     small curated set covering at minimum:

       - apple_scab
       - powdery_mildew
       - fusarium_blight_lawn
       - boxwood_moth (visible webbing / caterpillars)
       - healthy

  2. Register the model in Unity Catalog Model Registry:

         mlflow.set_registry_uri("databricks-uc")
         mlflow.<framework>.log_model(
             model,
             "model",
             registered_model_name="<catalog>.yard_pro.vision",
         )

  3. Create a Mosaic AI Model Serving endpoint, e.g.:

         from databricks.sdk import WorkspaceClient
         from databricks.sdk.service.serving import (
             EndpointCoreConfigInput,
             ServedEntityInput,
         )
         ws = WorkspaceClient()
         ws.serving_endpoints.create(
             name="yard-pro-vision-v1",
             config=EndpointCoreConfigInput(
                 served_entities=[
                     ServedEntityInput(
                         entity_name="<catalog>.yard_pro.vision",
                         entity_version="1",
                         workload_type="CPU",
                         workload_size="Small",
                         scale_to_zero_enabled=True,
                     ),
                 ],
             ),
         )

  4. Set the env var so the app picks it up:

         YARD_PRO_VISION_ENDPOINT=yard-pro-vision-v1

  5. Re-run this script to verify.

In the meantime, the cockpit's snap-and-diagnose card will render the
'Snap-and-diagnose requires configuration' state per lessons §18.
================================================================
"""


def _print_sample_curl(host: str, endpoint_name: str) -> None:
    print(
        "\nSample curl to test the endpoint (substitute IMAGE_BASE64):\n"
        f"  curl -X POST {host}/serving-endpoints/{endpoint_name}/invocations \\\n"
        '       -H "Authorization: Bearer $DATABRICKS_TOKEN" \\\n'
        '       -H "Content-Type: application/json" \\\n'
        '       -d \'{"inputs": [{"image_b64": "IMAGE_BASE64"}]}\''
    )


def verify_vision_endpoint(ws, endpoint_name: str) -> bool:
    """Look up the named serving endpoint. Return True if it exists and
    is READY; False otherwise. Prints status + sample curl."""
    try:
        endpoint = ws.serving_endpoints.get(name=endpoint_name)
    except Exception as exc:  # noqa: BLE001 — SDK raises typed not-found
        msg = str(exc).lower()
        if "not found" in msg or "404" in msg or "does not exist" in msg:
            return False
        raise
    state = (
        endpoint.state.ready.value if endpoint.state and endpoint.state.ready
        else "UNKNOWN"
    )
    print(f"  Endpoint '{endpoint_name}' exists. Readiness: {state}")
    host = ws.config.host.rstrip("/")
    print(f"  URL: {host}/serving-endpoints/{endpoint_name}/invocations")
    _print_sample_curl(host, endpoint_name)
    return state in ("READY", "true", "True")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify the yard-pro Mosaic AI Vision endpoint (P0 shell).",
    )
    parser.add_argument(
        "--endpoint-name", default=DEFAULT_ENDPOINT_NAME,
        help=f"Endpoint name (default: {DEFAULT_ENDPOINT_NAME})",
    )
    parser.add_argument("--workspace-url", default=None)
    parser.add_argument("--profile", default=None)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    from databricks.sdk import WorkspaceClient

    if args.profile:
        ws = WorkspaceClient(profile=args.profile)
    elif args.workspace_url:
        ws = WorkspaceClient(host=args.workspace_url)
    else:
        ws = WorkspaceClient()

    print(f"== yard-pro Vision endpoint check ({args.endpoint_name}) ==")
    print(f"  Workspace: {ws.config.host}")

    ready = verify_vision_endpoint(ws, args.endpoint_name)
    if not ready:
        print(SETUP_INSTRUCTIONS)
        return 1
    print("\n  Status: READY")
    print(f"\n  Set in app.yml / .env:\n    YARD_PRO_VISION_ENDPOINT={args.endpoint_name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
