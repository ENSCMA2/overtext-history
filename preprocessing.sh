#!/bin/bash

set -e

TEXT_FILE=$1
OUT_DIR=tmp/`basename $TEXT_FILE | sed 's/.txt//'`
mkdir -p $OUT_DIR
OUT_PREFIX=$OUT_DIR/out
python run-sbert.py $TEXT_FILE --output-prefix $OUT_PREFIX
python vect-to-sim.py $OUT_PREFIX.vectors.npy $OUT_PREFIX.sentences.txt --output-prefix $OUT_PREFIX
python cluster.py $OUT_PREFIX.vectors.npy $OUT_PREFIX.sentences.txt --output-prefix $OUT_PREFIX
python3 form-tables.py ${OUT_PREFIX}.ap.txt ${OUT_PREFIX}.sim.txt ${OUT_PREFIX}.agg.json --output-prefix ${OUT_PREFIX} --ndocs 30000 > ${OUT_PREFIX}.parse-log.txt

