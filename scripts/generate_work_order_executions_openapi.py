#!/usr/bin/env python3
"""Generate openapi/work-order-executions.json and MDX snippet data for Work Order Execution API."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

BASE = "https://expertappapi-sandbox.deere.com"
PREFIX = "/delsol/workorder-micro-v2"

# (method, path_after_prefix, summary, description, extra_query_params, path_param_desc)
# path starts with /api or /testharness

OPERATIONS: list[tuple[str, str, str, str, list[dict], dict[str, str]]] = []

def op(
    method: str,
    rel_path: str,
    summary: str,
    description: str,
    queries: list[dict] | None = None,
    param_desc: dict[str, str] | None = None,
) -> None:
    OPERATIONS.append(
        (method, rel_path, summary, description, queries or [], param_desc or {})
    )


# --- Register all operations (order matches logical groups in source doc) ---

op("GET", "/api/customer/dbsCustomer", "getDBSCustomers", "Retrieve DBS customer records for the authenticated context.")
op("GET", "/api/features", "Get feature toggle list", "Returns feature toggles available for the current user.")
op("GET", "/api/feature", "Check feature for user", "Returns whether a feature is enabled for the given user.")

op("POST", "/api/images", "Upload image or file", "Upload an image or file attached to a job.")
op("GET", "/api/images/{id}", "Download image or file", "Download an image or file attached to a job by identifier.")
op("PUT", "/api/images/{id}", "Replace image", "Replace the image or file for the supplied identifier.")
op("DELETE", "/api/images/{id}", "Delete image or file", "Delete an image or file after it is removed from the associated job.")

op("GET", "/api/inspections", "Get completed inspections", "List inspections filtered by status (for example `COMPLETED`).", [{"name": "status", "schema": {"type": "string", "example": "COMPLETED"}, "description": "Filter inspections by status."}])

op("GET", "/api/locations/{locationId}/technicianLocations", "Technician locations by location", "Returns all locations for the given location identifier.")
op("GET", "/api/technicians/{userId}/technicianLocations", "Technician locations by user", "Returns all locations for the given user identifier.")

op("GET", "/api/machine/{serialNumber}/smartInfo", "Machine smart info", "View machine information for the supplied serial number.")
op("GET", "/api/machines/{serialNumber}/warrantydetails", "Machine warranty details", "View warranty details for the given machine.")

op("GET", "/api/segments/{id}", "Get segment by ID", "View a segment related to a work order.")
op("GET", "/api/segments", "List segments", "View all segments related to a work order.")

op("POST", "/api/servicequotes/byId", "Create service quote by ID", "Create a new service quote with optional Expert Services job IDs or checklist ID at segment level.")
op("GET", "/api/servicequotes/groupByServiceArea", "List service quotes by service area", "View all available service quotes grouped by service area.")
op("GET", "/api/servicequotes/{id}", "Get service quote", "View a service quote. Optional query `groupby=serviceArea` returns grouping by service area.", [{"name": "groupby", "schema": {"type": "string", "example": "serviceArea"}, "description": "Optional grouping."}])
op("PUT", "/api/servicequotes/{id}", "Update service quote", "Update a service quote. Optional `reportType=SERVICE_QUOTE_SUMMARY` generates a summary report.", [{"name": "reportType", "schema": {"type": "string", "example": "SERVICE_QUOTE_SUMMARY"}, "description": "When set, triggers report generation."}, {"name": "notificationType", "schema": {"type": "string", "example": "SERVICE_QUOTE_SUMMARY"}, "description": "When set, triggers notification behavior."}])
op("DELETE", "/api/servicequotes/{id}", "Delete service quote", "Delete a service quote.")
op("HEAD", "/api/servicequotes/{id}", "serviceQuoteExists", "Returns headers indicating whether the service quote exists.")
op("PATCH", "/api/servicequotes/{id}", "Patch service quote", "Update specific properties of a service quote.")
op("GET", "/api/servicequotes/{id}/groupByServiceArea", "Get service quote by service area", "View a service quote grouped by service area.")
op("PUT", "/api/servicequotes/{id}/notification", "Send service quote email notification", "Send email notification for the service quote.")
op("PUT", "/api/servicequotes/{id}/patch", "Patch service quote (alternate path)", "Update specific properties of a service quote.")
op("PUT", "/api/servicequotes/{id}/report", "Generate service quote summary report", "Generate a service quote summary report.")

op("GET", "/api/servicequotes/{serviceQuoteId}/segments", "List segments for service quote", "View all segments for a service quote. Optional `groupby=serviceArea`. Optional `notificationType=PARTS_ONLY_SUMMARY` for parts-only email.", [{"name": "groupby", "schema": {"type": "string"}, "description": "Group results by service area."}, {"name": "notificationType", "schema": {"type": "string", "example": "PARTS_ONLY_SUMMARY"}, "description": "Parts-only email notification."}])
op("POST", "/api/servicequotes/{serviceQuoteId}/segments", "Create segment on service quote", "Create a new segment on a service quote.")
op("POST", "/api/servicequotes/{serviceQuoteId}/segments/adHoc", "Add ad hoc segment to service quote", "Add an ad hoc job segment to a service quote.")
op("POST", "/api/servicequotes/{serviceQuoteId}/segments/byId", "Add segment by checklist or jobs", "Add a segment from Expert Services checklist ID or job IDs.")
op("GET", "/api/servicequotes/{serviceQuoteId}/segments/groupByServiceArea/{id}", "Get segment grouped by service area", "View a segment related to a service quote with service-area grouping.")
op("GET", "/api/servicequotes/{serviceQuoteId}/segments/groupByServiceArea", "List segments grouped by service area", "View all segments for a service quote grouped by service area.")
op("PUT", "/api/servicequotes/{serviceQuoteId}/segments/notification", "Parts-only email for service quote segments", "Send parts-only email notification for segments.")
op("GET", "/api/servicequotes/{serviceQuoteId}/segments/{id}", "Get segment on service quote", "View a segment. Optional `groupby=serviceArea`.", [{"name": "groupby", "schema": {"type": "string"}, "description": "Optional grouping."}])
op("PUT", "/api/servicequotes/{serviceQuoteId}/segments/{id}", "Update segment on service quote", "Update a segment related to a service quote.")
op("DELETE", "/api/servicequotes/{serviceQuoteId}/segments/{id}", "Delete segment on service quote", "Delete a segment related to a service quote.")
op("PATCH", "/api/servicequotes/{serviceQuoteId}/segments/{id}", "Patch segment on service quote", "Update specific properties of a segment.")

op("POST", "/api/servicequotes/{serviceQuoteId}/segments/{segmentId}/checklists/byId", "Add checklist by ID to segment", "Create and add a checklist to a segment using an Expert Services checklist ID.")
op("POST", "/api/servicequotes/{serviceQuoteId}/segments/{segmentId}/checklists/{checklistId}/jobs/adHoc", "Ad hoc job on checklist (service quote)", "Create an ad hoc job in Expert Services and add it to the checklist.")
op("POST", "/api/servicequotes/{serviceQuoteId}/segments/{segmentId}/checklists/{checklistId}/jobs/byId", "Add Expert Services job to checklist", "Add a published Expert Services job to a checklist on a segment.")

# Parts under checklist / tasks — explicit
base_sq_parts = "/api/servicequotes/{serviceQuoteId}/segments/{segmentId}/checklists/{checklistId}/tasks/{jobId}/parts"
op("GET", f"{base_sq_parts}/{{partId}}", "Get part (service quote checklist task)", "Get a part by ID for a checklist task on a service quote.")
op("PUT", f"{base_sq_parts}/{{partId}}", "Put part (service quote checklist task)", "Update a part by ID on a checklist task.")
op("DELETE", f"{base_sq_parts}/{{partId}}", "Delete part (service quote checklist task)", "Delete a part by ID on a checklist task.")
op("PATCH", f"{base_sq_parts}/{{partId}}", "Patch part (service quote checklist task)", "Patch a part by ID on a checklist task.")
op("GET", base_sq_parts, "List parts (service quote checklist task)", "Get all parts on the service estimate job (checklist task path).")
op("PUT", base_sq_parts, "Put parts array (service quote checklist task)", "Replace parts using a part array.")
op("POST", base_sq_parts, "Create part (service quote checklist task)", "Create a new part on the job.")

op("GET", "/api/servicequotes/{serviceQuoteId}/segments/{segmentId}/checklists/{id}", "Get checklist on service quote segment", "View a checklist inside a segment for a service quote.")
op("POST", "/api/servicequotes/{serviceQuoteId}/segments/{segmentId}/checklists", "Create checklist on segment", "Create and add a checklist to a segment. Use query `type=byId` with Expert Services checklist ID in body.", [{"name": "type", "schema": {"type": "string", "example": "byId"}, "description": "When `byId`, body references Expert Services checklist identifier."}])

op("GET", "/api/servicequotes/{serviceQuoteId}/segments/{segmentId}/jobs", "List jobs on service quote segment", "View all jobs inside a segment for a service quote.")
op("GET", "/api/servicequotes/{serviceQuoteId}/segments/{segmentId}/jobs/{id}", "Get job on service quote segment", "View a job inside a segment for a service quote.")
op("PUT", "/api/servicequotes/{serviceQuoteId}/segments/{segmentId}/jobs/{id}", "Update job on service quote segment", "Update a job inside a segment for a service quote.")
op("PATCH", "/api/servicequotes/{serviceQuoteId}/segments/{segmentId}/jobs/{id}", "Patch job on service quote segment", "Update specific properties of a job.")

base_sq_job_parts = "/api/servicequotes/{serviceQuoteId}/segments/{segmentId}/jobs/{jobId}/parts"
op("GET", f"{base_sq_job_parts}/{{partId}}", "Get part (service quote job path)", "Get a part by ID on a service quote segment job.")
op("PUT", f"{base_sq_job_parts}/{{partId}}", "Put part (service quote job path)", "Update a part by ID on a segment job.")
op("DELETE", f"{base_sq_job_parts}/{{partId}}", "Delete part (service quote job path)", "Delete a part by ID on a segment job.")
op("PATCH", f"{base_sq_job_parts}/{{partId}}", "Patch part (service quote job path)", "Patch a part by ID on a segment job.")
op("GET", base_sq_job_parts, "List parts (service quote job path)", "Get all parts on the service estimate job.")
op("PUT", base_sq_job_parts, "Put parts array (service quote job path)", "Replace parts using a part array.")
op("POST", base_sq_job_parts, "Create part (service quote job path)", "Create a new part on the job.")

op("GET", "/api/servicequotes", "List service quotes", "View all available service quotes. Optional `groupby=serviceArea`.", [{"name": "groupby", "schema": {"type": "string", "example": "serviceArea"}, "description": "Group quotes by service area."}])
op("POST", "/api/servicequotes", "Create service quote", "Create a new empty service quote.")

# Work orders
op("POST", "/api/workorders/byId", "Create work order by ID", "Create a work order with optional Expert Services job IDs or checklist ID at segment level.")
op("GET", "/api/workorders/groupByServiceArea", "List work orders by service area", "View work orders grouped by service area.")
op("GET", "/api/workorders/{id}", "Get work order", "View a work order. Optional `groupby=serviceArea`.", [{"name": "groupby", "schema": {"type": "string", "example": "serviceArea"}, "description": "Group by service area."}])
op("PUT", "/api/workorders/{id}", "Update work order", "Update a work order. Optional `reportType=WORK_ORDER_SUMMARY` to generate a summary report.", [{"name": "reportType", "schema": {"type": "string", "example": "WORK_ORDER_SUMMARY"}, "description": "When set, generates work order summary report."}])
op("DELETE", "/api/workorders/{id}", "Delete work order", "Delete a work order.")
op("HEAD", "/api/workorders/{id}", "workOrderExists", "Returns whether the work order exists.")
op("PATCH", "/api/workorders/{id}", "Patch work order", "Update specific properties of a work order.")
op("GET", "/api/workorders/{id}/groupByServiceArea", "Get work order by service area", "View a work order grouped by service area.")
op("PUT", "/api/workorders/{id}/message", "Send work order XML to Service Delivery", "Send work order notification XML to Service Delivery.")
op("PUT", "/api/workorders/{id}/notification", "Work order summary email", "Send email notification of work order summary.")
op("PUT", "/api/workorders/{id}/patch", "Patch work order (alternate path)", "Update properties of a work order.")
op("PUT", "/api/workorders/{id}/report", "Generate work order summary report", "Generate report of work order summary.")

op("POST", "/api/workorders/{workOrderId}/segments/adHoc", "Add ad hoc segment to work order", "Add an ad hoc job segment to a work order.")
op("POST", "/api/workorders/{workOrderId}/segments/byId", "Add segment by checklist or jobs", "Add a segment from job IDs or checklist ID.")
op("GET", "/api/workorders/{workOrderId}/segments/groupByServiceArea", "List WO segments by service area", "View segments for a work order grouped by service area.")
op("GET", "/api/workorders/{workOrderId}/segments/{id}", "Get work order segment", "View a segment related to a work order.")
op("PUT", "/api/workorders/{workOrderId}/segments/{id}", "Update work order segment", "Update a segment related to a work order.")
op("DELETE", "/api/workorders/{workOrderId}/segments/{id}", "Delete work order segment", "Delete a segment related to a work order.")
op("PATCH", "/api/workorders/{workOrderId}/segments/{id}", "Patch work order segment", "Update properties of a segment.")
op("GET", "/api/workorders/{workOrderId}/segments/{id}/groupByServiceArea", "Get WO segment by service area", "View a segment with service-area grouping.")
op("PUT", "/api/workorders/{workOrderId}/segments/{id}/notification", "Inspection summary email (segment)", "Send email notification of inspection summary details.")
op("PUT", "/api/workorders/{workOrderId}/segments/{id}/repairNotification", "Repair notification email", "Send email notification for repair summary.")
op("PUT", "/api/workorders/{workOrderId}/segments/{id}/repairReport", "Repair summary report", "Generate inspection summary report (repair).")
op("PUT", "/api/workorders/{workOrderId}/segments/{id}/report", "Inspection summary report", "Generate inspection summary report. Optional `reportType=INSPECTION_SUMMARY`.", [{"name": "reportType", "schema": {"type": "string", "example": "INSPECTION_SUMMARY"}, "description": "Report variant."}])

op("POST", "/api/workorders/{workOrderId}/segments/{segmentId}/actions", "Create segment action", "Create a new segment action.")
op("GET", "/api/workorders/{workOrderId}/segments/{segmentId}/actions/{actionId}", "Get segment action", "Return an action for the given business key.")

op("POST", "/api/workorders/{workOrderId}/segments/{segmentId}/checklists/{checklistId}/jobs/{jobId}/images", "Add image to checklist task", "Add an image to a checklist task.")
op("DELETE", "/api/workorders/{workOrderId}/segments/{segmentId}/checklists/{checklistId}/jobs/{jobId}/images/{id}", "Remove image from checklist task", "Remove an image from the checklist task.")

op("POST", "/api/workorders/{workOrderId}/segments/{segmentId}/checklists/{checklistId}/tasks", "Create checklist task", "Create a new task on a checklist.")
op("GET", "/api/workorders/{workOrderId}/segments/{segmentId}/checklists/{checklistId}/tasks/{id}", "Get checklist task", "Get a task on a checklist.")
op("DELETE", "/api/workorders/{workOrderId}/segments/{segmentId}/checklists/{checklistId}/tasks/{id}", "Delete checklist task", "Delete a task on a checklist.")
op("PATCH", "/api/workorders/{workOrderId}/segments/{segmentId}/checklists/{checklistId}/tasks/{id}", "Patch checklist task", "Update properties on a checklist task.")

base_wo_ck_parts = "/api/workorders/{workOrderId}/segments/{segmentId}/checklists/{checklistId}/tasks/{jobId}/parts"
op("GET", f"{base_wo_ck_parts}/{{partId}}", "Get part (work order checklist task)", "Get a part by ID on a work order checklist task.")
op("PUT", f"{base_wo_ck_parts}/{{partId}}", "Put part (work order checklist task)", "Update a part on a checklist task.")
op("DELETE", f"{base_wo_ck_parts}/{{partId}}", "Delete part (work order checklist task)", "Delete a part on a checklist task.")
op("PATCH", f"{base_wo_ck_parts}/{{partId}}", "Patch part (work order checklist task)", "Patch a part on a checklist task.")
op("GET", base_wo_ck_parts, "List parts (work order checklist task)", "Get all parts on the work order job.")
op("PUT", base_wo_ck_parts, "Put parts array (work order checklist task)", "Replace parts using a part array.")
op("POST", base_wo_ck_parts, "Create part (work order checklist task)", "Create a new part on the job.")

op("GET", "/api/workorders/{workOrderId}/segments/{segmentId}/checklists/{id}", "Get checklist on work order segment", "View a checklist inside a segment for a work order.")
op("PATCH", "/api/workorders/{workOrderId}/segments/{segmentId}/checklists/{id}", "Patch checklist", "Patch values on a checklist.")
op("POST", "/api/workorders/{workOrderId}/segments/{segmentId}/checklists", "Create checklist on WO segment", "Add a checklist using query `type=byId` and Expert Services checklist ID.", [{"name": "type", "schema": {"type": "string", "example": "byId"}, "description": "Use `byId` to reference Expert Services checklist."}])

op("GET", "/api/workorders/{workOrderId}/segments/{segmentId}/jobs", "List jobs on work order segment", "View all jobs inside a segment for a work order.")
op("GET", "/api/workorders/{workOrderId}/segments/{segmentId}/jobs/{id}", "Get job on work order segment", "View a job inside a segment for a work order.")
op("PUT", "/api/workorders/{workOrderId}/segments/{segmentId}/jobs/{id}", "Update job on work order segment", "Update a job inside a segment for a work order.")
op("PATCH", "/api/workorders/{workOrderId}/segments/{segmentId}/jobs/{id}", "Patch job on work order segment", "Update properties of a job.")

base_wo_job_parts = "/api/workorders/{workOrderId}/segments/{segmentId}/jobs/{jobId}/parts"
op("GET", f"{base_wo_job_parts}/{{partId}}", "Get part (work order job path)", "Get a part by ID on a work order segment job.")
op("PUT", f"{base_wo_job_parts}/{{partId}}", "Put part (work order job path)", "Update a part by ID on a segment job.")
op("DELETE", f"{base_wo_job_parts}/{{partId}}", "Delete part (work order job path)", "Delete a part by ID on a segment job.")
op("PATCH", f"{base_wo_job_parts}/{{partId}}", "Patch part (work order job path)", "Patch a part by ID on a segment job.")
op("GET", base_wo_job_parts, "List parts (work order job path)", "Get all parts on the work order job.")
op("PUT", base_wo_job_parts, "Put parts array (work order job path)", "Replace parts using a part array.")
op("POST", base_wo_job_parts, "Create part (work order job path)", "Create a new part on the job.")

op("POST", "/api/workorders/{workOrderId}/segments/{segmentId}/laborResources", "Create labor resource", "Create a new labor resource (POST).")
op("GET", "/api/workorders/{workOrderId}/segments/{segmentId}/laborResources/{laborResourceId}", "Get labor resource", "Get a labor resource for the given business key.")
op("PUT", "/api/workorders/{workOrderId}/segments/{segmentId}/laborResources/{laborResourceId}", "Upsert labor resource", "Create or update a labor resource by identifier.")

op("GET", "/api/workorders/{workOrderId}/segments", "List work order segments", "View segments for a work order. Optional `groupby=serviceArea`.", [{"name": "groupby", "schema": {"type": "string"}, "description": "Group by service area."}])
op("POST", "/api/workorders/{workOrderId}/segments", "Create work order segment", "Create a new segment related to a work order.")

op("GET", "/api/workorders", "List work orders", "View all available work orders. Optional `groupby=serviceArea`.", [{"name": "groupby", "schema": {"type": "string", "example": "serviceArea"}, "description": "Group by service area."}])
op("POST", "/api/workorders", "Create work order", "Create a new work order.")

op("GET", "/api/translations/locales", "List translation locales", "Get all locales available for translations.")
op("POST", "/api/translations/update", "Update translations", "Update translations for a locale.")
op("GET", "/api/translations", "Get translations", "Get translations for the requested locale.")

op("GET", "/api/undercarriage", "Get undercarriage info", "Get undercarriage information for equipment (query parameters as required by the service).")

op("GET", "/testharness", "Health check", "Service health check endpoint.")


def path_to_operation_id(method: str, full_path: str) -> str:
    slug = re.sub(r"[{}]", "", full_path)
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", slug).strip("_")
    # Do not truncate — long paths must stay unique (e.g. .../parts vs .../parts/{partId}).
    return f"{method.lower()}_{slug}"


def path_params(path: str) -> list[str]:
    return re.findall(r"\{([^}]+)\}", path)


def build_curl(method: str, full_path: str, queries: list[dict]) -> str:
    """Example URL with placeholder path segments."""
    example = full_path
    replacements = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "serviceQuoteId": "sq-1001",
        "workOrderId": "wo-2002",
        "segmentId": "seg-3003",
        "checklistId": "chk-4004",
        "jobId": "job-5005",
        "partId": "part-6006",
        "locationId": "loc-7007",
        "userId": "user-8008",
        "serialNumber": "1XYZ1234567890123",
        "laborResourceId": "lr-9009",
        "actionId": "act-1010",
    }
    for name, val in replacements.items():
        example = example.replace("{" + name + "}", val)
    q = "&".join(
        f"{p['name']}={p.get('schema', {}).get('example', 'value')}"
        for p in queries[:1]
    )
    url = f"{BASE}{example}"
    if q and "?" not in example:
        url = f"{url}?{q}"
    accept = "application/json"
    if method == "DELETE" and "images" in full_path:
        accept = "*/*"
    if full_path.endswith("/testharness"):
        accept = "application/xml"
    if method == "GET" and full_path.endswith("/api/customer/dbsCustomer"):
        accept = "*/*"
    if method == "GET" and full_path.endswith("/api/features"):
        accept = "*/*"
    if method == "GET" and full_path.endswith("/api/feature"):
        accept = "*/*"
    if "translations" in full_path and method in ("GET", "POST"):
        accept = "*/*"
    lines = [
        f"curl --request {method} \\",
        f"  --url '{url}' \\",
        "  --header 'Authorization: Bearer <access_token>' \\",
        f"  --header 'Accept: {accept}'",
    ]
    if method in ("POST", "PUT", "PATCH"):
        lines[-1] = lines[-1] + " \\"
        lines.append("  --header 'Content-Type: application/json' \\")
        lines.append("  --data '{}'" if method != "PUT" or "parts" not in full_path else "  --data '[]'")
    return "\\n".join(lines)


def error_responses() -> dict[str, Any]:
    er = {"$ref": "#/components/schemas/ErrorResponse"}
    return {
        "401": {"description": "Unauthorized.", "content": {"application/json": {"schema": er}}},
        "403": {"description": "Forbidden.", "content": {"application/json": {"schema": er}}},
    }


def build_spec() -> dict[str, Any]:
    paths: dict[str, Any] = {}
    for method, rel, summary, desc, queries, param_desc in OPERATIONS:
        full_path = PREFIX + rel
        if full_path not in paths:
            paths[full_path] = {}
        op_id = path_to_operation_id(method, full_path)
        parameters: list[dict] = []
        for pname in path_params(rel):
            parameters.append(
                {
                    "name": pname,
                    "in": "path",
                    "required": True,
                    "description": param_desc.get(pname, f"Path parameter `{pname}`."),
                    "schema": {"type": "string", "example": "string"},
                }
            )
        for q in queries:
            parameters.append(
                {
                    "name": q["name"],
                    "in": "query",
                    "required": False,
                    "description": q.get("description", ""),
                    "schema": q.get("schema", {"type": "string"}),
                }
            )
        body_methods = {"POST", "PUT", "PATCH"}
        request_body = None
        if method in body_methods and method != "DELETE":
            request_body = {
                "required": False,
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/JsonPayload"},
                        "example": {},
                    }
                },
            }
        if method == "PUT" and "/parts" in rel and rel.endswith("/parts"):
            request_body = {
                "required": False,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/JsonPayload"},
                        },
                        "example": [],
                    }
                },
            }

        responses: dict[str, Any] = {
            "200": {
                "description": "Successful response.",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/JsonPayload"},
                        "example": {"status": "ok"},
                    }
                },
            },
            **error_responses(),
        }
        if method == "DELETE":
            responses = {
                "204": {"description": "Deleted successfully."},
                **error_responses(),
            }
        elif method == "HEAD":
            responses = {
                "200": {"description": "Resource exists."},
                "404": {"description": "Not found."},
                **error_responses(),
            }
        if method == "POST" and rel == "/api/images":
            responses["200"]["content"]["application/json"]["example"] = {"id": "img-uuid", "url": "..."}
        if method == "GET" and rel == "/testharness":
            responses["200"]["content"] = {
                "application/xml": {
                    "schema": {"type": "string"},
                    "example": "<status>ok</status>",
                }
            }

        op_obj: dict[str, Any] = {
            "operationId": op_id,
            "summary": summary,
            "description": desc,
            "security": [{"OAuth2": ["axiom"]}],
            "parameters": parameters,
            "x-codeSamples": [
                {
                    "lang": "bash",
                    "label": "cURL",
                    "source": build_curl(method, PREFIX + rel, queries),
                }
            ],
            "responses": responses,
        }
        if request_body is not None:
            op_obj["requestBody"] = request_body
        paths[full_path][method.lower()] = op_obj

    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Work Order Execution Microservice API",
            "description": "Dealers and technicians can inspect, repair, and maintain equipment by creating digital work orders and service estimates. The API supports step-by-step jobs, segments, checklists, parts, labor, notifications, and integration with Service Delivery.",
            "version": "2.0.0",
        },
        "servers": [{"url": BASE, "description": "Sandbox (Expert App API — work order microservice)"}],
        "components": {
            "securitySchemes": {
                "OAuth2": {
                    "type": "oauth2",
                    "description": "OAuth 2.0. Use the authorization code flow (three-legged) for interactive users, or the client credentials grant for machine-to-machine access. The `axiom` scope is required unless your product documentation states otherwise.",
                    "flows": {
                        "clientCredentials": {
                            "tokenUrl": "https://signin.johndeere.com/oauth2/aus78tnlaysMraFhC1t7/v1/token",
                            "scopes": {"axiom": "Dealer Solutions API access"},
                        }
                    },
                }
            },
            "schemas": {
                "JsonPayload": {
                    "type": "object",
                    "description": "JSON request or response body; shape depends on the operation.",
                    "additionalProperties": True,
                    "example": {"id": "550e8400-e29b-41d4-a716-446655440000", "status": "OPEN"},
                },
                "ErrorResponse": {
                    "type": "object",
                    "properties": {
                        "error": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "string", "example": "UNAUTHORIZED"},
                                "message": {"type": "string", "example": "Invalid or expired access token."},
                            },
                        }
                    },
                },
            },
        },
        "paths": paths,
    }


def generate_mdx() -> str:
    lines: list[str] = [
        '---',
        'title: "Work Order Execution API"',
        'description: "Create and manage digital work orders and service estimates, including segments, checklists, jobs, parts, and Service Delivery integration."',
        "---",
        "",
        "## Overview",
        "",
        "The Work Order Execution microservice lets dealers and technicians inspect, repair, and maintain equipment through digital **work orders** and **service estimates** (service quotes). Technicians can run step-by-step jobs, add segments from Expert Services checklists or job IDs, manage parts and labor, and send notifications and reports. The API aligns with **Service Delivery** for creating and updating work orders and supports customer quoting.",
        "",
        "<CardGroup cols={2}>",
        '  <Card title="Work orders" icon="wrench">',
        "    Create, list, update, and delete work orders; group by service area; send notifications, XML to Service Delivery, and summary reports.",
        "  </Card>",
        '  <Card title="Service quotes" icon="file-invoice">',
        "    Manage service estimates with the same segment, checklist, job, and part flows as work orders.",
        "  </Card>",
        '  <Card title="Equipment & customers" icon="tractor">',
        "    Machine smart info, warranty details, undercarriage data, DBS customers, locations, and technician locations.",
        "  </Card>",
        '  <Card title="OAuth 2.0" icon="lock">',
        "    Authenticate with John Deere Dealer Solutions using the authorization code flow or client credentials. These endpoints require the **axiom** scope.",
        "  </Card>",
        "</CardGroup>",
        "",
        "---",
        "",
        "## Authentication",
        "",
        "John Deere Dealer Solutions APIs use **OAuth 2.0**. Use the **authorization code** flow (three-legged) for interactive users, or the **client credentials** grant for machine-to-machine integrations.",
        "",
        "**OAuth scope required for these endpoints:** `axiom` (unless your product documentation specifies a different scope).",
        "",
        "### Client credentials (machine-to-machine)",
        "",
        "<Steps>",
        "  <Step title=\"Create an application on Developer.Deere.com\">",
        "    Register your application to receive a **Client Key** and **Client Secret**. All API requests are signed with these credentials.",
        "",
        "    In the Security section of your application, add at least one Callback URL (Redirect URI). You may use a placeholder such as `https://localhost:9090/callback` if a redirect URI is not required for your flow.",
        "  </Step>",
        "  <Step title=\"Call the well-known URL\">",
        "    Discover the authorization and token endpoints, and the scopes available for your integration.",
        "",
        "    ```bash",
        "    GET https://signin.johndeere.com/oauth2/aus78tnlaysMraFhC1t7/.well-known/oauth-authorization-server",
        "    ```",
        "  </Step>",
        "  <Step title=\"Acquire an access token\">",
        "    POST to the token endpoint using the `client_credentials` grant. Place your Client Key and Secret in the HTTP `Authorization` header using HTTP Basic Auth — **not** in the request body.",
        "",
        "    ```bash",
        "    POST https://signin.johndeere.com/oauth2/aus78tnlaysMraFhC1t7/v1/token",
        "    ```",
        "",
        "    **Headers:**",
        "",
        "    ```",
        "    Authorization: Basic <base64(clientKey:clientSecret)>",
        "    Accept: application/json",
        "    Content-Type: application/x-www-form-urlencoded",
        "    ```",
        "",
        "    **Body:**",
        "",
        "    ```",
        "    grant_type=client_credentials&scope=axiom",
        "    ```",
        "",
        "    **Response:**",
        "",
        "    ```json",
        "    {",
        '      "token_type": "Bearer",',
        '      "expires_in": 43200,',
        '      "access_token": "eyJhbG[...]1LQ",',
        '      "scope": "axiom"',
        "    }",
        "    ```",
        "",
        "    <Note>",
        "      The access token expires after **12 hours**. Refresh it by repeating this step before expiry.",
        "    </Note>",
        "  </Step>",
        "  <Step title=\"Call the API with your access token\">",
        "    Include the token in the `Authorization` header of every request.",
        "",
        "    ```bash",
        "    Authorization: Bearer <access_token>",
        "    ```",
        "  </Step>",
        "</Steps>",
        "",
        "### Authorization code (interactive users)",
        "",
        "For three-legged OAuth, send `response_type=code` with your client ID, URL-encoded redirect URI, `state`, and required scopes (including `axiom`). Exchange the authorization code at the token endpoint. Request `offline_access` if you need a refresh token (refresh tokens expire after 365 days of non-use).",
        "",
        "<Note>",
        "  If callback URLs do not sync correctly, users may see a **400 Bad Redirect** after authentication. Save redirect URIs on Developer.Deere.com and contact support if redirects fail in testing.",
        "</Note>",
        "",
        "---",
        "",
        "## Base URL",
        "",
        "```",
        BASE,
        "```",
        "",
        "API paths for this microservice are rooted under `/delsol/workorder-micro-v2` (for example `/delsol/workorder-micro-v2/api/workorders`).",
        "",
        "---",
        "",
        "## Endpoints",
        "",
    ]

    for method, rel, summary, desc, queries, _param_desc in OPERATIONS:
        full = PREFIX + rel
        nav_key = f"{method} {full}"
        lines.append(f"### {summary}")
        lines.append("")
        lines.append(desc)
        lines.append("")
        lines.append(f"```")
        lines.append(f"{method} {full}")
        lines.append("```")
        lines.append("")
        lines.append("**OAuth Scope Required:** `axiom`")
        lines.append("")
        for pname in path_params(rel):
            lines.append(f'<ParamField path="{pname}" type="string" required>')
            lines.append(f"  Path parameter `{pname}`.")
            lines.append("</ParamField>")
            lines.append("")
        for q in queries:
            qn = q["name"]
            lines.append(f'<ParamField query="{qn}" type="string">')
            lines.append(f"  {q.get('description', '')}")
            lines.append("</ParamField>")
            lines.append("")
        if method in ("POST", "PUT", "PATCH"):
            lines.append('<ParamField body="payload" type="object">')
            lines.append("  JSON body for this operation (structure depends on the resource).")
            lines.append("</ParamField>")
            lines.append("")
        sample = build_curl(method, full, queries).replace("\\n", "\n")
        lines.append("<CodeGroup>")
        lines.append("")
        lines.append("```bash cURL")
        lines.append(sample)
        lines.append("```")
        lines.append("")
        lines.append("</CodeGroup>")
        lines.append("")
        lines.append("#### Response")
        lines.append("")
        lines.append('<ResponseField name="(body)" type="object">')
        lines.append("  Response is JSON unless otherwise noted (for example `GET /testharness` may return XML).")
        lines.append("</ResponseField>")
        lines.append("")
        lines.append(f'<Card title="Try it in the API Playground" icon="play" href="/{nav_key}">')
        lines.append("  Test this endpoint interactively with your access token.")
        lines.append("</Card>")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    spec = build_spec()
    out = root / "openapi" / "work-order-executions.json"
    out.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out} with {len(OPERATIONS)} operations")

    mdx_path = root / "dealer_solutions" / "service" / "work-order-executions.mdx"
    mdx_path.write_text(generate_mdx(), encoding="utf-8")
    print(f"Wrote {mdx_path}")


if __name__ == "__main__":
    main()
