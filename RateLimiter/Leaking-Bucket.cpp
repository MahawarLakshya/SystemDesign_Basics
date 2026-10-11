
#include <bits/stdc++.h>
using namespace std;

// LEAKY BUCKET RATE LIMITER
//
// 1. Bucket has a predefined maximum capacity.
// 2. Incoming requests are added to a queue.
// 3. Requests are processed at a fixed leak rate.
// 4. If queue has space, request is accepted.
// 5. Requested pulled from queue and processed at regular interval of time
// 6. If queue is full, request is dropped.
// 7. Requests leak based on elapsed time.
//
// SHOPIFY uses it
// Two configuration parameters:
//   Bucket Size (capacity)
//   Outflow Rate (requests per second)

class LeakyBucket
{
private:
    int capacity;
    double Outflow_Rate;

    queue<int> requests;
    chrono::steady_clock::time_point lastLeak_Time;

public:
    LeakyBucket(int cap, double rate)
    {

        if (cap <= 0 || !isfinite(rate) || rate <= 0)
        {
            throw invalid_argument("Invalid capacity or outflow rate");
        }

        capacity = cap;
        Outflow_Rate = rate;

        lastLeak_Time = chrono::steady_clock::now();
    }

    bool allowRequest(int requestId)
    {

        // Step 1: Get current time
        auto now = chrono::steady_clock::now();

        // Step 2: Calculate elapsed seconds
        double elapsed =
            chrono::duration<double>(
                now - lastLeak_Time)
                .count();

        // Step 3: Calculate processed requests
        long long leaked =
            static_cast<long long>(
                floor(elapsed * Outflow_Rate));

        // Step 4: Remove processed requests
        long long processed =
            min(leaked, (long long)requests.size());

        for (long long i = 0; i < processed; i++)
        {
            requests.pop();
        }

        // Step 5: Update last leak timestamp

        if (requests.empty())
        {

            // No pending requests
            // Reset reference time
            lastLeak_Time = now;
        }
        else if (leaked > 0)
        {

            // Time consumed by completed leak intervals
            double seconds = leaked / Outflow_Rate;

            // Convert seconds to chrono duration
            chrono::duration<double> duration(seconds);

            // Convert to steady_clock-compatible duration
            auto timeToAdd =
                chrono::duration_cast<chrono::steady_clock::duration>(
                    duration);

            // Preserve fractional elapsed time
            lastLeak_Time += timeToAdd;
        }

        // Step 6: Accept or reject request
        if (requests.size() < capacity)
        {
            requests.push(requestId);
            return true;
        }

        return false;
    }
};

int main()
{

    // Capacity = 5 requests
    // Leak rate = 2 requests per second
    LeakyBucket limiter(5, 2);

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
