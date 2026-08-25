# Text-to-Speech App — DevOps Case Study

A gTTS-powered Text-to-Speech service (FastAPI backend + HTML/CSS/JS frontend),
deployed with production-grade DevOps practices: Docker, Terraform-provisioned AWS
ECS/Fargate, GitHub Actions CI/CD, and Prometheus/Grafana monitoring — with an
equivalent Kubernetes deployment path included.

> **Note on the brief:** the assignment template referenced a "Spring Boot" app.
> The actual application here is the FastAPI/gTTS service described above; every
> infra/pipeline component below targets that app instead (container port `8000`,
> Python test tooling, `/health` and `/metrics` endpoints, etc.).

---

## 1. Architecture

```
Browser (frontend/index.html)
        │  fetch()
        ▼
Application Load Balancer  (public subnets)
        │
        ▼
ECS Fargate Service (2–6 tasks, private subnets)
        │
        ▼
FastAPI container ── gTTS ──> Google Translate TTS endpoint (outbound only)
        │
        ▼
CloudWatch Logs  +  /metrics ── Prometheus ── Grafana
```

- **No inbound SSH anywhere** — Fargate tasks have no host to SSH into. This is a
  deliberate security improvement over the "allow SSH" line in the original brief,
  not an oversight. Use `aws ecs execute-command` for interactive debugging.
- **Stateless by design** — generated `.mp3` files live in a container-local `/tmp`
  directory and are deleted after download; nothing persists across task restarts.

---

## 2. Repository layout

```
.
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI routes: /health, /voices, /convert, /audio/{id}, /metrics
│   │   ├── tts_service.py   # gTTS wrapper + curated voice presets
│   │   ├── models.py        # Pydantic request/response schemas
│   │   └── config.py
│   ├── tests/test_main.py   # pytest suite (7 tests, run in CI)
│   ├── requirements.txt
│   ├── Dockerfile           # multi-stage, non-root, ~150MB slim image
│   └── .dockerignore
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js            # voice select, preview, save-as-mp3
├── infra/terraform/
│   ├── main.tf               # provider + S3/DynamoDB remote state
│   ├── vpc.tf                 # VPC, public/private subnets, NAT, routing
│   ├── security_groups.tf     # ALB sg (80/443 in) + ECS task sg (from ALB only)
│   ├── ecr.tf                 # repo, scan-on-push, keep-last-5 lifecycle policy
│   ├── alb.tf                 # ALB, target group (/health), listener
│   ├── iam.tf                 # execution role, task role, GitHub OIDC deploy role
│   ├── ecs.tf                 # cluster, task def, service, autoscaling (CPU 60%)
│   ├── variables.tf / outputs.tf
│   └── terraform.tfvars.example
├── k8s/                       # Kubernetes equivalent (EKS-ready)
│   ├── namespace.yaml / configmap.yaml
│   ├── deployment.yaml        # 2 replicas, probes, non-root, read-only rootfs
│   ├── service.yaml / ingress.yaml   # ALB Ingress Controller
│   └── hpa.yaml                # CPU 60% / memory 75% autoscaling
├── .github/workflows/ci-cd.yaml   # build→test→push→prune→deploy→smoke-test
├── monitoring/
│   ├── prometheus.yml
│   ├── cloudwatch-exporter-config.yml
│   └── grafana-dashboard.json
└── docs/README.md (this file)
```

---

