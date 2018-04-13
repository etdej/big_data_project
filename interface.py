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
        self.DataFrames = [self.get_dataframe(path) for path in self.paths]
   
    def get_dataframe(self, path):
        df = spark.read.json(path, multiLine=True)
        df.registerTempTable("df")
        
        dfCol = df.select(explode(df.meta.view.columns))
        dfCol = dfCol.select('col.fieldName')
        
        columns = [i.fieldName for i in dfCol.collect()]

        dfData = df.select(explode(df.data))
        dfData = dfData.select(*[dfData.col[i] for i in range(len(columns))]).toDF(*columns)
        print(dfData.show())
        return dfData

    def get_columns(self, withword, without):
        #return the datasets idx and the columns that contain with but do not contain without
        return
if __name__ == '__main__':
    cs = Column_selecter(['zwt9-6u9n.json'])
    cs.DataFrames.write.save('interface.out')
    #print(cs.get_columns(withword='BRONX', without='23'))


#spark.clearActiveSession()
#spark.clearDefaultSession()
