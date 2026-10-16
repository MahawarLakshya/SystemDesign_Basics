
#include <bits/stdc++.h>
using namespace std;

// CONSISTENT HASHING - SYSTEM DESIGN
//
// 1. Consistent Hashing distributes keys across multiple servers.
// 2. Both servers and keys are mapped onto a circular hash ring.
// 3. Each key is assigned to the nearest server in clockwise direction.
// 4. Adding a server affects only a subset of existing keys.
// 5. Removing a server reassigns its keys to the next clockwise server.
// 6. Virtual Nodes improve load distribution among physical servers.
// 7. Consistent Hashing minimizes data redistribution during scaling.
// 8. Replication can be added separately for fault tolerance.
//
// REAL-WORLD IMPLEMENTATIONS:
//   Apache Cassandra -> Distributed database partitioning
//   Amazon Dynamo    -> Distributed key-value storage
//   Memcached clients -> Distributed caching
//
// CONFIGURATION PARAMETER:
//   replicas -> Number of virtual nodes per physical server
//
// DATA STRUCTURES:
//   map<size_t, string> ring
//      KEY   -> Hash position of a virtual node
//      VALUE -> Physical server name
//
//   set<size_t> sorted_keys
//      Stores virtual node hash positions in sorted order.
//
// EXAMPLE:
//   ring:
//      100 -> Node_A
//      300 -> Node_B
//      600 -> Node_C
//      900 -> Node_A
//
//   sorted_keys = {100, 300, 600, 900}
//
// KEY ASSIGNMENT:
//   Hash(key1) = 250 -> Node_B (position 300)
//   Hash(key2) = 500 -> Node_C (position 600)
//   Hash(key3) = 950 -> Node_A (wrap around to 100)
//
// TIME COMPLEXITY:
//   Add Node    -> O(R * log M)
//   Remove Node -> O(R * log M)
//   Get Node    -> O(log M)
//
//   R = Virtual nodes per physical server
//   M = Total virtual nodes in the ring
//
// SPACE COMPLEXITY:
//   O(M) -> map + set store virtual node positions.
//
// NOTE:
// std::hash<string> is suitable for local demonstrations,
// but does not guarantee identical hashes across platforms.
// Distributed clients must use an agreed deterministic hash.

class ConsistentHashRing
{
private:
    // Stores hash position -> physical node
    map<size_t, string> ring;

    // Maintains all hash positions in sorted order
    set<size_t> sorted_keys;

    // Number of virtual nodes for each physical node
    int replicas;

    // -------------------------------------------
    // STEP 1: HASH FUNCTION
    // -------------------------------------------
    //
    // PSEUDOCODE:
    //
    // 1. Take a string as input.
    // 2. Apply the hash function.
    // 3. Generate a numeric hash position.
    // 4. Return the hash position.
    //
    // Example:
    //   get_hash("Node_A_0") -> 100
    //   get_hash("Node_A_1") -> 450
    //   get_hash("Node_A_2") -> 900
    //
    // Above hash values are illustrative.

    size_t get_hash(const string &value)
    {
        hash<string> hash_function;

        return hash_function(value);
    }

public:
    // -------------------------------------------
    // STEP 2: CONSTRUCTOR
    // -------------------------------------------
    //
    // PSEUDOCODE:
    //
    // 1. Initialize number of virtual nodes.
    // 2. Each physical node gets 'replicas' positions.
    // 3. Initially the hash ring is empty.
    //
    // Example:
    //   replicas = 3
    //
    //   Node_A -> Node_A_0, Node_A_1, Node_A_2
    //   Node_B -> Node_B_0, Node_B_1, Node_B_2

    ConsistentHashRing(int replicas = 3) : replicas(replicas)
    {
        if (replicas <= 0)
        {
            throw invalid_argument("Invalid replicas");
        }
    }

    // -------------------------------------------
    // STEP 3: ADD NODE TO HASH RING
    // -------------------------------------------
    //
    // PSEUDOCODE:
    //
    // 1. Take physical node name as input.
    // 2. Generate 'replicas' virtual nodes.
    // 3. Calculate hash for each virtual node.
    // 4. Insert hash position and node into map.
    // 5. Insert hash position into sorted set.
    //
    // Example:
    //   add_node("Node_A")
    //
    //   Node_A_0 -> 100
    //   Node_A_1 -> 450
    //   Node_A_2 -> 900
    //
    // All three virtual nodes belong to Node_A.

