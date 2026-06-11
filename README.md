# NaaVRE Quality Assessment Service

This repository is intended to contain the backend service for assessing the
quality of research assets in NaaVRE.

The service should receive research assets from NaaVRE, evaluate them against a
quality model, persist the assessment results, and expose those results through
an API so users and scientists can understand the quality of a research asset.

## NaaVRE Architecture

This service follows the API-service pattern described in the
[NaaVRE architecture overview](https://github.com/NaaVRE/NaaVRE-architecture/blob/main/overview.md).

Relevant NaaVRE architecture assumptions:

- NaaVRE runs on top of JupyterLab.
- User-facing interactions happen through JupyterLab extensions.
- JupyterLab extensions communicate with backend API services through the
  NaaVRE communication layer.
- Backend services are deployed separately, usually as Docker images with Helm
  charts for Kubernetes.
- Services that need a database should be implemented with Django REST
  Framework.
- API services should validate OIDC/JWT bearer tokens against Keycloak.
- API services should avoid direct service-to-service calls inside NaaVRE unless
  explicitly required by the architecture.

Because quality assessment needs persistence for quality models, assessment
runs, and reports, this service is expected to be implemented with Django and
Django REST Framework.

## Role in NaaVRE

The quality assessment service sits outside the NaaVRE JupyterLab environment as
an independent backend API service.

The intended flow is:

1. A user interacts with a NaaVRE JupyterLab extension.
2. The extension sends a request through the NaaVRE communication layer.
3. The quality assessment service receives a research asset or asset reference.
4. The service authenticates the request using Keycloak/OIDC.
5. The service evaluates the asset using one or more quality models.
6. The service stores the assessment result in its database.
7. The service exposes the result and report through its API.
8. The frontend presents the quality information to the user/scientist.

This is captured in the local architecture diagram:

- [`diagrams/quality_assessment_architecture_naavre.png`](diagrams/quality_assessment_architecture_naavre.png)

## Internal Service Architecture

The current internal design is captured in:

- [`diagrams/quality_assessment_service_internal.png`](diagrams/quality_assessment_service_internal.png)

The proposed internal components are:

- **API**: Django REST Framework endpoints for creating assessments, retrieving
  results, listing quality models, and exposing reports.
- **Auth**: request authentication and authorization based on NaaVRE/Keycloak
  bearer tokens.
- **Evaluation Pipeline**: orchestration layer that takes an asset, selects or
  applies a quality model, computes metrics, and produces an assessment result.
- **Quality Models**: definitions of the criteria, dimensions, checks, weights,
  and scoring logic used to assess research assets.
- **Reporting**: formatting of assessment outcomes into user-facing summaries,
  detailed metric results, and machine-readable API responses.
- **DB Interface**: Django models and persistence logic for assets, quality
  models, assessment runs, metric results, and reports.

## Research Assets

The service should be able to assess research assets that originate from NaaVRE, which includes:
- notebooks
- cells or workflow components
- workflow definitions
- catalogue items
- datasets or dataset references
- containerized research components

The service can accept either embedded asset metadata or references to assets
known by NaaVRE, depending on how the surrounding NaaVRE components integrate
with it.

## Quality Assessment Model

The quality model should be represented explicitly rather than hidden inside
endpoint code. A model may include:

- quality dimensions
- measurable criteria
- metric definitions
- scoring rules
- weights
- thresholds
- result categories

## Expected API Capabilities

The API should eventually support:

- submitting an asset for assessment
- retrieving an assessment run
- listing assessment results for an asset
- listing available quality models
- retrieving a quality model definition
- retrieving a generated report
- health and readiness endpoints for deployment

## Authentication

Following the NaaVRE architecture recommendations, API requests should use
OIDC/JWT bearer tokens issued by Keycloak.

Authentication is not implemented in the initial scaffold yet. For local
development and tests, the service may later support a fake-auth mode similar to
other NaaVRE services:

```text
DISABLE_AUTH=true
```

When auth is enabled, requests should be validated against the configured
Keycloak issuer/JWKS endpoint.

## Deployment Expectations

As a NaaVRE backend service, the implementation should eventually include:

- Docker image build
- Helm chart
- configurable environment variables
- database connection configuration
- health/readiness probes
- CI checks for tests and linting

## Local Development

Install dependencies and run migrations:

```bash
pip install -r requirements.txt
python app/manage.py migrate
```

Run the development server:

```bash
python app/manage.py runserver
```

OpenAPI documentation is available at:

```text
http://127.0.0.1:8000/api/docs/
```

The raw OpenAPI schema is available at:

```text
http://127.0.0.1:8000/api/schema/
```

Run tests:

```bash
python app/manage.py test assessments
```