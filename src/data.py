#!/usr/bin/env python3

import json
import argparse
import textwrap
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from umap import UMAP
import plotly.express as px

def convert_token(token):
    token = "(".join(token.split("-LRB-"))
    token = ")".join(token.split("-RRB-"))
    return token

class Row:
    def __init__(self, values, best_type, full_comment, sentence, multi_sentence, context, cluster):
        self.values = values
        self.best_type = best_type
        self.multi_sentence = multi_sentence > 1
        self.full_comment = full_comment
        self.sentence = sentence
        self.context = context
        self.cluster = cluster

    def __lt__(self, other):
        return False

class OurTable:
    def __init__(self, table_data):
        self.fields = []
        self.rows = []
        self.agg = table_data['agg']
        self.default_agg = table_data['default-agg']
        self.filename = table_data['name']
        self.clustered = "_clustered" in self.filename
        self.name = " ".join(self.filename.split("_")[0].split("-"))

        # Set up fields
        self.fields = table_data['fields']
        for field, name in enumerate(self.fields):
            alignment = 'center'
            if '_' in name:
                end = name.split("_")[-1]
                if end in ['left', 'right', 'center', 'hidden']:
                    alignment = end
                    name = name[:-len("_"+ alignment)]
            self.fields[field] = (name, alignment)

        # Read data
        for item_no, item in enumerate(table_data['items']):
            best_type = item['best_or_not']
            first_sentence = item['sent']
            full_comment = item['doc']
            multi_sentence = item['multi_sent_doc']
            cluster = item['cluster_id']

            context = (item['before'], item['after'])

            edited = []
            for field, val in enumerate(item['text']):
                val = ' '.join([convert_token(v[0]) for v in val])
                edited.append(val)

            self.rows.append(Row(edited, best_type, full_comment, first_sentence, multi_sentence, context, cluster))

def get_center(cluster, sentences, method, embeddings):
    if method == 'first':
        return cluster[0]
    elif method == 'shortest':
        options = [(len(sentences[v]), v) for v in cluster]
        options.sort()
        return options[0]
    elif method == 'central':
        best = None
        for option in cluster:
            emb0 = embeddings[option]
            dist = 0
            if len(sentences[option]) > 100:
                dist += 10000
            for other in cluster:
                emb1 = embeddings[other]
                dist += np.linalg.norm(emb0 - emb1, ord=2)
            if best is None or dist < best[1]:
                best = (option, dist)
        return best[0]
    assert False

# TODO: move this into a preprocessing step that occurs outside the server
def prep_dot_data(datasets, args):
    data_frames = {}
    agg_cluster_counts = {}
    for name, dataset in datasets.items():
        data_info = {}
        data_frames[name] = data_info

        # Read embeddings
        embeddings = dataset['embeddings']

        # Run PCA on the complete embeddings
        dim_reducer = UMAP(n_components=2, init='random', random_state=0)
        if args.dim_reducer == 'pca':
            dim_reducer = PCA(n_components=2)
        elif args.dim_reducer == 'umap':
            dim_reducer = UMAP(n_components=2, init='random', random_state=0)
        elif args.dim_reducer == 'tsne':
            dim_reducer = TSNE(n_components=2, learning_rate='auto', init='random')

        reduced_embeddings = dim_reducer.fit_transform(embeddings)
        x_vals = [v[0] for v in reduced_embeddings]
        y_vals = [v[1] for v in reduced_embeddings]

        sentences = dataset['wrapped_sentences']

        # Read clusters
        clusters = []
        for cluster_no, cluster_content in dataset['clusters'].items():
            for sent_no in cluster_content:
                clusters.append((sent_no, cluster_no))
        clusters.sort()

        # TODO: Sometimes labels disappear then reappear as we change level.
        # This is probably a bug in this section of the code.

        # Do not render all levels
        agg_info = dataset['agg']
        mod_map = agg_info['cluster-map'][-50:]
        print(len(mod_map), "levels for", name)
