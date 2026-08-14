# Stage 1: build the frontend ------------------------------------------------
FROM node:22-slim AS webbuild
WORKDIR /build
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

# Stage 2: serve API + built frontend ----------------------------------------
# python:3.8-slim matches the interpreter the model bundle was pickled under
# (venv is 3.8.10); sklearn pickles are not guaranteed portable across
# Python/sklearn versions.
FROM python:3.8-slim
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY api/ api/
COPY src/normalize.py src/predict.py src/
COPY models/triage_model.joblib models/
COPY --from=webbuild /build/dist web/dist

# Shadow logs live on the container disk -- ephemeral on free-tier hosts
# (wiped on redeploy). Fine for the pilot; documented in the README steps.
RUN mkdir -p data/shadow

EXPOSE 8000
# $PORT is injected by Render; default to 8000 for local `docker run`.
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
