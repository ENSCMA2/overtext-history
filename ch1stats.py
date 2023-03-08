from split_to_sentences import *

'''
Calculating the number of sentence samples in my thesis' dataset.
'''

news = ["thesis/el_progreso_1915.csv", "thesis/el_progreso_1919.csv",
        "thesis/la_vara_1936.csv", "thesis/la_vara_1942.csv"]
news_sentences = sum([len(sentence_process(item)["sentence"].tolist()) for item in news])
print("news:", news_sentences)

poems = [
"thesis/if_i_did_not_believe_in_you.csv", 
"thesis/revelation.csv",
"thesis/saving_the_puffins.csv",
"thesis/silence.csv", "thesis/sometimes_people_think.csv",
"thesis/suspect_fashion.csv", "thesis/tell_us_no_more_train_stories.csv",
"thesis/the_mystical_child.csv", "thesis/they_all_went.csv"]
poems_sentences = sum([len(sentence_process(item)["sentence"].tolist()) for item in poems])
print("poems:", poems_sentences)

interviews = ["thesis/laura_varon.csv",
"thesis/regina_amira.csv", 
"thesis/rosa_berro.csv", "thesis/esther_kahn.csv",	
"thesis/fortuna_calvo.csv",
"thesis/victoria_israel.csv"]
interviews_sentences = sum([len(sentence_process(item)["sentence"].tolist()) for item in interviews])
print("interviews:", interviews_sentences)

essays = ["thesis/erica.csv",
"thesis/from_survivors_to_pieces_of_glass.csv", "thesis/the_inquiry.csv",
"thesis/la_tia_estambolia.csv"]
essays_sentences = sum([len(sentence_process(item)["sentence"].tolist()) for item in essays])
print("essays:", essays_sentences)

memoirs = ["thesis/marguerite.csv",
"thesis/farewell_to_salonica.csv",
"thesis/i_remember_rhodes.csv",
"thesis/inshallah.csv",
"thesis/the_house_of_jacob.csv",
"thesis/the_juderia.csv"]
memoirs_sentences = sum([len(sentence_process(item)["sentence"].tolist()) for item in memoirs])
print("memoirs:", memoirs_sentences)
print("total:", news_sentences + poems_sentences + interviews_sentences + essays_sentences + memoirs_sentences)
