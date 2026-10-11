
import time
import math

# SLIDING WINDOW COUNTER RATE LIMITER
#
# 1. Maintains counters for current and previous windows.
# 2. Uses a weighted portion of the previous window.
# 3. Estimates requests in the sliding window.
# 4. If estimated count + new request <= limit,
#    the request is accepted.
# 5. Otherwise, the request is rejected.
#
# Two configuration parameters:
#   maxRequests (maximum allowed requests)
#   windowSize (window duration in seconds)
#
# Time Complexity: O(1) per request
# Space Complexity: O(1)


class SlidingWindowCounter:

    def __init__(self, limit, window):

        if limit <= 0 or not math.isfinite(window) or window <= 0:
            raise ValueError("Invalid request limit or window size")

        self.maxRequests = limit
        self.windowSize = window

        self.currentCount = 0
        self.previousCount = 0

        self.currentWindowId = -1

    def allowRequest(self, requestId):

        # Step 1: Get current time
        nowSeconds = time.monotonic()

        # Step 2: Calculate current window ID
        windowId = math.floor(
            nowSeconds / self.windowSize
        )

        # Step 3: Update counters when window changes
        if windowId != self.currentWindowId:

            if (self.currentWindowId >= 0 and
                    windowId == self.currentWindowId + 1):

                self.previousCount = self.currentCount

            else:
                self.previousCount = 0

            self.currentCount = 0
            self.currentWindowId = windowId

        # Step 4: Calculate elapsed time in current window
        elapsed = (
            nowSeconds - self.currentWindowId * self.windowSize
        )

        # Step 5: Calculate previous window weight
        weight = 1.0 - (elapsed / self.windowSize)

        weight = max(0.0, min(1.0, weight))

        # Step 6: Estimate sliding window request count
        estimatedCount = (
            self.currentCount + (self.previousCount * weight)
        )

        # Step 7: Accept or reject request
        if estimatedCount + 1.0 <= self.maxRequests:

            self.currentCount += 1
            return True

        return False


def main():

    # Maximum = 5 requests
    # Window = 10 seconds
    limiter = SlidingWindowCounter(5, 10)

    for i in range(1, 9):

        if limiter.allowRequest(i):
            print(f"Request {i}: Accepted")
        else:
            print(f"Request {i}: Rejected")


if __name__ == "__main__":
    main()
