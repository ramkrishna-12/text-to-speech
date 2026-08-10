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