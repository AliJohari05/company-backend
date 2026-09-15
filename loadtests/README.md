# CtrlOps load testing

Run Locust in its dedicated Docker container:

```bash
docker compose --profile loadtest up -d --build locust
```

Open `http://localhost:8089`, start with 10 users and a spawn rate of 2. The
container reaches Django through the Compose service address `http://web:8000`.

Inspect or stop the runner with:

```bash
docker compose logs -f locust
docker compose --profile loadtest stop locust
```

Run heavier tests only against staging, never against production without an
approved maintenance window. The public baseline intentionally excludes
write, login, upload, and download operations.
