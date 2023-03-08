#!/usr/bin/env python3

import json
import argparse
import re

from flask import Flask

import data
import vis.overtext
import vis.dots

def data_selection_page(vis_name, datasets):
    page = [
        "<p>Choose a dataset:</p>",
    ]
    for dataset in datasets:
        page.append('<p><a href="/{}/{}/">{}</a></p>'.format(vis_name, dataset, dataset))
    return '\n'.join(page)

def fully_specified_page(vis_name, dataset_name, page_config):
    if dataset_name not in datasets:
        return "Dataset {} is not available".format(dataset_name)
    dataset = datasets[dataset_name]
    make_page = None
    if vis_name == 'overtext':
        make_page = vis.overtext.make_page
    else:
        print(vis_name)

    return make_page(dataset, list(datasets.keys()), dataset_name, page_config)

def create_app(datasets):
    app = Flask(__name__)

    @app.route("/")
    def path_empty():
        page = [
            "<p>Choose a visualisation method:</p>",
        ]
        for vis_name in ['overtext', 'baseline-dots', 'baseline-text']:
            page.append('<p><a href="/{}/">{}</a></p>'.format(vis_name, vis_name))
        return '\n'.join(page)

    @app.route("/overtext/")
    def path_overtext():
        return data_selection_page("overtext", datasets)

    @app.route("/baseline-text/")
    def path_baseline_text():
        return data_selection_page("baseline-text", datasets)

    @app.route("/overtext/<dataset>/")
    def path_overtext_dataset(dataset):
        return fully_specified_page("overtext", dataset, "")

    @app.route("/baseline-text/<dataset>/")
    def path_baseline_text_dataset(dataset):
        return fully_specified_page("baseline-text", dataset, "")

    @app.route("/overtext/<dataset>/<page_config>/")
    def path_overtext_full(dataset, page_config):
        return fully_specified_page("overtext", dataset, page_config)

    @app.route("/baseline-text/<dataset>/<page_config>/")
    def path_baseline_text_full(dataset, page_config):
        return fully_specified_page("baseline-text", dataset, page_config)

    with app.app_context():
        from vis.dots import init_vis

        data_frames, agg_cluster_counts = data.prep_dot_data(datasets, args)
        app = init_vis(app, data_frames, agg_cluster_counts)

        return app

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert tables to html.')

    # Data files
    parser.add_argument('--data-prefixes', nargs="+",
                        help='Prefix for filenames')
    # Info about each dataset
    parser.add_argument('--names', nargs="+",
                        help='Names of datasets')

    # Options for dot vis
    parser.add_argument('--label-selection', default="central",
                        choices=['random', 'shortest', 'central'],
                        help='Method for choosing what is labeled')
    parser.add_argument('--dim-reducer', default="umap",
                        choices=['pcs', 'tsne', 'umap'],
                        help='Dimensionality reduction method')

    # Server options
    parser.add_argument('--port', default=5003,
                        help='Port for webserver')
    parser.add_argument('--profile', action='store_true',
                        help='Profile the app to see where time is being spent')
    args = parser.parse_args()

    datasets = data.read_data(args)

    # Start app
    app = create_app(datasets)
    if args.profile:
        from werkzeug.middleware.profiler import ProfilerMiddleware
        app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])
    app.run(host="127.0.0.1", port=args.port, use_reloader=True)
