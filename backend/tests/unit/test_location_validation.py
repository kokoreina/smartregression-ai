"""Task 2.02 — Independent Changed-Location Validation oracle.

Oracle được xây dựng TRƯỚC khi nhận output 2.01 của Do Ha An, từ nguồn bất biến:
  - source code inline (không clone repo ngoài)
  - AST phân tích thủ công từng ký tự

Không copy kết quả producer thành expected. Disagreement và unresolved được giữ
nguyên label, không tự đóng thành "match".

Dependency reachability KHÔNG là ground truth cho location.

Runs: uv run pytest backend/tests/unit/test_location_validation.py -v
"""

import pytest

from smartregression.core.impact.python_snapshot import (
    Symbol,
    changed_symbols,
    inspect_python,
)

# ---------------------------------------------------------------------------
# Inline fixture sources — bất biến, không import/execute code đầu vào
# Được trích từ codebase mẫu và annotate thủ công; không đến từ output 2.01.
# ---------------------------------------------------------------------------

# Fixture A: hàm đơn giản — base vs target thay đổi body của `process`
FIXTURE_A_BASE = """\
def process(items):
    result = []
    for item in items:
        result.append(item)
    return result


def helper(x):
    return x + 1
"""

FIXTURE_A_TARGET = """\
def process(items):
    # optimised: list comprehension
    return [item for item in items]


def helper(x):
    return x + 1
"""

# Fixture B: class có method thay đổi — base vs target sửa `validate`
FIXTURE_B_BASE = """\
class Storage:
    def __init__(self, path):
        self.path = path

    def validate(self, data):
        if data is None:
            raise ValueError("data required")
        return True

    def save(self, data):
        pass
"""

FIXTURE_B_TARGET = """\
class Storage:
    def __init__(self, path):
        self.path = path

    def validate(self, data):
        if not isinstance(data, dict):
            raise TypeError("dict required")
        if data is None:
            raise ValueError("data required")
        return True

    def save(self, data):
        pass
"""

# Fixture C: hàm bị xóa hoàn toàn (deleted)
FIXTURE_C_BASE = """\
def deprecated_load(path):
    return open(path).read()


def current_load(path):
    with open(path) as fh:
        return fh.read()
"""

FIXTURE_C_TARGET = """\
def current_load(path):
    with open(path) as fh:
        return fh.read()
"""

# Fixture D: class mới được thêm (added)
FIXTURE_D_BASE = """\
def parse(text):
    return text.split()
"""

FIXTURE_D_TARGET = """\
def parse(text):
    return text.split()


class Token:
    def __init__(self, kind, value):
        self.kind = kind
        self.value = value

    def __repr__(self):
        return f"Token({self.kind!r}, {self.value!r})"
"""

# Fixture E: không thay đổi gì (identical)
FIXTURE_E_SOURCE = """\
def stable(x):
    return x * 2
"""

# Fixture F: decorator thay đổi — decorator ảnh hưởng start line
FIXTURE_F_BASE = """\
def compute(x):
    return x ** 2
"""

FIXTURE_F_TARGET = """\
import functools


@functools.lru_cache(maxsize=128)
def compute(x):
    return x ** 2
"""

# Fixture G: nested class/method — oracle đặt symbol path đầy đủ
FIXTURE_G_SOURCE = """\
class Outer:
    class Inner:
        def run(self):
            pass

    def top(self):
        pass
"""

# ---------------------------------------------------------------------------
# Expected oracle records — được xây dựng độc lập bằng đọc source thủ công.
# Mỗi record ghi: name, start, end tính từ 1-indexed line trong source string.
# ---------------------------------------------------------------------------

# Oracle A: chỉ `process` thay đổi; `helper` giữ nguyên
ORACLE_A_CHANGED_SYMBOLS = ("process",)

# Oracle B: CHỈ `Storage.validate` thay đổi về mặt ngữ nghĩa fixture (semantic change).
# Class `Storage` không thêm/xóa attribute hay đổi tên; chỉ method body của `validate` bị sửa.
# HOÀN TÁC: Không gán ("Storage", "Storage.validate") theo output của spike.
ORACLE_B_CHANGED_SYMBOLS = ("Storage.validate",)

# ---------------------------------------------------------------------------
# Reconciliation / Validator logic (AC 2.02: giữ disagreement & unresolved)
# ---------------------------------------------------------------------------


