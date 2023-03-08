import sys
from collections import Counter
import nltk
from nltk.tokenize import word_tokenize
nltk.download('punkt')

def topk(word, k):
    neighbors = []
    with open("data/clean_" + sys.argv[1] + ".txt", "r") as o:
        for line in o:
            tokenized = word_tokenize(line)
            for i in range(len(tokenized)):
                if tokenized[i] == word:
                    if i > 0:
                        neighbors.append(tokenized[i - 1])
                    if i < len(tokenized) - 1:
                        neighbors.append(tokenized[i + 1])
    neighbors_count = Counter(neighbors)
    return neighbors_count.most_common(k)

print(topk(sys.argv[2], int(sys.argv[3])))
