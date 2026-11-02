"""Small, static source fixtures for Task 2.03 graph expectations."""

REPOSITORY = "fixture-repository"
REVISION = "a" * 40

SOURCES = {
    "pkg/__init__.py": "",
    "pkg/models.py": "class User:\n    pass\n",
    "pkg/service.py": (
        "from .models import User\n"
        "from . import models\n"
        "import pkg.models\n"
        "from .missing import Missing\n"
        "from pkg.models import *\n"
        "import external_package\n"
        "import importlib\n"
        "module = importlib.import_module('pkg.dynamic')\n"
    ),
}

EXPECTED_SUPPORTED_EDGES = (
    ("pkg/service.py", "pkg/models.py", "absolute_import"),
    ("pkg/service.py", "pkg/models.py", "relative_import"),
)

EXPECTED_UNRESOLVED = {
    ("pkg/service.py", "pkg.missing", "relative_import"),
    ("pkg/service.py", "pkg.models", "star_import"),
    ("pkg/service.py", "external_package", "absolute_import"),
    ("pkg/service.py", "importlib", "absolute_import"),
    ("pkg/service.py", "pkg.dynamic", "dynamic_import"),
}
