# NaaVRE Quality Assessment Service

This repository contains the backend service for assessing the quality of NaaVRE scientific workflows.
The .naavrewf speification file serves as the main asset under assessment, in which various metrics will be derived.

The quality assessment service sits outside the NaaVRE JupyterLab environment as an independent backend API service.

## Deployment
After changes are merged into main, the `Publish container image` pipeline can be triggered manually to publish the image to GHCR.

## Local Development
Create a python virtual environment, install dependencies and run migrations:

```bash
python -m venv .venv
./venv/Scripts/activate
pip install -r requirements.txt
python app/manage.py migrate
```

Run the development server:

```bash
python app/manage.py runserver 8001
```

OpenAPI documentation is available at:

```text
http://127.0.0.1:8001/api/docs/
```

The raw OpenAPI schema is available at:

```text
http://127.0.0.1:8001/api/schema/
```