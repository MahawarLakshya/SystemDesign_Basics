
import time

# TOKEN BUCKET RATE LIMITER
#
# 1. Bucket has a predefined maximum capacity.
# 2. Tokens are generated at a predefined refill rate.
# 3. Once the bucket is full, extra tokens are discarded.
# 4. Each request consumes one token.
# 5. If tokens >= 1, request is allowed.
# 6. Otherwise, request is rejected.
# 7. Tokens refill based on elapsed time, not request count.
#
# Two configuration parameters:
#   Bucket Size (capacity)
#   Refill Rate (tokens per second)
#
# Time Complexity: O(1) per request
# Space Complexity: O(1) per bucket


class TokenBucket:

    def __init__(self, cap, rate):

        if cap < 1 or rate <= 0:
            raise ValueError("Invalid capacity or refill rate")

        self.capacity = cap
        self.tokens = cap
        self.refillRate = rate

        self.lastRefill_Time = time.monotonic()

    def allowRequest(self):

        # Step 1: Get current time
        now = time.monotonic()

        # Step 2: Calculate elapsed time in seconds
        elapsed = now - self.lastRefill_Time

        # Step 3: Refill tokens based on elapsed time
        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.refillRate
        )

        # Step 4: Update last refill timestamp
        self.lastRefill_Time = now

        # Step 5: Allow or reject request
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True

        return False


def main():

    # Bucket size = 5
    # Refill rate = 2 tokens per second
    limiter = TokenBucket(5, 2)

    for i in range(1, 9):

        if limiter.allowRequest():
            print(f"Request {i}: Allowed")
        else:
            print(f"Request {i}: Rejected")


if __name__ == "__main__":
    main()
