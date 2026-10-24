# Git — read-only spike

Đã có adapter [LocalGit](../../adapters/git_local.py) cho diff hai full SHA và đọc
blob bất biến. Xem [phạm vi/evidence](../../../../../docs/research/sprint-1/git-diff-spike.md).
Resolve refs/PR semantics và ingestion production còn pending.

Resolve refs thành full commit IDs, đọc diff từ repo cục bộ và tạo ChangedComponent.
Không clone/checkout hoặc chạy code đầu vào trong bootstrap. Spike phải xử lý
rename/delete/binary, path ngoài repo và commit không tồn tại trước khi thêm adapter.
