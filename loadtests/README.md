# CtrlOps load testing

Install Locust separately from development dependencies:

```bash
python -m pip install locust
locust -f loadtests/locustfile.py --host http://localhost:8000
```

Open `http://localhost:8089`, start with 10 users and a spawn rate of 2.
Run heavier tests only against staging, never against production without an
approved maintenance window. The public baseline intentionally excludes
write, login, upload, and download operations.
