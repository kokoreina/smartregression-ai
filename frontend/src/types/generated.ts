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
