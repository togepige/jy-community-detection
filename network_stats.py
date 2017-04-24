import networkx as nx
import sys, os
import re
from collections import defaultdict
import matplotlib.pyplot as plt

class NetworkStats(object):

    def __init__(self):
        self.network = nx.DiGraph()
        self.communities = {}
    # Extract edges data from snap network file
    def _get_edges(self, file_name):
        edges = []
        with open(file_name) as f:
            for line in f:
                if line.startswith("#") or line.startswith("Source,"):
                    continue
                else:
                    nodes = map(lambda s: int(s.replace("\n", " ").strip()), re.split("[,]", line))
                    edges.append(tuple(nodes))
        return edges
    
    def read_graph_from_file(self, file_name):
        edges = self._get_edges(file_name)
        self.network.add_edges_from(edges)
    

    # read the community information from file
    def read_community_from_file(self, file_name):
        memberships = defaultdict(set)
        if not os.path.exists(file_name):
            return
        with open(file_name) as f:
            for line in f:
                node_s, communities = map(lambda s: s.replace("\n", " ").strip(), re.split("[\t,]", line))
                for commu in communities.split(" "):
                    memberships[commu].add(int(node_s))
        
        self.communities = memberships
        
        
    def init_fome_directory(self, directory):
        self.read_graph_from_file(os.path.join(directory, "dataset.csv"))
        self.read_community_from_file(os.path.join(directory, "community.txt"))

    # def degree_distribution(self):
    #     degrees = nx.degree(self.network)
    #     degree_dist = defaultdict(int)
        
    #     for _, d in degrees.items():
    #         degree_dist[d] += 1
            
    #     return degree_dist
    
    # def avg_degree(self):
    #     degree_sum = sum(self.network.degree().values())
    #     avg_degree = degree_sum / float(len(self.network.nodes()))
    #     return avg_degree

    # def avg_coefficient(self):
    #     return nx.average_clustering(self.network)

    # def diameter_of_largest_component(self):
    #     sub_component = max(nx.connected_component_subgraphs(self.network), key=len)
    #     return nx.diameter(sub_component)

    # def components(self):
    #     return list(nx.connected_components(self.network))


    # def plot_distribution(self, distribution):
    #     max_dist = 0
    #     for dist, count in distribution.items():
    #         max_dist = max(max_dist, dist)
        
    #     vals = [0] * (max_dist + 1)
    #     bins = range(max_dist + 2)
        
    #     for dist, count in distribution.items():
    #         vals[dist] = count
        
    #     plt.hist(vals, bins=bins)
    #     plt.show()

# if __name__ == "__main__":
#     file_name = sys.argv[1]
#     ns = NetworkStats()
#     ns.init_from_file(file_name)

#     degrees = ns.degree_distribution()
#     print("Degree distribution: {0}".format(degrees))
#     ns.plot_distribution(degrees)

#     print("Average coefficient: {0}".format(ns.avg_coefficient()) )
#     print("Average degree: {0}".format(ns.avg_degree()) )
#     components = ns.components()
#     print("Number of components: {0}".format( len(components) ))
#     print("Diameter of largest component: {0}".format(ns.diameter_of_largest_component()))