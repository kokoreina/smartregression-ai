// Generated from backend models. Do not edit.
export interface paths {
    "/health": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Health */
        get: operations["health_health_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /** AnalysisReport */
        AnalysisReport: {
            /**
             * Analysis Duration Seconds
             * @default null
             */
            analysis_duration_seconds?: number | null;
            /**
             * Analysis Status
             * @enum {string}
             */
            analysis_status: "completed" | "partial" | "failed" | "not_implemented";
            commits: components["schemas"]["CommitPair"];
            /**
             * Data Kind
             * @enum {string}
             */
            data_kind: "demo" | "real";
            /** Evidence */
            evidence: components["schemas"]["EvidenceReference"][];
            /** Execution Results */
            execution_results: components["schemas"]["ExecutionResult"][];
            /**
             * Execution Status
             * @enum {string}
             */
            execution_status: "not_run" | "completed" | "partial" | "error";
            /** Findings */
            findings: components["schemas"]["ImpactFinding"][];
            /**
             * Llm Cost Usd
             * @default null
             */
            llm_cost_usd?: number | null;
            /** Notes */
            notes?: string[];
            /** Report Id */
            report_id: string;
            /** Repository */
            repository: string;
            /**
             * Schema Version
             * @default 1.0.0
             * @constant
             */
            schema_version?: "1.0.0";
            selection: components["schemas"]["TestSelection"];
        };
        /** AnalysisRequest */
        AnalysisRequest: {
            commits: components["schemas"]["CommitPair"];
            /** Repository */
            repository: string;
            /**
             * Schema Version
             * @default 1.0.0
             * @constant
             */
            schema_version?: "1.0.0";
        };
        /** AnalysisStages */
        AnalysisStages: {
            changes: components["schemas"]["StageResult_ChangePayload_"];
            evidence: components["schemas"]["StageResult_EvidencePayload_"];
            graph: components["schemas"]["StageResult_GraphPayload_"];
            impact: components["schemas"]["StageResult_ImpactPayload_"];
            inventory: components["schemas"]["StageResult_InventoryPayload_"];
            retrieval: components["schemas"]["StageResult_RetrievalPayload_"];
            review_ordering: components["schemas"]["StageResult_ReviewPayload_"];
            snapshots: components["schemas"]["StageResult_SnapshotPayload_"];
        };
        /** ChangePayload */
        ChangePayload: {
            /** Components */
            components: components["schemas"]["StageComponent"][];
            /** Files */
            files: components["schemas"]["FileCoverage"][];
        };
        /** ChangedComponent */
        ChangedComponent: {
            /**
             * Change
             * @enum {string}
             */
            change: "added" | "modified" | "deleted" | "renamed";
            /** Path */
            path: string;
            /**
             * Previous Path
             * @default null
             */
            previous_path?: string | null;
            /**
             * Schema Version
             * @default 1.0.0
             * @constant
             */
            schema_version?: "1.0.0";
            /**
             * Symbol
             * @default null
             */
            symbol?: string | null;
        };
        /** CommitPair */
        CommitPair: {
            /** Base */
            base: string;
            /**
             * Schema Version
             * @default 1.0.0
             * @constant
             */
            schema_version?: "1.0.0";
            /** Target */
            target: string;
        };
        /** ErrorResponse */
        ErrorResponse: {
            /** Code */
            code: string;
            /** Message */
            message: string;
            /**
             * Schema Version
             * @default 1.0.0
             * @constant
             */
            schema_version?: "1.0.0";
        };
        /**
         * EvidenceBundle
         * @description Atomic domain unit for task 2.05; not a connection or database schema.
         */
        EvidenceBundle: {
            changes: components["schemas"]["ChangePayload"];
            evidence: components["schemas"]["EvidencePayload"];
            graph: components["schemas"]["GraphPayload"];
            identity: components["schemas"]["RunIdentity"];
            impact: components["schemas"]["ImpactPayload"];
        };
        /** EvidencePayload */
        EvidencePayload: {
            /** Items */
            items: components["schemas"]["StageEvidence"][];
        };
        /** EvidenceReference */
        EvidenceReference: {
            /** Commit */
            commit: string;
            /**
             * Excerpt
             * @default null
             */
            excerpt?: string | null;
            /** Id */
            id: string;
            /** Line End */
            line_end: number;
            /** Line Start */
            line_start: number;
            /** Path */
            path: string;
            /**
             * Schema Version
             * @default 1.0.0
             * @constant
             */
            schema_version?: "1.0.0";
            /**
             * Symbol
             * @default null
             */
            symbol?: string | null;
        };
        /** ExecutionResult */
        ExecutionResult: {
            /**
             * Detail
             * @default null
             */
            detail?: string | null;
            /**
             * Duration Seconds
             * @default null
             */
            duration_seconds?: number | null;
            /**
             * Outcome
             * @enum {string}
             */
            outcome: "passed" | "failed" | "skipped" | "error" | "not_run";
            /**
             * Schema Version
             * @default 1.0.0
             * @constant
             */
            schema_version?: "1.0.0";
            /** Test Id */
            test_id: string;
        };
        /** FileCoverage */
        FileCoverage: {
            /** Limitations */
            limitations: string[];
            /** Path */
            path: string;
            /**
             * Status
             * @enum {string}
             */
            status: "completed" | "partial" | "file_only";
        };
        /** GraphPayload */
        GraphPayload: {
            /**
             * Edge Direction
             * @default importer_to_importee
             * @constant
             */
            edge_direction?: "importer_to_importee";
            /** Edges */
            edges: components["schemas"]["StageEdge"][];
            /** Nodes */
            nodes: string[];
            snapshot: components["schemas"]["SnapshotIdentity"];
            /** Unresolved */
            unresolved: components["schemas"]["ImportLimitation"][];
        };
        /** HealthResponse */
        HealthResponse: {
            /**
             * Schema Version
             * @default 1.0.0
             * @constant
             */
            schema_version?: "1.0.0";
            /**
             * Scope
             * @default service_only
             * @constant
             */
            scope?: "service_only";
            /**
             * Service
             * @default smartregression-api
             * @constant
             */
            service?: "smartregression-api";
            /**
             * Status
             * @default ok
             * @constant
             */
            status?: "ok";
        };
        /** ImpactCandidate */
        ImpactCandidate: {
            /** Changed Component Id */
            changed_component_id: string;
            /** Evidence Ids */
            evidence_ids?: string[];
            /**
             * Explanation
             * @default null
             */
            explanation?: string | null;
            /** Id */
            id: string;
            /** Path */
            path: string;
            /** Path Ids */
            path_ids: string[];
            /**
             * Relationship
             * @enum {string}
             */
            relationship: "changed" | "direct" | "indirect";
            /**
             * Symbol
             * @default null
             */
            symbol?: string | null;
        };
        /** ImpactFinding */
        ImpactFinding: {
            component: components["schemas"]["ChangedComponent"];
            /** Evidence Ids */
            evidence_ids: string[];
            /** Explanation */
            explanation: string;
            /** Id */
            id: string;
            /**
             * Schema Version
             * @default 1.0.0
             * @constant
             */
            schema_version?: "1.0.0";
        };
        /** ImpactPath */
        ImpactPath: {
            /** Changed Component Id */
            changed_component_id: string;
            /** Id */
            id: string;
            /** Nodes */
            nodes: string[];
        };
        /** ImpactPayload */
        ImpactPayload: {
            /** Candidates */
            candidates: components["schemas"]["ImpactCandidate"][];
            /** Paths */
            paths: components["schemas"]["ImpactPath"][];
            snapshot: components["schemas"]["SnapshotIdentity"];
        };
        /** ImportLimitation */
        ImportLimitation: {
            /** Kind */
            kind: string;
            /** Reason */
            reason: string;
            /** Reference */
            reference: string;
            /** Source Path */
            source_path: string;
        };
        /** InventoryPayload */
        InventoryPayload: {
            /**
             * Completeness
             * @enum {string}
             */
            completeness: "complete" | "partial";
            /**
             * Framework
             * @constant
             */
            framework: "pytest";
            snapshot: components["schemas"]["SnapshotIdentity"];
            /** Test Ids */
            test_ids: string[];
        };
        /** RetrievalItem */
        RetrievalItem: {
            /** Configuration Id */
            configuration_id: string;
            /** Content Sha256 */
            content_sha256: string;
            /** Id */
            id: string;
            /** Index Id */
            index_id: string;
            location: components["schemas"]["SourceLocation"];
            /** Path */
            path: string;
            /** Rank */
            rank: number;
            /**
             * Score
             * @default null
             */
            score?: number | null;
            snapshot: components["schemas"]["SnapshotIdentity"];
        };
        /** RetrievalPayload */
        RetrievalPayload: {
            /** Items */
            items: components["schemas"]["RetrievalItem"][];
            /** Sources */
            sources: components["schemas"]["RetrievalSource"][];
        };
        /** RetrievalSource */
        RetrievalSource: {
            /** Configuration Id */
            configuration_id: string;
            /** Index Id */
            index_id: string;
            snapshot: components["schemas"]["SnapshotIdentity"];
        };
        /** ReviewItem */
        ReviewItem: {
            /** Path */
            path: string;
            /** Reason */
            reason: string;
            /**
             * Symbol
             * @default null
             */
            symbol?: string | null;
            /**
             * Tier
             * @enum {integer}
             */
            tier: 1 | 2 | 3;
        };
        /** ReviewPayload */
        ReviewPayload: {
            /** Candidates */
            candidates: components["schemas"]["ReviewItem"][];
            /** Rule Version */
            rule_version: string;
            snapshot: components["schemas"]["SnapshotIdentity"];
        };
        /** RunIdentity */
        RunIdentity: {
            base: components["schemas"]["SnapshotIdentity"];
            /**
             * Comparison Mode
             * @constant
             */
            comparison_mode: "direct_two_tree";
            /** Repository Id */
            repository_id: string;
            /** Run Id */
            run_id: string;
            target: components["schemas"]["SnapshotIdentity"];
        };
        /** SnapshotIdentity */
        SnapshotIdentity: {
            /** Commit */
            commit: string;
            /** Repository Id */
            repository_id: string;
            /** Snapshot Id */
            snapshot_id: string | null;
        };
        /** SnapshotPayload */
        SnapshotPayload: {
            base: components["schemas"]["SnapshotIdentity"];
            target: components["schemas"]["SnapshotIdentity"];
        };
        /** SourceLocation */
        SourceLocation: {
            /** Line End */
            line_end: number;
            /** Line Start */
            line_start: number;
        };
        /** StageAnalysisReport */
        StageAnalysisReport: {
            /**
             * Analysis Duration Seconds
             * @default null
             */
            analysis_duration_seconds?: number | null;
            /**
             * Analysis Status
             * @enum {string}
             */
            analysis_status: "not_implemented" | "not_run" | "completed" | "partial" | "failed";
            /**
             * Data Kind
             * @enum {string}
             */
            data_kind: "demo" | "real";
            identity: components["schemas"]["RunIdentity"];
            /**
             * Llm Cost Usd
             * @default null
             */
            llm_cost_usd?: number | null;
            /** Report Id */
            report_id: string;
            /**
             * Schema Version
             * @constant
             */
            schema_version: "2.0.0";
            stages: components["schemas"]["AnalysisStages"];
        };
        /** StageComponent */
        StageComponent: {
            /** @default null */
            base_location?: components["schemas"]["SourceLocation"] | null;
            /**
             * Change
             * @enum {string}
             */
            change: "added" | "modified" | "deleted" | "renamed";
            /** Id */
            id: string;
            /**
             * Kind
             * @enum {string}
             */
            kind: "file" | "module" | "class" | "function" | "method";
            /** Path */
            path: string;
            /**
             * Previous Path
             * @default null
             */
            previous_path?: string | null;
            /** Reason */
            reason: string;
            /**
             * Symbol
             * @default null
             */
            symbol?: string | null;
            /** @default null */
            target_location?: components["schemas"]["SourceLocation"] | null;
        };
        /** StageEdge */
        StageEdge: {
            /** Kind */
            kind: string;
            /** Source */
            source: string;
            /** Target */
            target: string;
        };
        /** StageEvidence */
        StageEvidence: {
            /**
             * Excerpt
             * @default null
             */
            excerpt?: string | null;
            /** Id */
            id: string;
            location: components["schemas"]["SourceLocation"];
            /** Path */
            path: string;
            /**
             * Resolution
             * @default unverified
             * @enum {string}
             */
            resolution?: "unverified" | "resolved" | "missing" | "mismatched";
            snapshot: components["schemas"]["SnapshotIdentity"];
            /**
             * Support
             * @default unverified
             * @enum {string}
             */
            support?: "unverified" | "supported" | "unsupported";
            /**
             * Symbol
             * @default null
             */
            symbol?: string | null;
            /**
             * Verification Reason
             * @default null
             */
            verification_reason?: string | null;
        };
        /** StageIssue */
        StageIssue: {
            /** Code */
            code: string;
            /**
             * Path
             * @default null
             */
            path?: string | null;
        };
        /** StageResult[ChangePayload] */
        StageResult_ChangePayload_: {
            /** @default null */
            data?: components["schemas"]["ChangePayload"] | null;
            /**
             * Error Code
             * @default null
             */
            error_code?: string | null;
            /** Limitations */
            limitations?: components["schemas"]["StageIssue"][];
            /**
             * Reason
             * @default null
             */
            reason?: string | null;
            /**
             * Status
             * @enum {string}
             */
            status: "not_implemented" | "not_run" | "completed" | "partial" | "failed";
        };
        /** StageResult[EvidencePayload] */
        StageResult_EvidencePayload_: {
            /** @default null */
            data?: components["schemas"]["EvidencePayload"] | null;
            /**
             * Error Code
             * @default null
             */
            error_code?: string | null;
            /** Limitations */
            limitations?: components["schemas"]["StageIssue"][];
            /**
             * Reason
             * @default null
             */
            reason?: string | null;
            /**
             * Status
             * @enum {string}
             */
            status: "not_implemented" | "not_run" | "completed" | "partial" | "failed";
        };
        /** StageResult[GraphPayload] */
        StageResult_GraphPayload_: {
            /** @default null */
            data?: components["schemas"]["GraphPayload"] | null;
            /**
             * Error Code
             * @default null
             */
            error_code?: string | null;
            /** Limitations */
            limitations?: components["schemas"]["StageIssue"][];
            /**
             * Reason
             * @default null
             */
            reason?: string | null;
            /**
             * Status
             * @enum {string}
             */
            status: "not_implemented" | "not_run" | "completed" | "partial" | "failed";
        };
        /** StageResult[ImpactPayload] */
        StageResult_ImpactPayload_: {
            /** @default null */
            data?: components["schemas"]["ImpactPayload"] | null;
            /**
             * Error Code
             * @default null
             */
            error_code?: string | null;
            /** Limitations */
            limitations?: components["schemas"]["StageIssue"][];
            /**
             * Reason
             * @default null
             */
            reason?: string | null;
            /**
             * Status
             * @enum {string}
             */
            status: "not_implemented" | "not_run" | "completed" | "partial" | "failed";
        };
        /** StageResult[InventoryPayload] */
        StageResult_InventoryPayload_: {
            /** @default null */
            data?: components["schemas"]["InventoryPayload"] | null;
            /**
             * Error Code
             * @default null
             */
            error_code?: string | null;
            /** Limitations */
            limitations?: components["schemas"]["StageIssue"][];
            /**
             * Reason
             * @default null
             */
            reason?: string | null;
            /**
             * Status
             * @enum {string}
             */
            status: "not_implemented" | "not_run" | "completed" | "partial" | "failed";
        };
        /** StageResult[RetrievalPayload] */
        StageResult_RetrievalPayload_: {
            /** @default null */
            data?: components["schemas"]["RetrievalPayload"] | null;
            /**
             * Error Code
             * @default null
             */
            error_code?: string | null;
            /** Limitations */
            limitations?: components["schemas"]["StageIssue"][];
            /**
             * Reason
             * @default null
             */
            reason?: string | null;
            /**
             * Status
             * @enum {string}
             */
            status: "not_implemented" | "not_run" | "completed" | "partial" | "failed";
        };
        /** StageResult[ReviewPayload] */
        StageResult_ReviewPayload_: {
            /** @default null */
            data?: components["schemas"]["ReviewPayload"] | null;
            /**
             * Error Code
             * @default null
             */
            error_code?: string | null;
            /** Limitations */
            limitations?: components["schemas"]["StageIssue"][];
            /**
             * Reason
             * @default null
             */
            reason?: string | null;
            /**
             * Status
             * @enum {string}
             */
            status: "not_implemented" | "not_run" | "completed" | "partial" | "failed";
        };
        /** StageResult[SnapshotPayload] */
        StageResult_SnapshotPayload_: {
            /** @default null */
            data?: components["schemas"]["SnapshotPayload"] | null;
            /**
             * Error Code
             * @default null
             */
            error_code?: string | null;
            /** Limitations */
            limitations?: components["schemas"]["StageIssue"][];
            /**
             * Reason
             * @default null
             */
            reason?: string | null;
            /**
             * Status
             * @enum {string}
             */
            status: "not_implemented" | "not_run" | "completed" | "partial" | "failed";
        };
        /** TestDecision */
        TestDecision: {
            /** Evidence Ids */
            evidence_ids?: string[];
            /** Reason */
            reason: string;
            /**
             * Schema Version
             * @default 1.0.0
             * @constant
             */
            schema_version?: "1.0.0";
            /** Test Id */
            test_id: string;
        };
        /** TestSelection */
        TestSelection: {
            /**
             * Fallback Reason
             * @default null
             */
            fallback_reason?: string | null;
            /** Framework */
            framework: string;
            /**
             * Schema Version
             * @default 1.0.0
             * @constant
             */
            schema_version?: "1.0.0";
            /** Selected */
            selected: components["schemas"]["TestDecision"][];
            /** Skipped */
            skipped: components["schemas"]["TestDecision"][];
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    health_health_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HealthResponse"];
                };
            };
        };
    };
}
