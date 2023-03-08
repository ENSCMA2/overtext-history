# Flask parameters
SQLALCHEMY_DATABASE_URI = 'sqlite:///db.sqlite'
SQLALCHEMY_TRACK_MODIFICATIONS = False
TEMPLATES_AUTO_RELOAD = True

# sample from my thesis project - files not available due to copyright
wwii_docs = ["thesis/the_juderia.csv", "thesis/erica.csv",
"thesis/from_survivors_to_pieces_of_glass.csv",
"thesis/if_i_did_not_believe_in_you.csv", "thesis/la_vara_1936.csv",
"thesis/la_vara_1942.csv", "thesis/laura_varon.csv",
"thesis/regina_amira.csv", "thesis/revelation.csv",
"thesis/rosa_berro.csv", "thesis/saving_the_puffins.csv",
"thesis/silence.csv", "thesis/sometimes_people_think.csv",
"thesis/suspect_fashion.csv", "thesis/tell_us_no_more_train_stories.csv",
"thesis/the_inquiry.csv",
"thesis/the_mystical_child.csv", "thesis/they_all_went.csv"]
wwii_news = ["thesis/la_vara_1936.csv", "thesis/la_vara_1942.csv"]
wwii_salonica_docs = ["thesis/erica.csv", "thesis/from_survivors_to_pieces_of_glass.csv",
"thesis/the_inquiry.csv"]
wwi_news = ["thesis/el_progreso_1915.csv", "thesis/el_progreso_1919.csv"]
wwi_docs = ["thesis/el_progreso_1915.csv", "thesis/marguerite.csv",
"thesis/el_progreso_1919.csv",
"thesis/esther_kahn.csv",	
"thesis/farewell_to_salonica.csv",
"thesis/fortuna_calvo.csv",
"thesis/i_remember_rhodes.csv",
"thesis/inshallah.csv",
"thesis/the_house_of_jacob.csv",
"thesis/la_tia_estambolia.csv", "thesis/victoria_israel.csv"]
wwi_news = ["thesis/el_progreso_1915.csv", "thesis/el_progreso_1919.csv"]
wwi_women = ["thesis/marguerite.csv",
"thesis/esther_kahn.csv",	
"thesis/fortuna_calvo.csv",
"thesis/i_remember_rhodes.csv",
"thesis/inshallah.csv",
"thesis/the_house_of_jacob.csv",
"thesis/la_tia_estambolia.csv", "thesis/victoria_israel.csv"]

# sample you can run
sample_docs = ["sample.csv"]

# change these variables for your own sources!
docs_1 = sample_docs # sources to display on left column
docs_2 = sample_docs # sources to display on right column
kw1 = "she" # keyword to search for in docs_1
kw2 = "he" # keyword to search for in docs_2
neighbor = "right" # must be "left" or right"
