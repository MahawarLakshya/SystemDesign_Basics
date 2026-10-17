"""Test Lua rate limiting with threads, processes, and window expiration."""

import time
import uuid
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from threading import Barrier, Event

from distributed_rate_limiter import DistributedSlidingWindow


def unique_user(label):
    return f"test:{label}:{uuid.uuid4().hex}"


def test_three_simultaneous_requests():
    limiter = DistributedSlidingWindow(limit=5, window_ms=60_000)
    user = unique_user("three")

    # Leave exactly one slot in the window
    for _ in range(4):
        assert limiter.allow_request(user)[0]

    barrier = Barrier(3)

    def send_request():
        barrier.wait(timeout=10)
        return limiter.allow_request(user)[0]

    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(lambda _: send_request(), range(3)))

    final_count = limiter.client.zcard(f"rate_limit:{user}")
    print(f"Three concurrent: allowed={sum(results)}, final_count={final_count}")
    assert sum(results) == 1
    assert final_count == 5


def test_one_hundred_concurrent_requests():
    limiter = DistributedSlidingWindow(limit=5, window_ms=60_000)
    user = unique_user("hundred")
    start = Event()

    def send_request():
        start.wait(timeout=10)
        return limiter.allow_request(user)[0]

    with ThreadPoolExecutor(max_workers=25) as executor:
        futures = [executor.submit(send_request) for _ in range(100)]
        start.set()
        results = [future.result() for future in futures]

    accepted = sum(results)
    print(f"100 threaded: allowed={accepted}, rejected={100 - accepted}")
    assert accepted == 5
    assert limiter.client.zcard(f"rate_limit:{user}") == 5


def independent_process_worker(user):
    # Each process creates its own Redis connection and Lua script wrapper
    limiter = DistributedSlidingWindow(limit=5, window_ms=60_000)
    return sum(limiter.allow_request(user)[0] for _ in range(10))


def test_three_processes():
    user = unique_user("processes")
    with ProcessPoolExecutor(max_workers=3) as executor:
        accepted_per_process = list(executor.map(independent_process_worker, [user] * 3))

    total_accepted = sum(accepted_per_process)
    print(f"Three processes (30 requests): allowed={total_accepted}")
    assert total_accepted == 5


def test_window_expiration():
    limiter = DistributedSlidingWindow(limit=2, window_ms=300)
    user = unique_user("expiry")

    assert limiter.allow_request(user)[0]
    assert limiter.allow_request(user)[0]
    assert not limiter.allow_request(user)[0]

    time.sleep(0.4)
    allowed, count = limiter.allow_request(user)
    print(f"After window expires: allowed={allowed}, count={count}")
    assert allowed and count == 1


def main():
    DistributedSlidingWindow().client.ping()
    test_three_simultaneous_requests()
    test_one_hundred_concurrent_requests()
    test_three_processes()
    test_window_expiration()
    print("All Redis concurrency tests passed.")


if __name__ == "__main__":
    main()
