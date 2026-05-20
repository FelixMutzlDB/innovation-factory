"""yard-pro accelerator package.

Importing the package registers the ``yp_*`` SQLModel tables with
``SQLModel.metadata`` so ``Runtime.initialize_models()`` creates them at
app startup. The router-aggregator import path (``backend/router.py``)
loads this package, so registration happens whether or not the seed runs.
"""
from . import models  # noqa: F401 — side-effect: register yp_* with SQLModel metadata
