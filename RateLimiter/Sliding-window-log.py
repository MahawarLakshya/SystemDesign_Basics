
import time
import math
from collections import deque

# SLIDING WINDOW LOG RATE LIMITER
#
# 1. Maintains timestamps of accepted requests.
# 2. Uses a sliding window of fixed duration.
# 3. Removes requests older than the window.
# 4. If requests within the window are below the limit,
#    the new request is accepted.
# 5. Otherwise, the request is rejected.
#
# Two configuration parameters:
#   maxRequests (maximum allowed requests)
#   windowSize (window duration in seconds)
#
# Time Complexity: O(1) amortized per request
# Space Complexity: O(maxRequests)


class SlidingWindowLog:

    def __init__(self, limit, window):

        if limit <= 0 or not math.isfinite(window) or window <= 0:
            raise ValueError("Invalid request limit or window size")

        self.maxRequests = limit
        self.windowSize = window

        # FIFO queue to store request timestamps
        self.requests = deque()

    def allowRequest(self, requestId):

        # Step 1: Get current time
        now = time.monotonic()

        # Step 2: Remove expired requests
        while self.requests:

            elapsed = now - self.requests[0]

            if elapsed >= self.windowSize:
                self.requests.popleft()
            else:
                break

        # Step 3: Accept or reject request
        if len(self.requests) < self.maxRequests:

            self.requests.append(now)
            return True

        # Step 4: Reject request
        return False


def main():

    # Maximum = 5 requests
    # Window = 10 seconds
    limiter = SlidingWindowLog(5, 10)

    for i in range(1, 9):

        if limiter.allowRequest(i):
            print(f"Request {i}: Accepted")
        else:
            print(f"Request {i}: Rejected")


if __name__ == "__main__":
    main()
