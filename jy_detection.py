import csv
import networkx as nx
import heapq
from collections import defaultdict
from network_stats import NetworkStats


# return tuples
def find_triangles(network):
    # 1. find the bi-direction edge first
    bidirect_edges = []
    for n1 in network.nodes():
        for n2 in network.nodes():
            # this edge has been checked
            if sorted([n1, n2]) in bidirect_edges:
                continue
            # this edge is not a bi-direct edge
            if not network.has_edge(n1, n2) or not network.has_edge(n2, n1):
                continue
            
            # add this edge to the bidirect_edges array
            bidirect_edges.append(sorted([n1, n2]))
    return bidirect_edges
    # print(bidirect_edges)
    # 2. find all triangles

def find_community(network, bi_edges):
    communities = []
    community_hash = defaultdict(list)
    index = 1
    # 1. assume the nodes in a bi-edges are belong to the same community
    for edge in bi_edges:
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
                if score > 0.3 or float(connected) / len(network.successors(neighbor)) > 0.7:
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
                    if jaccard > 0.2:
                        local_validated.add(node)
                        community_hash[node].append(index)
                
                # print(local_validated == local)
                # print(local)
                if local_validated not in communities:
                    communities.append(local_validated)
            index += 1
    return (communities, community_hash)
if __name__ == "__main__":
    ns = NetworkStats()
    ns.init_from_file("../benchmark.csv")

    bi_edges = find_triangles(ns.network)
    communities, community_hash = find_community(ns.network, bi_edges)
    # print(123)
    print(communities)
    print(community_hash)

    print(list(nx.k_clique_communities(ns.network.to_undirected(), 4)))
    # degrees = ns.degree_distribution()
    # print("Degree distribution: {0}".format(degrees))

    # # print(nx.triangles(ns.network))

    # print(ns.network.has_edge(11, 14))
    # print(ns.network.has_edge(14, 11))