import nltk
from nltk.corpus import wordnet as wn

nltk.download('wordnet')

# Note, requires nltk:
#   pip install --user -U nltk
#
# Not included in requirements.txt because this code just had to be run once to generate the word list


with open('person-like-nouns.txt', 'w') as outfile:
    words = set()
    done = set()
    todo = [wn.synset('person.n.01')]
    while len(todo) > 0:
        cur = todo.pop()
        words.add(cur.name())
        for hyp in cur.hyponyms():
            if hyp.name() not in done:
                done.add(hyp.name())
                todo.append(hyp)

    for word in sorted(words):
        print(word, file=outfile)

