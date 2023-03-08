from itertools import chain
import numpy as np
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim
import spacy

# semantic search
def semantic_sim(sentences):
    mpnet = SentenceTransformer('all-mpnet-base-v2') # SOTA model, better than SBERT
    embeddings = mpnet.encode(sentences) # generate sentence embeddings
    sim = np.zeros((len(sentences), len(sentences)))
    for i in range(len(sentences)):
        sim[i:,i] = cos_sim(embeddings[i], embeddings[i:]) # half of the table is filled
    j = 1
    for i in range(len(sentences)-1):
        sim[i, j:] = sim[j:,i] # need to fill in all the zeros for our specific use case
        j += 1
    return sim # pairwise cosine similarity values, dimensions: len(sentences) * len(sentences)


# helper function for syntactic search
def generate_tags(doc):
    stopwords = ['DT']
    rst = []
    for token in doc:
        if token.tag_ in stopwords:
            continue
        elif token.tag_ in ['JJ', 'JJR', 'JJS']:
            rst.append('JJ')
        elif token.tag_ in ['NN', 'NNS', 'NNP', 'NNPS']:
            rst.append('NN')
        elif token.tag_ in ['RB', 'RBR', 'RBS']:
            rst.append('RB')
        elif token.tag_ in ['VB', 'VBP', 'VBD', 'VBZ']:
            rst.append('VB')
            rst.append('VB*') # Accentuate verb phrases
        else:
            rst.append(token.tag_)
    return rst

def ngrams(sequence, n, pad_left=False, pad_right=False, pad_symbol=None):
    """
    A utility that produces a sequence of ngrams from a sequence of items.
    For example:

    ngrams([1,2,3,4,5], 3) returns
    [(1, 2, 3), (2, 3, 4), (3, 4, 5)]

    ngrams([1,2,3,4,5], 2, pad_right=True) returns
    [(1, 2), (2, 3), (3, 4), (4, 5), (5, None)]
    """
    if pad_left:
        sequence = chain((pad_symbol,) * (n-1), sequence)
    if pad_right:
        sequence = chain(sequence, (pad_symbol,) * (n-1))
    sequence = list(sequence)

    count = max(0, len(sequence) - n + 1)
    return [tuple(sequence[i:i+n]) for i in range(count)] 

# syntactic search
def syntactic_sim(sentences):
    nlp = spacy.load('en_core_web_sm')
    docs = [nlp(sent) for sent in sentences]
    rst = np.zeros((len(sentences), len(sentences)))
    for i in range(len(sentences)):
        for j in range(i, len(sentences)):
            if i == j:
                rst[i,j] = 1
            else:
                X_list = generate_tags(docs[i]) # POS tags
                Y_list = generate_tags(docs[j]) # POS tags
                l1 =[]
                l2 =[]
                X_ngrams = set(ngrams(X_list, 2, pad_left=True, pad_symbol='S')) # bigrams with left padding
                Y_ngrams = set(ngrams(Y_list, 2, pad_left=True, pad_symbol='S')) # bigrams with left padding
                rvector = X_ngrams.union(Y_ngrams)
                for ngram in rvector:
                    if ngram in X_ngrams:
                        l1.append(1)
                    else:
                        l1.append(0)
                    if ngram in Y_ngrams:
                        l2.append(1)
                    else:
                        l2.append(0)
                c = 0
                for k in range(len(rvector)):
                    c+= l1[k]*l2[k]
                score = c / float((sum(l1)*sum(l2))**0.5)
                rst[i,j] = min(score, 0.99) # set upper bound to make sure the selected sentence is the top sentence
                rst[j,i] = min(score, 0.99)
                # print(' '.join(X_list))
                # print(' '.join(Y_list))
                # print(score)
    return rst


# greedy search returns a 2d matrix, given a 2d matrix
def greedy(m):
    rst = np.zeros((len(m), len(m)))
    n = np.argsort(-m) # descending order, matrix of indices
    for i in range(len(n)):
        start = i
        current = set()
        acc = 0
        while acc < len(n):
            j = 0
            while n[start, j] in current:
                j+=1
            current.add(n[start, j])
            start = n[start, j]
            rst[i,start] = acc
            acc += 1
    return rst
            








