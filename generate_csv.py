import csv
import spacy
from nltk.tree import *
import benepar

benepar.download('benepar_en3')
nlp = spacy.load('en_core_web_sm')
if spacy.__version__.startswith('2'):
    nlp.add_pipe(benepar.BeneparComponent("benepar_en3"))
else:
    nlp.add_pipe("benepar", config={"model": "benepar_en3"})

def tree2str(tree):
    return " ".join([_ for _ in tree.leaves()])


def build_row(sentence):
    doc = nlp(sentence)
    sent = list(doc.sents)[0]
    tree = Tree.fromstring(sent._.parse_string)
    np = ''
    vp = ''
    sbar = ''
    for subtree_pos in tree.treepositions():
        if not isinstance(tree[subtree_pos], str):  # avoid leaves
            if len(np) == 0 and tree[subtree_pos].label() == 'NP':
                np = tree2str(tree[subtree_pos])
            if len(vp) == 0 and tree[subtree_pos].label() == 'VP':
                vp = tree2str(tree[subtree_pos])
            if len(sbar) == 0 and tree[subtree_pos].label() == 'SBAR':
                sbar = tree2str(tree[subtree_pos])
                np = np.replace(tree2str(tree[subtree_pos]), '')
                vp = vp.replace(tree2str(tree[subtree_pos]), '')
    return [np, vp, sbar]
                


with open('foia.txt') as f:
    SENTENCES = f.readlines()
  

row_list = []
for sent in SENTENCES:
    row_list.append(build_row(sent))

row_list = sorted(row_list, key=lambda l:len(l[2]))
row_list.insert(0, ['NP', 'VP', 'SBAR'])


with open('foia.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerows(row_list)
