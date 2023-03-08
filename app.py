from flask import Flask, render_template, request, redirect, url_for
import os, sys
import pandas as pd
from split_to_sentences import sentence_process
import nltk
nltk.download('omw-1.4')
from nltk import word_tokenize
from themes import *
from co_occurring import *
from config import *
import numpy as np
from sentence_transformers.util import cos_sim

os.environ["TOKENIZERS_PARALLELISM"] = "false" # disable warnings on deadlocks caused by parallelism
os.environ["WEB_CONCURRENCY"] = "1" # comment or uncomment this line depending on whether sentences show up twice

app = Flask(__name__) # Initiate the web app
app.config.from_pyfile('config.py')

sentences_all = []
# get top neighbors & sentences in which they occur for each group of sources
info_1 = get_info(docs_1, kw1, lr = neighbor)
info_2 = get_info(docs_2, kw2, lr = neighbor)

class Sentence():
    '''
    A database model for sentence excerpts. Include 5 fields:
    id: Integer, primary field
    pre: String, text before entity
    entity: String, name of the entity
    post: String, text after entity
    '''
    def __init__(self, pre, entity, post, source, cluster, slam, cat):
        self.id = id
        self.pre = pre
        self.entity = entity
        self.post = post
        self.source = source
        self.cluster = cluster
        self.slam = slam
        self.cat = cat

# pass in data to the front end
@app.route('/')
def index():
    data = []
    data2 = []
    entities_1 = []
    entities_2 = []
    mlens_1 = []
    totals_1 = []
    mlens_2 = []
    totals_2 = []
    counter = 0
    embs_1 = []
    embs_2 = []
    # do this twice - once for each group of sources
    for key in info_1.keys():
        sentences = [" ".join(item[1]) for item in info_1[key]]
        total = len(sentences)
        tokenized_sentences = [item[1] for item in info_1[key]]
        mlen = np.median([len(s) for s in tokenized_sentences])
        sources = [item[0] for item in info_1[key]]
        # get clusters based on MPNet embeddings of sentences, within each neighbor
        clumps, embs = clusters(sentences, kw1, key, sources, neighbor)
        embs_1.append(embs)
        # summary statistics - median # words per sentence & total # sentences per table
        mlens_1.append(mlen)
        totals_1.append(total)
        for category in clumps.keys():
            num_in_clump = len(clumps[category][0])
            for i in range(num_in_clump):
                sent = clumps[category][0][i].replace('\n', '')
                SOURCE = clumps[category][1][i]
                # find where to split the sentence based on where the keyword-neighbor combo is
                tmp = sent.lower().find(key + " " + kw1) if neighbor == "left" else sent.lower().find(kw1 + " " + key)
                if tmp >= 0:
                    pre = sent[:tmp]
                    entity = sent[tmp:tmp + len(key) + len(kw1) + 1]
                    post = sent[tmp + len(key) + len(kw1) + 1:]
                    entities_1.append(entity)
                    sentences_all.append(Sentence(pre = pre, 
                                                  entity = entity, 
                                                  post = post, 
                                                  source = SOURCE, 
                                                  cluster = counter,
                                                  slam = "yes" if i == len(clumps[category][0]) - 1 else "no", # thick blue lines demarcate clusters
                                                  cat = 1))
            counter += 1
    counter = 0
    for key in info_2.keys():
        sentences = [" ".join(item[1]) for item in info_2[key]]
        tokenized_sentences = [item[1] for item in info_2[key]]
        mlen = np.median([len(s) for s in tokenized_sentences])
        total = len(sentences)
        sources = [item[0] for item in info_2[key]]
        clumps, embs = clusters(sentences, kw2, key, sources, neighbor) # category: sentences, sources
        embs_2.append(embs)
        mlens_2.append(mlen)
        totals_2.append(total)
        for category in clumps.keys():
            for i in range(len(clumps[category][0])):
                sent = clumps[category][0][i].replace('\n', '')
                SOURCE = clumps[category][1][i]
                tmp = sent.lower().find(key + " " + kw2) if neighbor == "left" else sent.lower().find(kw2 + " " + key)
                if tmp >= 0:
                    pre = sent[:tmp]
                    entity = sent[tmp:tmp + len(key) + len(kw2) + 1]
                    post = sent[tmp + len(key) + len(kw2) + 1:]
                    entities_2.append(entity)
                    sentences_all.append(Sentence(pre = pre, 
                                                  entity = entity, 
                                                  post = post, 
                                                  source = SOURCE, 
                                                  cluster = counter,
                                                  slam = "yes" if i == len(clumps[category][0]) - 1 else "no",
                                                  cat = 2))
            counter += 1
    for sentence in sentences_all: # prepare data to pass into frontend
        point = {
                    'id': sentence.id,
                    'pre': sentence.pre,
                    'entity': sentence.entity,
                    'post': sentence.post,
                    'source': sentence.source,
                    'cluster': sentence.cluster,
                    'slam': sentence.slam
                }
        if sentence.cat == 1:
            data.append(point)
        elif sentence.cat == 2:
            data2.append(point)
    c1 = Counter(entities_1).most_common(len(set(entities_1)))
    c2 = Counter(entities_2).most_common(len(set(entities_2)))
    e1 = [item[0] for item in c1]
    e2 = [item[0] for item in c2]
    min_num_entities = min(len(e1), len(e2))
    e1 = e1[:min_num_entities]
    e2 = e2[:min_num_entities]
    sims = []
    sims_2 = []
    all_sims = np.empty((len(e1), len(e1)))
    all_sims.fill(-float("inf"))
    # calculate most similar table in opposite column to jump to
    for i in range(len(e1)):
        for j in range(len(e1)):
            all_sims[i, j] = cos_sim(embs_1[i], embs_2[j])
    for i in range(len(e1)):
        sims.append(np.argmax(all_sims[i]))
        sims_2.append(np.argmax(all_sims[:,j]))
    return render_template('base.html', 
                           sentence_list = data, 
                           sentence_list2 = data2,
                           entities_1 = e1,
                           entities_2 = e2,
                           num_entities = min_num_entities,
                           mlens_1 = mlens_1,
                           mlens_2 = mlens_2,
                           totals_1 = totals_1,
                           totals_2 = totals_2,
                           kw1 = kw1,
                           kw2 = kw2, 
                           sims = sims,
                           sims2 = sims_2)


if __name__ == "__main__":
    with app.app_context():
        app.run(debug=False)
