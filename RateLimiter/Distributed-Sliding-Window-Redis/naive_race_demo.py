"""Reproduce a check-then-insert race in a deliberately unsafe limiter."""

import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from distributed_rate_limiter import REDIS_URL
import redis


client = redis.Redis.from_url(REDIS_URL, decode_responses=True)


def naive_request(key, start_barrier):
    # First check request count (this check is NOT linked atomically to ZADD)
    count = client.zcard(key)

    # Force all three threads to observe the old count before inserting
    start_barrier.wait(timeout=10)

    if count < 5:
        client.zadd(key, {str(uuid.uuid4()): time.time_ns() // 1_000_000})
        return True
    return False


def main():
    client.ping()
    key = f"rate_limit:naive:{uuid.uuid4().hex}"
    now = time.time_ns() // 1_000_000

    # Preload four recently accepted requests
    for i in range(4):
        client.zadd(key, {f"seed-{i}": now})
    client.pexpire(key, 60_000)

    barrier = Barrier(3)
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(naive_request, key, barrier) for _ in range(3)]
        results = [future.result() for future in futures]

    print("Initially accepted: 4")
    print("New accepted:", sum(results))
    print("Final count:", client.zcard(key))
    assert client.zcard(key) == 7, "Expected to reproduce the race"


if __name__ == "__main__":
    main()
