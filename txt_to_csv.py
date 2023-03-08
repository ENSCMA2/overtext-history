import sys
import pandas as pd

# convert txt file to csv file to feed into visualization
with open(sys.argv[1] + ".txt") as i:
	lines = list(i.readlines())
	src = [sys.argv[2]] * len(lines)
	df = pd.DataFrame(data = {"source": src, "sentence": lines})
	df.to_csv(sys.argv[1] + ".csv")
