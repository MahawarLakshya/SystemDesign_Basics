
from bisect import bisect_left, insort
from hashlib import md5

class ConsistentHashRing:

    # Step 1: Initialize hash ring, sorted keys and replicas
    def __init__(self, replicas=3):
        self.ring = {}
        self.sorted_keys = []
        self.replicas = replicas

    # Step 2: Generate hash value for a given string
    def get_hash(self, value):
        return int(md5(value.encode()).hexdigest(), 16)

    # Step 3: Add physical node and its virtual nodes to the ring
    def add_node(self, node):
        for i in range(self.replicas):

            # Create virtual node identifier
            virtual_node = node + "_" + str(i)

            # Calculate hash position
            replica_key = self.get_hash(virtual_node)

            # Check whether hash position already exists
            if replica_key in self.ring:
                if self.ring[replica_key] != node:
                    raise ValueError("Hash collision detected")
                continue

            # Store hash position and physical node
            self.ring[replica_key] = node

            # Insert hash position in sorted order
            insort(self.sorted_keys, replica_key)

    # Step 4: Remove physical node and its virtual nodes
    def remove_node(self, node):
        for i in range(self.replicas):

            # Generate virtual node identifier
            virtual_node = node + "_" + str(i)

            # Calculate hash position
            replica_key = self.get_hash(virtual_node)

            # Check whether virtual node exists and belongs to the node
            if replica_key in self.ring and self.ring[replica_key] == node:

                # Remove virtual node from hash ring
                del self.ring[replica_key]

                # Remove hash position from sorted list
                self.sorted_keys.remove(replica_key)

    # Step 5: Find the nearest clockwise node for a key
    def get_node(self, key):

        # Return empty string if ring is empty
        if not self.ring:
            return ""

        # Calculate hash of incoming key
        hash_value = self.get_hash(key)

        # Find first hash position greater than or equal to key hash
        idx = bisect_left(self.sorted_keys, hash_value)

        # Wrap around to beginning if needed
        if idx == len(self.sorted_keys):
            idx = 0

        # Return corresponding physical node
        return self.ring[self.sorted_keys[idx]]


if __name__ == "__main__":

    # Step 6: Initialize hash ring with 3 virtual nodes per server
    hash_ring = ConsistentHashRing(3)

    # Step 7: Add physical nodes
    hash_ring.add_node("Node_A")
    hash_ring.add_node("Node_B")
    hash_ring.add_node("Node_C")

    # Step 8: Find node responsible for a key
    key = "first_key"
    node = hash_ring.get_node(key)

    print(f"The key '{key}' is mapped to node: {node}")

    # Step 9: Add a new physical node
    hash_ring.add_node("Node_D")
    print("After adding Node_D:", hash_ring.get_node(key))

    # Step 10: Remove an existing physical node
    hash_ring.remove_node("Node_B")
    print("After removing Node_B:", hash_ring.get_node(key))