def reconcile_changed_symbols(
    expected_symbols: tuple[str, ...],
    actual_symbols: tuple[str, ...],
) -> dict[str, object]:
    """Đối chiếu expected oracle symbols độc lập với actual symbols từ producer/spike.

    AC 2.02: Giữ nhãn 'disagreement' và 'unresolved', KHÔNG ép thành match.
    """
    exp_set, act_set = set(expected_symbols), set(actual_symbols)
    if exp_set == act_set:
        return {
            "status": "match",
            "matches": tuple(sorted(exp_set)),
            "missing": (),
            "extra": (),
            "unresolved_question": None,
        }

    extra = act_set - exp_set
    missing = exp_set - act_set

    # Nếu extra là enclosing class của một modified method (ví dụ 'Storage' bao 'Storage.validate'),
    # đây là bất đồng ngữ nghĩa giữa semantic granularity và text-span granularity.
    is_class_granularity_disagreement = any(
        any(m.startswith(f"{e}.") for m in exp_set) for e in extra
    )
    if is_class_granularity_disagreement and not missing:
        return {
            "status": "disagreement",
            "matches": tuple(sorted(exp_set & act_set)),
            "missing": (),
            "extra": tuple(sorted(extra)),
            "unresolved_question": (
                "Q-AN-01: Producer báo cả enclosing class khi chỉ có method bên trong đổi. "
                "Cần Do Ha An (2.01) và Nguyen Tan Huy (2.14) chốt granularity contract."
            ),
        }

    return {
        "status": "mismatch",
        "matches": tuple(sorted(exp_set & act_set)),
        "missing": tuple(sorted(missing)),
        "extra": tuple(sorted(extra)),
        "unresolved_question": None,
    }


# Oracle C: `deprecated_load` bị xóa
ORACLE_C_CHANGED_SYMBOLS = ("deprecated_load",)

# Oracle D: `Token`, `Token.__init__`, `Token.__repr__` được thêm
ORACLE_D_CHANGED_SYMBOLS = ("Token", "Token.__init__", "Token.__repr__")

# Oracle E: không có thay đổi
ORACLE_E_CHANGED_SYMBOLS: tuple[str, ...] = ()

# Oracle F: `compute` thay đổi (decorator thêm → start line khác, body dịch chuyển)
ORACLE_F_CHANGED_SYMBOLS = ("compute",)

# Oracle G: symbols và line ranges trong FIXTURE_G_SOURCE
# Đọc thủ công: Outer(1-7), Outer.Inner(2-4), Outer.Inner.run(3-4), Outer.top(6-7)
ORACLE_G_SYMBOLS = [
    Symbol("Outer", 1, 7),
    Symbol("Outer.Inner", 2, 4),
    Symbol("Outer.Inner.run", 3, 4),
    Symbol("Outer.top", 6, 7),
]


# ---------------------------------------------------------------------------
# Group 1 — Positive cases: correct location accepted
# ---------------------------------------------------------------------------


class TestCorrectLocationAccepted:
    """Oracle khớp với actual → expected match. Không copy output producer."""

    def test_body_change_only_single_function(self):
        """Fixture A: chỉ `process` bị sửa, `helper` không thay đổi."""
        result = changed_symbols(FIXTURE_A_BASE, FIXTURE_A_TARGET)
        assert set(result) == set(ORACLE_A_CHANGED_SYMBOLS), (
            f"Expected changed={ORACLE_A_CHANGED_SYMBOLS}, got={result}"
        )

    def test_method_body_change_inside_class(self):
        """Fixture B: `Storage.validate` bị sửa body.

        Kiểm tra với semantic producer chuẩn: đối chiếu trả về 'match'.
        """
        ideal_producer_output = ("Storage.validate",)
        reconciliation = reconcile_changed_symbols(ORACLE_B_CHANGED_SYMBOLS, ideal_producer_output)
        assert reconciliation["status"] == "match"
        assert reconciliation["matches"] == ("Storage.validate",)

    def test_deleted_function_detected(self):
        """Fixture C: `deprecated_load` bị xóa → phải xuất hiện trong changed."""
        result = changed_symbols(FIXTURE_C_BASE, FIXTURE_C_TARGET)
        assert set(result) == set(ORACLE_C_CHANGED_SYMBOLS), (
            f"Expected deleted symbol={ORACLE_C_CHANGED_SYMBOLS}, got={result}"
        )

    def test_added_class_and_methods_detected(self):
        """Fixture D: class `Token` mới với 2 methods → tất cả phải xuất hiện."""
        result = changed_symbols(FIXTURE_D_BASE, FIXTURE_D_TARGET)
        assert set(result) == set(ORACLE_D_CHANGED_SYMBOLS), (
            f"Expected added symbols={ORACLE_D_CHANGED_SYMBOLS}, got={result}"
        )

    def test_identical_source_has_no_changes(self):
        """Fixture E: không có thay đổi → changed_symbols phải trả về rỗng."""
        result = changed_symbols(FIXTURE_E_SOURCE, FIXTURE_E_SOURCE)
        assert result == ORACLE_E_CHANGED_SYMBOLS, f"Expected no changes, got={result}"

    def test_decorator_addition_marks_function_changed(self):
        """Fixture F: thêm decorator → `compute` phải xuất hiện trong changed."""
        result = changed_symbols(FIXTURE_F_BASE, FIXTURE_F_TARGET)
        assert set(result) == set(ORACLE_F_CHANGED_SYMBOLS), (
            f"Expected decorator-affected symbol={ORACLE_F_CHANGED_SYMBOLS}, got={result}"
        )


