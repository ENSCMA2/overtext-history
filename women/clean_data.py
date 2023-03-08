import sys
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import string
nltk.download('stopwords')
nltk.download('wordnet')

lines = []

stop_words = stopwords.words("english")
exclude = set(string.punctuation)
lemma = WordNetLemmatizer()

def clean(doc):
   stop_free = " ".join([i for i in doc.lower().split() if i not in stop_words])
   punc_free = ''.join([ch for ch in stop_free if ch not in exclude])
   normalized = " ".join([lemma.lemmatize(word) for word in punc_free.split()])
   return normalized

def half_clean(doc):
   punc_free = ''.join([ch for ch in doc if ch not in exclude])
   return punc_free

with open("data/" + sys.argv[1] + ".txt", "r") as o:
    for line in o:
        lines.extend(str(line).split(". "))

with open("data/clean_" + sys.argv[1] + ".txt", "w") as o:
    for i in range(len(lines)):
        cleaned = clean(lines[i])
        if len(cleaned.strip()) > 0:
            o.write(cleaned + "\n")

with open("data/unlemmatized_" + sys.argv[1] + ".txt", "w") as o:
    for i in range(len(lines)):
        cleaned = half_clean(lines[i])
        if len(cleaned.strip()) > 0:
            o.write(cleaned + "\n")
