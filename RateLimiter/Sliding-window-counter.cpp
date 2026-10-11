
#include <bits/stdc++.h>
using namespace std;

// SLIDING WINDOW COUNTER RATE LIMITER
//
// 1. Maintains counters for current and previous windows.
// 2. Uses a weighted portion of the previous window.
// 3. Estimates requests in the sliding window.
// 4. If estimated count + new request <= limit,
//    the request is accepted.
// 5. Otherwise, the request is rejected.
//
// Two configuration parameters:
//   maxRequests (maximum allowed requests)
//   windowSize (window duration in seconds)

class SlidingWindowCounter
{
private:
    int maxRequests;
    double windowSize;

    int currentCount;
    int previousCount;

    long long currentWindowId;

    

public:
    SlidingWindowCounter(int limit, double window)
    {

        if (limit <= 0 || !isfinite(window) || window <= 0)
        {
            throw invalid_argument("Invalid request limit or window size");
        }

        maxRequests = limit;
        windowSize = window;

        currentCount = 0;
        previousCount = 0;

        currentWindowId = -1;
    }

    bool allowRequest(int requestId)
    {


        // Step 1: Get current time
        auto now = chrono::steady_clock::now();

        double nowSeconds =
            chrono::duration<double>(
                now.time_since_epoch())
                .count();

        // Step 2: Calculate current window ID
        long long windowId =
            static_cast<long long>(
                floor(nowSeconds / windowSize));

        // Step 3: Update counters when window changes
        if (windowId != currentWindowId)
        {

            if (currentWindowId >= 0 &&
                windowId == currentWindowId + 1)
            {
                previousCount = currentCount;
            }
            else
            {
                previousCount = 0;
            }

            currentCount = 0;
            currentWindowId = windowId;
        }

        // Step 4: Calculate elapsed time in current window
        double elapsed =
            nowSeconds - currentWindowId * windowSize;

        // Step 5: Calculate previous window weight
        double weight = 1.0 - (elapsed / windowSize);

        weight = max(0.0, min(1.0, weight));

        // Step 6: Estimate sliding window request count
        double estimatedCount =
            currentCount + (previousCount * weight);

        // Step 7: Accept or reject request
        if (estimatedCount + 1.0 <= maxRequests)
        {
            currentCount++;
            return true;
        }

        return false;
    }
};

int main()
{

    // Maximum = 5 requests
    // Window = 10 seconds
    SlidingWindowCounter limiter(5, 10);

    for (int i = 1; i <= 8; i++)
    {

        if (limiter.allowRequest(i))
        {
            cout << "Request " << i
                 << ": Accepted\n";
        }
        else
        {
            cout << "Request " << i
                 << ": Rejected\n";
        }
    }

    return 0;
}
