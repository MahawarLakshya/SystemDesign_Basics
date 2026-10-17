# Distributed Sliding-Window Rate Limiter — Redis + Lua

An extension of the original in-memory `Sliding-window-log.py`, designed for concurrent threads and independent application processes.

## Why?

A naive `ZCARD` check followed by `ZADD` can exceed the limit when multiple servers read the same count before any of them write. Redis Lua scripts keep expiration cleanup, counting, limit validation, and insertion atomic on one authoritative Redis primary.

## Files

- `rate_limiter.lua` — atomic sliding-window log using `ZREMRANGEBYSCORE`, `ZCARD`, `ZADD`, and `PEXPIRE`.
- `distributed_rate_limiter.py` — Python wrapper and sequential demo.
- `naive_race_demo.py` — intentionally unsafe example with a barrier to reproduce the bug.
- `concurrency_test.py` — verifies three concurrent requests, 100 concurrent requests, three independent Python processes, and window expiration.
- `requirements.txt` — Python Redis client dependency.

## Setup

Redis 7+ is recommended. Start Redis with Docker:

```powershell
docker run -d --name redis-rate-limiter -p 6379:6379 redis:7
docker exec redis-rate-limiter redis-cli ping
```

Install dependencies in this directory:

```powershell
python -m pip install -r requirements.txt
```

Set `REDIS_URL` if Redis is not running at `redis://localhost:6379/0`. Do not commit passwords or connection strings with credentials.

## Run

```powershell
python distributed_rate_limiter.py
python naive_race_demo.py
python concurrency_test.py
```

Expected output (abbreviated, from fresh test keys):

```text
Request 1: Allowed | Active count: 1
...
Request 5: Allowed | Active count: 5
Request 6: Rejected | Active count: 5
Request 7: Rejected | Active count: 5

Initially accepted: 4
New accepted: 3
Final count: 7

Three concurrent: allowed=1, final_count=5
100 threaded: allowed=5, rejected=95
Three processes (30 requests): allowed=5
After window expires: allowed=True, count=1
All Redis concurrency tests passed.
```

These are **expected** outputs; run the programs locally to obtain your actual results.

## Architecture

```text
Client -> Load Balancer -> App A / App B / App C
                               |     |     |
                               +-----+-----+
                                     |
                                Redis primary
                                     |
                          atomic Lua script execution
                                     |
                         ZREMRANGEBYSCORE -> ZCARD
                                     |
                         allowed? -> ZADD -> PEXPIRE
```

## How it works

1. Use one Redis Sorted Set key per user, such as `rate_limit:user123`.
2. Store timestamps in milliseconds as scores and UUIDs as members.
3. Remove scores at or before `now - window_ms`.
4. Count remaining members; deny when `count >= limit`.
5. Otherwise, add the new member and refresh the key's TTL.
6. Run all steps atomically in one Lua script.

## Complexity

- `ZREMRANGEBYSCORE`: O(log N + M), where M is the number removed.
- `ZCARD`: O(1).
- `ZADD`: O(log N).
- `PEXPIRE`: O(1).
- Overall: O(log N + M) per request, O(N) entries per active user.

## Important limits

- Lua prevents interleaving on one authoritative Redis primary; it **does not** guarantee durability through failover or globally consistent decisions across independent regions.
- Every attempt receives a new UUID. If your application retries after an ambiguous timeout, it may double-count without additional idempotency design.
- Redis scripts block other commands while executing, so keep scripts short.
- Sliding-window logs store every accepted request; extremely high traffic increases memory usage.
- Expiry is refreshed on accepted requests only; once no accepted requests remain in the active window, the key can disappear.
- Threads/processes tests model concurrent clients. For multiple machines, point every application instance to the same Redis authority.

Official docs: https://redis.io/docs/latest/develop/programmability/eval-intro/ and https://redis.io/docs/latest/develop/data-types/sorted-sets/
