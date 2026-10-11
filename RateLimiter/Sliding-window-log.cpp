
#include <bits/stdc++.h>
using namespace std;

// SLIDING WINDOW LOG RATE LIMITER
//
// 1. Maintains timestamps of accepted requests.
// 2. Uses a sliding window of fixed duration.
// 3. Removes requests older than the window.
// 4. If requests within the window are below the limit,
//    the new request is accepted.
// 5. Otherwise, the request is rejected.
//
// Two configuration parameters:
//   maxRequests (maximum allowed requests)
//   windowSize (window duration in seconds)

class SlidingWindowLog
{
private:
    int maxRequests;
    double windowSize;

    queue<chrono::steady_clock::time_point> requests;

    

public:
    SlidingWindowLog(int limit, double window)
    {

        if (limit <= 0 || !isfinite(window) || window <= 0)
        {
            throw invalid_argument("Invalid request limit or window size");
        }

        maxRequests = limit;
        windowSize = window;
    }

    bool allowRequest(int requestId)
    {



        // Step 1: Get current time
        auto now = chrono::steady_clock::now();

        // Step 2: Remove expired requests
        while (!requests.empty())
        {

            double elapsed =
                chrono::duration<double>(
                    now - requests.front())
                    .count();

            if (elapsed >= windowSize)
            {
                requests.pop();
            }
            else
            {
                break;
            }
        }

        // Step 3: Accept or reject request
        if (requests.size() < maxRequests)
        {
            requests.push(now);
            return true;
        }

        // Step 4: Reject request
        return false;
    }
};

int main()
{

    // Maximum = 5 requests
    // Window = 10 seconds
    SlidingWindowLog limiter(5, 10);

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
