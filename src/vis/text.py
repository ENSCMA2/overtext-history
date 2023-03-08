#!/usr/bin/env python3

import argparse
import sys
import json

import numpy as np
from flask import Flask

def html_for_cluster(cluster_id, cluster, center, sentences, visible, sent_order):
    ans = {
        'html': [],
        'script': [],
        'expand_script': [],
        'hide_script': [],
    }
    html = ans['html']
    display = 'block' if visible else 'none'
    html.append('<div id="outer-cluster{}" style="display: {};">'.format(cluster_id, display))
    if len(cluster) == 1:
        html.append('<p style="margin:3px;">{}</p>'.format(sentences[cluster[0]]))
    else:
        ans['script'] = [
                "var button = document.getElementById('cluster{}');".format(cluster_id),
                "button.onclick = function() {",
                "    var div = document.getElementById('div-cluster{}');".format(cluster_id),
                "    if (div.style.display !== 'none') {",
                "        div.style.display = 'none';",
                "    }",
                "    else {",
                "        div.style.display = 'block';",
                "    }",
                "};"
        ]
        ans['expand_script'].append("    var div = document.getElementById('div-cluster{}');\ndiv.style.display = 'block';".format(cluster_id))
        ans['hide_script'].append("    var div = document.getElementById('div-cluster{}');\ndiv.style.display = 'none';".format(cluster_id))

        html.append('<p id="cluster{}" style="margin:3px; font-weight: bold;">{}</p>'.format(cluster_id, sentences[center]))
        html.append('<div id="div-cluster{}" style="display: block;">'.format(cluster_id))

        for sent_id in sent_order:
            if sent_id != center and sent_id in cluster:
                html.append('<p style="margin:3px">{}</p>'.format(sentences[sent_id]))
        html.append('</div>')

    html.append("<hr />")
    html.append("</div>")
    return ans

def get_center(cluster, sentences, method):
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
            if best is None or best[1] > dist:
                best = (option, dist)
        return best[0]
    assert False

def make_page(clusters, centers, sentences, agg_cluster_order, agg_centers, agg_clusters, agg_info, sent_order):
    merge_level = len(agg_info['merges']) - len(clusters) + 1
    merge_state = agg_info['cluster-map'][merge_level]
    content = [
        '    <div style="text-align: center;">',
        '        <button id="expand-all">Expand all</button>',
        '        <button id="hide-all">Contract all</button>',
        '    </div>',
        '    <br />',
        '    <div style="text-align: center;">',
        '        <span>Smaller clusters</span>',
        '        <input type="range" min="0" max="{}" value="{}" class="slider" id="cluster-level">'.format(len(agg_info['merges']), merge_level),
        '        <span>Bigger clusters</span>',
        '    </div>',
    ]
    script = []

    # Make the slider
    script.append('  var slider = document.getElementById("cluster-level");')
    script.append('  slider.oninput = function() {')
    for cluster_id in agg_clusters:
        script.append('  var outer_div{} = document.getElementById("outer-cluster{}");'.format(cluster_id, cluster_id))
        script.append('  var inner_div{} = document.getElementById("div-cluster{}");'.format(cluster_id, cluster_id))
    # For each merger 
    script += [
        '  let new_val = this.value;',
    ]
    for level, cur_sent_to_cluster in enumerate(agg_info["cluster-map"]):
        cur_clusters = set(cur_sent_to_cluster)
        script += [
            '    if (new_val == {}) {{'.format(level),
        ]
        for cluster_id in agg_clusters:
            if cluster_id in cur_clusters:
                script.append('      outer_div{}.style.display = "block";'.format(cluster_id))
        for cluster_id in agg_clusters:
            if cluster_id not in cur_clusters:
                script += [
                    '      outer_div{}.style.display = "none";'.format(cluster_id),
                ]
        script += [
            '    }'
        ]
    script.append('}')


    expand_script = [
        'var button_show = document.getElementById("expand-all");',
        'button_show.onclick = function() {',
    ]
    hide_script = [
        'var button_hide = document.getElementById("hide-all");',
        'button_hide.onclick = function() {',
    ]

    for cluster_id in agg_cluster_order:
        display = True if cluster_id in merge_state else False
        cluster = agg_clusters[cluster_id]
        center = agg_centers[cluster_id]
        to_add = html_for_cluster(cluster_id, cluster, center, sentences, display, sent_order)
        content += to_add['html']
        script += to_add['script']
        expand_script += to_add['expand_script']
        hide_script += to_add['hide_script']

    expand_script.append("};")
    hide_script.append("};")

    start = ["<!DOCTYPE html>", "<html>"]
    script = ["<script>"] + script + expand_script + hide_script + ["</script>"]
    body = ["<body>"] + content + script + ["</body>"]
    end = ["</html>"]
    html = start + body + end

    return "\n".join(html)

def create_app(clusters, centers, sentences, agg_cluster_order, agg_centers, agg_clusters, agg_info, sent_order):
    app = Flask(__name__)

    @app.route("/")
    def main():
        return make_page(clusters, centers, sentences, agg_cluster_order, agg_centers, agg_clusters, agg_info, sent_order)

    return app

if __name__ == '__main__':


    # Get centers for all clusters
    centers = {}
    for cluster_id, cluster in clusters.items():
        centers[cluster_id] = get_center(cluster, sentences, args.label_selection)
    agg_centers = {}
    agg_clusters = {}
    for row_no, row in enumerate(agg_info['cluster-map'][::-1]):
        todo = {}
        for sent_id, cluster_id in enumerate(row):
            if cluster_id not in agg_clusters:
                todo.setdefault(cluster_id, []).append(sent_id)
        for cluster_id, cluster in todo.items():
            agg_clusters[cluster_id] = cluster
            # Check if this contains the sentence that was the center of a larger cluster, if so, reuse it
            center = None
            if row_no > 0:
                for sent_id in cluster:
                    prev_row = len(agg_info['cluster-map']) - row_no
                    prev_cluster = agg_info['cluster-map'][prev_row][sent_id]
                    if agg_centers[prev_cluster] == sent_id:
                        center = sent_id
            if center is None:
                center = get_center(cluster, sentences, args.label_selection)
            agg_centers[cluster_id] = center

    # Work out order for agg clusters
    agg_cluster_order = []
    for c0, c1, merged in agg_info['merges'][::-1]:
        # Base case, insert the final cluster seen
        if len(agg_cluster_order) == 0:
            agg_cluster_order.append(merged)

        # Get the position of the current cluster
        cpos = agg_cluster_order.index(merged)

        # Work out an order
        c0_top = agg_centers[c0] == agg_centers[merged]
        c1_top = agg_centers[c1] == agg_centers[merged]
        if not (c0_top or c1_top):
            # Center changes, choose top based on size
            if len(agg_clusters[c0]) > len(agg_clusters[c1]):
                c0_top = True
            else:
                c1_top = True
        agg_cluster_order.insert(cpos + 1, c0)
        if c1_top:
            agg_cluster_order.insert(cpos + 1, c1)
        else:
            agg_cluster_order.insert(cpos + 2, c1)

    sent_order = []
    for cluster in agg_cluster_order:
        if len(agg_clusters[cluster]) == 1:
            sent_order.append(agg_clusters[cluster][0])

    print(make_page(clusters, centers, sentences, agg_cluster_order, agg_centers, agg_clusters, agg_info, sent_order))
