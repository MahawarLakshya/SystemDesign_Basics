"""Redis + Lua distributed sliding-window log rate limiter."""

import os
import uuid
from pathlib import Path

import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


class DistributedSlidingWindow:
    def __init__(self, limit=5, window_ms=60_000, redis_client=None):
        if type(limit) is not int or limit <= 0:
            raise ValueError("limit must be a positive integer")
        if type(window_ms) is not int or window_ms <= 0:
            raise ValueError("window_ms must be a positive integer")

        self.limit = limit
        self.window_ms = window_ms
        self.client = redis_client if redis_client is not None else redis.Redis.from_url(
            REDIS_URL, decode_responses=True
        )

        script_path = Path(__file__).with_name("rate_limiter.lua")
        self.lua_script = script_path.read_text(encoding="utf-8")
        self.script = self.client.register_script(self.lua_script)

    def allow_request(self, user_id):
        if not user_id:
            raise ValueError("user_id must not be empty")

        key = f"rate_limit:{user_id}"
        request_id = str(uuid.uuid4())

        allowed, count = self.script(
            keys=[key], args=[self.limit, self.window_ms, request_id]
        )
        return bool(allowed), int(count)


def main():
    limiter = DistributedSlidingWindow(limit=5, window_ms=60_000)
    limiter.client.ping()

    user_id = f"demo:{uuid.uuid4().hex}"  # Fresh key every run
    for number in range(1, 8):
        allowed, count = limiter.allow_request(user_id)
        status = "Allowed" if allowed else "Rejected"
        print(f"Request {number}: {status} | Active count: {count}")


if __name__ == "__main__":
    main()
