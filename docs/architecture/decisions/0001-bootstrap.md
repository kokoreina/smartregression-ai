# ADR 0001 — Bootstrap monorepo và contract

Trạng thái: accepted cho bootstrap, ngày 2026-10-06.

Bối cảnh: nhóm 5 sinh viên, workspace trống, chưa có proposal; chỉ cần bộ khung có thể
chạy và giải thích. Chưa chốt ngôn ngữ/framework repo đầu vào.

Quyết định: Python 3.14/uv, FastAPI/Pydantic, pytest/Ruff; React 19/TypeScript strict/
Vite 7/npm/ESLint; GitHub Actions cho source SmartRegression. Chọn runtime theo máy
sẵn có; lockfile do package manager sinh. Một src package, không microservices.

Backend models là nguồn contract duy nhất; OpenAPI + openapi-typescript có drift checks.
Dashboard bundle fixture DEMO, API chỉ health. Không cần demo endpoint hoặc DB chỉ để
chạy demo. Measurements chưa đo là null. Failed tests không tạo fault labels.

Hệ quả: dễ chạy/review, chưa đánh giá chất lượng thuật toán hay readiness dependency.
Runtime support hẹp; mở rộng cần CI evidence. Fixture pytest không chốt framework MVP.

Pending sau spike: ngôn ngữ/framework đầu vào, parser/test discovery, LLM provider,
embedding/vector store/database, storage retention, runner isolation/transport,
validation/fallback policy, dataset/baselines/metrics và ngân sách thực nghiệm.