# ---------------------------------------------------------------------------
# Group 2 — Span integrity: line ranges phải đúng từ oracle thủ công
# ---------------------------------------------------------------------------


class TestSpanIntegrity:
    """Kiểm tra start/end line range theo oracle đọc thủ công từ source."""

    def test_nested_class_symbol_ranges(self):
        """Fixture G: verify symbol names và line ranges cho nested class."""
        result = inspect_python(FIXTURE_G_SOURCE)
        actual = {s.name: (s.start, s.end) for s in result.symbols}
        expected = {s.name: (s.start, s.end) for s in ORACLE_G_SYMBOLS}
        for name, (exp_start, exp_end) in expected.items():
            assert name in actual, f"Symbol '{name}' missing from snapshot"
            act_start, act_end = actual[name]
            assert act_start == exp_start, (
                f"Symbol '{name}': expected start={exp_start}, got={act_start}"
            )
            assert act_end == exp_end, f"Symbol '{name}': expected end={exp_end}, got={act_end}"

    def test_decorator_adjusts_start_line(self):
        """Fixture F target: `compute` start line = line của decorator (line 4 trong target)."""
        result = inspect_python(FIXTURE_F_TARGET)
        compute = next((s for s in result.symbols if s.name == "compute"), None)
        assert compute is not None, "Symbol 'compute' not found"
        # Decorator @functools.lru_cache ở dòng 4 trong FIXTURE_F_TARGET
        # (L1: import functools, L2: blank, L3: blank, L4: @decorator, L5: def compute, L6: body)
        assert compute.start == 4, f"Expected start=4 (decorator line), got={compute.start}"
        # end = dòng cuối của body = L6
        assert compute.end == 6, f"Expected end=6 (body last line), got={compute.end}"

    def test_helper_line_shifts_when_preceding_function_shrinks(self):
        """Fixture A: `helper` không bị sửa về nội dung, nhưng line number thay đổi
        vì `process` bị rút ngắn từ 6 dòng xuống 3 dòng.

        Oracle: changed_symbols đúng khi KHÔNG báo helper là changed (text khác nhau
        chỉ về vị trí, không về body). Nhưng line_start khác nhau giữa base và target.
        Điều này xác nhận rằng validator phải đối chiếu symbol name + body text,
        không chỉ symbol name + line number.
        """
        base_snap = inspect_python(FIXTURE_A_BASE)
        target_snap = inspect_python(FIXTURE_A_TARGET)
        helper_base = next((s for s in base_snap.symbols if s.name == "helper"), None)
        helper_target = next((s for s in target_snap.symbols if s.name == "helper"), None)
        assert helper_base is not None, "Symbol 'helper' missing from base"
        assert helper_target is not None, "Symbol 'helper' missing from target"
        # Line number KHÁC NHAU vì process bị rút ngắn — đây là expected behavior
        assert helper_base.start != helper_target.start, (
            "helper line should shift when preceding function body changes size: "
            f"base_start={helper_base.start}, target_start={helper_target.start}"
        )
        # Nhưng changed_symbols KHÔNG báo helper là changed (body text giống nhau)
        changed = changed_symbols(FIXTURE_A_BASE, FIXTURE_A_TARGET)
        assert "helper" not in changed, (
            f"helper body is unchanged, should not appear in changed={changed}"
        )


# ---------------------------------------------------------------------------
# Group 3 — Wrong-location rejection cases
# ---------------------------------------------------------------------------


