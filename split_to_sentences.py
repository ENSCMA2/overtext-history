import nltk
from nltk.tokenize import sent_tokenize
import pandas as pd

# splits sources into sentences so you don't have to!
def sentence_process(in_file):
	df = pd.read_csv(in_file, index_col = 0)
	new_df = pd.DataFrame()
	sources = []
	sentences = []
	for index, item in df.iterrows():
		sentence = item["sentence"]
		new_sentences = sent_tokenize(sentence)
		sources.extend([item["source"] for i in range(len(new_sentences))])
		sentences.extend(new_sentences)
	assert(len(sources) == len(sentences))
	new_df["source"] = sources
	new_df["sentence"] = sentences
	return new_df
