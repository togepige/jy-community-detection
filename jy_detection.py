import csv
import networkx as nx
import heapq, os
from collections import defaultdict
from network_stats import NetworkStats

class JYCommunityDetection(object):
    def __init__(self, local_threshold=0.3, node_threshold=0.7, jaccard_threshold=0.2):
        self.local_threshold = local_threshold
        self.node_threshold = node_threshold
        self.jaccard_threshold = jaccard_threshold
    
    def _find_full_edge(self, network):
        full_edges = []
        for n1 in network.nodes():
            for n2 in network.nodes():
                # this edge has been checked
                if sorted([n1, n2]) in full_edges:
                    continue
                # this edge is not a bi-direct edge
                if not network.has_edge(n1, n2) or not network.has_edge(n2, n1):
                    continue
                
                # add this edge to the full_edges array
                full_edges.append(sorted([n1, n2]))
        return full_edges
    
    def accuracy(self, communities, memberships, community_truth):
        pass

    def detect(self, network):
        full_edges = self._find_full_edge(network)
        communities = []
        community_hash = defaultdict(set)
        index = 1
        # 1. assume the nodes in a bi-edges are belong to the same community
        for edge in full_edges:
            n1, n2 = edge
            local = set([n1, n2])
            local_validated = set(local)
            # the two nodes have been checked and assigned to the community
            if n1 in community_hash and n2 in community_hash:
                continue
            
            neighbors = set(list(network.successors(n1))  + list(network.predecessors(n1)) + list(network.successors(n2))  + list(network.predecessors(n2)) )
            neighbor_scores = []
            while True:
                new_neighbors = neighbors
                print(neighbors)
                candidates = []
                for neighbor in neighbors:
                    # calculate the score of the neighbor node
                    connected = 0
                    for local_node in local:
                        if network.has_edge(neighbor, local_node):
                            connected += 1
                    score = float(connected) / len(local)
                    # heapq.heappush(neighbor_scores, (-score, neighbors))
                    if score > self.local_threshold or float(connected) / len(network.successors(neighbor)) > self.node_threshold:
                        candidates.append(neighbor)

                for candidate in candidates:
                    # remove un-related candidate
                    inside_connection = 0
                    outside_connection = len(set(network.successors(candidate) + network.predecessors(candidate) + list(local)))
                    for node in local:
                        if network.has_edge(node, candidate) or network.has_edge(candidate, node):
                            inside_connection += 1
                    # print(candidate)
                    # print(float(inside_connection) / outside_connection)
                    if float(inside_connection) / outside_connection < 0:
                        continue
                    local.add(candidate)
                    # neighbors.discard(neighbor
                    new_neighbors = new_neighbors.union(list(network.successors(candidate))  + list(network.predecessors(candidate)))

                new_neighbors  = new_neighbors - local

                # print(new_neighbors)
                if new_neighbors == neighbors:
                    break
                else:
                    neighbors = new_neighbors
                    for node in local:
                        # final filter to check if the node is really belongs to the community
                        node_neighbors = list(network.successors(node))  + list(network.predecessors(node))
                        local_neighbors = [n for n in node_neighbors if n in local]
                        neighbor_union = local.union(node_neighbors)
                        jaccard = float(len(local_neighbors)) / len(neighbor_union)
                        if jaccard > self.jaccard_threshold:
                            local_validated.add(node)
                            community_hash[node].add(index)
                    
                    if local_validated not in communities:
                        communities.append(local_validated)
            index += 1
        return (communities, community_hash)


    
if __name__ == "__main__":
    ns = NetworkStats()

    dir_path = os.path.dirname(os.path.realpath(__file__))
    ns.init_fome_directory(os.path.join(dir_path, "data/benchmark_1"))

    detector = JYCommunityDetection()
    communities, community_hash = detector.detect(ns.network)
    
    print(communities)
    print(community_hash)
    print(list(nx.k_clique_communities(ns.network.to_undirected(), 4)))