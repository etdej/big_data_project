module load python/gnu/3.4.4
module load spark/2.2.0
export PYSPARK_PYTHON='/share/apps/python/3.4.4/bin/python'
export PYSPARK_DRIVER_PYTHON='/share/apps/python/3.4.4/bin/python'

TMPFILE="interface.out"

if [ -e "$DIFFFILE" ]; then
        rm "$DIFFFILE"
fi

/usr/bin/hadoop fs -rm -r "interface.out"

spark-submit --conf spark.pyspark.python=/share/apps/python/3.4.4/bin/python interface.py 
/usr/bin/hadoop fs -getmerge "interface.out" "$TMPFILE".tmp
cat "$TMPFILE".tmp | sort -n > "$TMPFILE"
rm "$TMPFILE".tmp

