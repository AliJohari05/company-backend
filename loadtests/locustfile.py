import os

from locust import HttpUser, between, task


class PublicUser(HttpUser):
    wait_time = between(1, 3)
    host = os.getenv("LOCUST_HOST", "http://localhost:8000")

    @task(5)
    def services(self):
        self.client.get("/api/v1/services/")

    @task(5)
    def blog_posts(self):
        self.client.get("/api/v1/blog/posts/")

    @task(2)
    def health(self):
        self.client.get("/health/")
