
#include <bits/stdc++.h>


using namespace std;

// TOKEN BUCKET RATE LIMITER
//
// 1. Bucket has a predefined maximum capacity.
// 2. Tokens are generated at a predefined refill rate.
// 3. Once the bucket is full, extra tokens are discarded.
// 4. Each request consumes one token.
// 5. If tokens >= 1, request is allowed.
// 6. Otherwise, request is rejected.
// 7. Tokens refill based on elapsed time, not request count.
//
// Two configuration parameters:
//   Bucket Size (capacity)
//   Refill Rate (tokens per second)
//
// AMAZON and STRIPE uses it
// Time Complexity: O(1) per request
// Space Complexity: O(1) per bucket

class TokenBucket {
private:
    double capacity;
    double tokens;
    double refillRate;

    chrono::steady_clock::time_point lastRefill_Time;
    

public:
    TokenBucket(double cap, double rate) {

        if (cap < 1 || rate <= 0) {
            throw invalid_argument("Invalid capacity or refill rate");
        }

        capacity = cap;
        tokens = cap;
        refillRate = rate;

        lastRefill_Time = chrono::steady_clock::now();
    }

    bool allowRequest() {


        // Step 1: Get current time
        auto now = chrono::steady_clock::now();

        // Step 2: Calculate elapsed time in seconds
        double elapsed =
            chrono::duration<double>(
                now - lastRefill_Time
            ).count();

        // Step 3: Refill tokens based on elapsed time
        tokens = min(
            capacity,
            tokens + elapsed * refillRate
        );

        // Step 4: Update last refill timestamp
        lastRefill_Time = now;

        // Step 5: Allow or reject request
        if (tokens >= 1.0) {
            tokens -= 1.0;
            return true;
        }

        return false;
    }
};

int main() {

    // Bucket size = 5
    // Refill rate = 2 tokens per second
    TokenBucket limiter(5, 2);

    for (int i = 1; i <= 8; i++) {

        if (limiter.allowRequest()) {
            cout << "Request " << i
                 << ": Allowed" << endl;
        }
        else {
            cout << "Request " << i
                 << ": Rejected" << endl;
        }
    }

    return 0;
}
