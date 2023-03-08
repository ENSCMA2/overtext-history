import sys
import argparse
import json
import time

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.cluster import AffinityPropagation
from sklearn.cluster import DBSCAN
from sklearn.cluster import AgglomerativeClustering

parser = argparse.ArgumentParser(description='Cluster comments.')
parser.add_argument('embeddings',
                    help='file containing embeddings')
parser.add_argument('sentences',
                    help='file containing sentences')
parser.add_argument('--output-prefix', default="vis.out.{}".format(int(time.time())),
                    help='prefix for filenames of tables to be produced')
parser.add_argument('--nclusters', default=10, type=int,
                    help='number of clusters for kmeans')
args = parser.parse_args()

# Read embeddings
embeddings = None
with open(args.embeddings, 'rb') as f:
    embeddings = np.load(f)

# Read sentences
sentences = {}
with open(args.sentences, 'r') as f:
    for line in f.readlines():
        parts = line.strip().split()
        if len(parts) > 0:
            sent_id = int(parts[0])
            sent = line.strip()[len(parts[0]) + 1:]
            sentences[sent_id] = sent

# Exit if we didn't get data
if len(sentences) != len(embeddings) or len(embeddings) == 0:
    print("Missing data")
    sys.exit(1)

# Run clustering methods on the complete embeddings

def print_clustering(clustering, name):
    with open(args.output_prefix + ".{}.txt".format(name), 'w') as outfile:
        to_print = []
        for sent_id, cluster in enumerate(clustering.labels_):
            to_print.append((cluster, sent_id, sentences[sent_id]))
        to_print.sort()
        prev = None
        for cluster, sent_id, sent in to_print:
            if prev is not None and cluster != prev:
                print("", file=outfile)
            print(cluster, sent_id, sent, file=outfile)
            prev = cluster

# Print a sorted version of the clusterings
clustering_kmeans = KMeans(n_clusters=min(args.nclusters, len(embeddings)), random_state=0).fit(embeddings)
clustering_ap = AffinityPropagation(random_state=5, damping=0.5, max_iter=20000).fit(embeddings)
clustering_dbscan = DBSCAN(eps=5, min_samples=2).fit(embeddings)
print_clustering(clustering_kmeans, 'kmeans')
print_clustering(clustering_ap, 'ap')
print_clustering(clustering_dbscan, 'dbscan')


# Get hierarchical clustering
model = AgglomerativeClustering(distance_threshold=0, n_clusters=None)
# affinity = one of [euclidean, l1, l2, manhattan, cosine]
# linkage = one of [ward, complete, average, single]
#    ward - minimizes the variance of the clusters being merged.
#    average - uses the average of the distances of each observation of the two sets.
#    complete - uses the maximum distances between all observations of the two sets.
#    single - uses the minimum of the distances between all observations of the two sets.

model = model.fit(embeddings)
cluster_map = [[i for i in range(len(sentences))]]
merges = []
for i, merge in enumerate(model.children_):
    cluster_map.append([])
    merges.append((int(merge[0]), int(merge[1]), i + len(sentences)))
    for pos in cluster_map[-2]:
        if pos in merge:
            cluster_map[-1].append(i + len(sentences))
        else:
            cluster_map[-1].append(pos)

with open(args.output_prefix + ".agg.json", 'w') as outfile:
    to_print = {
        'cluster-map': cluster_map,
        'merges': merges
    }
    print(json.dumps(to_print), file=outfile)
