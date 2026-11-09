# Journey Observatory

Journey Observatory joins booking, stay, billing, and support events into one case per guest journey. It finds where the journey breaks, keeps a guest's own exit and a policy stop apart from a missing event, and models what fixing each break could be worth.

It is for a hotel development or finance analyst who has to choose which fix to do first.

The data is synthetic. Every dollar figure is a modeled estimate, not cash that was booked or collected.

## Stack

Python, SQL, DuckDB, Airflow, and a Next.js dashboard. The pipeline writes three CSV marts so a Tableau workbook can sit on them.

## Run the pipeline

From the repository root, create a virtual environment, install the Python requirements, and run the pipeline module.

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pipeline.run
```

Tests live next to the pipeline. Run them with pytest.

## Dashboard

From the web directory, install packages and build. The site reads the exported files. It does not open a database and it does not use a secret.

```
npm install
npm run build
```

## Vercel

Framework is Next.js. Build command is npm run build. Leave the output directory on the Next.js default. The app writes a static export, and Vercel reads that from the Next.js build.

If the Git repository is connected, set the root directory to web. The current project was deployed from that directory, so its root is the web app.

Suggested project name: journey-observatory. After a deploy the site is at https://journey-observatory.vercel.app

Page title: Journey Observatory.

Description: Joins booking, stay, billing, and support events into guest journeys, finds where they break, and models what fixing each break could be worth.

## Airflow

The DAG runs the same steps locally in Docker Compose. It is not deployed with the site.

```
docker compose -f airflow/docker-compose.yml up --build
```