###        increment = 10
###        mod_map = []
###        for i, row in enumerate(agg_info['cluster-map']):
###            if i == len(agg_info['cluster-map']) or i % 10 == 0:
###                mod_map.append(row)

        agg_centers = {}
        agg_clusters = {}
        for row_no in range(len(mod_map) -1, -1, -1):
            row = mod_map[row_no]
            todo = {}
            for sent_id, cluster_id in enumerate(row):
                if cluster_id not in agg_clusters:
                    todo.setdefault(cluster_id, []).append(sent_id)
            for cluster_id, cluster in todo.items():
                agg_clusters[cluster_id] = cluster
                # Check if this contains the sentence that was the center of a
                # larger cluster, if so, reuse it
                center = None
                if row_no < len(mod_map) - 1:
                    for sent_id in cluster:
                        prev_cluster = mod_map[row_no + 1][sent_id]
                        if agg_centers[prev_cluster] == sent_id:
                            center = sent_id
                if center is None:
                    center = get_center(cluster, sentences, args.label_selection, embeddings)
                agg_centers[cluster_id] = center
        agg_cluster_counts[name] = len(agg_clusters)
        cluster_parents = {}
        for c0, c1, merged in agg_info['merges']:
            cluster_parents[c0] = merged
            cluster_parents[c1] = merged
        seen = set()
        for row in mod_map:
            for cluster_id in row:
                seen.add(cluster_id)
        nparents = {}
        for cluster_id, parent in cluster_parents.items():
            while parent not in seen and parent in cluster_parents:
                parent = cluster_parents[parent]
            if parent in seen:
                nparents[cluster_id] = parent
        cluster_parents = nparents

        # Form dataframe
        full_data = {
            'sentences': [],
            'x_vals': [],
            'y_vals': [],
            'color': [],
            'cluster': [],
            'label': [],
            'marker': [],
            'size': [],
            'agg_level': [],
        }

        cluster_chains = []
        for sent_id, _ in sentences.items():
            chain = {sent_id}
            cluster_id = sent_id
            if cluster_id not in seen:
                cluster_id = cluster_parents[cluster_id]
            while cluster_id in cluster_parents and agg_centers[cluster_parents[cluster_id]] == agg_centers[cluster_id]:
                chain.add(cluster_id)
                cluster_id = cluster_parents[cluster_id]
            chain.add(cluster_id)
            cluster_chains.append(chain)
        cluster_to_chain = {}
        for chain_id, chain in enumerate(cluster_chains):
            for cluster in chain:
                cluster_to_chain[cluster] = chain_id

        mark_for_chain = []
        # Symbols and colours
        # https://plotly.com/python/discrete-color/
        symbols = ["circle", "square", "diamond", "triangle-up", "triangle-down", "star", "x", "circle-open", "square-open", "diamond-open", "triangle-up-open", "triangle-down-open", "star-open", "x-open", ]
        colors = px.colors.qualitative.Plotly
        while len(mark_for_chain) < len(cluster_chains):
            for symbol in range(len(symbols)):
                for color in range(len(colors)):
                    mark_for_chain.append(symbol)

        for agg_level, row in enumerate(mod_map):
            for sent_id, cluster_id in enumerate(row):
                full_data['sentences'].append(sentences[sent_id])
                full_data['x_vals'].append(x_vals[sent_id])
                full_data['y_vals'].append(y_vals[sent_id])
                full_data['cluster'].append(str(cluster_id))
                full_data['size'].append(1)
                full_data['agg_level'].append(agg_level)

                # Show a label only for cluster centers
                if agg_centers[cluster_id] == sent_id:
                    full_data['label'].append(sentences[sent_id])
                else:
                    full_data['label'].append('')

                # Set marker style and color
                color = str(cluster_to_chain[cluster_id] % len(colors))
                mark = mark_for_chain[cluster_to_chain[cluster_id]]
                full_data['marker'].append(mark)
                full_data['color'].append(color)

        data_info['color_map'] = {str(i): colors[int(i) % len(colors)] for i in range(len(cluster_chains))}

        # Create a dataframe for visualisation
        data_info['df'] = pd.DataFrame(data=full_data)
    return data_frames, agg_cluster_counts

def read_data(args):
    datasets = {}
    for prefix, name  in zip(args.data_prefixes, args.names):
        if '.txt' in prefix:
            prefix = ''.join(prefix.split(".txt"))
        prefix = 'tmp/' + prefix.split("/")[-1] +"/"
        table_file = prefix +"out.tables.json"
        embedding_file = prefix +"out.vectors.npy"
        sentence_file = prefix +"out.sentences.txt"
        cluster_file = prefix +"out.ap.txt"
        agg_file = prefix +"out.agg.json"
 
        dataset = {}
        datasets[name] = dataset

        # Read tables
        tables = []
        tables_for_bottom = []
        with open(table_file) as table_src:
            assert table_file.endswith(".json")
            table_data = json.load(table_src)
            for table in table_data:
                ntable = OurTable(table)
                if 'Other' in ntable.name:
                    tables_for_bottom.append(ntable)
                else:
                    tables.append(ntable)
        for table in tables_for_bottom:
            tables.append(table)
        dataset['tables'] = tables

        # Read embeddings
        with open(embedding_file, 'rb') as f:
            dataset['embeddings'] = np.load(f)

        # Read clusters
        clusters = {}
        with open(cluster_file) as f:
            for line in f.readlines():
                parts = line.strip().split()
                if len(parts) > 0:
                    cluster = int(parts[0])
                    sent_id = int(parts[1])
                    clusters.setdefault(cluster, []).append(sent_id)
        dataset['clusters'] = clusters

        # Read sentences
        sentences = {}
        wrapped_sentences = {}
        with open(sentence_file) as f:
            for line in f.readlines():
                parts = line.strip().split()
                if len(parts) > 0:
                    sent_id = int(parts[0])
                    sent = line.strip()[len(parts[0]) + 1:]
                    sentences[sent_id] = sent
                    wrapped = '<br />'.join(textwrap.wrap(sent, 50))
                    wrapped_sentences[sent_id] = wrapped
        dataset['sentences'] = sentences
        dataset['wrapped_sentences'] = wrapped_sentences

        # Read agglomerative clustering
        with open(agg_file) as f:
            assert agg_file.endswith(".json")
            dataset['agg'] = json.load(f)

    return datasets

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Read data.')
    parser.add_argument('tables', nargs="+",
                        help='JSON file with information from form-tables.py')
    args = parser.parse_args()

    datasets = read_data(args)
