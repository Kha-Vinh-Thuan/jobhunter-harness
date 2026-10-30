---
name: jobhunter-aws-deployment
description: Prepare or validate the future Jobhunter AI backend deployment pipeline on AWS ECS Fargate in the owning backend repository, while keeping existing Odoo hosting separate.
---

# Jobhunter AWS deployment

This skill governs future backend deployment work. Read the [project context](../../../context/project.md), relevant [decisions](../../../context/decisions.md), [product contract](../../../context/product-contract.md), and [capabilities](../../../context/capabilities.json). Deployment code and workflows belong in the external owning backend repository, not in this harness folder.

## Workflow

1. Discover the backend repository, AWS account, region, network, domain, ECS resources, runtime dependencies, and Odoo connectivity from the actual environment. Treat unset targets as missing input; never invent account IDs, endpoints, resources, or a running deployment.
2. Use **ECS Fargate for the AI backend**. Keep the existing Odoo application and its deployment separate. Inspect the backend's process model and shutdown behavior before selecting API/worker tasks and rollout settings.
3. Build the pipeline in the backend repository: offline checks/tests, container build, ECR push, staging deployment, smoke verification, production promotion, and post-deployment health verification. Use immutable commit-linked image digests so the running revision and rollback target can be identified.
4. Authenticate CI with GitHub OIDC and narrowly scoped IAM roles. Separate runtime task permissions from image-pull/logging execution permissions. Reference Secrets Manager/SSM for runtime secrets; do not place secrets in source, images, workflow output, browser bundles, or harness progress.
5. Keep durable execution checkpoints in external Postgres and artifacts/progress snapshots in S3. Fargate task storage is not durable execution state. Verify recovery after task replacement and prevent duplicate external effects on resume.
6. Configure health checks, graceful shutdown, operational logs/metrics, deployment failure detection, and rollback to the previous successful image/revision. Validate streaming connection behavior and Odoo network access in staging, including reconnect during task replacement.
7. Execute only the deployment work authorized for the concrete target. Skill invocation alone does not authorize provisioning, production changes, live Odoo writes, or business actions. Use available tools discovered in the current session and report unavailable capabilities precisely.
8. Return the deployed revision, environment, health evidence, rollback target, migration status, and open issues. A generated pipeline is prepared, not deployed; a healthy container alone does not prove Odoo integration or an interview flow works.

Only the coordinator updates harness progress using `.venv/bin/python scripts/harness.py progress update`. Until the target app/infrastructure is available, deployment checks remain **Not run** or **Not configured**, not passed.

## Sources

Original local workflow; no third-party skill package is vendored. Source links checked on **2026-10-30**; recheck deployment APIs and regional availability when implementing.

- [AWS ECR with GitHub Actions and OIDC](https://docs.aws.amazon.com/prescriptive-guidance/latest/patterns/build-and-push-docker-images-to-amazon-ecr-using-github-actions-and-terraform.html)
- [ECS IAM roles](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/security-iam-roles.html)
- [ECS deployment circuit breaker and rollback](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-circuit-breaker.html)
- [Project source registry](../../../context/sources.json)
