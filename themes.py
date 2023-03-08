import nltk
nltk.download('averaged_perceptron_tagger')
nltk.download('stopwords')
from nltk.corpus import wordnet as wn
from sklearn.decomposition import LatentDirichletAllocation
import gensim
from gensim.utils import simple_preprocess
from nltk.corpus import stopwords
import pandas as pd
import numpy as np
import os
import re
import gensim.corpora as corpora
from pprint import pprint
import pickle 
from sklearn.cluster import KMeans
from nltk import pos_tag, word_tokenize
from nltk.stem import WordNetLemmatizer
from numpy.random import choice
import hdbscan
from collections import Counter
from sentence_transformers import SentenceTransformer

# filler words that we don't want to count
stop = stopwords.words('english')
stop.extend(['from', 'subject', 're', 'edu', 'use', 'go', 'way', 'got', 
				  'went', 'get', 'come', 'going', 'said',
                  'say', 'saying', 'really', 'da', 'la'])

# source for the following 3 functions:
# https://github.com/kapadias/medium-articles/blob/master/natural-language-processing/topic-modeling/Introduction%20to%20Topic%20Modeling.ipynb
def sent_to_words(sentences):
    for sentence in sentences:
        # deacc=True removes punctuations
        yield(gensim.utils.simple_preprocess(str(sentence), deacc=True))

def remove_stopwords(texts):
    return [[word for word in simple_preprocess(str(doc)) 
             if word not in stop] for doc in texts]

# remove stop words
def preprocess(papers):
	papers = pd.DataFrame(papers, columns = ["paper_text"])
	# Remove punctuation
	papers['paper_text_processed'] = \
	papers['paper_text'].map(lambda x: re.sub('[,\.!?]', '', x))

	# Convert the titles to lowercase
	papers['paper_text_processed'] = \
	papers['paper_text_processed'].map(lambda x: x.lower())

	data = papers.paper_text_processed.values.tolist()
	data_words = list(sent_to_words(data))
	id2word = corpora.Dictionary(data_words)
	texts = data_words
	corpus = [id2word.doc2bow(text) for text in texts]

	return papers['paper_text_processed'].tolist(), corpus, id2word

# get HDBSCAN-based clusters of sentences containing kw1 + kw2
def clusters(in_sentences, kw1, kw2, sources, lr):
	mpnet = SentenceTransformer('all-mpnet-base-v2')
	kw1 = kw1.lower()
	kw2 = kw2.lower()
	# turn sentences into vectors
	embeddings = mpnet.encode(in_sentences)
	assert(embeddings.shape[0] == len(in_sentences))
	if len(in_sentences) > 1:
		clusterer = hdbscan.HDBSCAN(min_cluster_size = 2)
		labels = clusterer.fit_predict(embeddings)
	else:
		labels = [0]
	assert(len(labels) == embeddings.shape[0])
	clusters = []
	unique_labels = list(set(labels))
	n_clusters = len(unique_labels)
	for i in range(n_clusters):
		clusters.append([w for w in range(len(embeddings)) if labels[w] == unique_labels[i]])
	# HDBSCAN has a bug where one cluster is an empty list - we filter it out here
	valid_cluster_numbers = sorted([i for i in range(len(clusters)) if len(clusters[i]) > 0], 
								   key = lambda i: len(clusters[i]), 
								   reverse = True)
	# return clustered sentences and mean of all embeddings that we will later use to calculate similar tables
	return {i: ([in_sentences[j] for j in clusters[i]], 
				[sources[j] for j in clusters[i]]) for i in valid_cluster_numbers}, np.mean(embeddings, axis = 0)
