import os
os.system('./init_script.sh')

from csv import reader
from pyspark import SparkContext
import sys
import json

from pyspark.sql import SQLContext, SparkSession
from pyspark.sql.functions import split, explode

spark = SparkSession \
    .builder \
    .appName("Python Spark SQL basic example") \
    .config("spark.some.config.option", "some-value") \
    .getOrCreate()


base_path='/user/bigdata/nyc_open_data/'

class Column_selecter:
    def __init__(self, datasets_path):
        self.paths = [os.path.join(base_path, path) for path in datasets_path]
        df = spark.read.json(self.paths[0], multiLine=True)
        df.registerTempTable("df")
        
        dfCol = df.select(explode(df.meta.view.columns))
        dfCol = dfCol.select('col.fieldName')
        
        columns = [i.fieldName for i in dfCol.collect()]

        print(columns)
        #print(dfCol.printSchema())
        #print(dfCol.show())
         #print(df.show())
        dfData = df.select(explode(df.data))
        print(dfData.show())
        dfData = dfData.select(*[dfData.col[i] for i in range(len(columns))]).toDF(*columns)
        print(dfData.printSchema())
        print(dfData.show())
        #dfMeta = df.select(df.meta)
        #print(dfMeta.show())
        #print(self.data_set0.select('columns'))
	#print(self.data_set0.get('data'))
        #data = json.load(open(self.paths[0]))
        #print(data['columns'])
        #print(data['data'])

if __name__ == '__main__':
    cs = Column_selecter(['zwt9-6u9n.json'])

spark.clearActiveSession()
spark.clearDefaultSession()

