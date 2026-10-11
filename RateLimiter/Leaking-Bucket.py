
import time
import math
from collections import deque

# LEAKY BUCKET RATE LIMITER
#
# 1. Bucket has a predefined maximum capacity.
# 2. Incoming requests are added to a queue.
# 3. Requests are processed at a fixed leak rate.
# 4. If queue has space, request is accepted.
# 5. Requests are pulled from the queue and processed at regular intervals.
# 6. If queue is full, request is dropped.
# 7. Requests leak based on elapsed time.
#
# Two configuration parameters:
#   Bucket Size (capacity)
#   Outflow Rate (requests per second)
#
# Time Complexity: O(processed requests) per call
# Space Complexity: O(capacity)


class LeakyBucket:

    def __init__(self, cap, rate):

        if cap <= 0 or not math.isfinite(rate) or rate <= 0:
            raise ValueError("Invalid capacity or outflow rate")

        self.capacity = cap
        self.Outflow_Rate = rate

        # FIFO queue
        self.requests = deque()

        self.lastLeak_Time = time.monotonic()

    def allowRequest(self, requestId):

        # Step 1: Get current time
        now = time.monotonic()

        # Step 2: Calculate elapsed seconds
        elapsed = now - self.lastLeak_Time

        # Step 3: Calculate processed requests
        leaked = math.floor(
            elapsed * self.Outflow_Rate
        )

        # Step 4: Remove processed requests
        processed = min(
            leaked,
            len(self.requests)
        )

        for i in range(processed):
            self.requests.popleft()

        # Step 5: Update last leak timestamp
        if not self.requests:

            # No pending requests
            # Reset reference time
            self.lastLeak_Time = now

        elif leaked > 0:

            # Time consumed by completed leak intervals
            seconds = leaked / self.Outflow_Rate

            # Preserve fractional elapsed time
            self.lastLeak_Time += seconds

        # Step 6: Accept or reject request
        if len(self.requests) < self.capacity:
            self.requests.append(requestId)
            return True

        return False


def main():

    # Capacity = 5 requests
    # Leak rate = 2 requests per second
    limiter = LeakyBucket(5, 2)

    for i in range(1, 9):

        if limiter.allowRequest(i):
            print(f"Request {i}: Accepted")
        else:
            print(f"Request {i}: Rejected")


if __name__ == "__main__":
    main()
