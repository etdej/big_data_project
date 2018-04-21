import os
import operator
#os.system('./init_script.sh')
import time

from csv import reader
from pyspark import SparkContext
import sys
import json

from pyspark.sql import SQLContext, SparkSession
from pyspark.sql.functions import split, explode
from pyspark.sql.functions import *

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
        result = []
        for df in self.DataFrames:
            columns = df.columns
            for column in columns:
                if df.select(column).where(col(column) == withword).count() > 0 and df.select(column).where(col(column) == without).count() == 0 :
                    result.append(column)

        return  result

    def get_intersection(self, dataset1, column1, dataset2, column2):
        elements1 = self.DataFrames[dataset1].select(column1).distinct()
        nb_el1 = elements1.count()
        elements2 = self.DataFrames[dataset2].select(column2).distinct()
        nb_el2 = elements2.count()
        inter = elements1.intersect(elements2)
        jaccard = inter.count()/(nb_el1 + nb_el2 - inter.count())       

        return jaccard, inter


    def get_intersection(self, dataset_column_list):
       # The dataset_column_list argument is a lsit of couple (dataset, column). dataset is the index of the dataset to use, column is the id of the column
        for i, (dataset, column) in enumerate(dataset_column_list):
            if( i == 0 ):
                inter = self.DataFrames[dataset].select(column).distinct()
            else :
                elements = self.DataFrames[dataset].select(column).distinct()
                inter = inter.intersect(elements)
	
            print(inter.show(100))
    def propose_similar_columns(self, dataset1, dataset2):
        cols1 = self.DataFrames[dataset1].columns
        cols2 = self.DataFrames[dataset2].columns	
        d = {}
        for col1 in cols1:
            for col2 in cols2:
                jac, inter = self.get_intersection(dataset1, col1, dataset2, col2)
                d[(col1, col2)] = jac
        sorted_d = sorted(d.items(), key=operator.itemgetter(1), reverse=True)
        # Print the first 20 elements
        for e in sorted_d[:20]:
            print(e)

if __name__ == '__main__':
    cs = Column_selecter(['zwt9-6u9n.json', 'zwt9-6u9n.json'])
    #print(cs.get_columns(withword=1, without='23'))
    #cs.propose_similar_columns(0, 1)
    cs.get_intersection([(0, ':created_at'), (0, ':created_at')])
#spark.clearActiveSession()
#spark.clearDefaultSession()