## 3. Local development

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend — just open frontend/index.html, or serve it:
cd frontend
python -m http.server 5500
# then set window.TTS_API_BASE = "http://localhost:8000" before app.js loads
# if serving frontend and backend from different origins.
```

Run tests:
```bash
cd backend
pip install pytest httpx
pytest tests/ -v
```

Build and run the container:
```bash
cd backend
docker build -t tts-backend:local .
docker run -p 8000:8000 tts-backend:local
curl http://localhost:8000/health
```

---

## 4. AWS deployment (Terraform + ECS)

**Prerequisites (one-time, manual):**
1. Create the S3 bucket + DynamoDB table referenced in `main.tf`'s backend block.
2. Update `iam.tf`'s GitHub OIDC role trust condition with your actual `org/repo`.
3. In the GitHub repo, add these **Secrets**:
   - `AWS_DEPLOY_ROLE_ARN` — output of `terraform output github_actions_role_arn`
   - `ECR_REGISTRY` — e.g. `123456789012.dkr.ecr.ap-south-1.amazonaws.com`
   - `APP_URL` — `terraform output alb_dns_name`, used by the CI smoke test

**Provision infra:**
```bash
cd infra/terraform
terraform init -backend-config="bucket=<your-state-bucket>"
terraform plan  -var-file=terraform.tfvars.example
terraform apply -var-file=terraform.tfvars.example
```

After `apply`, `terraform output alb_dns_name` gives you the public URL. Push
`backend/` code to `main` and GitHub Actions takes over from there.

---

## 5. CI/CD pipeline (GitHub Actions)

`.github/workflows/ci-cd.yaml` runs four stages on every push to `main` that touches `backend/`:

| Stage | What happens |
|---|---|
| **Test** | Install deps, run `pytest`, build the image locally to confirm the Dockerfile is valid (not pushed yet) |
| **Push** | Authenticate to AWS via **OIDC** (no long-lived keys), build & tag the image with the short git SHA + `latest`, push both tags, then **prune ECR down to the newest 5 images** |
| **Deploy** | Pull the current ECS task definition, render the new image into it, register a new revision, and `ecs update-service` — ECS handles the rolling replacement with `deployment_circuit_breaker` auto-rollback on failure |
| **Smoke test** | Poll `/health` on the live ALB until it returns `200` (10 retries, 10s apart), then check `/voices` returns real data |

**Image retention** is enforced twice, deliberately redundant:
- The Terraform `aws_ecr_lifecycle_policy` (`ecr.tf`) expires anything beyond the
  newest 5 images regardless of how it got pushed.
- The workflow's prune step actively deletes old digests right after each push, so
  the repo never sits above 5 images even between lifecycle policy evaluations.

---

## 6. Kubernetes path (EKS)

The `k8s/` manifests are a drop-in alternative to ECS if you're running EKS instead:

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml   # swap in your real ECR account ID first
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml      # requires the AWS Load Balancer Controller add-on
kubectl apply -f k8s/hpa.yaml          # requires the metrics-server add-on
```

Notable choices: `readOnlyRootFilesystem: true` with an `emptyDir` mounted at
`/tmp/audio` (matches the container's actual write path), non-root user, dropped
Linux capabilities, and `maxUnavailable: 0` for zero-downtime rollouts.

---

## 7. Monitoring

- **App metrics**: `prometheus-fastapi-instrumentator` exposes `/metrics` (request
  count, latency histograms, in-progress requests) — scraped directly by Prometheus
  in the K8s job via pod annotations, or via an ADOT sidecar on ECS.
- **Infra metrics**: `cloudwatch-exporter` bridges ECS CPU/memory and ALB
  latency/error-rate/healthy-host-count into Prometheus (`monitoring/cloudwatch-exporter-config.yml`).
- **Dashboard**: `monitoring/grafana-dashboard.json` — import directly into Grafana.
  Panels: request rate, p95 latency, 5xx rate, ECS CPU/memory, ALB healthy hosts,
  pod restarts.
- **Logs**: container stdout/stderr → CloudWatch Logs (`/ecs/tts-app-backend`,
  14-day retention) via the `awslogs` driver.

---

## 8. Security notes

- ECS tasks run in **private subnets** with no public IP; only the ALB is internet-facing.
- ECS task security group only accepts traffic **from the ALB security group**, not the open internet.
- ECR image tags are **immutable**; images are scanned on push.
- CI/CD uses **GitHub OIDC federation** to assume an AWS IAM role — no static AWS
  access keys stored as GitHub secrets.
- Container runs as a **non-root user** (both the Dockerfile and the K8s
  `securityContext`), with a read-only root filesystem in K8s.
- IAM roles are scoped to the minimum actions needed (ECR push/pull on this one
  repo, ECS deploy actions, `PassRole` limited to the two specific ECS roles).

---

## 9. Scaling & maintainability

- **Scaling**: both ECS (`aws_appautoscaling_policy`) and K8s (`hpa.yaml`) scale on
  60% CPU utilization, 2–6 replicas by default — one-line change to raise ceilings.
- **Maintainability**: all infra is Terraform (declarative, versioned, `plan`-able
  before `apply`); the task definition's container image is the only thing CI/CD
  mutates at deploy time, so infra changes and app releases are decoupled.
- **Immutable infrastructure**: every deploy is a brand-new task definition
  revision pointing at a brand-new, immutably-tagged image — never a live patch to
  a running container.
