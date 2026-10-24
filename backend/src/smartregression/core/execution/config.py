"""Host-controlled configuration for the explicitly requested G1 fixture worker."""

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from typing import ClassVar

from smartregression.core.git.changes import validate_path


@dataclass(frozen=True)
class ExecutionConfig:
    framework: str = "pytest"
    test_paths: tuple[str, ...] = ("tests",)
    approved_args: tuple[str, ...] = ("-q",)
    timeout_seconds: float = 30
    cpu_count: float = 1
    memory_mib: int = 256
    output_bytes: int = 65536
    command: ClassVar[tuple[str, ...]] = ("python", "-m", "pytest")

    def __post_init__(self) -> None:
        caps = {
            "timeout_seconds": 300,
            "cpu_count": 4,
            "memory_mib": 4096,
            "output_bytes": 1024 * 1024,
        }
        for name, cap in caps.items():
            value = getattr(self, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or not 0 < value <= cap
            ):
                raise ValueError("invalid_resource_limit")
        if type(self.memory_mib) is not int or type(self.output_bytes) is not int:
            raise ValueError("integer_resource_limit_required")
        if self.framework != "pytest" or not self.test_paths:
            raise ValueError("unsupported_framework_or_paths")
        for path in self.test_paths:
            validate_path(path)
        if any(arg not in {"-q", "--strict-markers"} for arg in self.approved_args):
            raise ValueError("unapproved_argument")

    @property
    def fingerprint(self) -> str:
        return hashlib.sha256(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()