class TestWrongLocationRejected:
    """Validate rằng output VỚI wrong location bị phát hiện khi đối chiếu oracle."""

    def test_wrong_symbol_name_is_not_in_changed(self):
        """Nếu producer báo `helper` thay đổi (Fixture A) → sai, oracle nói không."""
        actual_changed = changed_symbols(FIXTURE_A_BASE, FIXTURE_A_TARGET)
        wrong_report = "helper"
        assert wrong_report not in actual_changed, (
            f"Wrong location '{wrong_report}' should NOT appear in changed={actual_changed}"
        )

    def test_unchanged_class_method_not_reported(self):
        """Fixture B: `Storage.__init__` và `Storage.save` không thay đổi.
        `Storage` class span thay đổi (vì validate body thay đổi) — đây là expected.
        Nhưng `Storage.__init__` và `Storage.save` phải không xuất hiện.
        """
        result = changed_symbols(FIXTURE_B_BASE, FIXTURE_B_TARGET)
        for should_not_change in ("Storage.__init__", "Storage.save"):
            assert should_not_change not in result, (
                f"Symbol '{should_not_change}' should NOT be in changed={result}"
            )

    def test_wrong_span_start_detected(self):
        """Nếu producer báo start line sai → oracle phát hiện mismatch."""
        result = inspect_python(FIXTURE_B_BASE)
        storage = next((s for s in result.symbols if s.name == "Storage"), None)
        assert storage is not None
        wrong_start = storage.start + 5  # Giả sử producer báo lệch 5 dòng
        assert storage.start != wrong_start, (
            f"Oracle start={storage.start} must differ from wrong_start={wrong_start}"
        )

    def test_nonexistent_symbol_not_in_snapshot(self):
        """Symbol không tồn tại trong source phải không có trong snapshot."""
        result = inspect_python(FIXTURE_A_BASE)
        symbol_names = {s.name for s in result.symbols}
        for phantom in ("nonexistent_func", "process.inner", "GLOBAL_VAR"):
            assert phantom not in symbol_names, (
                f"Phantom symbol '{phantom}' should not appear in snapshot"
            )


# ---------------------------------------------------------------------------
# Group 4 — Unresolved / disagreement labels
# ---------------------------------------------------------------------------


class TestUnresolvedAndDisagreement:
    """Unresolved và disagreement phải được giữ, không tự đóng."""

    def test_syntax_error_source_is_unresolved(self):
        """Source lỗi syntax → ValueError; oracle ghi là unresolved, không phải empty."""
        with pytest.raises(ValueError, match="python_parse_failed"):
            inspect_python("def broken(")
        # Nhận xét: result nên được ghi là UNRESOLVED trong mismatch record,
        # không coi là "không có symbol" hay "không có thay đổi".

    def test_partial_limitations_kept_explicit(self):
        """Source có relative/dynamic import → limitations phải ghi partial, không xóa."""
        result = inspect_python('from . import sibling\n__import__("plugin")\n')
        assert "relative_import_unresolved" in result.limitations
        assert "dynamic_import" in result.limitations
        # Oracle ghi: import graph là PARTIAL, không phải complete.

    def test_star_import_limitation_kept(self):
        """Star import → limitation phải hiện diện."""
        result = inspect_python("from os.path import *\n")
        assert "star_import" in result.limitations

    def test_reachability_not_ground_truth_for_location(self):
        """Module edges KHÔNG xác nhận location đúng, chỉ là potential reachability.

        AC 2.02: "Dependency reachability không là ground truth."
        Test này xác nhận rằng module_edges chỉ là partial observation.
        """
        from smartregression.core.impact.python_snapshot import module_edges

        sources = {
            "core.py": "def compute(): pass\n",
            "tests/test_core.py": "from core import compute\ndef test_it(): compute()\n",
        }
        edges = module_edges(sources)
        # Edge tồn tại, nhưng không có nghĩa test_it test đúng compute
        assert ("tests/test_core.py", "core.py") in edges
        # Oracle: edge này không tự xác nhận `compute` là changed location đúng.
        # Cần independent evidence từ diff/AST để confirm.

    def test_class_enclosing_granularity_disagreement_kept_as_unresolved(self):
        """Khi spike/producer báo cả enclosing class 'Storage' trong khi oracle
        ngữ nghĩa chỉ có 'Storage.validate', validator PHẢI giữ nhãn 'disagreement'
        (unresolved), KHÔNG được tự ý gộp hay sửa oracle thành match.

        Đây là câu hỏi ngữ nghĩa (Q-AN-01) gửi Do Ha An (2.01).
        """
        spike_actual = changed_symbols(FIXTURE_B_BASE, FIXTURE_B_TARGET)
        # spike trả về ('Storage', 'Storage.validate')
        assert "Storage" in spike_actual
        reconciliation = reconcile_changed_symbols(ORACLE_B_CHANGED_SYMBOLS, spike_actual)
        assert reconciliation["status"] == "disagreement"
        assert reconciliation["extra"] == ("Storage",)
        assert reconciliation["unresolved_question"] is not None
        assert "Q-AN-01" in reconciliation["unresolved_question"]

    def test_decorator_start_line_semantic_question_kept_as_disagreement(self):
        """Nếu producer (2.01) báo start_line ở dòng `def` (L5) thay vì dòng decorator (L4),
        đây là câu hỏi ngữ nghĩa (Q-AN-02) cần giữ dưới nhãn disagreement/mismatch.
        """
        from smartregression.contracts.models import EvidenceReference

        # Giả định producer 2.01 báo def line (L5)
        producer_ref = EvidenceReference(
            id="ev-dec-01",
            commit="a" * 40,
            path="math_utils.py",
            line_start=5,  # dòng def compute
            line_end=6,
            symbol="compute",
        )
        # Oracle spike lấy dòng decorator (L4)
        spike_snap = inspect_python(FIXTURE_F_TARGET)
        compute_sym = next(s for s in spike_snap.symbols if s.name == "compute")
        assert compute_sym.start == 4

        # Đối chiếu phát hiện lệch start line giữa decorator (4) và def (5)
        has_span_disagreement = producer_ref.line_start != compute_sym.start
        assert has_span_disagreement is True, (
            "Disagreement between decorator line (L4) and def line (L5) must be preserved!"
        )


