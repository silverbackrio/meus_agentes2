"""Django settings modular: base + dev + prod.

Exporte DJANGO_ENV=prod para produção, omita para dev.
"""

import os

ENVIRONMENT = os.environ.get("DJANGO_ENV", "dev")

if ENVIRONMENT == "prod":
    from .prod import *
elif ENVIRONMENT == "dev":
    from .dev import *
else:
    from .base import *
    from .dev import *
