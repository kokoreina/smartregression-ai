"""Static assistance and two-snapshot impact; repository text is never executed."""

from smartregression.contracts.repo_assistant import (
    AssistantFact,
    AssistantReply,
    ChangeReport,
    ScopeImpact,
)
from smartregression.contracts.snapshots import SourceRange
from smartregression.core.explorer.assistance import evidence, reading_guide, search_features
from smartregression.core.explorer.graph import impact
from smartregression.core.retrieval.exclusions import contains_recognized_secret

LIMITATIONS = [
    "Quan hệ tĩnh có thể thiếu; không chứng minh chương trình chạy đúng hoặc không có lỗi.",
    "Phạm vi ảnh hưởng chính là Python; JavaScript Explorer có mức hỗ trợ riêng. Không suy "
    "quan hệ xuyên ngôn ngữ.",
]


def selected(path, scope):
    return any(path == root or path.startswith(root + "/") for root in scope)


def excerpts(sources, proofs, commit):
    result = []
    seen = set()
    total = 0
    for proof in proofs:
        if proof.path in seen or proof.path not in sources:
            continue
        seen.add(proof.path)
        lines = sources[proof.path].splitlines()
        start = proof.line_start or 1
        end = min(start + 39, len(lines))
        content = "\n".join(lines[start - 1 : end])
        size = len(content.encode())
        if (
            not content
            or size > 6000
            or total + size > 16000
            or contains_recognized_secret(content)
        ):
            continue
        total += size
        result.append(
            SourceRange(
                commit=commit, path=proof.path, line_start=start, line_end=end, content=content
            )
        )
        if len(result) == 5:
            break
    return result


def overview(graph, sources):
    guide = reading_guide(graph, sources)
    facts = []
    docs = sorted(p for p in sources if p.rsplit("/", 1)[-1].lower().startswith("readme"))[:3]
    for path in docs:
        facts.append(
            AssistantFact(
                text="Tài liệu mô tả dự án: " + path,
                evidence=[
                    evidence(graph, path, 1, min(40, max(1, len(sources[path].splitlines()))))
                ],
            )
        )
    for step in guide.steps[:20]:
        facts.append(
            AssistantFact(
                text=f"{step.category}: {step.path}. {step.reason}", evidence=[step.evidence]
            )
        )
    proofs = [p for fact in facts for p in fact.evidence]
    return AssistantReply(
        commit=graph.commit,
        kind="overview",
        summary=f"Snapshot có {len(graph.coverage.analyzed_files)} file đã phân tích, "
        f"{len(graph.coverage.unparsed_files)} file parse lỗi và "
        f"{len(graph.coverage.unsupported_files)} file ngoài phạm vi. "
        "Đây là bản đồ đọc mã tĩnh; mở trích đoạn để hiểu mục đích và chi tiết.",
        facts=facts,
        coverage=graph.coverage,
        limitations=LIMITATIONS + guide.limitations,
        excerpts=excerpts(sources, proofs, graph.commit),
    )


def answer(graph, sources, question, history=(), change=None):
    if change is not None:
        proofs = [proof for item in change.scope_impacts for proof in item.evidence]
        facts = [
            AssistantFact(
                text=f"{item.path}: {item.relationship}. " + " ← ".join(item.chain),
                evidence=item.evidence,
            )
            for item in change.scope_impacts[:24]
        ]
        return AssistantReply(
            commit=graph.commit,
            kind="changes",
            summary=f"So sánh {change.base[:8]} → {change.target[:8]}: "
            f"{len(change.changes)} file thay đổi; "
            f"{len(change.scope_impacts)} file trong vùng theo dõi có liên hệ tĩnh. "
            "Chưa tìm thấy liên hệ không đồng nghĩa không ảnh hưởng.",
            facts=facts,
            coverage=graph.coverage,
            limitations=change.limitations,
            excerpts=excerpts(
                sources, [p for p in proofs if p.commit == graph.commit], graph.commit
            ),
        )
    query = question
    # Prior user words improve lexical recall; assistant answers are never evidence.
    if history:
        query = (question + " " + " ".join(history[-2:]))[:600]
    found = search_features(graph, sources, query)
    facts = [
        AssistantFact(
            text=f"{item.path}: từ khóa khớp " + ", ".join(item.matched_terms),
            evidence=[item.evidence],
        )
        for item in found.items
    ]
    return AssistantReply(
        commit=graph.commit,
        kind="search" if facts else "no_evidence",
        summary="Tìm thấy các đoạn mã liên quan theo từ khóa. Có thể yêu cầu AI giải thích "
        "sau khi xem bằng chứng."
        if facts
        else "Chưa tìm thấy bằng chứng phù hợp. Hãy nêu tên file, symbol hoặc chức năng cụ "
        "thể hơn.",
        facts=facts,
        coverage=graph.coverage,
        limitations=LIMITATIONS + found.limitations,
        excerpts=excerpts(sources, [i.evidence for i in found.items], graph.commit),
    )


def change_report(base, target, changes, branch, scope):
    if base.repository_id != target.repository_id or base.config_digest != target.config_digest:
        raise ValueError("change_snapshot_mismatch")
    changed = {c.path for c in changes}
    impacts = {}
    truncated = False
    for graph in (base, target):
        known = {n.path for n in graph.nodes if n.kind == "file"}
        result = impact(graph, changed & known)
        truncated |= result.paths_truncated
        for path in sorted(changed | set(result.direct) | set(result.indirect)):
            if not selected(path, scope):
                continue
            chain = result.paths.get(path, [path] if path in changed else [])
            if not chain:
                truncated = True
                continue
            proofs = []
            if path in changed:
                node = next((n for n in graph.nodes if n.kind == "file" and n.path == path), None)
                if node and node.evidence:
                    proofs.append(node.evidence)
            for dependency, consumer in zip(chain, chain[1:], strict=False):
                edge = next(
                    (
                        e
                        for e in graph.edges
                        if e.kind == "imports"
                        and e.source_path == consumer
                        and e.target_path == dependency
                    ),
                    None,
                )
                if edge:
                    proofs.append(edge.evidence)
            relation = (
                "changed" if path in changed else "direct" if path in result.direct else "indirect"
            )
            item = ScopeImpact(path=path, relationship=relation, chain=chain, evidence=proofs)
            old = impacts.get(path)
            if old is None or len(item.chain) < len(old.chain):
                impacts[path] = item
    # A directly changed unsupported file is still relevant to its selected scope.
    for path in sorted(changed):
        if selected(path, scope) and path not in impacts:
            impacts[path] = ScopeImpact(
                path=path, relationship="changed", chain=[path], evidence=[]
            )
    values = [impacts[p] for p in sorted(impacts)]
    return ChangeReport(
        base=base.commit,
        target=target.commit,
        config_digest=target.config_digest,
        branch=branch,
        changes=changes,
        scope=scope,
        scope_impacts=values[:150],
        impacts_truncated=truncated or len(values) > 150,
        base_coverage=base.coverage,
        target_coverage=target.coverage,
        limitations=LIMITATIONS
        + [
            "So sánh hai cây Git; không mô phỏng merge, không thấy thay đổi local chưa push.",
            "Rename được biểu diễn là xóa và thêm. Quan hệ xóa được kiểm tra từ snapshot base.",
            "Các sự kiện gần nhau có thể được gộp từ baseline tới head mới nhất; không phải "
            "toàn bộ event history.",
        ]
        + (["Chưa chọn vùng mã cá nhân; kết quả chỉ liệt kê thay đổi chung."] if not scope else []),
    )