    void add_node(const string &node)
    {
        // Step 1: Generate virtual nodes
        for (int i = 0; i < replicas; ++i)
        {
            // Step 2: Create unique virtual node identifier
            string virtual_node =
                node + "_" + to_string(i);

            // Step 3: Calculate hash position
            size_t replica_key = get_hash(virtual_node);

            // Step 4: Check for existing hash position
            if (ring.count(replica_key))
            {
                if (ring.at(replica_key) != node)
                {
                    throw runtime_error(
                        "Hash collision detected");
                }

                // Already registered for this node
                continue;
            }

            // Step 5: Store hash position -> physical node
            ring[replica_key] = node;

            // Step 6: Maintain sorted hash positions
            sorted_keys.insert(replica_key);
        }
    }

    // -------------------------------------------
    // STEP 4: REMOVE NODE FROM HASH RING
    // -------------------------------------------
    //
    // PSEUDOCODE:
    //
    // 1. Take physical node name as input.
    // 2. Generate its virtual node identifiers.
    // 3. Calculate their hash positions.
    // 4. Remove positions from map and set.
    // 5. Remaining nodes handle affected keys.
    //
    // Example:
    //   Before:
    //     100 -> Node_A
    //     300 -> Node_B
    //     600 -> Node_C
    //
    //   remove_node("Node_B")
    //
    //   After:
    //     100 -> Node_A
    //     600 -> Node_C
    //
    // Keys previously mapped to Node_B
    // are now routed to their next clockwise node.

    void remove_node(const string &node)
    {
        // Step 1: Iterate over virtual nodes
        for (int i = 0; i < replicas; ++i)
        {
            // Step 2: Generate virtual node identifier
            string virtual_node =
                node + "_" + to_string(i);

            // Step 3: Calculate hash position
            size_t replica_key = get_hash(virtual_node);

            // Step 4: Check whether it belongs to this node
            auto it = ring.find(replica_key);

            if (it != ring.end() && it->second == node)
            {
                // Step 5: Remove from hash ring
                ring.erase(it);

                // Step 6: Remove from sorted set
                sorted_keys.erase(replica_key);
            }
        }
    }

    // -------------------------------------------
    // STEP 5: FIND NODE FOR A KEY
    // -------------------------------------------
    //
    // PSEUDOCODE:
    //
    // 1. Check whether the hash ring is empty.
    // 2. Calculate hash of the incoming key.
    // 3. Use lower_bound() to find first node
    //    whose hash position >= key hash.
    // 4. If no such node exists, wrap around.
    // 5. Retrieve physical node from map.
    // 6. Return the node.
    //
    // Example:
    //   sorted_keys = {100, 300, 600, 900}
    //
    //   Hash("key1") = 250
    //   lower_bound(250) -> 300 -> Node_B
    //
    //   Hash("key2") = 750
    //   lower_bound(750) -> 900 -> Node_A
    //
    //   Hash("key3") = 950
    //   lower_bound(950) -> end()
    //   Wrap around -> 100 -> Node_A

    string get_node(const string &key)
    {
        // Step 1: Check if ring is empty
        if (ring.empty())
        {
            return "";
        }

        // Step 2: Calculate hash of incoming key
        size_t hash_value = get_hash(key);

        // Step 3: Find nearest clockwise virtual node
        auto it = sorted_keys.lower_bound(hash_value);

        // Step 4: Handle circular wraparound
        if (it == sorted_keys.end())
        {
            it = sorted_keys.begin();
        }

        // Step 5: Get physical node from hash position
        return ring.at(*it);
    }
};

int main()
{
    // -------------------------------------------
    // STEP 6: INITIALIZE HASH RING
    // -------------------------------------------

    // Each physical node has 3 virtual nodes
    ConsistentHashRing hash_ring(3);

    // -------------------------------------------
    // STEP 7: ADD PHYSICAL NODES
    // -------------------------------------------

    hash_ring.add_node("Node_A");
    hash_ring.add_node("Node_B");
    hash_ring.add_node("Node_C");

    // Total virtual nodes = 3 * 3 = 9
    // Assuming no hash collisions

    // -------------------------------------------
    // STEP 8: ASSIGN KEY TO NODE
    // -------------------------------------------

    string key = "first_key";

    string node = hash_ring.get_node(key);

    cout << "The key '" << key
         << "' is mapped to node: "
         << node << endl;

    // -------------------------------------------
    // STEP 9: ADD A NEW NODE
    // -------------------------------------------

    hash_ring.add_node("Node_D");

    cout << "After adding Node_D: "
         << hash_ring.get_node(key) << endl;

    // Only affected key ranges change ownership.

    // -------------------------------------------
    // STEP 10: REMOVE AN EXISTING NODE
    // -------------------------------------------

    hash_ring.remove_node("Node_B");

    cout << "After removing Node_B: "
         << hash_ring.get_node(key) << endl;

    // Keys owned by Node_B now map to their
    // next available clockwise physical node.

    return 0;
}
