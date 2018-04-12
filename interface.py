from csv import reader
from pyspark import SparkContext
import sys

import os

sc =SparkContext()
sqlContext = new org.apache.spark.sql.SQLContext(sc)
base_bath='/user/bigdata/nyc_open_data/'

class Column_selecter:
    def __init__(datasets_path):
        self.paths = [os.path.join(base_path, path) for path in datasets_path]
        self.data_set0 = sqlContext.read.json(self.paths[0])
        print(self.data_set0.get('columns'))
        print(self.data_set0.get('data'))

if __name__ == '__main__':
    cs = Column_selecter(['zwt9-6u9n.json'])

