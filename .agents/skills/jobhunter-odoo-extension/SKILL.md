---
name: jobhunter-odoo-extension
description: Build or review the Jobhunter AI extension in its owning Odoo 20 addon repository, including Odoo data access, permissions, and coexistence with existing recruiting automation.
---

# Jobhunter Odoo extension

This is a development workflow. Apply application changes in the external owning repository identified in [project context](../../../context/project.md), not in this harness repository. Read the [product contract](../../../context/product-contract.md) and relevant [decisions](../../../context/decisions.md) before choosing an implementation.

## Workflow

1. Discover the actual Odoo checkout, version, addon layout, recruitment models, access rules, and test commands. Confirm the local Odoo 20 target from evidence; do not treat a configured path as proof the server is running.
2. Implement the integration as a new addon that extends the current internal Odoo application. Keep Odoo as the system of record for jobs, candidates, permissions, and business stages. The separately deployed AI backend owns its execution state and derived artifacts.
3. Inspect [capabilities](../../../context/capabilities.json) and real integration interfaces before selecting tools. Registered capabilities are requirements or observations, not callable tool names. Discover available tools in the current session.
4. Carry authenticated user/company scope into every data operation. Respect Odoo access rights and record rules; avoid direct SQL or blanket `sudo()` to bypass them. Keep credentials outside source files and browser bundles.
5. Map Odoo identifiers and source versions to the backend contract. Preserve original document references and available content hashes so changed or deleted sources can invalidate affected outputs.
6. Make coexistence opt-in per enabled harness job. Disable old conflicting automation only for jobs using the new extension; preserve legacy behavior elsewhere. Include an upgrade and rollback path that preserves existing records.
7. Validate installation/update, authorized and unauthorized access, company isolation, source refresh, opt-in coexistence, and rollback in a disposable development database. Report actual commands and results to the coordinator.

Invoking this skill does not authorize live candidate-stage changes, criteria approval, outreach, booking, or other business mutations. Build the requested integration without performing recruiting operations. Only the coordinator updates harness progress with `.venv/bin/python scripts/harness.py progress update`; return evidence for that update.

## Sources

Original local workflow; no third-party skill package is vendored. Source links checked on **2026-10-30**; verify version-specific APIs against the actual checkout when implementing.

- [Odoo 20 access-control guidance](https://www.odoo.com/documentation/20.0/developer/tutorials/restrict_data_access.html)
- [Odoo 20 testing guidance](https://www.odoo.com/documentation/20.0/developer/tutorials/unit_tests.html)
- [Project source registry](../../../context/sources.json)
