URL Shortener — Implementation and Interview Explanation
1. What the project does
The CLI accepts an HTTP/HTTPS long URL, generates a Snowflake integer, encodes it in Base62, stores the mapping in PostgreSQL, and warms a Redis cache. The resolve command looks in Redis first, then PostgreSQL and repopulates the cache.

Important: https://sho.rt/... is an illustrative URL string, not an active public redirect. Browser redirects require a deployed HTTP endpoint and control of the domain.
2. End-to-end sequence
Create: input URL → validate_url → Snowflake.generate → encode → PostgreSQL INSERT → Redis SETEX (best effort) → return BASE_URL/code.

Resolve: code → Redis GET → (if miss) PostgreSQL SELECT → Redis SETEX (best effort) → long URL.

PostgreSQL is the durable source of truth. Redis is a cache, not a replacement for the database. Cache expiry is 3600 seconds; the database record does not expire automatically.
3. Base62 explained line by line
- ALPHABET: 62 symbols, in the exact order 0-9, a-z, A-Z.
- if number < 0: reject negative IDs.
- if number == 0: return the single digit 0.
- number % 62: obtain the least-significant Base62 digit, as an index from 0 to 61.
- ALPHABET[number % 62] + code: prepend the digit because remainders arrive from rightmost to leftmost.
- number //= 62: integer division removes that digit.
- while number: stop after the quotient reaches zero.
Example: 125 / 62 gives remainder 1 and quotient 2; 2 / 62 gives remainder 2 and quotient 0. Read remainders backwards: 21 (Base62). The encoding is reversible and does not hash the long URL.
4. Snowflake explained line by line
- EPOCH_MS: fixed custom epoch, in milliseconds, common to all generator instances.
- SEQUENCE_BITS=12: sequence ranges from 0 to 2^12-1=4095.
- WORKER_BITS=10: worker ranges from 0 to 2^10-1=1023.
- self.worker_id: a unique ID assigned to each concurrent generator process (not just machine).
- self.last_ms: previous timestamp, initially -1.
- self.sequence: number within the current millisecond.
- self.lock: protects shared generator state from concurrent threads in the same process.
- with self.lock: acquires and automatically releases the lock.
- time.time_ns() // 1_000_000: converts current nanoseconds into milliseconds.
- if now < self.last_ms: stop when the wall clock moves backward. Otherwise the same ID might be generated again.
- if now == self.last_ms: increment sequence for another ID in the same millisecond.
- & MAX_SEQUENCE: keep only the lowest 12 bits, wrapping after 4095.
- if self.sequence == 0: after wrap, wait until the next millisecond so sequence 0 is not reused in the same millisecond.
- else: self.sequence=0: restart sequence in a new millisecond.
- elapsed = now - EPOCH_MS: fit time into 41 bits relative to the custom epoch.
- 0 <= elapsed < (1 << 41): guard against timestamps outside the field's range.
- self.last_ms = now: update state after generation.
- return ...: pack fields into a 63-bit nonnegative integer.
Why (elapsed << 22) | (worker_id << 12) | sequence?
Layout: [41 timestamp bits][10 worker bits][12 sequence bits] = 63 data bits plus an unused sign bit in the familiar 64-bit Snowflake representation.
- Sequence uses the rightmost 12 bits; shift 0.
- Worker uses the next 10 bits; shift 12 to leave room for the sequence.
- Timestamp uses the upper 41 bits; shift 10+12=22 to leave room for both lower fields.
- << is binary left shift (equivalent to multiplying by a power of two for nonnegative integers).
- | is bitwise OR; with disjoint bit regions it combines the fields without interference.
Example with elapsed=5, worker=3, sequence=2: 5*2^22 + 3*2^12 + 2 = 20,983,810.
What the lock does and does not do
Two concurrent threads might both read sequence 5 and return sequence 6 if no lock is used. The lock serializes the entire operation. In a strictly single-threaded CLI demo, it is optional; for a shared multithreaded generator, keep it. A Python threading lock does not synchronize multiple processes, containers, or servers; these require distinct worker IDs. Also, worker ID must not be reused while an old generator may still generate IDs.
5. URL validation
urlsplit(url) parses the URL; the code allows HTTP and HTTPS and requires a hostname. .strip() removes accidental leading/trailing spaces. Parsing alone does not guarantee the destination is safe or publicly reachable. This is an educational validator, not a full production anti-abuse/SSRF policy.
6. URLShortener initialization
- os.environ.get('WORKER_ID', '1'): reads optional environment config; int converts string to integer. Set a unique value for every concurrent generator instance.
- BASE_URL.rstrip('/'): avoids a double slash when constructing the short URL.
- psycopg.connect(..., autocommit=True): opens PostgreSQL connection and automatically commits individual statements.
- CREATE TABLE IF NOT EXISTS: creates storage if needed. short_code VARCHAR(16) PRIMARY KEY enforces uniqueness, long_url TEXT NOT NULL stores the destination, created_at TIMESTAMPTZ DEFAULT NOW() records creation time.
- redis.Redis.from_url: creates the Redis client; decode_responses=True converts byte values to strings; 0.5-second socket timeouts bound cache delays.
7. Shorten flow
- validate_url: reject invalid input early.
- for _ in range(3): attempt to allocate/insert a code at most three times. _ means loop index is intentionally unused.
- encode(self.generator.generate()): generate a number then Base62-encode it.
- INSERT INTO ... VALUES (%s,%s), values passed as tuple: parameterized query protects against SQL injection and handles quoting safely.
- except UniqueViolation: continue: retry on duplicate primary key. A persistent collision indicates broken worker ID/clock configuration.
- break: leave the retry loop when insert succeeds. for ... else executes only if the loop did not break.
- cache.setex('url:<code>',3600,long_url): write-through cache warm with a one-hour TTL.
- Catch redis.RedisError: do not discard a durable write because the cache failed.
- f'{base_url}/{code}': return the short URL string.
8. Resolve flow
- .removeprefix(BASE_URL + '/'): accept either a short code or a full local short URL.
- cache.get('url:<code>'): fast lookup. Cache hit returns immediately.
- On cache error/miss: SELECT long_url FROM urls WHERE short_code=%s.
- (code,): one-element tuple in Python (comma is necessary).
- .fetchone(): returns one row tuple or None; row[0] is the original long URL.
- cache.setex: populate Redis following a PostgreSQL lookup for future speed.
- return None: unmapped code.
This is the cache-aside pattern on reads. If records ever become updateable or deletable, cached mappings must be invalidated or updated or they may become stale.
9. Main loop and cleanup
input() reads strings; .strip() removes surrounding whitespace. while True repeats the menu until option 3. try/except handles common input/database errors. finally closes database and cache clients. if __name__ == '__main__' prevents CLI startup when the module is imported by tests.