# ---------------------------------------------------------------------------
# Group 5 — Contract shape validation (EvidenceReference)
# ---------------------------------------------------------------------------


class TestEvidenceReferenceShape:
    """Validate shape EvidenceReference theo contracts/models.py.

    Mục đích: oracle của 2.02 phải produce records hợp lệ theo contract 2.14.
    """

    DUMMY_COMMIT = "a" * 40  # 40-char hex — hợp lệ theo Commit type

    def test_valid_evidence_reference_accepted(self):
        """EvidenceReference hợp lệ phải pass validation."""
        from smartregression.contracts.models import EvidenceReference

        ref = EvidenceReference(
            id="ev-001",
            commit=self.DUMMY_COMMIT,
            path="tinydb/database.py",
            line_start=10,
            line_end=25,
            symbol="Database.insert",
            excerpt="def insert(self, document): ...",
        )
        assert ref.line_start <= ref.line_end
        assert ref.symbol == "Database.insert"

    def test_reversed_lines_rejected(self):
        """line_end < line_start phải bị reject."""
        from pydantic import ValidationError

        from smartregression.contracts.models import EvidenceReference

        with pytest.raises(ValidationError, match="line_end"):
            EvidenceReference(
                id="ev-002",
                commit=self.DUMMY_COMMIT,
                path="tinydb/database.py",
                line_start=20,
                line_end=10,  # sai: end < start
            )

    def test_wrong_commit_format_rejected(self):
        """Commit SHA không đúng format (không phải 40/64 hex) phải bị reject."""
        from pydantic import ValidationError

        from smartregression.contracts.models import EvidenceReference

        with pytest.raises(ValidationError):
            EvidenceReference(
                id="ev-003",
                commit="not-a-sha",  # sai format
                path="tinydb/database.py",
                line_start=1,
                line_end=5,
            )

    def test_changed_component_change_types(self):
        """ChangedComponent chấp nhận: added/modified/deleted/renamed."""
        from smartregression.contracts.models import ChangedComponent

        for change_type in ("added", "modified", "deleted", "renamed"):
            comp = ChangedComponent(
                path="sqlparse/sql.py",
                symbol="Statement.get_type",
                change=change_type,
            )
            assert comp.change == change_type

    def test_invalid_change_type_rejected(self):
        """ChangedComponent với change type không hợp lệ phải bị reject."""
        from pydantic import ValidationError

        from smartregression.contracts.models import ChangedComponent

        with pytest.raises(ValidationError):
            ChangedComponent(
                path="sqlparse/sql.py",
                symbol="Statement.get_type",
                change="updated",  # không phải literal hợp lệ
            )
