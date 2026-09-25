# MineGuard Ghana

MineGuard Ghana is a stakeholder demonstration MVP for mining health, safety and environmental intelligence. It connects structured reporting, environmental monitoring, transparent risk priorities, corrective action tracking and management reporting.

## Architecture

* `frontend` contains the responsive web interface
* `backend` contains the FastAPI service and relational data model
* PostgreSQL stores submitted incident and monitoring records
* `render.yaml` provisions the frontend, API and database on Render

The application contains no seeded incident or monitoring data. New deployments begin with an empty database.

## Responsible use

MineGuard provides operational decision support only. It does not diagnose occupational disease, determine legal liability or replace qualified safety, environmental, clinical or regulatory professionals. Production use requires authentication, least privilege access, audit logging, expert validation, security assessment and approved governance.

## Local development

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Serve the `frontend` directory with any static server. Update `frontend/config.js` if the API is not running at the configured address.

## Deployment

Use the Render Blueprint in `render.yaml` to deploy the static frontend, FastAPI backend and PostgreSQL database.

Created by Ebenezer Kwaw as an EK Synergy Ltd responsible technology project.
