# OverText

Based on:

<https://overtext.eecs.umich.edu/>


## Setup

1. Clone this repository:

```
git clone git@github.com:ENSCMA2/overtext-history.git
cd overtext-history
```

2. If you use anaconda or a similar library, deactivate it:

```
conda deactivate
```

If you are not sure, run the command above (it is harmless if you are not using anaconda).

3. Create a Python virtual environment and install the requirements:

```
python3 -m venv env-sim
source env-sim/bin/activate
pip install -r requirements.txt
```

Note, the `pip install` command could take a few minutes. It may generate a lot of scary errors if you don't have an updated version of pip, e.g., `python3 -m pip install --upgrade pip`.

## Example of Running the Code

After doing the setup above, within the top-level directory of this repository, run the following, once per primary source file you have (note that all files must end in `.txt`):
```
python txt_to_csv.py path_to_file_without_txt_extension Name_Of_Source_You_Want_Displayed
```

For example, if you have a file called `new_york_times.txt` and want it to show up as `NYT`, you'd run:
```
python txt_to_csv.py new_york_times NYT
```

This will generate a file called `new_york_times.csv` that can then be fed into the visualization.  

Then, open `config.py` and toggle `docs_1`, `docs_2`, `kw1`, `kw2`, and `neighbor` to whatever values you want them to be. `kw1` and `kw2` are the keywords you want to compare, `docs_1` and `docs_2` are lists of file paths (all paths must end in `.csv`, as generated from the previous step) for the groups of sources that you want to compare, and `neighbor` specifies whether you want to look for left- or right-neighbors (so it must be either `"left"` or `"right"`. Variable names ending in `1` are the words/sources that will show up on the left-hand column of the visualization, and variable names ending in `2` will show up on the right-hand column. An example is populated in `config.py`.

After that is ready, run the following to render the visualization:
```
flask run
```

Then go to <http://127.0.0.1:5000/> If that doesn't work check the URL given in the terminal by the command above. The most likely thing is that a different port number was chosen. If you see an import error, `pip install` the package that is said to be missing, and try `flask run` again (and repeat for each import error until it works).

To stop the server, use CTRL+C.

If the visualization renders each sentence twice, kill the server, go to `app.py`, comment out line 15 (where it says `os.environ["WEB_CONCURRENCY"] = "1"`), and run it again. Conversely, if this line is commented out, and the visualization renders each sentence twice, kill the server, uncomment that line, and start it again.

## Some relevant related work

- https://pair-code.github.io/interpretability/context-atlas/blogpost/index.html
- https://projector.tensorflow.org/
- https://storage.googleapis.com/bert-wsd-vis/demo/index.html?#word=lie
- https://www.cc.gatech.edu/gvu/ii/jigsaw/
- network analysis: https://journals.sagepub.com/doi/full/10.1177/1461444818792393
- https://journals.uic.edu/ojs/index.php/fm/article/view/10168/10065
- https://www.jbe-platform.com/content/journals/10.1075/jlac.00065.sag
- https://www.researchgate.net/profile/Yun-Jung-Lee-3/publication/232629293_Detecting_and_Visualizing_the_Dispute_Structure_of_the_Replying_Comments_in_the_Internet_Forum_Sites/links/5513492d0cf283ee083380c7/Detecting-and-Visualizing-the-Dispute-Structure-of-the-Replying-Comments-in-the-Internet-Forum-Sites.pdf
- https://www.microsoft.com/en-us/research/wp-content/uploads/2014/03/Divide-And-Correct_LearningAtScale2014.pdf
- https://ieeexplore.ieee.org/abstract/document/5329123
- https://library.harvard.edu/services-tools/check-harvard-library-bookmark
- https://dl.acm.org/doi/pdf/10.1145/3231644.3231648
 http://hint.fm/papers/forumreader.pdf

