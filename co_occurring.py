from split_to_sentences import *
from collections import Counter
import nltk
from nltk.tokenize import word_tokenize
import sys
from nltk.corpus import stopwords
import json
from themes import *

stops = stopwords.words('english')

def strip_punc(w):
	return "".join([char for char in w if char in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"])

# get neighbors for a word and a list of docs
def get_info(list_of_docs, word, lr = "right", top = 10):
    sources = []
    sentences = []
    for doc in list_of_docs:
        df = sentence_process(doc)
        sources.extend(df["source"])
        sentences.extend(df["sentence"])
    giant_df = pd.DataFrame(data = {"source": sources, "sentence": preprocess(sentences)[0]})
    df_relevant = giant_df[giant_df["sentence"].str.contains(word)]
    relevant_sources = []
    relevant_sentences = []
    # make sure all sentences not containing word have been filtered out
    for index, item in df_relevant.iterrows():
    	split_sentence = [strip_punc(w) for w in item["sentence"].split()]
    	if word in split_sentence:
    		relevant_sources.append(item["source"])
    		relevant_sentences.append(item["sentence"])
    df_relevant = pd.DataFrame(data = {"source": relevant_sources, "sentence": relevant_sentences})
    neighbors = []
    indices = []
    split_sentences = []
    # standardize sentences, find neighbors
    for index, item in df_relevant.iterrows():
        split_sentence = [strip_punc(w) for w in item["sentence"].split()]
        place = split_sentence.index(word)
        split_sentences.append(split_sentence)
        indices.append(place)
        if place > 0 and lr == "left":
            neighbors.append(split_sentence[place - 1])
        elif place < len(split_sentence) - 1 and lr == "right":
            neighbors.append(split_sentence[place + 1])
    neighbors = [n for n in neighbors if n not in stops]
    neighbors_count = Counter(neighbors)
    # find top neighbors
    top_neighbors = neighbors_count.most_common(top)
    neighbors_out = {n[0]: [] for n in top_neighbors}
    for i in range(len(top_neighbors)):
        neighbor = top_neighbors[i][0]
        for j in range(len(split_sentences)):
            if lr == "right" and indices[j] + 1 < len(split_sentences[j]) and split_sentences[j][indices[j] + 1] == neighbor:
                neighbors_out[neighbor].append((relevant_sources[j], split_sentences[j]))
            elif lr == "left" and indices[j] - 1 >= 0 and split_sentences[j][indices[j] - 1] == neighbor:
                neighbors_out[neighbor].append((relevant_sources[j], split_sentences[j]))
    return neighbors_out

# execute a clunky terminal-based visualization of the get_info results
def execute_interaction():
	files = []
	files.append(input(("Enter first data file.\n")))
	done = False
	while not done:
		next_file = input("Enter next file, or \"done\" to finish entering files.\n")
		if next_file != "done":
			files.append(next_file)
		else:
			done = True
	word = input("Enter key word.\n")
	num = int(input("How many neighbors would you like to see?\n"))
	info = get_info(files, word, num)
	with open("thesis/out/" + sys.argv[1] + ".json", "w") as outfile:
		json.dump(info, outfile)
	print(f"The top {num} neighbors of {word} are: {', '.join(list(info.keys()))}.")
	to_viz = input("Enter a word to see stats and sentences containing the word. Type \"i am done\" to exit.\n")
	while to_viz != "i am done":
		if to_viz in info.keys():
			word_info = info[to_viz]
			print(f"The word {to_viz} appears as a neighbor of {word} {len(word_info)} times.")
			yn = input("Would you like to see the sentences? Type \"yes\" or \"no\".\n")
			if yn == "yes":
				for i in range(len(word_info)):
					print(word_info[i][0], "\t", " ".join(word_info[i][1]))
		to_viz = input("Enter a word to see stats and sentences containing the word. Type \"i am done\" to exit.\n")

# execute_interaction()