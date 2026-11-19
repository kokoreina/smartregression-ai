// Generated from backend models. Do not edit.
export interface paths {
    "/api/v1/auth/change-password": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Change */
        post: operations["change_api_v1_auth_change_password_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/csrf": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Csrf */
        get: operations["get_csrf_api_v1_auth_csrf_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/forgot-password": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Forgot */
        post: operations["forgot_api_v1_auth_forgot_password_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/login": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Login */
        post: operations["login_api_v1_auth_login_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/logout": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Logout */
        post: operations["logout_api_v1_auth_logout_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/me": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Me */
        get: operations["me_api_v1_auth_me_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update Me */
        patch: operations["update_me_api_v1_auth_me_patch"];
        trace?: never;
    };
    "/api/v1/auth/register": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Register */
        post: operations["register_api_v1_auth_register_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/resend-verification": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Resend */
        post: operations["resend_api_v1_auth_resend_verification_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/reset-password": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Reset */
        post: operations["reset_api_v1_auth_reset_password_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/verify-email": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Verify */
        post: operations["verify_api_v1_auth_verify_email_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/capabilities": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Capabilities */
        get: operations["capabilities_api_v1_capabilities_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/github/webhook": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Webhook */
        post: operations["webhook_api_v1_github_webhook_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Listing */
        get: operations["listing_api_v1_projects_get"];
        put?: never;
        /** Create */
        post: operations["create_api_v1_projects_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Detail */
        get: operations["detail_api_v1_projects__project_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update */
        patch: operations["update_api_v1_projects__project_id__patch"];
        trace?: never;
    };
    "/api/v1/projects/{project_id}/activity": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Activity */
        get: operations["activity_api_v1_projects__project_id__activity_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/archive": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Archive */
        post: operations["archive_api_v1_projects__project_id__archive_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/assistance/ai": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Assistance List */
        get: operations["assistance_list_api_v1_projects__project_id__assistance_ai_get"];
        put?: never;
        /** Assistance */
        post: operations["assistance_api_v1_projects__project_id__assistance_ai_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/assistance/ai/{request_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Assistance Get */
        get: operations["assistance_get_api_v1_projects__project_id__assistance_ai__request_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/assistant/check": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Check */
        post: operations["check_api_v1_projects__project_id__assistant_check_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/assistant/notifications": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Notifications */
        get: operations["notifications_api_v1_projects__project_id__assistant_notifications_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/assistant/notifications/{notification_id}/read": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Mark Read */
        post: operations["mark_read_api_v1_projects__project_id__assistant_notifications__notification_id__read_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/assistant/overview": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Overview */
        post: operations["overview_api_v1_projects__project_id__assistant_overview_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/assistant/threads": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Threads */
        get: operations["threads_api_v1_projects__project_id__assistant_threads_get"];
        put?: never;
        /** Create Thread */
        post: operations["create_thread_api_v1_projects__project_id__assistant_threads_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/assistant/threads/{thread_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Delete Thread */
        delete: operations["delete_thread_api_v1_projects__project_id__assistant_threads__thread_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/assistant/threads/{thread_id}/messages": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Messages */
        get: operations["messages_api_v1_projects__project_id__assistant_threads__thread_id__messages_get"];
        put?: never;
        /** Send */
        post: operations["send_api_v1_projects__project_id__assistant_threads__thread_id__messages_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/assistant/threads/{thread_id}/preview": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Preview */
        post: operations["preview_api_v1_projects__project_id__assistant_threads__thread_id__preview_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/assistant/watch": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Watch */
        get: operations["watch_api_v1_projects__project_id__assistant_watch_get"];
        /** Save Watch */
        put: operations["save_watch_api_v1_projects__project_id__assistant_watch_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/graph-comparisons": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Versions */
        post: operations["versions_api_v1_projects__project_id__graph_comparisons_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/notes": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Listing */
        get: operations["listing_api_v1_projects__project_id__notes_get"];
        put?: never;
        /** Create */
        post: operations["create_api_v1_projects__project_id__notes_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/notes/{note_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update */
        patch: operations["update_api_v1_projects__project_id__notes__note_id__patch"];
        trace?: never;
    };
    "/api/v1/projects/{project_id}/repository": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Repository */
        get: operations["repository_api_v1_projects__project_id__repository_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/restore": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Restore */
        post: operations["restore_api_v1_projects__project_id__restore_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/runs": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Listing */
        get: operations["listing_api_v1_projects__project_id__runs_get"];
        put?: never;
        /** Create */
        post: operations["create_api_v1_projects__project_id__runs_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/runs/{run_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Detail */
        get: operations["detail_api_v1_projects__project_id__runs__run_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/runs/{run_id}/ai": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Request Ai */
        post: operations["request_ai_api_v1_projects__project_id__runs__run_id__ai_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/runs/{run_id}/ai/{request_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Detail */
        get: operations["detail_api_v1_projects__project_id__runs__run_id__ai__request_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/runs/{run_id}/export": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Run */
        post: operations["run_api_v1_projects__project_id__runs__run_id__export_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/runs/{run_id}/report": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Report */
        get: operations["report_api_v1_projects__project_id__runs__run_id__report_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/scenario-comparisons": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Compare */
        post: operations["compare_api_v1_projects__project_id__scenario_comparisons_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/scenarios": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Listing */
        get: operations["listing_api_v1_projects__project_id__scenarios_get"];
        put?: never;
        /** Create */
        post: operations["create_api_v1_projects__project_id__scenarios_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/scenarios/{scenario_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Detail */
        get: operations["detail_api_v1_projects__project_id__scenarios__scenario_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/scenarios/{scenario_id}/export": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Scenario */
        post: operations["scenario_api_v1_projects__project_id__scenarios__scenario_id__export_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/scenarios/{scenario_id}/graph": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Graph */
        get: operations["graph_api_v1_projects__project_id__scenarios__scenario_id__graph_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/scenarios/{scenario_id}/source": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Source */
        get: operations["source_api_v1_projects__project_id__scenarios__scenario_id__source_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/snapshots": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Materialize */
        post: operations["materialize_api_v1_projects__project_id__snapshots_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/snapshots/{commit}/calls": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Calls */
        get: operations["calls_api_v1_projects__project_id__snapshots__commit__calls_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/snapshots/{commit}/graph": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Graph */
        get: operations["graph_api_v1_projects__project_id__snapshots__commit__graph_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/snapshots/{commit}/hotspots": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Hotspots */
        get: operations["hotspots_api_v1_projects__project_id__snapshots__commit__hotspots_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/snapshots/{commit}/impact": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Impact */
        get: operations["impact_api_v1_projects__project_id__snapshots__commit__impact_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/snapshots/{commit}/nodes": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Nodes */
        get: operations["nodes_api_v1_projects__project_id__snapshots__commit__nodes_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/snapshots/{commit}/reading-guide": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Guide */
        get: operations["guide_api_v1_projects__project_id__snapshots__commit__reading_guide_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/snapshots/{commit}/search": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Search */
        post: operations["search_api_v1_projects__project_id__snapshots__commit__search_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/snapshots/{commit}/source": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Source */
        get: operations["source_api_v1_projects__project_id__snapshots__commit__source_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/snapshots/{commit}/tree": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Tree */
        get: operations["tree_api_v1_projects__project_id__snapshots__commit__tree_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/tree": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Tree */
        get: operations["tree_api_v1_projects__project_id__tree_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/projects/{project_id}/view-state": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** View */
        get: operations["view_api_v1_projects__project_id__view_state_get"];
        /** Save */
        put: operations["save_api_v1_projects__project_id__view_state_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/reporting/views": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Create */
        post: operations["create_api_v1_reporting_views_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/reporting/views/{view_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Read */
        get: operations["read_api_v1_reporting_views__view_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/reporting/views/{view_id}/csv": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Download */
        post: operations["download_api_v1_reporting_views__view_id__csv_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/reporting/views/{view_id}/runs": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Listing */
        get: operations["listing_api_v1_reporting_views__view_id__runs_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/reporting/views/{view_id}/usage": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Usage */
        get: operations["usage_api_v1_reporting_views__view_id__usage_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/usage": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Usage */
        get: operations["usage_api_v1_usage_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
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
    "/repositories/inspect": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Inspect Repository */
        post: operations["inspect_repository_repositories_inspect_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/repositories/tree": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Repository Tree */
        post: operations["repository_tree_repositories_tree_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/repository-analyses": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Analyze Repository */
        post: operations["analyze_repository_repository_analyses_post"];
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
        /** Activity */
        Activity: {
            /** Action */
            action: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Object Id */
            object_id: string;
            /**
             * Project Id
             * Format: uuid
             */
            project_id: string;
        };
        /** ActivityPage */
        ActivityPage: {
            /** Items */
            items: components["schemas"]["Activity"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** AiJob */
        AiJob: {
            /**
             * Action
             * @enum {string}
             */
            action: "commit" | "hypothesis" | "reading_guide" | "search" | "file" | "folder" | "overview" | "chat" | "changes";
            /** Context Hash */
            context_hash?: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Finished At */
            finished_at: string | null;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Provenance */
            provenance?: {
                [key: string]: unknown;
            };
            result: components["schemas"]["NarrativeResult"] | null;
            /** Run Id */
            run_id: string | null;
            /**
             * Schema Version
             * @default 1.0.0
             * @constant
             */
            schema_version?: "1.0.0";
            /**
             * Scope Key
             * @default
             */
            scope_key?: string;
            /**
             * Status
             * @enum {string}
             */
            status: "queued" | "running" | "completed" | "failed";
        };
        /** AiQuota */
        AiQuota: {
            /** Cap Micro Usd */
            cap_micro_usd: number;
            /** Granted Calls */
            granted_calls: number;
            /** Known Actual Micro Usd */
            known_actual_micro_usd: number;
            /** Reserved Micro Usd */
            reserved_micro_usd: number;
            /** Unknown Actual Count */
            unknown_actual_count: number;
            /** Used Calls */
            used_calls: number;
        };
        /** AiRequest */
        AiRequest: {
            /**
             * Allow Metadata Egress
             * @default false
             */
            allow_metadata_egress?: boolean;
            /** Idempotency Key */
            idempotency_key: string;
            /**
             * Question
             * @default Giải thích ảnh hưởng từ bằng chứng phân tích.
             */
            question?: string;
        };
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
        /** AssistanceAiRequest */
        AssistanceAiRequest: {
            /**
             * Action
             * @enum {string}
             */
            action: "hypothesis" | "reading_guide" | "search" | "file" | "folder";
            /**
             * Allow Excerpt Egress
             * @default false
             */
            allow_excerpt_egress?: boolean;
            /**
             * Allow Metadata Egress
             * @default false
             */
            allow_metadata_egress?: boolean;
            /** Commit */
            commit: string;
            /** Excerpts */
            excerpts?: components["schemas"]["ExcerptRange"][];
            /** Idempotency Key */
            idempotency_key: string;
            /** Path */
            path?: string | null;
            /**
             * Question
             * @default
             */
            question?: string;
            /** Scenario Id */
            scenario_id?: string | null;
        };
        /** AssistantFact */
        AssistantFact: {
            /** Evidence */
            evidence?: components["schemas"]["GraphEvidence"][];
            /** Text */
            text: string;
        };
        /** AssistantMessage */
        AssistantMessage: {
            ai?: components["schemas"]["AiJob"] | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Question */
            question: string;
            reply: components["schemas"]["AssistantReply"];
            /**
             * Schema Version
             * @default 1.0.0
             * @constant
             */
            schema_version?: "1.0.0";
            /**
             * Thread Id
             * Format: uuid
             */
            thread_id: string;
        };
        /** AssistantReply */
        AssistantReply: {
            /** Commit */
            commit: string;
            coverage: components["schemas"]["GraphCoverage"];
            /** Excerpts */
            excerpts?: components["schemas"]["SourceRange"][];
            /** Facts */
            facts?: components["schemas"]["AssistantFact"][];
            /**
             * Kind
             * @enum {string}
             */
            kind: "overview" | "search" | "changes" | "no_evidence";
            /** Limitations */
            limitations: string[];
            /**
             * Schema Version
             * @default 1.0.0
             * @constant
             */
            schema_version?: "1.0.0";
            /** Summary */
            summary: string;
        };
        /** AssistantThread */
        AssistantThread: {
            /** Commit */
            commit: string;
            /** Config Digest */
            config_digest: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Project Id
             * Format: uuid
             */
            project_id: string;
            /**
             * Schema Version
             * @default 1.0.0
             * @constant
             */
            schema_version?: "1.0.0";
            /** Title */
            title: string;
        };
        /** AuthErrorResponse */
        AuthErrorResponse: {
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
        /** AuthMessage */
        AuthMessage: {
            /** Message */
            message: string;
            /**
             * Schema Version
             * @default 1.0.0
             * @constant
             */
            schema_version?: "1.0.0";
        };
        /** CallPaths */
        CallPaths: {
            /**
             * Interpretation
             * @default static_paths_not_runtime
             * @constant
             */
            interpretation?: "static_paths_not_runtime";
            /** Nodes */
            nodes?: components["schemas"]["ExplorerNode"][];
            /** Paths */
            paths: string[][];
            /** Truncated */
            truncated: boolean;
            /** Unresolved */
            unresolved: components["schemas"]["UnresolvedRelation"][];
        };
        /** ChangeNotification */
        ChangeNotification: {
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Read At */
            read_at: string | null;
            report: components["schemas"]["ChangeReport"];
            /**
             * Schema Version
             * @default 1.0.0
             * @constant
             */
            schema_version?: "1.0.0";
        };
        /** ChangePayload */
        ChangePayload: {
            /** Components */
            components: components["schemas"]["StageComponent"][];
            /** Files */
            files: components["schemas"]["FileCoverage"][];
        };
        /** ChangeReport */
        ChangeReport: {
            /** Base */
            base: string;
            base_coverage: components["schemas"]["GraphCoverage"];
            /** Branch */
            branch: string;
            /** Changes */
            changes: components["schemas"]["ChangedComponent"][];
            /** Config Digest */
            config_digest: string;
            /** Impacts Truncated */
            impacts_truncated: boolean;
            /** Limitations */
            limitations: string[];
            /**
             * Schema Version
             * @default 1.0.0
             * @constant
             */
            schema_version?: "1.0.0";
            /** Scope */
            scope: string[];
            /** Scope Impacts */
            scope_impacts: components["schemas"]["ScopeImpact"][];
            /** Target */
            target: string;
            target_coverage: components["schemas"]["GraphCoverage"];
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
        /** ClassifiedReference */
        ClassifiedReference: {
            /**
             * Category
             * @enum {string}
             */
            category: "builtin" | "stdlib";
            /**
             * Kind
             * @enum {string}
             */
            kind: "call" | "import";
            /**
             * Line
             * @default 1
             */
            line?: number;
            /** Path */
            path: string;
            /** Reference */
            reference: string;
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
        /** CoverageDiagnostics */
        CoverageDiagnostics: {
            /** Classified By Kind */
            classified_by_kind: {
                [key: string]: number;
            };
            /** Excluded Files */
            excluded_files?: string[];
            /** File Groups */
            file_groups: {
                [key: string]: string[];
            };
            /** Unresolved By Reason */
            unresolved_by_reason: {
                [key: string]: number;
            };
        };
        /** CsrfToken */
        CsrfToken: {
            /**
             * Schema Version
             * @default 1.0.0
             * @constant
             */
            schema_version?: "1.0.0";
            /** Token */
            token: string;
        };
        /** CurrentUser */
        CurrentUser: {
            /** Display Name */
            display_name: string;
            /**
             * Email
             * Format: email
             */
            email: string;
            /** Id */
            id: string;
            /**
             * Schema Version
             * @default 1.0.0
             * @constant
             */
            schema_version?: "1.0.0";
            /** Verified */
            verified: boolean;
        };
        /** Dashboard */
        Dashboard: {
            /** Ai Statuses */
            ai_statuses: {
                [key: string]: number;
            };
            /** Daily Runs */
            daily_runs: {
                [key: string]: number;
            };
            /**
             * Expires At
             * Format: date-time
             */
            expires_at: string;
            /**
             * Export Limit
             * @default 10000
             */
            export_limit?: number;
            filters: components["schemas"]["ReportFilter"];
            /** Known Actual Micro Usd */
            known_actual_micro_usd: number | null;
            /** Limitations */
            limitations: string[];
            /** Project Count */
            project_count: number;
            /** Reservation Micro Usd */
            reservation_micro_usd: number;
            /**
             * Schema Version
             * @default 1.0.0
             * @constant
             */
            schema_version?: "1.0.0";
            /**
             * Snapshot Id
             * Format: uuid
             */
            snapshot_id: string;
            /** Static Statuses */
            static_statuses: {
                [key: string]: number;
            };
            /** Stored Rows */
            stored_rows: number;
            /** Total Runs */
            total_runs: number;
            /** Unknown Actual Count */
            unknown_actual_count: number;
        };
        /** DashboardQuery */
        DashboardQuery: {
            /** End */
            end?: string | null;
            /** Project Id */
            project_id?: string | null;
            /** Start */
            start?: string | null;
            /** Status */
            status?: ("queued" | "running" | "completed" | "failed" | "interrupted") | null;
            /**
             * Timezone
             * @default UTC
             */
            timezone?: string;
        };
        /** DurableRunExport */
        DurableRunExport: {
            /** Ai Requests */
            ai_requests: components["schemas"]["AiJob"][];
            /**
             * Exported At
             * Format: date-time
             */
            exported_at: string;
            payload: components["schemas"]["SavedRunReport"];
            /**
             * Report Kind
             * @default saved-web-run
             * @constant
             */
            report_kind?: "saved-web-run";
            /**
             * Schema Version
             * @default 1.0.0
             * @constant
             */
            schema_version?: "1.0.0";
        };
        /** EmailInput */
        EmailInput: {
            /**
             * Email
             * Format: email
             */
            email: string;
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
        /** ExcerptRange */
        ExcerptRange: {
            /** End */
            end: number;
            /** Path */
            path: string;
            /** Start */
            start: number;
        };
        /** ExecutionPayload */
        ExecutionPayload: {
            /** Dispatched Test Ids */
            dispatched_test_ids: string[];
            identity: components["schemas"]["RunIdentity"];
            /** Manifest Id */
            manifest_id: string;
            /** Observations */
            observations: components["schemas"]["TestObservation"][];
            /**
             * Termination
             * @enum {string}
             */
            termination: "exited" | "timeout" | "cancelled" | "infrastructure_error" | "output_limit";
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
        /** ExplorerEdge */
        ExplorerEdge: {
            evidence: components["schemas"]["GraphEvidence"];
            /** Id */
            id: string;
            /**
             * Kind
             * @enum {string}
             */
            kind: "contains" | "imports" | "calls";
            /** Source */
            source: string;
            /** Source Path */
            source_path: string;
            /** Target */
            target: string;
            /** Target Path */
            target_path: string;
        };
        /** ExplorerGraph */
        ExplorerGraph: {
            /** Classified References */
            classified_references?: components["schemas"]["ClassifiedReference"][];
            /** Commit */
            commit: string;
            /** Config Digest */
            config_digest: string;
            coverage: components["schemas"]["GraphCoverage"];
            /** Edges */
            edges: components["schemas"]["ExplorerEdge"][];
            /** Nodes */
            nodes: components["schemas"]["ExplorerNode"][];
            /** Overlay Digest */
            overlay_digest?: string | null;
            /** Repository Id */
            repository_id: string;
            /**
             * Schema Version
             * @default 1.0.0
             * @constant
             */
            schema_version?: "1.0.0";
            /** Unresolved */
            unresolved: components["schemas"]["UnresolvedRelation"][];
        };
        /** ExplorerNode */
        ExplorerNode: {
            evidence?: components["schemas"]["GraphEvidence"] | null;
            /** Id */
            id: string;
            /**
             * Kind
             * @enum {string}
             */
            kind: "directory" | "file" | "function" | "class" | "method";
            /** Label */
            label: string;
            /** Path */
            path: string;
            /** Symbol */
            symbol?: string | null;
        };
        /** FeatureMatch */
        FeatureMatch: {
            evidence: components["schemas"]["GraphEvidence"];
            /** Matched Terms */
            matched_terms: string[];
            /** Path */
            path: string;
            /** Score */
            score: number;
            /** Symbol */
            symbol?: string | null;
        };
        /** FeatureQuery */
        FeatureQuery: {
            /** Query */
            query: string;
            /**
             * Top K
             * @default 10
             */
            top_k?: number;
        };
        /** FeatureSearch */
        FeatureSearch: {
            /** Commit */
            commit: string;
            /** Config Digest */
            config_digest: string;
            /** Indexed Chunks */
            indexed_chunks: number;
            /** Items */
            items: components["schemas"]["FeatureMatch"][];
            /** Limitations */
            limitations: string[];
            /** Query */
            query: string;
            /** Repository Id */
            repository_id: string;
            /**
             * Retrieval Version
             * @default web-physical-lexical/1
             * @constant
             */
            retrieval_version?: "web-physical-lexical/1";
            /**
             * Schema Version
             * @default 1.0.0
             * @constant
             */
            schema_version?: "1.0.0";
            /**
             * Status
             * @enum {string}
             */
            status: "matched" | "no_evidence";
            /** Truncated */
            truncated: boolean;
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
        /** GraphCoverage */
        GraphCoverage: {
            /** Analyzed Files */
            analyzed_files: string[];
            diagnostics?: components["schemas"]["CoverageDiagnostics"] | null;
            /**
             * Status
             * @enum {string}
             */
            status: "complete" | "partial";
            /** Unparsed Files */
            unparsed_files: string[];
            /** Unsupported Files */
            unsupported_files: string[];
        };
        /** GraphDelta */
        GraphDelta: {
            /** Added Edges */
            added_edges: components["schemas"]["ExplorerEdge"][];
            /** Added Nodes */
            added_nodes: components["schemas"]["ExplorerNode"][];
            /** Base Commit */
            base_commit: string;
            /** Config Digest */
            config_digest: string;
            /** Limitations */
            limitations: string[];
            /** Removed Edges */
            removed_edges: components["schemas"]["ExplorerEdge"][];
            /** Removed Nodes */
            removed_nodes: components["schemas"]["ExplorerNode"][];
            /** Repository Id */
            repository_id: string;
            /** Retained Edge Count */
            retained_edge_count: number;
            /** Retained Node Count */
            retained_node_count: number;
            /** Target Commit */
            target_commit: string;
            /** Total Added Edges */
            total_added_edges: number;
            /** Total Added Nodes */
            total_added_nodes: number;
            /** Total Removed Edges */
            total_removed_edges: number;
            /** Total Removed Nodes */
            total_removed_nodes: number;
            /**
             * Truncated
             * @default false
             */
            truncated?: boolean;
        };
        /** GraphEvidence */
        GraphEvidence: {
            /** Commit */
            commit: string;
            /** Id */
            id: string;
            /**
             * Kind
             * @default source_range
             * @enum {string}
             */
            kind?: "metadata" | "source_range";
            /** Line End */
            line_end?: number | null;
            /** Line Start */
            line_start?: number | null;
            /** Overlay Digest */
            overlay_digest?: string | null;
            /** Path */
            path: string;
            /**
             * Source Kind
             * @default git
             * @enum {string}
             */
            source_kind?: "git" | "overlay";
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
        /** GraphView */
        GraphView: {
            /** Commit */
            commit: string;
            /** Config Digest */
            config_digest: string;
            coverage: components["schemas"]["GraphCoverage"];
            /** Edges */
            edges: components["schemas"]["ExplorerEdge"][];
            /** Nodes */
            nodes: components["schemas"]["ExplorerNode"][];
            /** Repository Id */
            repository_id: string;
            /** Total Edges */
            total_edges: number;
            /** Total Nodes */
            total_nodes: number;
            /** Truncated */
            truncated: boolean;
        };
        /** HTTPValidationError */
        HTTPValidationError: {
            /** Detail */
            detail?: components["schemas"]["ValidationError"][];
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
        /** Hotspots */
        Hotspots: {
            /** Cross Module Edges */
            cross_module_edges: string[];
            /** Cycles */
            cycles: string[][];
            /** Fan In */
            fan_in: {
                [key: string]: number;
            };
            /** Fan Out */
            fan_out: {
                [key: string]: number;
            };
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
        /** ImpactSummary */
        ImpactSummary: {
            /** Changed */
            changed: string[];
            /** Counts */
            counts: {
                [key: string]: number;
            };
            coverage: components["schemas"]["GraphCoverage"];
            /** Denominator */
            denominator: number | null;
            /** Direct */
            direct: string[];
            /** Indirect */
            indirect: string[];
            /**
             * Interpretation
             * @default potential_static_impact
             * @constant
             */
            interpretation?: "potential_static_impact";
            /** Paths */
            paths: {
                [key: string]: string[];
            };
            /**
             * Paths Truncated
             * @default false
             */
            paths_truncated?: boolean;
            /** Percentages */
            percentages: {
                [key: string]: number | null;
            };
            /** Unknown Changed Count */
            unknown_changed_count: number;
            /** Unresolved Count */
            unresolved_count: number;
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
        /** Login */
        Login: {
            /**
             * Email
             * Format: email
             */
            email: string;
            /**
             * Password
             * Format: password
             */
            password: string;
        };
        /** MessageCreate */
        MessageCreate: {
            /**
             * Action
             * @default chat
             * @enum {string}
             */
            action?: "chat" | "overview" | "changes";
            /**
             * Allow Excerpt Egress
             * @default false
             */
            allow_excerpt_egress?: boolean;
            /**
             * Allow Metadata Egress
             * @default false
             */
            allow_metadata_egress?: boolean;
            /**
             * Allow Model Fallback
             * @default false
             */
            allow_model_fallback?: boolean;
            /** Excerpts */
            excerpts?: components["schemas"]["ExcerptRange"][];
            /** Idempotency Key */
            idempotency_key: string;
            /** Question */
            question: string;
            /**
             * Use Llm
             * @default false
             */
            use_llm?: boolean;
        };
        /** NarrativeEvidence */
        NarrativeEvidence: {
            /**
             * Change
             * @default null
             */
            change?: string | null;
            /**
             * Explanation
             * @default null
             */
            explanation?: string | null;
            /** Id */
            id: string;
            /**
             * Imports
             * @default null
             */
            imports?: string | null;
            /** Path */
            path: string;
            /**
             * Relationship
             * @default null
             */
            relationship?: string | null;
            /**
             * Symbol
             * @default null
             */
            symbol?: string | null;
        };
        /** NarrativeResult */
        NarrativeResult: {
            /** @default null */
            data?: components["schemas"]["RepositoryExplanation"] | null;
            /**
             * Error Code
             * @default null
             */
            error_code?: ("provider_auth" | "provider_permission" | "provider_configuration" | "provider_quota" | "provider_rate_limit" | "provider_timeout" | "provider_transport" | "provider_unavailable" | "provider_refusal" | "provider_empty" | "provider_truncated" | "provider_invalid_output" | "provider_budget") | null;
            /**
             * Model
             * @default null
             */
            model?: string | null;
            /**
             * Prompt Sha256
             * @default null
             */
            prompt_sha256?: string | null;
            /**
             * Reason
             * @default null
             */
            reason?: string | null;
            /**
             * Status
             * @enum {string}
             */
            status: "not_run" | "completed" | "failed";
            /** @default null */
            usage?: components["schemas"]["ProviderUsage"] | null;
        };
        /** Note */
        Note: {
            /** Archived */
            archived: boolean;
            /**
             * Body
             * @default
             */
            body?: string;
            /** Commit */
            commit: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Kind
             * @default note
             * @enum {string}
             */
            kind?: "note" | "pin";
            /** Path */
            path: string;
            /** Stale */
            stale?: boolean | null;
            /** Title */
            title: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
            /** Version */
            version: number;
        };
        /** NoteCreate */
        NoteCreate: {
            /**
             * Body
             * @default
             */
            body?: string;
            /** Commit */
            commit: string;
            /**
             * Kind
             * @default note
             * @enum {string}
             */
            kind?: "note" | "pin";
            /** Path */
            path: string;
            /** Title */
            title: string;
        };
        /** NotePage */
        NotePage: {
            /** Items */
            items: components["schemas"]["Note"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** NoteUpdate */
        NoteUpdate: {
            /**
             * Archived
             * @default false
             */
            archived?: boolean;
            /**
             * Body
             * @default
             */
            body?: string;
            /** Title */
            title: string;
            /** Version */
            version: number;
        };
        /** PasswordChange */
        PasswordChange: {
            /**
             * Current Password
             * Format: password
             */
            current_password: string;
            /**
             * Password
             * Format: password
             */
            password: string;
        };
        /** PasswordReset */
        PasswordReset: {
            /**
             * Password
             * Format: password
             */
            password: string;
            /**
             * Token
             * Format: password
             */
            token: string;
        };
        /** ProfileUpdate */
        ProfileUpdate: {
            /** Display Name */
            display_name: string;
        };
        /** Project */
        Project: {
            /** Archived */
            archived: boolean;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Description */
            description: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Repository Url */
            repository_url: string;
            /**
             * Schema Version
             * @default 1.0.0
             * @constant
             */
            schema_version?: "1.0.0";
            /** Title */
            title: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
            /** Version */
            version: number;
        };
        /** ProjectCreate */
        ProjectCreate: {
            /**
             * Description
             * @default
             */
            description?: string;
            /** Repository Url */
            repository_url: string;
            /** Title */
            title: string;
        };
        /** ProjectPage */
        ProjectPage: {
            /** Items */
            items: components["schemas"]["Project"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** ProjectUpdate */
        ProjectUpdate: {
            /**
             * Description
             * @default
             */
            description?: string;
            /** Title */
            title: string;
            /** Version */
            version: number;
        };
        /** ProjectVersion */
        ProjectVersion: {
            /** Version */
            version: number;
        };
        /**
         * PromptContext
         * @description Authorized text supplied by application, never interpreted as policy.
         */
        PromptContext: {
            reference: components["schemas"]["RetrievalItem"];
            /** Text */
            text: string;
        };
        /** ProposalProvenance */
        ProposalProvenance: {
            /** Configuration Id */
            configuration_id: string;
            /** Context Sha256 */
            context_sha256: string;
            /** Evidence Sha256 */
            evidence_sha256: string;
            identity: components["schemas"]["RunIdentity"];
            /** Inventory Sha256 */
            inventory_sha256: string;
            /** Model */
            model: string;
            /** Prompt Version */
            prompt_version: string;
            /** Provider */
            provider: string;
        };
        /** ProposalRequest */
        ProposalRequest: {
            /** Context */
            context: components["schemas"]["PromptContext"][];
            evidence: components["schemas"]["EvidencePayload"];
            inventory: components["schemas"]["InventoryPayload"];
            provenance: components["schemas"]["ProposalProvenance"];
            retrieval: components["schemas"]["RetrievalPayload"];
            /**
             * Schema Version
             * @constant
             */
            schema_version: "3.0.0";
        };
        /** ProviderResult */
        ProviderResult: {
            /**
             * Actual Model Version
             * @default null
             */
            actual_model_version?: string | null;
            /**
             * Attempts
             * @default 0
             */
            attempts?: number;
            /** @default null */
            data?: components["schemas"]["TestProposal"] | null;
            /**
             * Error Code
             * @default null
             */
            error_code?: ("provider_auth" | "provider_permission" | "provider_configuration" | "provider_quota" | "provider_rate_limit" | "provider_timeout" | "provider_transport" | "provider_unavailable" | "provider_refusal" | "provider_empty" | "provider_truncated" | "provider_invalid_output" | "provider_budget") | null;
            /** @default null */
            provenance?: components["schemas"]["ProposalProvenance"] | null;
            /**
             * Reason
             * @default null
             */
            reason?: string | null;
            /**
             * Status
             * @enum {string}
             */
            status: "not_run" | "completed" | "failed";
            /** @default null */
            usage?: components["schemas"]["ProviderUsage"] | null;
        };
        /** ProviderUsage */
        ProviderUsage: {
            /**
             * Cost Usd
             * @default null
             */
            cost_usd?: number | null;
            /**
             * Duration Seconds
             * @default null
             */
            duration_seconds?: number | null;
            /**
             * Input Tokens
             * @default null
             */
            input_tokens?: number | null;
            /**
             * Output Tokens
             * @default null
             */
            output_tokens?: number | null;
            /**
             * Thinking Tokens
             * @default null
             */
            thinking_tokens?: number | null;
            /**
             * Total Tokens
             * @default null
             */
            total_tokens?: number | null;
        };
        /** ReadingGuide */
        ReadingGuide: {
            /** Commit */
            commit: string;
            /** Config Digest */
            config_digest: string;
            /**
             * Entrypoint Status
             * @enum {string}
             */
            entrypoint_status: "observed" | "unknown";
            /** Limitations */
            limitations: string[];
            /** Repository Id */
            repository_id: string;
            /**
             * Schema Version
             * @default 1.0.0
             * @constant
             */
            schema_version?: "1.0.0";
            /** Steps */
            steps: components["schemas"]["ReadingStep"][];
        };
        /** ReadingStep */
        ReadingStep: {
            /**
             * Category
             * @enum {string}
             */
            category: "entrypoint" | "module" | "data" | "tests";
            evidence: components["schemas"]["GraphEvidence"];
            /** Path */
            path: string;
            /** Reason */
            reason: string;
        };
        /** Registration */
        Registration: {
            /** Display Name */
            display_name: string;
            /**
             * Email
             * Format: email
             */
            email: string;
            /**
             * Password
             * Format: password
             */
            password: string;
        };
        /** ReportFilter */
        ReportFilter: {
            /**
             * As Of
             * Format: date-time
             */
            as_of: string;
            /**
             * End
             * Format: date-time
             */
            end: string;
            /** Project Id */
            project_id?: string | null;
            /**
             * Start
             * Format: date-time
             */
            start: string;
            /** Status */
            status?: ("queued" | "running" | "completed" | "failed" | "interrupted") | null;
            /** Timezone */
            timezone: string;
        };
        /** RepositoryAnalysisRequest */
        RepositoryAnalysisRequest: {
            /**
             * Allow Metadata Egress
             * @default false
             */
            allow_metadata_egress?: boolean;
            /** Base */
            base: string;
            /**
             * Question
             * @default Giải thích cấu trúc dự án và ảnh hưởng của các file thay đổi.
             */
            question?: string;
            /** Repository Url */
            repository_url: string;
            /** Target */
            target: string;
            /**
             * Use Llm
             * @default true
             */
            use_llm?: boolean;
        };
        /** RepositoryAnalysisResponse */
        RepositoryAnalysisResponse: {
            /**
             * Execution Status
             * @default not_run
             * @constant
             */
            execution_status?: "not_run";
            /** Files */
            files: string[];
            /** Limitations */
            limitations: string[];
            narrative: components["schemas"]["NarrativeResult"];
            /** Narrative Evidence */
            narrative_evidence: components["schemas"]["NarrativeEvidence"][];
            report: components["schemas"]["StageAnalysisReport"];
            repository: components["schemas"]["RepositoryOverview"];
            /**
             * Schema Version
             * @default 1.0.0
             * @constant
             */
            schema_version?: "1.0.0";
            /**
             * Selection Status
             * @default not_run
             * @constant
             */
            selection_status?: "not_run";
        };
        /** RepositoryCommit */
        RepositoryCommit: {
            /** Date */
            date: string;
            /** Message */
            message: string;
            /** Sha */
            sha: string;
        };
        /** RepositoryExplanation */
        RepositoryExplanation: {
            /** Findings */
            findings: components["schemas"]["RepositoryFinding"][];
            /** Limitations */
            limitations: string[];
            /** Summary */
            summary: string;
        };
        /** RepositoryFinding */
        RepositoryFinding: {
            /** Evidence Ids */
            evidence_ids: string[];
            /** Explanation */
            explanation: string;
            /** Path */
            path: string;
        };
        /** RepositoryLookup */
        RepositoryLookup: {
            /** Repository Url */
            repository_url: string;
        };
        /** RepositoryOverview */
        RepositoryOverview: {
            /** Commits */
            commits: components["schemas"]["RepositoryCommit"][];
            /** Default Branch */
            default_branch: string;
            /** Full Name */
            full_name: string;
            /** Repository Url */
            repository_url: string;
            /**
             * Schema Version
             * @default 1.0.0
             * @constant
             */
            schema_version?: "1.0.0";
        };
        /**
         * RepositoryReportExport
         * @description Portable offline report; export time is not the analysis execution time.
         */
        RepositoryReportExport: {
            /**
             * Exported At
             * Format: date-time
             */
            exported_at: string;
            payload: components["schemas"]["RepositoryAnalysisResponse"];
            /**
             * Report Kind
             * @default repository-analysis
             * @constant
             */
            report_kind?: "repository-analysis";
            /**
             * Schema Version
             * @default 1.0.0
             * @constant
             */
            schema_version?: "1.0.0";
        };
        /** RepositoryTree */
        RepositoryTree: {
            /** Commit */
            commit: string;
            /** Entries */
            entries: components["schemas"]["RepositoryTreeEntry"][];
            /** Repository Url */
            repository_url: string;
            /**
             * Schema Version
             * @default 1.0.0
             * @constant
             */
            schema_version?: "1.0.0";
            /** Tree Sha */
            tree_sha: string;
        };
        /** RepositoryTreeEntry */
        RepositoryTreeEntry: {
            /**
             * Kind
             * @enum {string}
             */
            kind: "directory" | "file" | "symlink" | "submodule";
            /** Path */
            path: string;
            /** Size */
            size?: number | null;
        };
        /** RepositoryTreeRequest */
        RepositoryTreeRequest: {
            /** Commit */
            commit: string;
            /** Repository Url */
            repository_url: string;
        };
        /** RepositoryWatch */
        RepositoryWatch: {
            /** Automatic */
            automatic: boolean;
            /** Branch */
            branch: string;
            /** Checked At */
            checked_at: string | null;
            /** Error Code */
            error_code: string | null;
            /** Interval Seconds */
            interval_seconds: number;
            /** Last Commit */
            last_commit: string;
            /**
             * Next Check At
             * Format: date-time
             */
            next_check_at: string;
            /** Paths */
            paths: string[];
            /** Pending */
            pending: boolean;
            /**
             * Schema Version
             * @default 1.0.0
             * @constant
             */
            schema_version?: "1.0.0";
            /** Version */
            version: number;
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
        /** RunCreate */
        RunCreate: {
            /** Base */
            base: string;
            /** Idempotency Key */
            idempotency_key: string;
            /** Target */
            target: string;
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
        /** RunPage */
        RunPage: {
            /** Items */
            items: components["schemas"]["WebRun"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** SavedRunReport */
        SavedRunReport: {
            payload: components["schemas"]["RepositoryAnalysisResponse"];
            run: components["schemas"]["WebRun"];
            /**
             * Schema Version
             * @default 1.0.0
             * @constant
             */
            schema_version?: "1.0.0";
        };
        /** Scenario */
        Scenario: {
            /**
             * Analysis Kind
             * @enum {string}
             */
            analysis_kind: "static_overlay" | "hypothesis";
            /** Baseline */
            baseline: string;
            /** Config Digest */
            config_digest: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            delta: components["schemas"]["GraphDelta"] | null;
            graph: components["schemas"]["ExplorerGraph"] | null;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            impact: components["schemas"]["ImpactSummary"] | null;
            /** Input */
            input: string;
            /** Input Digest */
            input_digest: string;
            /** Limitations */
            limitations: string[];
            /**
             * Mode
             * @enum {string}
             */
            mode: "code" | "diff" | "description";
            narrative: components["schemas"]["NarrativeResult"];
            /** Path */
            path: string;
            /**
             * Project Id
             * Format: uuid
             */
            project_id: string;
            /**
             * Schema Version
             * @default 1.0.0
             * @constant
             */
            schema_version?: "1.0.0";
            /** Title */
            title: string;
        };
        /** ScenarioCompareInput */
        ScenarioCompareInput: {
            /**
             * Left
             * Format: uuid
             */
            left: string;
            /**
             * Right
             * Format: uuid
             */
            right: string;
        };
        /** ScenarioComparison */
        ScenarioComparison: {
            /** Added Affected */
            added_affected: string[];
            /** Baseline */
            baseline: string;
            /**
             * Comparison Kind
             * @default static_overlays
             * @enum {string}
             */
            comparison_kind?: "static_overlays" | "hypotheses";
            /** Config Digest */
            config_digest: string;
            graph_delta: components["schemas"]["GraphDelta"] | null;
            /**
             * Interpretation
             * @default no_safety_ranking
             * @constant
             */
            interpretation?: "no_safety_ranking";
            /**
             * Left
             * Format: uuid
             */
            left: string;
            /** Removed Affected */
            removed_affected: string[];
            /** Retained Affected */
            retained_affected: string[];
            /**
             * Right
             * Format: uuid
             */
            right: string;
            /** Unresolved Left */
            unresolved_left: number | null;
            /** Unresolved Right */
            unresolved_right: number | null;
        };
        /** ScenarioCreate */
        ScenarioCreate: {
            /** Baseline */
            baseline: string;
            /** Idempotency Key */
            idempotency_key: string;
            /** Input */
            input: string;
            /**
             * Mode
             * @enum {string}
             */
            mode: "code" | "diff" | "description";
            /** Path */
            path: string;
            /** Title */
            title: string;
        };
        /** ScenarioExport */
        ScenarioExport: {
            /** Ai Requests */
            ai_requests: components["schemas"]["AiJob"][];
            /**
             * Exported At
             * Format: date-time
             */
            exported_at: string;
            payload: components["schemas"]["Scenario"];
            /**
             * Report Kind
             * @default saved-scenario
             * @constant
             */
            report_kind?: "saved-scenario";
            /**
             * Schema Version
             * @default 1.0.0
             * @constant
             */
            schema_version?: "1.0.0";
        };
        /** ScenarioView */
        ScenarioView: {
            /** Added Edge Count */
            added_edge_count: number | null;
            /** Added Node Count */
            added_node_count: number | null;
            /** Added Symbols */
            added_symbols: string[];
            /**
             * Analysis Kind
             * @enum {string}
             */
            analysis_kind: "static_overlay" | "hypothesis";
            /** Baseline */
            baseline: string;
            /** Config Digest */
            config_digest: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            impact: components["schemas"]["ImpactSummary"] | null;
            /** Input Digest */
            input_digest: string;
            /** Limitations */
            limitations: string[];
            /**
             * Mode
             * @enum {string}
             */
            mode: "code" | "diff" | "description";
            /** Path */
            path: string;
            /**
             * Project Id
             * Format: uuid
             */
            project_id: string;
            /** Removed Edge Count */
            removed_edge_count: number | null;
            /** Removed Node Count */
            removed_node_count: number | null;
            /** Removed Symbols */
            removed_symbols: string[];
            /** Title */
            title: string;
        };
        /** ScenarioViewPage */
        ScenarioViewPage: {
            /** Items */
            items: components["schemas"]["ScenarioView"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** ScopeImpact */
        ScopeImpact: {
            /** Chain */
            chain: string[];
            /** Evidence */
            evidence: components["schemas"]["GraphEvidence"][];
            /** Path */
            path: string;
            /**
             * Relationship
             * @enum {string}
             */
            relationship: "changed" | "direct" | "indirect";
        };
        /** SelectionManifest */
        SelectionManifest: {
            /** Configuration Id */
            configuration_id: string;
            identity: components["schemas"]["RunIdentity"];
            inventory: components["schemas"]["InventoryPayload"];
            /** Inventory Sha256 */
            inventory_sha256: string;
            /** Manifest Id */
            manifest_id: string;
            /**
             * Mode
             * @enum {string}
             */
            mode: "hybrid" | "dependency_fallback" | "full_suite" | "no_tests";
            /** Not Selected */
            not_selected: string[];
            /**
             * Policy Version
             * @constant
             */
            policy_version: "s1-selection-v1";
            /** Reason */
            reason: string;
            /** Selected */
            selected: string[];
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
        /** SnapshotInfo */
        SnapshotInfo: {
            /** Commit */
            commit: string;
            /** Config Digest */
            config_digest: string;
            coverage: components["schemas"]["GraphCoverage"];
            /** Excluded Count */
            excluded_count: number;
            /** Total Edges */
            total_edges: number;
            /** Total Nodes */
            total_nodes: number;
            /** Tree Entries */
            tree_entries: number;
        };
        /** SnapshotPayload */
        SnapshotPayload: {
            base: components["schemas"]["SnapshotIdentity"];
            target: components["schemas"]["SnapshotIdentity"];
        };
        /** SnapshotRequest */
        SnapshotRequest: {
            /** Commit */
            commit: string;
        };
        /** SourceLocation */
        SourceLocation: {
            /** Line End */
            line_end: number;
            /** Line Start */
            line_start: number;
        };
        /** SourceRange */
        SourceRange: {
            /** Commit */
            commit: string;
            /** Content */
            content: string;
            /** Line End */
            line_end: number;
            /** Line Start */
            line_start: number;
            /** Overlay Digest */
            overlay_digest?: string | null;
            /** Path */
            path: string;
            /**
             * Source Kind
             * @default git
             * @enum {string}
             */
            source_kind?: "git" | "overlay";
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
        /** StageResult[ExecutionPayload] */
        StageResult_ExecutionPayload_: {
            /** @default null */
            data?: components["schemas"]["ExecutionPayload"] | null;
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
        /** StageResult[SelectionManifest] */
        StageResult_SelectionManifest_: {
            /** @default null */
            data?: components["schemas"]["SelectionManifest"] | null;
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
        /** TestObservation */
        TestObservation: {
            /**
             * Duration Seconds
             * @default null
             */
            duration_seconds?: number | null;
            /**
             * Outcome
             * @enum {string}
             */
            outcome: "passed" | "failed" | "skipped" | "error";
            /** Test Id */
            test_id: string;
        };
        /** TestProposal */
        TestProposal: {
            /** Suggestions */
            suggestions: components["schemas"]["TestSuggestion"][];
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
        /** TestSuggestion */
        TestSuggestion: {
            /** Evidence Ids */
            evidence_ids: string[];
            /** Reason */
            reason: string;
            /** Test Id */
            test_id: string;
        };
        /** ThreadCreate */
        ThreadCreate: {
            /** Commit */
            commit: string;
            /** Idempotency Key */
            idempotency_key: string;
            /**
             * Title
             * @default Hỏi về repository
             */
            title?: string;
        };
        /** TokenInput */
        TokenInput: {
            /**
             * Token
             * Format: password
             */
            token: string;
        };
        /** UnresolvedRelation */
        UnresolvedRelation: {
            /**
             * Line
             * @default 1
             */
            line?: number;
            /** Path */
            path: string;
            /** Reason */
            reason: string;
            /** Reference */
            reference: string;
        };
        /** UsagePage */
        UsagePage: {
            /** Items */
            items: components["schemas"]["UsageRecord"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** UsageRecord */
        UsageRecord: {
            /** Action */
            action: string;
            /** Actual Micro Usd */
            actual_micro_usd: number | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Project Id
             * Format: uuid
             */
            project_id: string;
            /** Reservation Micro Usd */
            reservation_micro_usd: number;
            /** Run Id */
            run_id: string | null;
            /** Status */
            status: string;
        };
        /** ValidationError */
        ValidationError: {
            /** Context */
            ctx?: Record<string, never>;
            /** Input */
            input?: unknown;
            /** Location */
            loc: (string | number)[];
            /** Message */
            msg: string;
            /** Error Type */
            type: string;
        };
        /** VersionCompareInput */
        VersionCompareInput: {
            /** Base */
            base: string;
            /** Target */
            target: string;
        };
        /** ViewState */
        ViewState: {
            /** Commit */
            commit: string;
            /** Expanded Paths */
            expanded_paths?: string[];
            /**
             * Focus Only
             * @default false
             */
            focus_only?: boolean;
            /** Path */
            path?: string | null;
            /** Stale */
            stale?: boolean | null;
            /**
             * Tab
             * @default graph
             * @enum {string}
             */
            tab?: "tree" | "graph" | "details";
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
            /** Version */
            version: number;
        };
        /** ViewStateInput */
        ViewStateInput: {
            /** Commit */
            commit: string;
            /** Expanded Paths */
            expanded_paths?: string[];
            /**
             * Focus Only
             * @default false
             */
            focus_only?: boolean;
            /** Path */
            path?: string | null;
            /**
             * Tab
             * @default graph
             * @enum {string}
             */
            tab?: "tree" | "graph" | "details";
            /** Version */
            version: number;
        };
        /** WatchInput */
        WatchInput: {
            /**
             * Automatic
             * @default false
             */
            automatic?: boolean;
            /** Branch */
            branch: string;
            /**
             * Interval Seconds
             * @default 600
             */
            interval_seconds?: number;
            /** Paths */
            paths?: string[];
            /**
             * Version
             * @default 0
             */
            version?: number;
        };
        /** WebCapabilities */
        WebCapabilities: {
            /** Local Demo */
            local_demo: boolean;
            /**
             * Schema Version
             * @default 1.0.0
             * @constant
             */
            schema_version?: "1.0.0";
        };
        /** WebRun */
        WebRun: {
            /**
             * Ai Status
             * @enum {string}
             */
            ai_status: "not_run" | "running" | "completed" | "failed";
            /** Base */
            base: string;
            /** Config Digest */
            config_digest: string;
            /** Error Code */
            error_code: string | null;
            /** Finished At */
            finished_at: string | null;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Project Id
             * Format: uuid
             */
            project_id: string;
            /** Report Available */
            report_available: boolean;
            /** Repository Url */
            repository_url: string;
            /**
             * Schema Version
             * @default 1.0.0
             * @constant
             */
            schema_version?: "1.0.0";
            /**
             * Started At
             * Format: date-time
             */
            started_at: string;
            /**
             * Status
             * @enum {string}
             */
            status: "queued" | "running" | "completed" | "failed" | "interrupted";
            /** Target */
            target: string;
        };
        /** WebhookReceipt */
        WebhookReceipt: {
            /** Accepted */
            accepted: boolean;
            /** Duplicate */
            duplicate: boolean;
            /** Scheduled */
            scheduled: number;
        };
        /**
         * WorkflowReport
         * @description v3 envelope preserves the complete v2 analysis without fake later stages.
         */
        WorkflowReport: {
            analysis: components["schemas"]["StageAnalysisReport"];
            execution: components["schemas"]["StageResult_ExecutionPayload_"];
            proposal: components["schemas"]["ProviderResult"];
            /**
             * Schema Version
             * @constant
             */
            schema_version: "3.0.0";
            selection: components["schemas"]["StageResult_SelectionManifest_"];
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
    change_api_v1_auth_change_password_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PasswordChange"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthMessage"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unprocessable Content */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Too Many Requests */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
        };
    };
    get_csrf_api_v1_auth_csrf_get: {
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
                    "application/json": components["schemas"]["CsrfToken"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unprocessable Content */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Too Many Requests */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
        };
    };
    forgot_api_v1_auth_forgot_password_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["EmailInput"];
            };
        };
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthMessage"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unprocessable Content */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Too Many Requests */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
        };
    };
    login_api_v1_auth_login_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["Login"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CurrentUser"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unprocessable Content */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Too Many Requests */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
        };
    };
    logout_api_v1_auth_logout_post: {
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
                    "application/json": components["schemas"]["AuthMessage"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unprocessable Content */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Too Many Requests */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
        };
    };
    me_api_v1_auth_me_get: {
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
                    "application/json": components["schemas"]["CurrentUser"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unprocessable Content */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Too Many Requests */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
        };
    };
    update_me_api_v1_auth_me_patch: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ProfileUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CurrentUser"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unprocessable Content */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Too Many Requests */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
        };
    };
    register_api_v1_auth_register_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["Registration"];
            };
        };
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthMessage"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unprocessable Content */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Too Many Requests */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
        };
    };
    resend_api_v1_auth_resend_verification_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["EmailInput"];
            };
        };
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthMessage"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unprocessable Content */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Too Many Requests */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
        };
    };
    reset_api_v1_auth_reset_password_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PasswordReset"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthMessage"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unprocessable Content */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Too Many Requests */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
        };
    };
    verify_api_v1_auth_verify_email_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TokenInput"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthMessage"];
                };
            };
            /** @description Bad Request */
            400: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unauthorized */
            401: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Forbidden */
            403: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Unprocessable Content */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Too Many Requests */
            429: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
            /** @description Service Unavailable */
            503: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AuthErrorResponse"];
                };
            };
        };
    };
    capabilities_api_v1_capabilities_get: {
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
                    "application/json": components["schemas"]["WebCapabilities"];
                };
            };
        };
    };
    webhook_api_v1_github_webhook_post: {
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
                    "application/json": components["schemas"]["WebhookReceipt"];
                };
            };
        };
    };
    listing_api_v1_projects_get: {
        parameters: {
            query?: {
                search?: string;
                archived?: boolean;
                cursor?: string | null;
                limit?: number;
            };
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
                    "application/json": components["schemas"]["ProjectPage"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_api_v1_projects_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ProjectCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Project"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    detail_api_v1_projects__project_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
            };
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
                    "application/json": components["schemas"]["Project"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_api_v1_projects__project_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ProjectUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Project"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    activity_api_v1_projects__project_id__activity_get: {
        parameters: {
            query?: {
                cursor?: string | null;
                limit?: number;
            };
            header?: never;
            path: {
                project_id: string;
            };
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
                    "application/json": components["schemas"]["ActivityPage"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    archive_api_v1_projects__project_id__archive_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ProjectVersion"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Project"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    assistance_list_api_v1_projects__project_id__assistance_ai_get: {
        parameters: {
            query: {
                commit: string;
            };
            header?: never;
            path: {
                project_id: string;
            };
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
                    "application/json": components["schemas"]["AiJob"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    assistance_api_v1_projects__project_id__assistance_ai_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AssistanceAiRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AiJob"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    assistance_get_api_v1_projects__project_id__assistance_ai__request_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
                request_id: string;
            };
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
                    "application/json": components["schemas"]["AiJob"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    check_api_v1_projects__project_id__assistant_check_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RepositoryWatch"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    notifications_api_v1_projects__project_id__assistant_notifications_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
            };
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
                    "application/json": components["schemas"]["ChangeNotification"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    mark_read_api_v1_projects__project_id__assistant_notifications__notification_id__read_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
                notification_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    overview_api_v1_projects__project_id__assistant_overview_post: {
        parameters: {
            query?: {
                commit?: string | null;
            };
            header?: never;
            path: {
                project_id: string;
            };
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
                    "application/json": components["schemas"]["AssistantReply"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    threads_api_v1_projects__project_id__assistant_threads_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
            };
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
                    "application/json": components["schemas"]["AssistantThread"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_thread_api_v1_projects__project_id__assistant_threads_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ThreadCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AssistantThread"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    delete_thread_api_v1_projects__project_id__assistant_threads__thread_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
                thread_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    messages_api_v1_projects__project_id__assistant_threads__thread_id__messages_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
                thread_id: string;
            };
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
                    "application/json": components["schemas"]["AssistantMessage"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    send_api_v1_projects__project_id__assistant_threads__thread_id__messages_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
                thread_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["MessageCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AssistantMessage"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    preview_api_v1_projects__project_id__assistant_threads__thread_id__preview_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
                thread_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["MessageCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AssistantReply"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    watch_api_v1_projects__project_id__assistant_watch_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
            };
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
                    "application/json": components["schemas"]["RepositoryWatch"] | null;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    save_watch_api_v1_projects__project_id__assistant_watch_put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["WatchInput"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RepositoryWatch"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    versions_api_v1_projects__project_id__graph_comparisons_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["VersionCompareInput"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GraphDelta"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    listing_api_v1_projects__project_id__notes_get: {
        parameters: {
            query?: {
                cursor?: string | null;
                limit?: number;
                current?: string | null;
            };
            header?: never;
            path: {
                project_id: string;
            };
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
                    "application/json": components["schemas"]["NotePage"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_api_v1_projects__project_id__notes_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["NoteCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Note"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    update_api_v1_projects__project_id__notes__note_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
                note_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["NoteUpdate"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Note"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    repository_api_v1_projects__project_id__repository_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
            };
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
                    "application/json": components["schemas"]["RepositoryOverview"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    restore_api_v1_projects__project_id__restore_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ProjectVersion"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Project"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    listing_api_v1_projects__project_id__runs_get: {
        parameters: {
            query?: {
                cursor?: string | null;
                limit?: number;
            };
            header?: never;
            path: {
                project_id: string;
            };
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
                    "application/json": components["schemas"]["RunPage"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_api_v1_projects__project_id__runs_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RunCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["WebRun"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    detail_api_v1_projects__project_id__runs__run_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
                run_id: string;
            };
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
                    "application/json": components["schemas"]["WebRun"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    request_ai_api_v1_projects__project_id__runs__run_id__ai_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
                run_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AiRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AiJob"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    detail_api_v1_projects__project_id__runs__run_id__ai__request_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
                run_id: string;
                request_id: string;
            };
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
                    "application/json": components["schemas"]["AiJob"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    run_api_v1_projects__project_id__runs__run_id__export_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
                run_id: string;
            };
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
                    "application/json": components["schemas"]["DurableRunExport"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    report_api_v1_projects__project_id__runs__run_id__report_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
                run_id: string;
            };
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
                    "application/json": components["schemas"]["SavedRunReport"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    compare_api_v1_projects__project_id__scenario_comparisons_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ScenarioCompareInput"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ScenarioComparison"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    listing_api_v1_projects__project_id__scenarios_get: {
        parameters: {
            query?: {
                cursor?: string | null;
                limit?: number;
            };
            header?: never;
            path: {
                project_id: string;
            };
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
                    "application/json": components["schemas"]["ScenarioViewPage"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_api_v1_projects__project_id__scenarios_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ScenarioCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ScenarioView"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    detail_api_v1_projects__project_id__scenarios__scenario_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
                scenario_id: string;
            };
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
                    "application/json": components["schemas"]["ScenarioView"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    scenario_api_v1_projects__project_id__scenarios__scenario_id__export_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
                scenario_id: string;
            };
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
                    "application/json": components["schemas"]["ScenarioExport"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    graph_api_v1_projects__project_id__scenarios__scenario_id__graph_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
                scenario_id: string;
            };
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
                    "application/json": components["schemas"]["GraphView"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    source_api_v1_projects__project_id__scenarios__scenario_id__source_get: {
        parameters: {
            query?: {
                start?: number;
                end?: number;
            };
            header?: never;
            path: {
                project_id: string;
                scenario_id: string;
            };
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
                    "application/json": components["schemas"]["SourceRange"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    materialize_api_v1_projects__project_id__snapshots_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SnapshotRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SnapshotInfo"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    calls_api_v1_projects__project_id__snapshots__commit__calls_get: {
        parameters: {
            query: {
                node: string;
                depth?: number;
                limit?: number;
            };
            header?: never;
            path: {
                project_id: string;
                commit: string;
            };
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
                    "application/json": components["schemas"]["CallPaths"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    graph_api_v1_projects__project_id__snapshots__commit__graph_get: {
        parameters: {
            query?: {
                focus?: string | null;
                limit?: number;
                direction?: "both" | "dependencies" | "dependents";
                depth?: number;
            };
            header?: never;
            path: {
                project_id: string;
                commit: string;
            };
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
                    "application/json": components["schemas"]["GraphView"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    hotspots_api_v1_projects__project_id__snapshots__commit__hotspots_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
                commit: string;
            };
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
                    "application/json": components["schemas"]["Hotspots"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    impact_api_v1_projects__project_id__snapshots__commit__impact_get: {
        parameters: {
            query: {
                path: string;
            };
            header?: never;
            path: {
                project_id: string;
                commit: string;
            };
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
                    "application/json": components["schemas"]["ImpactSummary"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    nodes_api_v1_projects__project_id__snapshots__commit__nodes_get: {
        parameters: {
            query?: {
                offset?: number;
                limit?: number;
                search?: string;
            };
            header?: never;
            path: {
                project_id: string;
                commit: string;
            };
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
                    "application/json": components["schemas"]["ExplorerNode"][];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    guide_api_v1_projects__project_id__snapshots__commit__reading_guide_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
                commit: string;
            };
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
                    "application/json": components["schemas"]["ReadingGuide"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    search_api_v1_projects__project_id__snapshots__commit__search_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
                commit: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["FeatureQuery"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["FeatureSearch"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    source_api_v1_projects__project_id__snapshots__commit__source_get: {
        parameters: {
            query: {
                path: string;
                start?: number;
                end?: number;
            };
            header?: never;
            path: {
                project_id: string;
                commit: string;
            };
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
                    "application/json": components["schemas"]["SourceRange"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    tree_api_v1_projects__project_id__snapshots__commit__tree_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
                commit: string;
            };
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
                    "application/json": components["schemas"]["RepositoryTree"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    tree_api_v1_projects__project_id__tree_get: {
        parameters: {
            query: {
                commit: string;
            };
            header?: never;
            path: {
                project_id: string;
            };
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
                    "application/json": components["schemas"]["RepositoryTree"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    view_api_v1_projects__project_id__view_state_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
            };
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
                    "application/json": components["schemas"]["ViewState"] | null;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    save_api_v1_projects__project_id__view_state_put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                project_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ViewStateInput"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ViewState"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    create_api_v1_reporting_views_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["DashboardQuery"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Dashboard"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    read_api_v1_reporting_views__view_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                view_id: string;
            };
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
                    "application/json": components["schemas"]["Dashboard"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    download_api_v1_reporting_views__view_id__csv_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                view_id: string;
            };
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
                    "application/json": unknown;
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    listing_api_v1_reporting_views__view_id__runs_get: {
        parameters: {
            query?: {
                offset?: number;
                limit?: number;
            };
            header?: never;
            path: {
                view_id: string;
            };
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
                    "application/json": components["schemas"]["RunPage"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    usage_api_v1_reporting_views__view_id__usage_get: {
        parameters: {
            query?: {
                offset?: number;
                limit?: number;
            };
            header?: never;
            path: {
                view_id: string;
            };
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
                    "application/json": components["schemas"]["UsagePage"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    usage_api_v1_usage_get: {
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
                    "application/json": components["schemas"]["AiQuota"];
                };
            };
        };
    };
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
    inspect_repository_repositories_inspect_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RepositoryLookup"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RepositoryOverview"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    repository_tree_repositories_tree_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RepositoryTreeRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RepositoryTree"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    analyze_repository_repository_analyses_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RepositoryAnalysisRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RepositoryAnalysisResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
}
