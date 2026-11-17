"""Build portable exports through existing ownership-checked stores."""

from datetime import UTC, datetime

from smartregression.contracts.web_exports import DurableRunExport, ScenarioExport


class WebExportService:
    def __init__(self, runs, scenarios, ai):
        self.runs, self.scenarios, self.ai = runs, scenarios, ai

    def run(self, owner, project, identity):
        saved = self.runs.store.report(owner, project, identity)
        jobs = self.ai.store.run_list(owner, project, identity)
        self.runs.store.export_activity(owner, project, identity)
        return DurableRunExport(exported_at=datetime.now(UTC), payload=saved, ai_requests=jobs)

    def scenario(self, owner, project, identity):
        saved = self.scenarios.store.get(owner, project, identity)
        jobs = [
            job
            for job in self.ai.store.scoped_list(owner, project, saved.baseline)
            if job.provenance.get("scenario_id") == identity
        ]
        self.runs.store.export_activity(owner, project, identity)
        return ScenarioExport(exported_at=datetime.now(UTC), payload=saved, ai_requests=jobs)
