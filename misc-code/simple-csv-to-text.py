import csv
import sys
for datafile in sys.argv[1:]:
    datasrc = open(datafile)
    reader = csv.reader(datasrc)
    out = open(datafile +'.txt', 'w')
    data = [v for v in reader]
    for v in data:
      print(' '.join(v[1].split('\n')), file=out)

