import csv
import sys
from collections import Counter
import nltk
from nltk.tokenize import word_tokenize
nltk.download('punkt')

left = []
right = []
max_i = 0
with open("data/unlemmatized_" + sys.argv[1] + ".txt", "r") as o:
    for line in o:
        tokenized = word_tokenize(line)
        for i in range(len(tokenized)):
            if tokenized[i] == sys.argv[2]:
                right.append(tokenized[i:])
                left.append(tokenized[:i + 1])
                max_i = max(max_i, i + 1)

with open("outputs/" + "left_" + sys.argv[1] + "_" + sys.argv[2] + ".csv", "w") as o:
    for line in left:
        num_padding = max_i - len(line)
        o.write("," * num_padding + ",".join(line) + "\n")

with open("outputs/" + "right_" + sys.argv[1] + "_" + sys.argv[2] + ".csv", "w") as o:
    for line in right:
        o.write(",".join(line) + "\n")
