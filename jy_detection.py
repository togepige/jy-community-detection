import csv
import networkx as nx
import heapq, os, sys
from collections import defaultdict
from network_stats import NetworkStats
import json

class JYCommunityDetection(object):
    def __init__(self):
        # self.local_threshold = local_threshold
        # self.node_threshold = node_threshold
        # self.jaccard_threshold = jaccard_threshold
        pass

    def _find_full_edge(self, network):
        # print("Calculating full edges...")
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

        # print("Finish calculating full edges...")
        return full_edges
    
    def analyse(self, network, communities, community_truth, full_edges = []):
        """
        analyse result format:
        {
            number_of_nodes: 100,
            number_of_edges: 50
            number_of_full_edges: 10,
            number_of_community: 10,
            full_edges: [],
            community_truth: {
                community_id: []
            },
            data: {community_id: {
                    jaccard_similarity: 0.9
                    extra_nodes: [],
                    missing_nodes: []
                }
            },
            memberships: {
                node_id: [1, 2, 3]
            },
            jaccard_similarity_avg: 0.8,
            missing_nodes: []
        }
        """
        results = {
                "data": {}, 
                "number_of_nodes": network.number_of_nodes(), 
                "number_of_edges": network.number_of_edges(), 
                "number_of_full_edges": len(full_edges),
                "community_truth": community_truth,
                "full_edges": full_edges,
                "number_of_communities": len(community_truth),
                "number_of_detected_communities": len(communities)
            }
        sum_jaccard = 0
        checked_nodes = set()
        all_nodes = set()
        memberships = defaultdict(set)
        for index, community in community_truth.items():
            all_nodes = all_nodes.union(community)
            max_matched_percent = 0
            max_matched_community = set()
            for found_community in communities:
                matched_count = len(community.intersection(found_community))
                if float(matched_count) / len(community) > max_matched_percent:
                    max_matched_percent = float(matched_count) / len(community)
                    max_matched_community = found_community
                    
            for node in max_matched_community:
                memberships[node].add(index)
            checked_nodes = checked_nodes.union(max_matched_community)
            # result format: community_index: (accuracy, less count, more count)
            more_count = max_matched_community - community
            less_count = community - max_matched_community
            jaccard = float(len(max_matched_community.intersection(community))) / len(max_matched_community.union(community))
            results["data"][index] = (jaccard, less_count, more_count)
            sum_jaccard += jaccard
        
        results["memberships"] = memberships
        results["jaccard_avg"] = sum_jaccard / len(community_truth)
        results["checked_nodes"] = checked_nodes
        results["missing_nodes"] = all_nodes - checked_nodes
        print(communities)
        return results

    def detect(self, network, local_threshold=0.3, node_threshold=0.7, jaccard_threshold=0.2):
        full_edges = self._find_full_edge(network)
        communities = []
        community_hash = defaultdict(set)
        index = 1
        # 1. assume the nodes in a bi-edges are belong to the same community
        # print("Full edges count: {0}".format(full_edges))
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
                # print(neighbors)
                candidates = []
                for neighbor in neighbors:
                    # calculate the percentage of the internal edges
                    # score = full_edges * 10 + Edge(node->local) * 1
                    connected = 0
                    score = 0
                    for local_node in local_validated:
                        if network.has_edge(neighbor, local_node) and network.has_edge(local_node, neighbor): # full-edge from a local node to the current node
                            score += 10
                            connected += 1
                        elif network.has_edge(neighbor, local_node): #  or network.has_edge(local_node, neighbor): # one direction edge from neighbor to a local node
                            score += 1
                            connected += 1
                    
                    # score = float(connected) / len(local_validated)
                    heapq.heappush(neighbor_scores, (-score, -connected, neighbor))
                    # if score > local_threshold or (len(network.successors(neighbor)) != 0 and float(connected) / len(network.successors(neighbor)) > node_threshold):
                    #     candidates.append(neighbor)
                
                # 2. Check all candidate neighbors based on the order of score
                while neighbor_scores:
                    score, connected, node = heapq.heappop(neighbor_scores)
                    score = -score # negative to positive
                    connected = -connected
                    if float(connected) / len(local_validated) > local_threshold or (len(network.successors(neighbor)) != 0 and float(connected) / len(network.successors(neighbor)) > node_threshold):
                        candidates.append(node)
                
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
                        if jaccard > jaccard_threshold:
                            local_validated.add(node)
                            community_hash[node].add(index)
                    
                    if local_validated not in communities:
                        communities.append(local_validated)
            index += 1

        fill_nodes_to_community(network, communities)

        return (communities, community_hash, full_edges)
