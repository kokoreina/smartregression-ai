"""Public repository recovery codes only; unknown driver/source text never escapes."""

SAFE_REPOSITORY_ERRORS = frozenset(
    {
        "github_rate_limit",
        "github_timeout",
        "github_unavailable",
        "github_repository_or_commit_not_found",
        "github_redirect_rejected",
        "repository_limit",
        "repository_tree_limit",
        "repository_tree_incomplete",
        "snapshot_limit",
        "snapshot_mismatch",
        "invalid_commit",
        "public_github_repository_required",
    }
)


def public_repository_error(error: Exception, fallback: str) -> str:
    code = str(error) if isinstance(error, ValueError) else ""
    return code if code in SAFE_REPOSITORY_ERRORS else fallback
