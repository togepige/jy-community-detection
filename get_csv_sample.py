import random
import os, sys
import re
def get_sample_edges(file_name):
    edges = []
    with open(file_name) as f:
        for line in f:
            if line.startswith("#"):
                continue
            else:
                nodes = map(lambda s: s.replace("\n", "").strip(), re.split("[ \t]", line))
                edges.append(tuple(nodes))
    return edges

def write_sample(edges, file_name):
    sample_edges = random.sample(edges, 1000)
    with open(file_name, "w") as f:
        f.write("{0},{1}\n".format("Source", "Target"))
        for s, t in sample_edges:
            f.write("{0},{1}\n".format(s, t))
            


if __name__ == "__main__":
    file_name = sys.argv[1]
    # output_file = os.path.abspath()
    write_sample(get_sample_edges(file_name), os.path.splitext(file_name)[0] + ".csv")
    