# fill un-checked nodes to a closest community
def fill_nodes_to_community(network, communities):
    print("Missing to check...")
    if len(communities) == 0:
        return
    checked_nodes = reduce(set.union, communities)
    missing_nodes = set(network.nodes()) - checked_nodes
    # print(len(set(network.nodes())))
    # print(len(checked_nodes))
    for missing_node in missing_nodes:
        matched_community = None
        max_score = 0
        neighbors = set(list(network.successors(missing_node))  + list(network.predecessors(missing_node)))
        for community in communities:
            matched_count = 0
            for node in community:
                if network.has_edge(node, missing_node) or network.has_edge(missing_node, node):
                    matched_count += 1
            score = float(matched_count) / len(neighbors)
            if score > max_score:
                max_score = score
                matched_community = community
        
        matched_community.add(missing_node)
    

def save_results(analyse_result, file_path):
    """
    analyse result format:
    {
        number_of_nodes: 100,
        number_of_edges: 50
        number_of_full_edges: 10,
        number_of_community: 10,
        community_truth: {
            community_id: []
        },
        data: {community_id: {
                jaccard_similarity: 0.9
                extra_nodes: [],
                missing_nodes: []
            }
        },
        memberships: {
            node_id: [1, 2, 3]
        },
        jaccard_similarity_avg: 0.8,
        missing_nodes: []
    }
    """
    def set_default(obj):
        if isinstance(obj, set):
            return sorted(list(obj))
        
    # json.dumps(analyse_result)
    with open(file_path, "w") as text_file:
        text_file.write(json.dumps(analyse_result, default=set_default, sort_keys=True, indent=4))

if __name__ == "__main__":
    data_dir = sys.argv[1]
    local_threshold = 0.3
    node_threshold = 0.7
    jaccard_similarity = 0.2
    if len(sys.argv) == 5:
        local_threshold = float(sys.argv[2])
        node_threshold = float(sys.argv[3])
        jaccard_similarity = float(sys.argv[4])
        
    ns = NetworkStats()


    dir_path = os.path.dirname(os.path.realpath(__file__))
    data_dir = os.path.join(dir_path, data_dir)
    ns.init_fome_directory(data_dir)

    detector = JYCommunityDetection()
    communities, memberships, full_edges = detector.detect(ns.network, local_threshold, node_threshold, jaccard_similarity)
    print(ns.communities)
    print("-------------------------------------")
    print(communities)
    result = detector.analyse(ns.network, communities, ns.communities, full_edges)
    print(result["data"])
    print("--Accuracy--")
    print(result["jaccard_avg"])
    print("--Missing--")
    print(result["missing_nodes"])
    save_results(result, os.path.join(data_dir, "result.json"))


    print("-------------------------------------")
    clique_based_communities = list(nx.k_clique_communities(ns.network.to_undirected(), 4))
    print(clique_based_communities)
    result = detector.analyse(ns.network.to_undirected(), clique_based_communities,  ns.communities)
    print(result["data"])
    print("--Accuracy--")
    print(result["jaccard_avg"])
    print("--Missing--")
    print(result["missing_nodes"])
    save_results(result, os.path.join(data_dir, "result_clique.json"))
