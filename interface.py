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
        #self.paths = [os.path.join(base_path, path) for path in datasets_path]
        self.DataFrames = [self.get_dataframe(os.path.join(base_path, path), path) for path in datasets_path]
   
    def get_dataframe(self, path, datasets_path):
        df = spark.read.json(path, multiLine=True)
        df.registerTempTable("df")
        
        dfCol = df.select(explode(df.meta.view.columns))
        dfCol = dfCol.select('col.fieldName')
        
        columns = [i.fieldName for i in dfCol.collect()]

        dfData = df.select(explode(df.data))
        dfData = dfData.select(*[dfData.col[i] for i in range(len(columns))]).toDF(*columns)
        print(datasets_path)
        #print(dfData.show(1))
        print(dfData.columns)
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

    def get_intersection_(self, dataset1, column1, dataset2, column2):
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
                print(elements.show(10))
                inter = inter.intersect(elements)
	
            print(inter.show(10))


    def propose_similar_columns(self, dataset1, dataset2):
        cols1 = self.DataFrames[dataset1].columns
        cols2 = self.DataFrames[dataset2].columns	
        d = {}
        for col1 in cols1:
            for col2 in cols2:
                jac, inter = self.get_intersection_(dataset1, col1, dataset2, col2)
                d[(col1, col2)] = jac
        sorted_d = sorted(d.items(), key=operator.itemgetter(1), reverse=True)
        # Print the first 20 elements
        for e in sorted_d[:20]:
            print(e)

if __name__ == '__main__':
    ######## experiment 1 #######
    # cs = Column_selecter([ '2vha-97jm.json', '3pzk-fyqp.json', '2x8v-d8nh.json', '3qfc-4tta.json', '4wf2-7kdu.json'])
    # cs.get_intersection([(3, 'council_district'),(4, 'council_district')])
    # cs.get_intersection([(0, 'district'), (1, 'city_council_district'), (2, 'administrative_district'), (3, 'council_district'),(4, 'council_district')])

    ######## experiment 2 #######
    # cs = Column_selecter(['56e3-rp8d.json', '56u5-n9sa.json', '4wf2-7kdu.json'])
    # cs.get_intersection([(0, 'zip'),(1, 'zip_code'), (2, 'zip_code')])


    ######## experiment 3 #######
    # cs = Column_selecter(['3qfc-4tta.json', '4wf2-7kdu.json'])
    # cs.get_intersection([(0, 'borough'),(1, 'borough')])

    ######## experiment 4 #######
    # cs = Column_selecter(['pknx-dgka.json', 'pqbh-p6xe.json', '25aa-q86c.json', '4zdr-zwdi.json'])
    # cs.get_intersection([(0, 'school_name'),(1, 'school_name'), (2, 'school_name'),  (3, 'school') ])

    
    ######## experiment 5 #######
    # cs = Column_selecter(['56e3-rp8d.json', '56u5-n9sa.json'])
    # cs.propose_similar_columns(0, 1)


    ########
    # 56e3-rp8d.json
    # [':sid', ':id', ':position', ':created_at', ':created_meta', ':updated_at', ':updated_meta', ':meta', 'license_number', 'name', 'address', 'city', 'state', 'zip', 'phone', 'type', 'status', 'date', 'time']
    # 56u5-n9sa.json
    # [':sid', ':id', ':position', ':created_at', ':created_meta', ':updated_at', ':updated_meta', ':meta', 'borough_number', 'building_name', 'building_address', 'borough', 'state', 'zip_code', 'block', 'lot', 'fuel_oil_usage_mmbtu', 'latitude', 'longitude', 'community_board', 'council_district', 'census_tract', 'bin', 'bbl', 'nta']
    # ((':meta', ':meta'), 1.0)                                                       
    # ((':meta', 'community_board'), 0.1)
    # ((':meta', 'council_district'), 0.06666666666666667)
    # (('zip', 'zip_code'), 0.05263157894736842)
    # ((':meta', 'nta'), 0.047619047619047616)
    # ((':meta', 'census_tract'), 0.03333333333333333)
    # ((':meta', 'bin'), 0.018867924528301886)
    # ((':meta', 'bbl'), 0.018867924528301886)
    # ((':meta', 'longitude'), 0.01818181818181818)
    # ((':meta', 'latitude'), 0.01818181818181818)
    # ((':id', ':created_meta'), 0.0)
    # ((':id', 'community_board'), 0.0)
    # (('state', 'census_tract'), 0.0)
    # (('date', ':created_meta'), 0.0)
    # (('city', ':created_meta'), 0.0)
    # (('name', 'lot'), 0.0)
    # ((':created_meta', ':position'), 0.0)
    # (('license_number', ':meta'), 0.0)
    # ((':sid', 'council_district'), 0.0)
    # (('name', ':created_meta'), 0.0)

    ######## experiment 6 #######
    cs = Column_selecter(['pknx-dgka.json', 'pqbh-p6xe.json'])
    cs.propose_similar_columns(0, 1)





    ### reader ###
    #cs = Column_selecter(['57mv-nv28.json'])

#spark.clearActiveSession()
#spark.clearDefaultSession()

# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:46 /user/bigdata/nyc_open_data/4bg6-ub7f.json
# -rw-rwx---+  3 rpd302 bigdata    43561511 2018-04-06 10:46 /user/bigdata/nyc_open_data/4d7f-74pe.json
# -rw-rwx---+  3 rpd302 bigdata    41605521 2018-04-06 10:46 /user/bigdata/nyc_open_data/4e2n-s75z.json
# -rw-rwx---+  3 rpd302 bigdata       38705 2018-04-06 10:46 /user/bigdata/nyc_open_data/4e8h-wu86.json
# -rw-rwx---+  3 rpd302 bigdata       18260 2018-04-06 10:46 /user/bigdata/nyc_open_data/4epu-t832.json
# -rw-rwx---+  3 rpd302 bigdata     8204396 2018-04-06 10:46 /user/bigdata/nyc_open_data/4fnu-iufz.json
# -rw-rwx---+  3 rpd302 bigdata       17994 2018-04-06 10:46 /user/bigdata/nyc_open_data/4fsz-s7id.json
# -rw-rwx---+  3 rpd302 bigdata    34946671 2018-04-06 10:46 /user/bigdata/nyc_open_data/4fvw-nn9c.json
# -rw-rwx---+  3 rpd302 bigdata       89557 2018-04-06 10:46 /user/bigdata/nyc_open_data/4g4r-7dfb.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:46 /user/bigdata/nyc_open_data/4ks2-3rz5.json
# -rw-rwx---+  3 rpd302 bigdata       73744 2018-04-06 10:46 /user/bigdata/nyc_open_data/4kse-vfnd.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:46 /user/bigdata/nyc_open_data/4kym-4xw5.json
# -rw-rwx---+  3 rpd302 bigdata      470703 2018-04-06 10:46 /user/bigdata/nyc_open_data/4n2j-ut8i.json
# -rw-rwx---+  3 rpd302 bigdata     1796144 2018-04-06 10:47 /user/bigdata/nyc_open_data/4nft-bihw.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:47 /user/bigdata/nyc_open_data/4nxh-niuc.json

# -rw-rwx---+  3 rpd302 bigdata       16474 2018-04-06 10:46 /user/bigdata/nyc_open_data/3bpc-wa5v.json
# -rw-rwx---+  3 rpd302 bigdata     2727486 2018-04-06 10:46 /user/bigdata/nyc_open_data/3btx-p4av.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:46 /user/bigdata/nyc_open_data/3cdm-p29e.json
# -rw-rwx---+  3 rpd302 bigdata       50767 2018-04-06 10:46 /user/bigdata/nyc_open_data/3cn8-i54i.json
# -rw-rwx---+  3 rpd302 bigdata       17311 2018-04-06 10:46 /user/bigdata/nyc_open_data/3f5y-5web.json
# -rw-rwx---+  3 rpd302 bigdata   626534923 2018-04-06 10:42 /user/bigdata/nyc_open_data/22rf-yxcy.json
# -rw-rwx---+  3 rpd302 bigdata       22905 2018-04-06 10:42 /user/bigdata/nyc_open_data/22zm-qrtq.json
# -rw-rwx---+  3 rpd302 bigdata       17671 2018-04-06 10:42 /user/bigdata/nyc_open_data/23rb-xz43.json
# -rw-rwx---+  3 rpd302 bigdata       40577 2018-04-06 10:42 /user/bigdata/nyc_open_data/24nr-gahi.json
# -rw-rwx---+  3 rpd302 bigdata     5833620 2018-04-06 10:42 /user/bigdata/nyc_open_data/25aa-q86c.json
# -rw-rwx---+  3 rpd302 bigdata      456427 2018-04-06 10:42 /user/bigdata/nyc_open_data/25cx-4jug.json
# -rw-rwx---+  3 rpd302 bigdata     3685648 2018-04-06 10:42 /user/bigdata/nyc_open_data/25th-nujf.json
# -rw-rwx---+  3 rpd302 bigdata       84183 2018-04-06 10:42 /user/bigdata/nyc_open_data/26kp-bgdh.json
# -rw-rwx---+  3 rpd302 bigdata        8746 2018-04-06 10:42 /user/bigdata/nyc_open_data/26ze-s5bx.json
# -rw-rwx---+  3 rpd302 bigdata       37677 2018-04-06 10:42 /user/bigdata/nyc_open_data/276h-y36a.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:42 /user/bigdata/nyc_open_data/27b5-th78.json
# -rw-rwx---+  3 rpd302 bigdata      286825 2018-04-06 10:42 /user/bigdata/nyc_open_data/27h8-t3wt.json
# -rw-rwx---+  3 rpd302 bigdata      114072 2018-04-06 10:42 /user/bigdata/nyc_open_data/28rh-vpvr.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:42 /user/bigdata/nyc_open_data/294z-97kb.json
# -rw-rwx---+  3 rpd302 bigdata      822387 2018-04-06 10:42 /user/bigdata/nyc_open_data/29bv-qqsy.json
# -rw-rwx---+  3 rpd302 bigdata   378071072 2018-04-06 10:42 /user/bigdata/nyc_open_data/29bw-z7pj.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:42 /user/bigdata/nyc_open_data/29i8-bmct.json
# -rw-rwx---+  3 rpd302 bigdata     1084382 2018-04-06 10:42 /user/bigdata/nyc_open_data/29km-avyc.json
# -rw-rwx---+  3 rpd302 bigdata     4947134 2018-04-06 10:42 /user/bigdata/nyc_open_data/29ry-u5bf.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:42 /user/bigdata/nyc_open_data/29wz-ciej.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:42 /user/bigdata/nyc_open_data/2a5m-z82r.json
# -rw-rwx---+  3 rpd302 bigdata       47699 2018-04-06 10:42 /user/bigdata/nyc_open_data/2bh6-qmgg.json
# -rw-rwx---+  3 rpd302 bigdata  5010177915 2018-04-06 10:43 /user/bigdata/nyc_open_data/2bnn-yakx.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:43 /user/bigdata/nyc_open_data/2cav-chmn.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:43 /user/bigdata/nyc_open_data/2cd9-59fr.json
# -rw-rwx---+  3 rpd302 bigdata     2915619 2018-04-06 10:43 /user/bigdata/nyc_open_data/2cmn-uidm.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:43 /user/bigdata/nyc_open_data/2cxm-sdq3.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:43 /user/bigdata/nyc_open_data/2de2-6x2h.json
# -rw-rwx---+  3 rpd302 bigdata       15630 2018-04-06 10:43 /user/bigdata/nyc_open_data/2ei9-vg68.json
# -rw-rwx---+  3 rpd302 bigdata    16242476 2018-04-06 10:43 /user/bigdata/nyc_open_data/2emc-na4n.json
# -rw-rwx---+  3 rpd302 bigdata       10757 2018-04-06 10:43 /user/bigdata/nyc_open_data/2enn-s52j.json
# -rw-rwx---+  3 rpd302 bigdata       27939 2018-04-06 10:43 /user/bigdata/nyc_open_data/2eq2-trdu.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:43 /user/bigdata/nyc_open_data/2fpa-bnsx.json
# -rw-rwx---+  3 rpd302 bigdata   233539750 2018-04-06 10:43 /user/bigdata/nyc_open_data/2fra-mtpn.json
# -rw-rwx---+  3 rpd302 bigdata      282267 2018-04-06 10:43 /user/bigdata/nyc_open_data/2fws-68t6.json
# -rw-rwx---+  3 rpd302 bigdata       40770 2018-04-06 10:43 /user/bigdata/nyc_open_data/2gjq-v9z9.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:43 /user/bigdata/nyc_open_data/2hr8-czpv.json
# -rw-rwx---+  3 rpd302 bigdata       36137 2018-04-06 10:43 /user/bigdata/nyc_open_data/2iia-33q9.json
# -rw-rwx---+  3 rpd302 bigdata       13899 2018-04-06 10:43 /user/bigdata/nyc_open_data/2ij3-wj64.json
# -rw-rwx---+  3 rpd302 bigdata    28823525 2018-04-06 10:43 /user/bigdata/nyc_open_data/2j8u-wtju.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:43 /user/bigdata/nyc_open_data/2jj7-gj6x.json
# -rw-rwx---+  3 rpd302 bigdata      916653 2018-04-06 10:43 /user/bigdata/nyc_open_data/2jne-kr3f.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:43 /user/bigdata/nyc_open_data/2jnq-tef6.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:43 /user/bigdata/nyc_open_data/2mhq-um7h.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:43 /user/bigdata/nyc_open_data/2mvc-qg9q.json
# -rw-rwx---+  3 rpd302 bigdata       20146 2018-04-06 10:43 /user/bigdata/nyc_open_data/2n4x-d97d.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:43 /user/bigdata/nyc_open_data/2n64-63dq.json
# -rw-rwx---+  3 rpd302 bigdata  5219091990 2018-04-06 10:44 /user/bigdata/nyc_open_data/2np7-5jsg.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:44 /user/bigdata/nyc_open_data/2p3a-y7d4.json
# -rw-rwx---+  3 rpd302 bigdata       37522 2018-04-06 10:44 /user/bigdata/nyc_open_data/2p64-jbjs.json
# -rw-rwx---+  3 rpd302 bigdata     4007593 2018-04-06 10:44 /user/bigdata/nyc_open_data/2pmj-y4p4.json
# -rw-rwx---+  3 rpd302 bigdata       44317 2018-04-06 10:44 /user/bigdata/nyc_open_data/2pmt-skyq.json
# -rw-rwx---+  3 rpd302 bigdata      137094 2018-04-06 10:44 /user/bigdata/nyc_open_data/2q48-ip9a.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:44 /user/bigdata/nyc_open_data/2qj2-cctx.json
# -rw-rwx---+  3 rpd302 bigdata       33964 2018-04-06 10:44 /user/bigdata/nyc_open_data/2r9r-m6j4.json
# -rw-rwx---+  3 rpd302 bigdata       24029 2018-04-06 10:44 /user/bigdata/nyc_open_data/2rd2-9uwy.json
# -rw-rwx---+  3 rpd302 bigdata    10853943 2018-04-06 10:44 /user/bigdata/nyc_open_data/2sps-j9st.json
# -rw-rwx---+  3 rpd302 bigdata     2147078 2018-04-06 10:44 /user/bigdata/nyc_open_data/2t2c-qih9.json
# -rw-rwx---+  3 rpd302 bigdata       95199 2018-04-06 10:44 /user/bigdata/nyc_open_data/2t32-hbca.json
# -rw-rwx---+  3 rpd302 bigdata       40054 2018-04-06 10:44 /user/bigdata/nyc_open_data/2uk5-v8da.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:44 /user/bigdata/nyc_open_data/2v4z-66xt.json
# -rw-rwx---+  3 rpd302 bigdata    19602475 2018-04-06 10:44 /user/bigdata/nyc_open_data/2v9c-2k7f.json
# -rw-rwx---+  3 rpd302 bigdata      808144 2018-04-06 10:44 /user/bigdata/nyc_open_data/2vha-97jm.json
# -rw-rwx---+  3 rpd302 bigdata      588095 2018-04-06 10:44 /user/bigdata/nyc_open_data/2x8v-d8nh.json
# -rw-rwx---+  3 rpd302 bigdata     2510620 2018-04-06 10:44 /user/bigdata/nyc_open_data/2xh6-psuq.json
# -rw-rwx---+  3 rpd302 bigdata     4229738 2018-04-06 10:44 /user/bigdata/nyc_open_data/2xir-kwzz.json
# -rw-rwx---+  3 rpd302 bigdata      159894 2018-04-06 10:44 /user/bigdata/nyc_open_data/2zbg-i8fx.json
# -rw-rwx---+  3 rpd302 bigdata      217138 2018-04-06 10:44 /user/bigdata/nyc_open_data/32y8-s55c.json
# -rw-rwx---+  3 rpd302 bigdata       14722 2018-04-06 10:44 /user/bigdata/nyc_open_data/32yu-maz2.json
# -rw-rwx---+  3 rpd302 bigdata      111619 2018-04-06 10:44 /user/bigdata/nyc_open_data/33c5-b922.json
# -rw-rwx---+  3 rpd302 bigdata       35884 2018-04-06 10:44 /user/bigdata/nyc_open_data/33db-aeds.json
# -rw-rwx---+  3 rpd302 bigdata 19330143176 2018-04-06 10:46 /user/bigdata/nyc_open_data/34hf-h2fw.json
# -rw-rwx---+  3 rpd302 bigdata       81731 2018-04-06 10:46 /user/bigdata/nyc_open_data/34zf-iv73.json
# -rw-rwx---+  3 rpd302 bigdata       22360 2018-04-06 10:46 /user/bigdata/nyc_open_data/35f6-8qd2.json
# -rw-rwx---+  3 rpd302 bigdata       17641 2018-04-06 10:46 /user/bigdata/nyc_open_data/35fd-ehz6.json
# -rw-rwx---+  3 rpd302 bigdata       70255 2018-04-06 10:46 /user/bigdata/nyc_open_data/35sw-rdxj.json
# -rw-rwx---+  3 rpd302 bigdata       11036 2018-04-06 10:46 /user/bigdata/nyc_open_data/366m-74zg.json
# -rw-rwx---+  3 rpd302 bigdata       41586 2018-04-06 10:46 /user/bigdata/nyc_open_data/36hn-wea6.json
# -rw-rwx---+  3 rpd302 bigdata      695138 2018-04-06 10:46 /user/bigdata/nyc_open_data/37cg-gxjd.json
# -rw-rwx---+  3 rpd302 bigdata       16161 2018-04-06 10:46 /user/bigdata/nyc_open_data/37fm-7uaa.json
# -rw-rwx---+  3 rpd302 bigdata       65226 2018-04-06 10:46 /user/bigdata/nyc_open_data/37it-gmcp.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:46 /user/bigdata/nyc_open_data/388s-pnvc.json
# -rw-rwx---+  3 rpd302 bigdata       41293 2018-04-06 10:46 /user/bigdata/nyc_open_data/38ib-pjw5.json
# -rw-rwx---+  3 rpd302 bigdata       16571 2018-04-06 10:46 /user/bigdata/nyc_open_data/3955-c36a.json
# -rw-rwx---+  3 rpd302 bigdata     1442777 2018-04-06 10:46 /user/bigdata/nyc_open_data/39g5-gbp3.json
# -rw-rwx---+  3 rpd302 bigdata        8597 2018-04-06 10:46 /user/bigdata/nyc_open_data/39pe-uzy3.json
# -rw-rwx---+  3 rpd302 bigdata      350681 2018-04-06 10:46 /user/bigdata/nyc_open_data/39qw-754y.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:46 /user/bigdata/nyc_open_data/39yy-hdfd.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:46 /user/bigdata/nyc_open_data/3aim-ipk8.json
# -rw-rwx---+  3 rpd302 bigdata       18097 2018-04-06 10:46 /user/bigdata/nyc_open_data/3av7-txd8.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:46 /user/bigdata/nyc_open_data/3bkj-34v2.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:46 /user/bigdata/nyc_open_data/3g65-5ni7.json
# -rw-rwx---+  3 rpd302 bigdata       35335 2018-04-06 10:46 /user/bigdata/nyc_open_data/3gkd-ddzn.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:46 /user/bigdata/nyc_open_data/3gx8-vrcy.json
# -rw-rwx---+  3 rpd302 bigdata   753949680 2018-04-06 10:46 /user/bigdata/nyc_open_data/3h2n-5cm9.json
# -rw-rwx---+  3 rpd302 bigdata     1004094 2018-04-06 10:46 /user/bigdata/nyc_open_data/3kav-a6u5.json
# -rw-rwx---+  3 rpd302 bigdata       59224 2018-04-06 10:46 /user/bigdata/nyc_open_data/3kcn-nsb5.json
# -rw-rwx---+  3 rpd302 bigdata    51870840 2018-04-06 10:46 /user/bigdata/nyc_open_data/3khw-qi8f.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:46 /user/bigdata/nyc_open_data/3m2q-9maw.json
# -rw-rwx---+  3 rpd302 bigdata      245030 2018-04-06 10:46 /user/bigdata/nyc_open_data/3mim-bd27.json
# -rw-rwx---+  3 rpd302 bigdata      536713 2018-04-06 10:46 /user/bigdata/nyc_open_data/3miu-myq2.json
# -rw-rwx---+  3 rpd302 bigdata       18177 2018-04-06 10:46 /user/bigdata/nyc_open_data/3mji-gpg5.json
# -rw-rwx---+  3 rpd302 bigdata     7697472 2018-04-06 10:46 /user/bigdata/nyc_open_data/3mrr-8h5c.json
# -rw-rwx---+  3 rpd302 bigdata       47551 2018-04-06 10:46 /user/bigdata/nyc_open_data/3nja-bsch.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:46 /user/bigdata/nyc_open_data/3nr6-bnks.json
# -rw-rwx---+  3 rpd302 bigdata       58167 2018-04-06 10:46 /user/bigdata/nyc_open_data/3nw7-5vkw.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:46 /user/bigdata/nyc_open_data/3nxf-gbay.json
# -rw-rwx---+  3 rpd302 bigdata      552057 2018-04-06 10:46 /user/bigdata/nyc_open_data/3pge-73vq.json
# -rw-rwx---+  3 rpd302 bigdata       13358 2018-04-06 10:46 /user/bigdata/nyc_open_data/3pzk-fyqp.json
# -rw-rwx---+  3 rpd302 bigdata      202288 2018-04-06 10:46 /user/bigdata/nyc_open_data/3qfc-4tta.json
# -rw-rwx---+  3 rpd302 bigdata       17194 2018-04-06 10:46 /user/bigdata/nyc_open_data/3qty-g4aq.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:46 /user/bigdata/nyc_open_data/3qz8-muuu.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:46 /user/bigdata/nyc_open_data/3r4q-36zy.json
# -rw-rwx---+  3 rpd302 bigdata  1477922726 2018-04-06 10:46 /user/bigdata/nyc_open_data/3rfa-3xsf.json
# -rw-rwx---+  3 rpd302 bigdata      127722 2018-04-06 10:46 /user/bigdata/nyc_open_data/3spy-rjpw.json
# -rw-rwx---+  3 rpd302 bigdata    25268380 2018-04-06 10:46 /user/bigdata/nyc_open_data/3tfu-x2qk.json
# -rw-rwx---+  3 rpd302 bigdata      111955 2018-04-06 10:46 /user/bigdata/nyc_open_data/3ups-txji.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:46 /user/bigdata/nyc_open_data/3vjv-6tf5.json
# -rw-rwx---+  3 rpd302 bigdata       11629 2018-04-06 10:46 /user/bigdata/nyc_open_data/3vvi-fwjs.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:46 /user/bigdata/nyc_open_data/3w3r-v568.json
# -rw-rwx---+  3 rpd302 bigdata      323822 2018-04-06 10:46 /user/bigdata/nyc_open_data/3wxk-qa8q.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:46 /user/bigdata/nyc_open_data/3zjh-awfv.json
# -rw-rwx---+  3 rpd302 bigdata      124390 2018-04-06 10:46 /user/bigdata/nyc_open_data/42et-jh9v.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:46 /user/bigdata/nyc_open_data/42p9-q6fd.json
# -rw-rwx---+  3 rpd302 bigdata       25820 2018-04-06 10:46 /user/bigdata/nyc_open_data/432v-a7hc.json
# -rw-rwx---+  3 rpd302 bigdata    10491275 2018-04-06 10:46 /user/bigdata/nyc_open_data/436j-ja87.json
# -rw-rwx---+  3 rpd302 bigdata      157972 2018-04-06 10:46 /user/bigdata/nyc_open_data/43ab-v68i.json
# -rw-rwx---+  3 rpd302 bigdata   210883161 2018-04-06 10:46 /user/bigdata/nyc_open_data/43nn-pn8j.json
# -rw-rwx---+  3 rpd302 bigdata      442366 2018-04-06 10:46 /user/bigdata/nyc_open_data/43qc-8vv8.json
# -rw-rwx---+  3 rpd302 bigdata    95417184 2018-04-06 10:46 /user/bigdata/nyc_open_data/46g3-savk.json
# -rw-rwx---+  3 rpd302 bigdata      146064 2018-04-06 10:46 /user/bigdata/nyc_open_data/46m8-77gv.json
# -rw-rwx---+  3 rpd302 bigdata       20819 2018-04-06 10:46 /user/bigdata/nyc_open_data/46vt-ugs9.json
# -rw-rwx---+  3 rpd302 bigdata     1257272 2018-04-06 10:46 /user/bigdata/nyc_open_data/478a-yykk.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:46 /user/bigdata/nyc_open_data/47te-ez55.json
# -rw-rwx---+  3 rpd302 bigdata       12856 2018-04-06 10:46 /user/bigdata/nyc_open_data/483x-fy9e.json
# -rw-rwx---+  3 rpd302 bigdata      112703 2018-04-06 10:46 /user/bigdata/nyc_open_data/48ka-f6z6.json
# -rw-rwx---+  3 rpd302 bigdata       21172 2018-04-06 10:46 /user/bigdata/nyc_open_data/48pb-zy2g.json
# -rw-rwx---+  3 rpd302 bigdata      725069 2018-04-06 10:46 /user/bigdata/nyc_open_data/49kg-8sce.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:46 /user/bigdata/nyc_open_data/49mj-4gmb.json
# -rw-rwx---+  3 rpd302 bigdata      638638 2018-04-06 10:46 /user/bigdata/nyc_open_data/4axi-di9c.json
# -rw-rwx---+  3 rpd302 bigdata       78199 2018-04-06 10:46 /user/bigdata/nyc_open_data/4bew-e6kg.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:47 /user/bigdata/nyc_open_data/4p5v-sqmv.json
# -rw-rwx---+  3 rpd302 bigdata   245487702 2018-04-06 10:47 /user/bigdata/nyc_open_data/4pt5-3vv4.json
# -rw-rwx---+  3 rpd302 bigdata       17598 2018-04-06 10:47 /user/bigdata/nyc_open_data/4px5-vncp.json
# -rw-rwx---+  3 rpd302 bigdata       25633 2018-04-06 10:47 /user/bigdata/nyc_open_data/4rix-z2af.json
# -rw-rwx---+  3 rpd302 bigdata      116427 2018-04-06 10:47 /user/bigdata/nyc_open_data/4s7y-vm5x.json
# -rw-rwx---+  3 rpd302 bigdata       10776 2018-04-06 10:47 /user/bigdata/nyc_open_data/4se9-mk53.json
# -rw-rwx---+  3 rpd302 bigdata       13604 2018-04-06 10:47 /user/bigdata/nyc_open_data/4se9-u6dw.json
# -rw-rwx---+  3 rpd302 bigdata      546610 2018-04-06 10:47 /user/bigdata/nyc_open_data/4snd-in5m.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:47 /user/bigdata/nyc_open_data/4szu-rxzq.json
# -rw-rwx---+  3 rpd302 bigdata      125553 2018-04-06 10:47 /user/bigdata/nyc_open_data/4tqt-y424.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:47 /user/bigdata/nyc_open_data/4u36-44pe.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:47 /user/bigdata/nyc_open_data/4v4n-gnh2.json
# -rw-rwx---+  3 rpd302 bigdata       34721 2018-04-06 10:47 /user/bigdata/nyc_open_data/4vsa-fhnm.json
# -rw-rwx---+  3 rpd302 bigdata       52710 2018-04-06 10:47 /user/bigdata/nyc_open_data/4wf2-7kdu.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:47 /user/bigdata/nyc_open_data/4xfb-z29j.json
# -rw-rwx---+  3 rpd302 bigdata      250298 2018-04-06 10:47 /user/bigdata/nyc_open_data/4y9q-t4wb.json
# -rw-rwx---+  3 rpd302 bigdata      530830 2018-04-06 10:47 /user/bigdata/nyc_open_data/4ynw-b9aj.json
# -rw-rwx---+  3 rpd302 bigdata       50959 2018-04-06 10:47 /user/bigdata/nyc_open_data/4zdr-zwdi.json
# -rw-rwx---+  3 rpd302 bigdata    18864905 2018-04-06 10:47 /user/bigdata/nyc_open_data/52dp-yji6.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:47 /user/bigdata/nyc_open_data/53au-zf7x.json
# -rw-rwx---+  3 rpd302 bigdata       46048 2018-04-06 10:47 /user/bigdata/nyc_open_data/54k3-2wtq.json
# -rw-rwx---+  3 rpd302 bigdata      612425 2018-04-06 10:47 /user/bigdata/nyc_open_data/56b7-s9t5.json
# -rw-rwx---+  3 rpd302 bigdata       65270 2018-04-06 10:47 /user/bigdata/nyc_open_data/56bx-u7iw.json
# -rw-rwx---+  3 rpd302 bigdata       27960 2018-04-06 10:47 /user/bigdata/nyc_open_data/56e3-rp8d.json
# -rw-rwx---+  3 rpd302 bigdata       52430 2018-04-06 10:47 /user/bigdata/nyc_open_data/56u5-n9sa.json
# -rw-rwx---+  3 rpd302 bigdata       84063 2018-04-06 10:47 /user/bigdata/nyc_open_data/56u9-ryj4.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:47 /user/bigdata/nyc_open_data/57g5-etyj.json
# -rw-rwx---+  3 rpd302 bigdata  2767520946 2018-04-06 10:47 /user/bigdata/nyc_open_data/57mv-nv28.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:47 /user/bigdata/nyc_open_data/58k2-kgtb.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:47 /user/bigdata/nyc_open_data/59gn-q4ai.json
# -rw-rwx---+  3 rpd302 bigdata    57200510 2018-04-06 10:47 /user/bigdata/nyc_open_data/59kj-x8nc.json
# -rw-rwx---+  3 rpd302 bigdata      796203 2018-04-06 10:47 /user/bigdata/nyc_open_data/59t5-r7nb.json
# -rw-rwx---+  3 rpd302 bigdata     1197119 2018-04-06 10:47 /user/bigdata/nyc_open_data/5b3a-rs48.json
# -rw-rwx---+  3 rpd302 bigdata      480098 2018-04-06 10:47 /user/bigdata/nyc_open_data/5brf-q9de.json
# -rw-rwx---+  3 rpd302 bigdata       42389 2018-04-06 10:47 /user/bigdata/nyc_open_data/5c4s-jwtq.json
# -rw-rwx---+  3 rpd302 bigdata      141490 2018-04-06 10:47 /user/bigdata/nyc_open_data/5c5x-3qz9.json
# -rw-rwx---+  3 rpd302 bigdata       70396 2018-04-06 10:47 /user/bigdata/nyc_open_data/5c95-uqu5.json
# -rw-rwx---+  3 rpd302 bigdata       15627 2018-04-06 10:47 /user/bigdata/nyc_open_data/5c9e-33xj.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:47 /user/bigdata/nyc_open_data/5crx-5ivw.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:47 /user/bigdata/nyc_open_data/5dic-xnxs.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:47 /user/bigdata/nyc_open_data/5dmv-5d3w.json
# -rw-rwx---+  3 rpd302 bigdata       81281 2018-04-06 10:47 /user/bigdata/nyc_open_data/5e24-x4wa.json
# -rw-rwx---+  3 rpd302 bigdata       10562 2018-04-06 10:47 /user/bigdata/nyc_open_data/5fkx-9rt5.json
# -rw-rwx---+  3 rpd302 bigdata      546229 2018-04-06 10:47 /user/bigdata/nyc_open_data/5fn2-n363.json
# -rw-rwx---+  3 rpd302 bigdata    28427624 2018-04-06 10:47 /user/bigdata/nyc_open_data/5fn4-dr26.json
# -rw-rwx---+  3 rpd302 bigdata      340311 2018-04-06 10:47 /user/bigdata/nyc_open_data/5fsg-d8c9.json
# -rw-rwx---+  3 rpd302 bigdata     3719191 2018-04-06 10:47 /user/bigdata/nyc_open_data/5g59-fxev.json
# -rw-rwx---+  3 rpd302 bigdata     5681268 2018-04-06 10:47 /user/bigdata/nyc_open_data/5gde-fmj3.json
# -rw-rwx---+  3 rpd302 bigdata      346490 2018-04-06 10:47 /user/bigdata/nyc_open_data/5gxs-yzxw.json
# -rw-rwx---+  3 rpd302 bigdata      112876 2018-04-06 10:47 /user/bigdata/nyc_open_data/5hiy-kwc2.json
# -rw-rwx---+  3 rpd302 bigdata       45575 2018-04-06 10:47 /user/bigdata/nyc_open_data/5i9t-mvdt.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:47 /user/bigdata/nyc_open_data/5j86-5vbn.json
# -rw-rwx---+  3 rpd302 bigdata      909286 2018-04-06 10:47 /user/bigdata/nyc_open_data/5jat-czce.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:47 /user/bigdata/nyc_open_data/5jsj-cq4s.json
# -rw-rwx---+  3 rpd302 bigdata       12044 2018-04-06 10:47 /user/bigdata/nyc_open_data/5jwd-xj5z.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:47 /user/bigdata/nyc_open_data/5k4d-a692.json
# -rw-rwx---+  3 rpd302 bigdata      484602 2018-04-06 10:47 /user/bigdata/nyc_open_data/5mw2-hzqx.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:47 /user/bigdata/nyc_open_data/5p78-k3zm.json
# -rw-rwx---+  3 rpd302 bigdata       62367 2018-04-06 10:47 /user/bigdata/nyc_open_data/5pbr-mxtd.json
# -rw-rwx---+  3 rpd302 bigdata       18680 2018-04-06 10:47 /user/bigdata/nyc_open_data/5ps9-yuef.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:47 /user/bigdata/nyc_open_data/5q5r-bu4w.json
# -rw-rwx---+  3 rpd302 bigdata      261705 2018-04-06 10:47 /user/bigdata/nyc_open_data/5qbe-4vqd.json
# -rw-rwx---+  3 rpd302 bigdata     4356768 2018-04-06 10:47 /user/bigdata/nyc_open_data/5qrc-eb74.json
# -rw-rwx---+  3 rpd302 bigdata      535696 2018-04-06 10:47 /user/bigdata/nyc_open_data/5qza-frfc.json
# -rw-rwx---+  3 rpd302 bigdata      418093 2018-04-06 10:47 /user/bigdata/nyc_open_data/5r5y-pvs3.json
# -rw-rwx---+  3 rpd302 bigdata  1768949914 2018-04-06 10:47 /user/bigdata/nyc_open_data/5rsf-y7wv.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:47 /user/bigdata/nyc_open_data/5rx8-ct65.json
# -rw-rwx---+  3 rpd302 bigdata       13729 2018-04-06 10:47 /user/bigdata/nyc_open_data/5t4n-d72c.json
# -rw-rwx---+  3 rpd302 bigdata    39279073 2018-04-06 10:47 /user/bigdata/nyc_open_data/5tub-eh45.json
# -rw-rwx---+  3 rpd302 bigdata   233538465 2018-04-06 10:47 /user/bigdata/nyc_open_data/5uac-w243.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:47 /user/bigdata/nyc_open_data/5unr-w4sc.json
# -rw-rwx---+  3 rpd302 bigdata    64507064 2018-04-06 10:47 /user/bigdata/nyc_open_data/5uug-f49n.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:47 /user/bigdata/nyc_open_data/5vb5-y6cv.json
# -rw-rwx---+  3 rpd302 bigdata       24447 2018-04-06 10:47 /user/bigdata/nyc_open_data/5yay-3jd5.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:47 /user/bigdata/nyc_open_data/5zjm-4nny.json
# -rw-rwx---+  3 rpd302 bigdata      501735 2018-04-06 10:47 /user/bigdata/nyc_open_data/6246-94tp.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:47 /user/bigdata/nyc_open_data/62dw-nwnq.json
# -rw-rwx---+  3 rpd302 bigdata     1092103 2018-04-06 10:47 /user/bigdata/nyc_open_data/62mr-ukqs.json
# -rw-rwx---+  3 rpd302 bigdata  9382377748 2018-04-06 10:49 /user/bigdata/nyc_open_data/636b-3b5g.json
# -rw-rwx---+  3 rpd302 bigdata      536801 2018-04-06 10:49 /user/bigdata/nyc_open_data/63us-eqtq.json
# -rw-rwx---+  3 rpd302 bigdata    65501649 2018-04-06 10:49 /user/bigdata/nyc_open_data/64gx-bycn.json
# -rw-rwx---+  3 rpd302 bigdata     2525357 2018-04-06 10:49 /user/bigdata/nyc_open_data/64pu-zyr2.json
# -rw-rwx---+  3 rpd302 bigdata       16465 2018-04-06 10:49 /user/bigdata/nyc_open_data/64px-8x4k.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:49 /user/bigdata/nyc_open_data/64vf-hxyb.json
# -rw-rwx---+  3 rpd302 bigdata      103538 2018-04-06 10:49 /user/bigdata/nyc_open_data/656a-faqy.json
# -rw-rwx---+  3 rpd302 bigdata       18077 2018-04-06 10:49 /user/bigdata/nyc_open_data/65js-fhgz.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:49 /user/bigdata/nyc_open_data/65z6-rsii.json
# -rw-rwx---+  3 rpd302 bigdata       18376 2018-04-06 10:49 /user/bigdata/nyc_open_data/664m-n5th.json
# -rw-rwx---+  3 rpd302 bigdata    12399994 2018-04-06 10:49 /user/bigdata/nyc_open_data/66be-66yr.json
# -rw-rwx---+  3 rpd302 bigdata      354434 2018-04-06 10:49 /user/bigdata/nyc_open_data/66qr-66q7.json
# -rw-rwx---+  3 rpd302 bigdata      135658 2018-04-06 10:49 /user/bigdata/nyc_open_data/66yh-nemi.json
# -rw-rwx---+  3 rpd302 bigdata       52212 2018-04-06 10:49 /user/bigdata/nyc_open_data/68rr-d3jr.json
# -rw-rwx---+  3 rpd302 bigdata     1222365 2018-04-06 10:49 /user/bigdata/nyc_open_data/69bm-3bc2.json
# -rw-rwx---+  3 rpd302 bigdata       48080 2018-04-06 10:49 /user/bigdata/nyc_open_data/69wu-b929.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:49 /user/bigdata/nyc_open_data/6an6-9htp.json
# -rw-rwx---+  3 rpd302 bigdata     5581645 2018-04-06 10:49 /user/bigdata/nyc_open_data/6anw-twe4.json
# -rw-rwx---+  3 rpd302 bigdata       25716 2018-04-06 10:49 /user/bigdata/nyc_open_data/6ayi-u3p7.json
# -rw-rwx---+  3 rpd302 bigdata  1044681378 2018-04-06 10:49 /user/bigdata/nyc_open_data/6bgk-3dad.json
# -rw-rwx---+  3 rpd302 bigdata      152165 2018-04-06 10:49 /user/bigdata/nyc_open_data/6bic-qvek.json
# -rw-rwx---+  3 rpd302 bigdata      123591 2018-04-06 10:49 /user/bigdata/nyc_open_data/6bzx-emuu.json
# -rw-rwx---+  3 rpd302 bigdata       24544 2018-04-06 11:05 /user/bigdata/nyc_open_data/9ddq-vbjj.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:05 /user/bigdata/nyc_open_data/9dtd-h5vj.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:05 /user/bigdata/nyc_open_data/9dux-uz3w.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:05 /user/bigdata/nyc_open_data/9e4i-rd56.json
# -rw-rwx---+  3 rpd302 bigdata       17282 2018-04-06 11:05 /user/bigdata/nyc_open_data/9ev8-8rz6.json
# -rw-rwx---+  3 rpd302 bigdata      474059 2018-04-06 11:05 /user/bigdata/nyc_open_data/9f25-223x.json
# -rw-rwx---+  3 rpd302 bigdata       28733 2018-04-06 11:05 /user/bigdata/nyc_open_data/9f5k-vxxv.json
# -rw-rwx---+  3 rpd302 bigdata       12824 2018-04-06 11:05 /user/bigdata/nyc_open_data/9gzt-8w5q.json
# -rw-rwx---+  3 rpd302 bigdata      393063 2018-04-06 11:05 /user/bigdata/nyc_open_data/9h95-gife.json
# -rw-rwx---+  3 rpd302 bigdata       23341 2018-04-06 11:05 /user/bigdata/nyc_open_data/9ht6-44eh.json
# -rw-rwx---+  3 rpd302 bigdata      168650 2018-04-06 11:05 /user/bigdata/nyc_open_data/9hyh-zkx9.json
# -rw-rwx---+  3 rpd302 bigdata    18209106 2018-04-06 11:05 /user/bigdata/nyc_open_data/9hzi-kbqb.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:05 /user/bigdata/nyc_open_data/9ixa-eggw.json
# -rw-rwx---+  3 rpd302 bigdata       32259 2018-04-06 11:05 /user/bigdata/nyc_open_data/9jbx-hna8.json
# -rw-rwx---+  3 rpd302 bigdata       21251 2018-04-06 11:05 /user/bigdata/nyc_open_data/9jf7-zn7b.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:05 /user/bigdata/nyc_open_data/9jqw-r2a4.json
# -rw-rwx---+  3 rpd302 bigdata     9526327 2018-04-06 11:05 /user/bigdata/nyc_open_data/9k82-ys7w.json
# -rw-rwx---+  3 rpd302 bigdata      163873 2018-04-06 11:05 /user/bigdata/nyc_open_data/9m35-jch2.json
# -rw-rwx---+  3 rpd302 bigdata        7782 2018-04-06 11:05 /user/bigdata/nyc_open_data/9mhd-na2n.json
# -rw-rwx---+  3 rpd302 bigdata       50579 2018-04-06 11:05 /user/bigdata/nyc_open_data/9mjx-v8ip.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:05 /user/bigdata/nyc_open_data/9ned-hmak.json
# -rw-rwx---+  3 rpd302 bigdata  1147041809 2018-04-06 11:06 /user/bigdata/nyc_open_data/9p4w-7npp.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:06 /user/bigdata/nyc_open_data/9p99-55bh.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:06 /user/bigdata/nyc_open_data/9p9k-tusd.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:06 /user/bigdata/nyc_open_data/9rim-7u4b.json
# -rw-rwx---+  3 rpd302 bigdata    10982612 2018-04-06 11:06 /user/bigdata/nyc_open_data/9rz4-mjek.json
# -rw-rwx---+  3 rpd302 bigdata       73978 2018-04-06 11:06 /user/bigdata/nyc_open_data/9s68-zggy.json
# -rw-rwx---+  3 rpd302 bigdata      105584 2018-04-06 11:06 /user/bigdata/nyc_open_data/9sfa-4geq.json
# -rw-rwx---+  3 rpd302 bigdata       46132 2018-04-06 11:06 /user/bigdata/nyc_open_data/9sys-2i9y.json
# -rw-rwx---+  3 rpd302 bigdata       28425 2018-04-06 11:06 /user/bigdata/nyc_open_data/9tth-ctyd.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:06 /user/bigdata/nyc_open_data/9udg-56qp.json
# -rw-rwx---+  3 rpd302 bigdata      139615 2018-04-06 11:06 /user/bigdata/nyc_open_data/9umc-3b2y.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:06 /user/bigdata/nyc_open_data/9v8v-e23e.json
# -rw-rwx---+  3 rpd302 bigdata    11586234 2018-04-06 11:06 /user/bigdata/nyc_open_data/9vgx-wa3i.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:06 /user/bigdata/nyc_open_data/9wui-eigp.json
# -rw-rwx---+  3 rpd302 bigdata      124323 2018-04-06 11:06 /user/bigdata/nyc_open_data/9z9b-6hvk.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:06 /user/bigdata/nyc_open_data/a2ei-5yi4.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:06 /user/bigdata/nyc_open_data/a2ju-qb9a.json
# -rw-rwx---+  3 rpd302 bigdata       72716 2018-04-06 11:06 /user/bigdata/nyc_open_data/a2nf-cvfm.json
# -rw-rwx---+  3 rpd302 bigdata  1278634308 2018-04-06 11:06 /user/bigdata/nyc_open_data/a2nx-4u46.json
# -rw-rwx---+  3 rpd302 bigdata      219254 2018-04-06 11:06 /user/bigdata/nyc_open_data/a3vc-fsgj.json
# -rw-rwx---+  3 rpd302 bigdata       79286 2018-04-06 11:06 /user/bigdata/nyc_open_data/a5qt-5jpu.json
# -rw-rwx---+  3 rpd302 bigdata       20668 2018-04-06 11:06 /user/bigdata/nyc_open_data/a5ru-ygsr.json
# -rw-rwx---+  3 rpd302 bigdata       57113 2018-04-06 11:06 /user/bigdata/nyc_open_data/a6kg-wufg.json
# -rw-rwx---+  3 rpd302 bigdata      146820 2018-04-06 11:06 /user/bigdata/nyc_open_data/a6nj-cfbz.json
# -rw-rwx---+  3 rpd302 bigdata      548067 2018-04-06 11:06 /user/bigdata/nyc_open_data/a6zp-tcs3.json
# -rw-rwx---+  3 rpd302 bigdata       31446 2018-04-06 11:06 /user/bigdata/nyc_open_data/a8rp-fpnn.json
# -rw-rwx---+  3 rpd302 bigdata    58582148 2018-04-06 11:06 /user/bigdata/nyc_open_data/a8wp-rerh.json
# -rw-rwx---+  3 rpd302 bigdata       44803 2018-04-06 11:06 /user/bigdata/nyc_open_data/a94k-kjys.json
# -rw-rwx---+  3 rpd302 bigdata       10485 2018-04-06 11:06 /user/bigdata/nyc_open_data/a9es-3fcm.json
# -rw-rwx---+  3 rpd302 bigdata   254133663 2018-04-06 11:06 /user/bigdata/nyc_open_data/a9md-ynri.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:06 /user/bigdata/nyc_open_data/a9we-mtpn.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:06 /user/bigdata/nyc_open_data/a9xv-vek9.json
# -rw-rwx---+  3 rpd302 bigdata      833145 2018-04-06 11:06 /user/bigdata/nyc_open_data/aa5e-digs.json
# -rw-rwx---+  3 rpd302 bigdata       52805 2018-04-06 11:06 /user/bigdata/nyc_open_data/aa5u-mys6.json
# -rw-rwx---+  3 rpd302 bigdata       74625 2018-04-06 11:06 /user/bigdata/nyc_open_data/aagv-t6fa.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:06 /user/bigdata/nyc_open_data/aajk-7hbr.json
# -rw-rwx---+  3 rpd302 bigdata       44111 2018-04-06 11:06 /user/bigdata/nyc_open_data/abgn-8q46.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:06 /user/bigdata/nyc_open_data/abgy-h8ag.json
# -rw-rwx---+  3 rpd302 bigdata       99454 2018-04-06 11:06 /user/bigdata/nyc_open_data/abnr-s7g4.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:06 /user/bigdata/nyc_open_data/abrc-8mxy.json
# -rw-rwx---+  3 rpd302 bigdata     1540837 2018-04-06 11:06 /user/bigdata/nyc_open_data/ac4n-c5re.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:06 /user/bigdata/nyc_open_data/ac9y-je94.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:06 /user/bigdata/nyc_open_data/acxp-7ep7.json
# -rw-rwx---+  3 rpd302 bigdata      816112 2018-04-06 11:06 /user/bigdata/nyc_open_data/ad4c-mphb.json
# -rw-rwx---+  3 rpd302 bigdata     1283962 2018-04-06 11:06 /user/bigdata/nyc_open_data/ae5u-upr6.json
# -rw-rwx---+  3 rpd302 bigdata       58089 2018-04-06 11:06 /user/bigdata/nyc_open_data/afsf-hz68.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:06 /user/bigdata/nyc_open_data/agx7-ib66.json
# -rw-rwx---+  3 rpd302 bigdata     1619816 2018-04-06 11:06 /user/bigdata/nyc_open_data/ahjc-fdu3.json
# -rw-rwx---+  3 rpd302 bigdata    51571390 2018-04-06 11:06 /user/bigdata/nyc_open_data/aht6-vxai.json
# -rw-rwx---+  3 rpd302 bigdata  1553872374 2018-04-06 11:06 /user/bigdata/nyc_open_data/aiww-p3af.json
# -rw-rwx---+  3 rpd302 bigdata      223732 2018-04-06 11:06 /user/bigdata/nyc_open_data/ajxm-kzmj.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:06 /user/bigdata/nyc_open_data/ajyu-7sgg.json
# -rw-rwx---+  3 rpd302 bigdata       22571 2018-04-06 11:06 /user/bigdata/nyc_open_data/an6v-iuem.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:06 /user/bigdata/nyc_open_data/aprw-p4ws.json
# -rw-rwx---+  3 rpd302 bigdata       12367 2018-04-06 11:06 /user/bigdata/nyc_open_data/arhf-esqb.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:06 /user/bigdata/nyc_open_data/arq3-7z49.json
# -rw-rwx---+  3 rpd302 bigdata      869183 2018-04-06 11:06 /user/bigdata/nyc_open_data/arzb-yfdv.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:06 /user/bigdata/nyc_open_data/as38-8eb5.json
# -rw-rwx---+  3 rpd302 bigdata                0 2018-04-06 10:49 /user/bigdata/nyc_open_data/6cne-um3h.json
# -rw-rwx---+  3 rpd302 bigdata      433124 2018-04-06 10:49 /user/bigdata/nyc_open_data/6ctv-n46c.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:49 /user/bigdata/nyc_open_data/6dju-qj67.json
# -rw-rwx---+  3 rpd302 bigdata        8230 2018-04-06 10:49 /user/bigdata/nyc_open_data/6dn9-qgma.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:49 /user/bigdata/nyc_open_data/6dx8-h7s4.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:49 /user/bigdata/nyc_open_data/6ej9-7qyi.json
# -rw-rwx---+  3 rpd302 bigdata       38947 2018-04-06 10:49 /user/bigdata/nyc_open_data/6ggx-itps.json
# -rw-rwx---+  3 rpd302 bigdata      535726 2018-04-06 10:49 /user/bigdata/nyc_open_data/6gre-fvg9.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:49 /user/bigdata/nyc_open_data/6gvx-hydd.json
# -rw-rwx---+  3 rpd302 bigdata      131313 2018-04-06 10:49 /user/bigdata/nyc_open_data/6j6t-3ixh.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:49 /user/bigdata/nyc_open_data/6j86-5s7z.json
# -rw-rwx---+  3 rpd302 bigdata     8662884 2018-04-06 10:49 /user/bigdata/nyc_open_data/6jad-5sav.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:49 /user/bigdata/nyc_open_data/6jek-z9ge.json
# -rw-rwx---+  3 rpd302 bigdata     2115487 2018-04-06 10:49 /user/bigdata/nyc_open_data/6kcb-9g8d.json
# -rw-rwx---+  3 rpd302 bigdata      143668 2018-04-06 10:49 /user/bigdata/nyc_open_data/6kks-jijx.json
# -rw-rwx---+  3 rpd302 bigdata       23336 2018-04-06 10:49 /user/bigdata/nyc_open_data/6m3u-8rbh.json
# -rw-rwx---+  3 rpd302 bigdata       17172 2018-04-06 10:49 /user/bigdata/nyc_open_data/6m56-5mfb.json
# -rw-rwx---+  3 rpd302 bigdata   258735011 2018-04-06 10:49 /user/bigdata/nyc_open_data/6nxj-n6t5.json
# -rw-rwx---+  3 rpd302 bigdata 70974631557 2018-04-06 10:56 /user/bigdata/nyc_open_data/6phq-6kwz.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:56 /user/bigdata/nyc_open_data/6pui-xhxz.json
# -rw-rwx---+  3 rpd302 bigdata       13175 2018-04-06 10:56 /user/bigdata/nyc_open_data/6pwv-zmgh.json
# -rw-rwx---+  3 rpd302 bigdata       44970 2018-04-06 10:56 /user/bigdata/nyc_open_data/6qaj-niew.json
# -rw-rwx---+  3 rpd302 bigdata       11419 2018-04-06 10:56 /user/bigdata/nyc_open_data/6qzy-b4x8.json
# -rw-rwx---+  3 rpd302 bigdata       53982 2018-04-06 10:56 /user/bigdata/nyc_open_data/6r4h-c2y6.json
# -rw-rwx---+  3 rpd302 bigdata       18256 2018-04-06 10:56 /user/bigdata/nyc_open_data/6r8r-c474.json
# -rw-rwx---+  3 rpd302 bigdata       84662 2018-04-06 10:56 /user/bigdata/nyc_open_data/6rg9-pfbz.json
# -rw-rwx---+  3 rpd302 bigdata     1385109 2018-04-06 10:56 /user/bigdata/nyc_open_data/6rrm-vxj9.json
# -rw-rwx---+  3 rpd302 bigdata       15659 2018-04-06 10:56 /user/bigdata/nyc_open_data/6ryg-d2jg.json
# -rw-rwx---+  3 rpd302 bigdata       67381 2018-04-06 10:56 /user/bigdata/nyc_open_data/6smc-7mk6.json
# -rw-rwx---+  3 rpd302 bigdata    49710474 2018-04-06 10:56 /user/bigdata/nyc_open_data/6teu-xtgp.json
# -rw-rwx---+  3 rpd302 bigdata       16995 2018-04-06 10:56 /user/bigdata/nyc_open_data/6u6h-px7z.json
# -rw-rwx---+  3 rpd302 bigdata       35275 2018-04-06 10:56 /user/bigdata/nyc_open_data/6v9u-ndjg.json
# -rw-rwx---+  3 rpd302 bigdata     4608406 2018-04-06 10:56 /user/bigdata/nyc_open_data/6wcu-cfa3.json
# -rw-rwx---+  3 rpd302 bigdata       72839 2018-04-06 10:56 /user/bigdata/nyc_open_data/6wee-b7wf.json
# -rw-rwx---+  3 rpd302 bigdata       11505 2018-04-06 10:56 /user/bigdata/nyc_open_data/6wkw-kjx4.json
# -rw-rwx---+  3 rpd302 bigdata        8418 2018-04-06 10:56 /user/bigdata/nyc_open_data/6wve-ubwx.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:56 /user/bigdata/nyc_open_data/6wwu-giff.json
# -rw-rwx---+  3 rpd302 bigdata  1465659332 2018-04-06 10:56 /user/bigdata/nyc_open_data/6y3e-jcrc.json
# -rw-rwx---+  3 rpd302 bigdata       12604 2018-04-06 10:56 /user/bigdata/nyc_open_data/7299-2etw.json
# -rw-rwx---+  3 rpd302 bigdata       47147 2018-04-06 10:56 /user/bigdata/nyc_open_data/72db-huua.json
# -rw-rwx---+  3 rpd302 bigdata     1744829 2018-04-06 10:56 /user/bigdata/nyc_open_data/72mk-a8z7.json
# -rw-rwx---+  3 rpd302 bigdata       21682 2018-04-06 10:56 /user/bigdata/nyc_open_data/72n5-tp5u.json
# -rw-rwx---+  3 rpd302 bigdata      360813 2018-04-06 10:56 /user/bigdata/nyc_open_data/72ss-25qh.json
# -rw-rwx---+  3 rpd302 bigdata       28969 2018-04-06 10:56 /user/bigdata/nyc_open_data/72vt-ykjc.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:56 /user/bigdata/nyc_open_data/72wx-vdjr.json
# -rw-rwx---+  3 rpd302 bigdata       51917 2018-04-06 10:56 /user/bigdata/nyc_open_data/733r-da8r.json
# -rw-rwx---+  3 rpd302 bigdata   111485223 2018-04-06 10:56 /user/bigdata/nyc_open_data/735p-zed8.json
# -rw-rwx---+  3 rpd302 bigdata       43175 2018-04-06 10:56 /user/bigdata/nyc_open_data/73bd-vkmx.json
# -rw-rwx---+  3 rpd302 bigdata     1838988 2018-04-06 10:56 /user/bigdata/nyc_open_data/7479-ugqb.json
# -rw-rwx---+  3 rpd302 bigdata      830101 2018-04-06 10:56 /user/bigdata/nyc_open_data/752y-qk8b.json
# -rw-rwx---+  3 rpd302 bigdata     2517297 2018-04-06 10:56 /user/bigdata/nyc_open_data/75e9-fg2t.json
# -rw-rwx---+  3 rpd302 bigdata       17708 2018-04-06 10:56 /user/bigdata/nyc_open_data/767e-4ijc.json
# -rw-rwx---+  3 rpd302 bigdata      117339 2018-04-06 10:56 /user/bigdata/nyc_open_data/76bs-46w6.json
# -rw-rwx---+  3 rpd302 bigdata  3020836590 2018-04-06 10:57 /user/bigdata/nyc_open_data/76xm-jjuj.json
# -rw-rwx---+  3 rpd302 bigdata       59231 2018-04-06 10:57 /user/bigdata/nyc_open_data/77d2-9ebr.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:57 /user/bigdata/nyc_open_data/78dh-3ptz.json
# -rw-rwx---+  3 rpd302 bigdata       21973 2018-04-06 10:57 /user/bigdata/nyc_open_data/78sp-6jhj.json
# -rw-rwx---+  3 rpd302 bigdata      136660 2018-04-06 10:57 /user/bigdata/nyc_open_data/799n-b76v.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:57 /user/bigdata/nyc_open_data/79me-a7rs.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:57 /user/bigdata/nyc_open_data/79z8-9mcf.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:57 /user/bigdata/nyc_open_data/7acq-q3tq.json
# -rw-rwx---+  3 rpd302 bigdata     2154753 2018-04-06 10:57 /user/bigdata/nyc_open_data/7agf-bcsq.json
# -rw-rwx---+  3 rpd302 bigdata  1043749924 2018-04-06 10:57 /user/bigdata/nyc_open_data/7ahn-ypff.json
# -rw-rwx---+  3 rpd302 bigdata       22444 2018-04-06 10:57 /user/bigdata/nyc_open_data/7atn-adw6.json
# -rw-rwx---+  3 rpd302 bigdata      845512 2018-04-06 10:57 /user/bigdata/nyc_open_data/7atx-5a3s.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:57 /user/bigdata/nyc_open_data/7b32-6xny.json
# -rw-rwx---+  3 rpd302 bigdata      609518 2018-04-06 10:57 /user/bigdata/nyc_open_data/7btz-mnc8.json
# -rw-rwx---+  3 rpd302 bigdata       65489 2018-04-06 10:57 /user/bigdata/nyc_open_data/7ceq-6nwu.json
# -rw-rwx---+  3 rpd302 bigdata     1647436 2018-04-06 10:57 /user/bigdata/nyc_open_data/7crd-d9xh.json
# -rw-rwx---+  3 rpd302 bigdata      435932 2018-04-06 10:57 /user/bigdata/nyc_open_data/7drd-wqcf.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:57 /user/bigdata/nyc_open_data/7equ-j2vi.json
# -rw-rwx---+  3 rpd302 bigdata       57771 2018-04-06 10:57 /user/bigdata/nyc_open_data/7ewi-9cdf.json
# -rw-rwx---+  3 rpd302 bigdata       55291 2018-04-06 10:57 /user/bigdata/nyc_open_data/7fnf-kyf4.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:57 /user/bigdata/nyc_open_data/7fuk-i2af.json
# -rw-rwx---+  3 rpd302 bigdata       45248 2018-04-06 10:57 /user/bigdata/nyc_open_data/7ggc-ypzi.json
# -rw-rwx---+  3 rpd302 bigdata    58428846 2018-04-06 10:57 /user/bigdata/nyc_open_data/7gmq-dbas.json
# -rw-rwx---+  3 rpd302 bigdata    13760080 2018-04-06 10:57 /user/bigdata/nyc_open_data/7gvw-m7zn.json
# -rw-rwx---+  3 rpd302 bigdata      370214 2018-04-06 10:57 /user/bigdata/nyc_open_data/7h99-xsqt.json
# -rw-rwx---+  3 rpd302 bigdata       37265 2018-04-06 10:57 /user/bigdata/nyc_open_data/7hgn-sgmk.json
# -rw-rwx---+  3 rpd302 bigdata       22268 2018-04-06 10:57 /user/bigdata/nyc_open_data/7hi3-kaps.json
# -rw-rwx---+  3 rpd302 bigdata        8597 2018-04-06 10:57 /user/bigdata/nyc_open_data/7iqe-jary.json
# -rw-rwx---+  3 rpd302 bigdata       98155 2018-04-06 10:57 /user/bigdata/nyc_open_data/7iqz-npua.json
# -rw-rwx---+  3 rpd302 bigdata       37226 2018-04-06 10:57 /user/bigdata/nyc_open_data/7isb-wh4c.json
# -rw-rwx---+  3 rpd302 bigdata      102195 2018-04-06 10:57 /user/bigdata/nyc_open_data/7jkp-5w5g.json
# -rw-rwx---+  3 rpd302 bigdata    11754000 2018-04-06 10:57 /user/bigdata/nyc_open_data/7jpv-q9e2.json
# -rw-rwx---+  3 rpd302 bigdata      135098 2018-04-06 10:57 /user/bigdata/nyc_open_data/7k2e-ht2j.json
# -rw-rwx---+  3 rpd302 bigdata    11919502 2018-04-06 10:57 /user/bigdata/nyc_open_data/7k5d-rk33.json
# -rw-rwx---+  3 rpd302 bigdata      236933 2018-04-06 10:57 /user/bigdata/nyc_open_data/7kc8-z939.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:57 /user/bigdata/nyc_open_data/7kuu-zah7.json
# -rw-rwx---+  3 rpd302 bigdata       12175 2018-04-06 10:57 /user/bigdata/nyc_open_data/7m8q-jgtg.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:57 /user/bigdata/nyc_open_data/7mgd-s57w.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 10:57 /user/bigdata/nyc_open_data/7q5y-m6mr.json
# -rw-rwx---+  3 rpd302 bigdata       39621 2018-04-06 10:57 /user/bigdata/nyc_open_data/7r6i-tdj2.json
# -rw-rwx---+  3 rpd302 bigdata       18021 2018-04-06 10:57 /user/bigdata/nyc_open_data/7ree-jtaa.json
# -rw-rwx---+  3 rpd302 bigdata 68878091846 2018-04-06 11:04 /user/bigdata/nyc_open_data/7rnv-m532.json
# -rw-rwx---+  3 rpd302 bigdata       29214 2018-04-06 11:04 /user/bigdata/nyc_open_data/7s3q-rztu.json
# -rw-rwx---+  3 rpd302 bigdata     1377852 2018-04-06 11:04 /user/bigdata/nyc_open_data/7scx-rfrp.json
# -rw-rwx---+  3 rpd302 bigdata       26802 2018-04-06 11:04 /user/bigdata/nyc_open_data/7su9-xgtn.json
# -rw-rwx---+  3 rpd302 bigdata       81678 2018-04-06 11:04 /user/bigdata/nyc_open_data/7t6i-mkth.json
# -rw-rwx---+  3 rpd302 bigdata    11069745 2018-04-06 11:04 /user/bigdata/nyc_open_data/7u63-ib3x.json
# -rw-rwx---+  3 rpd302 bigdata        9029 2018-04-06 11:04 /user/bigdata/nyc_open_data/7ub6-8ecn.json
# -rw-rwx---+  3 rpd302 bigdata       17611 2018-04-06 11:04 /user/bigdata/nyc_open_data/7ujc-hpzg.json
# -rw-rwx---+  3 rpd302 bigdata      392389 2018-04-06 11:04 /user/bigdata/nyc_open_data/7uuj-b95m.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:04 /user/bigdata/nyc_open_data/7vpq-4bh4.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:04 /user/bigdata/nyc_open_data/7vsa-caz7.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:04 /user/bigdata/nyc_open_data/7vu2-3skk.json
# -rw-rwx---+  3 rpd302 bigdata      142759 2018-04-06 11:04 /user/bigdata/nyc_open_data/7vy4-ats6.json
# -rw-rwx---+  3 rpd302 bigdata      504416 2018-04-06 11:04 /user/bigdata/nyc_open_data/7xjx-2mhj.json
# -rw-rwx---+  3 rpd302 bigdata      386514 2018-04-06 11:04 /user/bigdata/nyc_open_data/7xq6-k6zy.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:04 /user/bigdata/nyc_open_data/7xqy-uv7r.json
# -rw-rwx---+  3 rpd302 bigdata      288705 2018-04-06 11:04 /user/bigdata/nyc_open_data/7yay-m4ae.json
# -rw-rwx---+  3 rpd302 bigdata     5833618 2018-04-06 11:04 /user/bigdata/nyc_open_data/7yc5-fec2.json
# -rw-rwx---+  3 rpd302 bigdata      140945 2018-04-06 11:04 /user/bigdata/nyc_open_data/7yds-6i8e.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:04 /user/bigdata/nyc_open_data/7yhi-h8kc.json
# -rw-rwx---+  3 rpd302 bigdata      385303 2018-04-06 11:04 /user/bigdata/nyc_open_data/7yig-nj52.json
# -rw-rwx---+  3 rpd302 bigdata       15815 2018-04-06 11:04 /user/bigdata/nyc_open_data/7z8d-msnt.json
# -rw-rwx---+  3 rpd302 bigdata       18478 2018-04-06 11:04 /user/bigdata/nyc_open_data/7zb8-7bpk.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:04 /user/bigdata/nyc_open_data/7zf5-7vum.json
# -rw-rwx---+  3 rpd302 bigdata       81186 2018-04-06 11:04 /user/bigdata/nyc_open_data/7zhs-43jt.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:04 /user/bigdata/nyc_open_data/824w-7c8u.json
# -rw-rwx---+  3 rpd302 bigdata       59201 2018-04-06 11:04 /user/bigdata/nyc_open_data/825b-niea.json
# -rw-rwx---+  3 rpd302 bigdata      645497 2018-04-06 11:04 /user/bigdata/nyc_open_data/82rt-zc4y.json
# -rw-rwx---+  3 rpd302 bigdata   546639085 2018-04-06 11:04 /user/bigdata/nyc_open_data/82zj-84is.json
# -rw-rwx---+  3 rpd302 bigdata       16750 2018-04-06 11:04 /user/bigdata/nyc_open_data/83kr-sbhe.json
# -rw-rwx---+  3 rpd302 bigdata      104467 2018-04-06 11:04 /user/bigdata/nyc_open_data/83z6-smyr.json
# -rw-rwx---+  3 rpd302 bigdata      589276 2018-04-06 11:04 /user/bigdata/nyc_open_data/8586-3zfm.json
# -rw-rwx---+  3 rpd302 bigdata      345692 2018-04-06 11:04 /user/bigdata/nyc_open_data/85ty-ti6v.json
# -rw-rwx---+  3 rpd302 bigdata    26983596 2018-04-06 11:04 /user/bigdata/nyc_open_data/867j-5pgi.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:04 /user/bigdata/nyc_open_data/8792-ebcp.json
# -rw-rwx---+  3 rpd302 bigdata      259988 2018-04-06 11:04 /user/bigdata/nyc_open_data/87b8-3t9t.json
# -rw-rwx---+  3 rpd302 bigdata    24993285 2018-04-06 11:04 /user/bigdata/nyc_open_data/87fx-28ei.json
# -rw-rwx---+  3 rpd302 bigdata       35992 2018-04-06 11:04 /user/bigdata/nyc_open_data/87hk-978a.json
# -rw-rwx---+  3 rpd302 bigdata      624165 2018-04-06 11:04 /user/bigdata/nyc_open_data/87y3-sqsx.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:04 /user/bigdata/nyc_open_data/88da-cha7.json
# -rw-rwx---+  3 rpd302 bigdata       19800 2018-04-06 11:04 /user/bigdata/nyc_open_data/88ds-ti7k.json
# -rw-rwx---+  3 rpd302 bigdata       33045 2018-04-06 11:04 /user/bigdata/nyc_open_data/89di-hi4s.json
# -rw-rwx---+  3 rpd302 bigdata       12338 2018-04-06 11:04 /user/bigdata/nyc_open_data/89j6-bdde.json
# -rw-rwx---+  3 rpd302 bigdata      599396 2018-04-06 11:04 /user/bigdata/nyc_open_data/8a4n-zmpj.json
# -rw-rwx---+  3 rpd302 bigdata     2013296 2018-04-06 11:04 /user/bigdata/nyc_open_data/8b9a-pywy.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:04 /user/bigdata/nyc_open_data/8d5p-rji6.json
# -rw-rwx---+  3 rpd302 bigdata       75994 2018-04-06 11:04 /user/bigdata/nyc_open_data/8dhd-zvi6.json
# -rw-rwx---+  3 rpd302 bigdata       18254 2018-04-06 11:04 /user/bigdata/nyc_open_data/8dxm-n5ha.json
# -rw-rwx---+  3 rpd302 bigdata    22412560 2018-04-06 11:04 /user/bigdata/nyc_open_data/8fei-z6rz.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:04 /user/bigdata/nyc_open_data/8fhn-c4v3.json
# -rw-rwx---+  3 rpd302 bigdata     5352923 2018-04-06 11:04 /user/bigdata/nyc_open_data/8fj8-3sgg.json
# -rw-rwx---+  3 rpd302 bigdata       17671 2018-04-06 11:04 /user/bigdata/nyc_open_data/8g9r-zz89.json
# -rw-rwx---+  3 rpd302 bigdata     2255006 2018-04-06 11:04 /user/bigdata/nyc_open_data/8gpu-s594.json
# -rw-rwx---+  3 rpd302 bigdata      105481 2018-04-06 11:04 /user/bigdata/nyc_open_data/8gqz-6v9v.json
# -rw-rwx---+  3 rpd302 bigdata      859525 2018-04-06 11:04 /user/bigdata/nyc_open_data/8gr8-ngjc.json
# -rw-rwx---+  3 rpd302 bigdata  4418351935 2018-04-06 11:05 /user/bigdata/nyc_open_data/8h5j-fqxa.json
# -rw-rwx---+  3 rpd302 bigdata       20807 2018-04-06 11:05 /user/bigdata/nyc_open_data/8hkx-uppz.json
# -rw-rwx---+  3 rpd302 bigdata     3311429 2018-04-06 11:05 /user/bigdata/nyc_open_data/8isn-pgv3.json
# -rw-rwx---+  3 rpd302 bigdata      400599 2018-04-06 11:05 /user/bigdata/nyc_open_data/8ius-dhrr.json
# -rw-rwx---+  3 rpd302 bigdata      449364 2018-04-06 11:05 /user/bigdata/nyc_open_data/8jfz-tjny.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:05 /user/bigdata/nyc_open_data/8k4a-z83b.json
# -rw-rwx---+  3 rpd302 bigdata     1551155 2018-04-06 11:05 /user/bigdata/nyc_open_data/8k4x-9mp5.json
# -rw-rwx---+  3 rpd302 bigdata       13114 2018-04-06 11:05 /user/bigdata/nyc_open_data/8kiv-2ukd.json
# -rw-rwx---+  3 rpd302 bigdata  1343704632 2018-04-06 11:05 /user/bigdata/nyc_open_data/8m42-w767.json
# -rw-rwx---+  3 rpd302 bigdata      374034 2018-04-06 11:05 /user/bigdata/nyc_open_data/8nqg-ia7v.json
# -rw-rwx---+  3 rpd302 bigdata      122454 2018-04-06 11:05 /user/bigdata/nyc_open_data/8qgy-ka3v.json
# -rw-rwx---+  3 rpd302 bigdata       13555 2018-04-06 11:05 /user/bigdata/nyc_open_data/8qru-nyj8.json
# -rw-rwx---+  3 rpd302 bigdata       42772 2018-04-06 11:05 /user/bigdata/nyc_open_data/8r6c-ydwk.json
# -rw-rwx---+  3 rpd302 bigdata   808221733 2018-04-06 11:05 /user/bigdata/nyc_open_data/8sdw-8vja.json
# -rw-rwx---+  3 rpd302 bigdata  1093570326 2018-04-06 11:05 /user/bigdata/nyc_open_data/8tdh-66hm.json
# -rw-rwx---+  3 rpd302 bigdata      404233 2018-04-06 11:05 /user/bigdata/nyc_open_data/8te3-bhtv.json
# -rw-rwx---+  3 rpd302 bigdata  1395120097 2018-04-06 11:05 /user/bigdata/nyc_open_data/8tjs-webf.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:05 /user/bigdata/nyc_open_data/8tt5-asjf.json
# -rw-rwx---+  3 rpd302 bigdata      105368 2018-04-06 11:05 /user/bigdata/nyc_open_data/8u85-k342.json
# -rw-rwx---+  3 rpd302 bigdata    11895270 2018-04-06 11:05 /user/bigdata/nyc_open_data/8u86-bviy.json
# -rw-rwx---+  3 rpd302 bigdata    18343075 2018-04-06 11:05 /user/bigdata/nyc_open_data/8vgb-zm6e.json
# -rw-rwx---+  3 rpd302 bigdata     5919786 2018-04-06 11:05 /user/bigdata/nyc_open_data/8vv7-7wx3.json
# -rw-rwx---+  3 rpd302 bigdata      317538 2018-04-06 11:05 /user/bigdata/nyc_open_data/8wau-idzf.json
# -rw-rwx---+  3 rpd302 bigdata    45099923 2018-04-06 11:05 /user/bigdata/nyc_open_data/8wbx-tsch.json
# -rw-rwx---+  3 rpd302 bigdata       16749 2018-04-06 11:05 /user/bigdata/nyc_open_data/8wpj-vk59.json
# -rw-rwx---+  3 rpd302 bigdata    10518735 2018-04-06 11:05 /user/bigdata/nyc_open_data/8yac-vygm.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:05 /user/bigdata/nyc_open_data/8ztn-rmii.json
# -rw-rwx---+  3 rpd302 bigdata     2013868 2018-04-06 11:05 /user/bigdata/nyc_open_data/922w-z7da.json
# -rw-rwx---+  3 rpd302 bigdata      459614 2018-04-06 11:05 /user/bigdata/nyc_open_data/93d2-wh7s.json
# -rw-rwx---+  3 rpd302 bigdata       48010 2018-04-06 11:05 /user/bigdata/nyc_open_data/93hz-wi47.json
# -rw-rwx---+  3 rpd302 bigdata       55533 2018-04-06 11:05 /user/bigdata/nyc_open_data/948r-3ads.json
# -rw-rwx---+  3 rpd302 bigdata       14344 2018-04-06 11:05 /user/bigdata/nyc_open_data/94g4-w6xz.json
# -rw-rwx---+  3 rpd302 bigdata       16079 2018-04-06 11:05 /user/bigdata/nyc_open_data/94ka-ussk.json
# -rw-rwx---+  3 rpd302 bigdata    51828829 2018-04-06 11:05 /user/bigdata/nyc_open_data/94ri-3ium.json
# -rw-rwx---+  3 rpd302 bigdata     1111591 2018-04-06 11:05 /user/bigdata/nyc_open_data/956m-xy24.json
# -rw-rwx---+  3 rpd302 bigdata      105139 2018-04-06 11:05 /user/bigdata/nyc_open_data/97iw-vtbx.json
# -rw-rwx---+  3 rpd302 bigdata       43971 2018-04-06 11:05 /user/bigdata/nyc_open_data/97pn-acdf.json
# -rw-rwx---+  3 rpd302 bigdata      362623 2018-04-06 11:05 /user/bigdata/nyc_open_data/97zg-4p9t.json
# -rw-rwx---+  3 rpd302 bigdata       10903 2018-04-06 11:05 /user/bigdata/nyc_open_data/996g-i4kh.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:05 /user/bigdata/nyc_open_data/99bc-9p23.json
# -rw-rwx---+  3 rpd302 bigdata      169302 2018-04-06 11:05 /user/bigdata/nyc_open_data/99br-frp6.json
# -rw-rwx---+  3 rpd302 bigdata       31964 2018-04-06 11:05 /user/bigdata/nyc_open_data/99ez-fwvc.json
# -rw-rwx---+  3 rpd302 bigdata       35558 2018-04-06 11:05 /user/bigdata/nyc_open_data/99gz-6gpw.json
# -rw-rwx---+  3 rpd302 bigdata      264998 2018-04-06 11:05 /user/bigdata/nyc_open_data/9a87-6m4x.json
# -rw-rwx---+  3 rpd302 bigdata       49488 2018-04-06 11:05 /user/bigdata/nyc_open_data/9ae4-niad.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:05 /user/bigdata/nyc_open_data/9auy-76zt.json
# -rw-rwx---+  3 rpd302 bigdata     1263993 2018-04-06 11:05 /user/bigdata/nyc_open_data/9ay9-xkek.json
# -rw-rwx---+  3 rpd302 bigdata     1312606 2018-04-06 11:05 /user/bigdata/nyc_open_data/9b9u-8989.json
# -rw-rwx---+  3 rpd302 bigdata       31984 2018-04-06 11:05 /user/bigdata/nyc_open_data/9bmk-bbj5.json
# -rw-rwx---+  3 rpd302 bigdata      315960 2018-04-06 11:05 /user/bigdata/nyc_open_data/9btm-sxj3.json
# -rw-rwx---+  3 rpd302 bigdata       96596 2018-04-06 11:05 /user/bigdata/nyc_open_data/9ct9-prf9.json
# -rw-rwx---+  3 rpd302 bigdata      395668 2018-04-06 11:05 /user/bigdata/nyc_open_data/9cvd-uyw6.json
# -rw-rwx---+  3 rpd302 bigdata    11260157 2018-04-06 11:05 /user/bigdata/nyc_open_data/9cw8-7heb.json
# -rw-rwx---+  3 rpd302 bigdata       47223 2018-04-06 11:05 /user/bigdata/nyc_open_data/9d9t-bmk7.json
# -rw-rwx---+  3 rpd302 bigdata      0 2018-04-06 11:06 /user/bigdata/nyc_open_data/asbw-cwm7.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:06 /user/bigdata/nyc_open_data/at6p-rk97.json
# -rw-rwx---+  3 rpd302 bigdata        7031 2018-04-06 11:06 /user/bigdata/nyc_open_data/au2v-djg4.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:06 /user/bigdata/nyc_open_data/aumr-wgtk.json
# -rw-rwx---+  3 rpd302 bigdata       25213 2018-04-06 11:06 /user/bigdata/nyc_open_data/auuc-fqzi.json
# -rw-rwx---+  3 rpd302 bigdata       25715 2018-04-06 11:06 /user/bigdata/nyc_open_data/av3y-hmjv.json
# -rw-rwx---+  3 rpd302 bigdata   179823233 2018-04-06 11:06 /user/bigdata/nyc_open_data/avhb-5jhc.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:06 /user/bigdata/nyc_open_data/aviq-jvfs.json
# -rw-rwx---+  3 rpd302 bigdata      152865 2018-04-06 11:06 /user/bigdata/nyc_open_data/avir-tzek.json
# -rw-rwx---+  3 rpd302 bigdata     5223706 2018-04-06 11:06 /user/bigdata/nyc_open_data/avsi-2fp7.json
# -rw-rwx---+  3 rpd302 bigdata 34245851344 2018-04-06 11:10 /user/bigdata/nyc_open_data/avz8-mqzz.json
# -rw-rwx---+  3 rpd302 bigdata       12109 2018-04-06 11:10 /user/bigdata/nyc_open_data/axmw-6kmf.json
# -rw-rwx---+  3 rpd302 bigdata      168829 2018-04-06 11:10 /user/bigdata/nyc_open_data/ay9k-vznm.json
# -rw-rwx---+  3 rpd302 bigdata       59798 2018-04-06 11:10 /user/bigdata/nyc_open_data/ayeb-p4mv.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:10 /user/bigdata/nyc_open_data/ayer-cga7.json
# -rw-rwx---+  3 rpd302 bigdata       17951 2018-04-06 11:10 /user/bigdata/nyc_open_data/az65-9z36.json
# -rw-rwx---+  3 rpd302 bigdata       16617 2018-04-06 11:10 /user/bigdata/nyc_open_data/azp6-hepu.json
# -rw-rwx---+  3 rpd302 bigdata        9849 2018-04-06 11:10 /user/bigdata/nyc_open_data/azyf-k3d6.json
# -rw-rwx---+  3 rpd302 bigdata       19246 2018-04-06 11:10 /user/bigdata/nyc_open_data/b2gb-nkrq.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:10 /user/bigdata/nyc_open_data/b2m2-7ih3.json
# -rw-rwx---+  3 rpd302 bigdata       43201 2018-04-06 11:10 /user/bigdata/nyc_open_data/b2sp-asbg.json
# -rw-rwx---+  3 rpd302 bigdata       18117 2018-04-06 11:10 /user/bigdata/nyc_open_data/b2y5-dstf.json
# -rw-rwx---+  3 rpd302 bigdata      115264 2018-04-06 11:10 /user/bigdata/nyc_open_data/b37b-brfu.json
# -rw-rwx---+  3 rpd302 bigdata       11860 2018-04-06 11:10 /user/bigdata/nyc_open_data/b3qc-c6fh.json
# -rw-rwx---+  3 rpd302 bigdata       36709 2018-04-06 11:10 /user/bigdata/nyc_open_data/b3wh-m425.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:10 /user/bigdata/nyc_open_data/b55q-34ps.json
# -rw-rwx---+  3 rpd302 bigdata      124669 2018-04-06 11:10 /user/bigdata/nyc_open_data/b59s-jsgk.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:10 /user/bigdata/nyc_open_data/b7t4-zm44.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:10 /user/bigdata/nyc_open_data/b937-zdky.json
# -rw-rwx---+  3 rpd302 bigdata      646181 2018-04-06 11:10 /user/bigdata/nyc_open_data/b9e9-2we4.json
# -rw-rwx---+  3 rpd302 bigdata    43474779 2018-04-06 11:10 /user/bigdata/nyc_open_data/b9km-gdpy.json
# -rw-rwx---+  3 rpd302 bigdata    15015252 2018-04-06 11:10 /user/bigdata/nyc_open_data/b9uf-7skp.json
# -rw-rwx---+  3 rpd302 bigdata 16507891394 2018-04-06 11:12 /user/bigdata/nyc_open_data/ba8s-jw6u.json
# -rw-rwx---+  3 rpd302 bigdata      133912 2018-04-06 11:12 /user/bigdata/nyc_open_data/bawj-6bgn.json
# -rw-rwx---+  3 rpd302 bigdata      396392 2018-04-06 11:12 /user/bigdata/nyc_open_data/bbg6-wf44.json
# -rw-rwx---+  3 rpd302 bigdata    85091854 2018-04-06 11:12 /user/bigdata/nyc_open_data/bbs3-q5us.json
# -rw-rwx---+  3 rpd302 bigdata       16764 2018-04-06 11:12 /user/bigdata/nyc_open_data/bbvw-ivc8.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:12 /user/bigdata/nyc_open_data/bc8t-ecyu.json
# -rw-rwx---+  3 rpd302 bigdata   326286411 2018-04-06 11:12 /user/bigdata/nyc_open_data/bdjm-n7q4.json
# -rw-rwx---+  3 rpd302 bigdata       14550 2018-04-06 11:12 /user/bigdata/nyc_open_data/bexe-qnej.json
# -rw-rwx---+  3 rpd302 bigdata       20399 2018-04-06 11:12 /user/bigdata/nyc_open_data/bfiu-cc7d.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:12 /user/bigdata/nyc_open_data/bhs9-p657.json
# -rw-rwx---+  3 rpd302 bigdata     3151927 2018-04-06 11:12 /user/bigdata/nyc_open_data/bhwu-wuzu.json
# -rw-rwx---+  3 rpd302 bigdata    10567680 2018-04-06 11:12 /user/bigdata/nyc_open_data/bi53-yph3.json
# -rw-rwx---+  3 rpd302 bigdata       10211 2018-04-06 11:12 /user/bigdata/nyc_open_data/bj6m-ydtj.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:12 /user/bigdata/nyc_open_data/bj76-nbjg.json
# -rw-rwx---+  3 rpd302 bigdata      275123 2018-04-06 11:12 /user/bigdata/nyc_open_data/bjmk-35w5.json
# -rw-rwx---+  3 rpd302 bigdata   355628099 2018-04-06 11:12 /user/bigdata/nyc_open_data/bjuu-44hx.json
# -rw-rwx---+  3 rpd302 bigdata   203791175 2018-04-06 11:12 /user/bigdata/nyc_open_data/bkfu-528j.json
# -rw-rwx---+  3 rpd302 bigdata    12685451 2018-04-06 11:12 /user/bigdata/nyc_open_data/bkwf-xfky.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:12 /user/bigdata/nyc_open_data/bmax-4kci.json
# -rw-rwx---+  3 rpd302 bigdata      392411 2018-04-06 11:12 /user/bigdata/nyc_open_data/bmhe-urrg.json
# -rw-rwx---+  3 rpd302 bigdata       19017 2018-04-06 11:12 /user/bigdata/nyc_open_data/bmxf-3rd4.json
# -rw-rwx---+  3 rpd302 bigdata       22844 2018-04-06 11:12 /user/bigdata/nyc_open_data/bn89-icuy.json
# -rw-rwx---+  3 rpd302 bigdata  4042530318 2018-04-06 11:12 /user/bigdata/nyc_open_data/bnx9-e6tj.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:12 /user/bigdata/nyc_open_data/bpt7-i8t8.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:12 /user/bigdata/nyc_open_data/bqbs-iwyn.json
# -rw-rwx---+  3 rpd302 bigdata      574069 2018-04-06 11:12 /user/bigdata/nyc_open_data/bquu-z2ht.json
# -rw-rwx---+  3 rpd302 bigdata    39478844 2018-04-06 11:12 /user/bigdata/nyc_open_data/bs8b-p36w.json
# -rw-rwx---+  3 rpd302 bigdata      675526 2018-04-06 11:12 /user/bigdata/nyc_open_data/bss9-579f.json
# -rw-rwx---+  3 rpd302 bigdata  1645559509 2018-04-06 11:12 /user/bigdata/nyc_open_data/bty7-2jhb.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:12 /user/bigdata/nyc_open_data/bvc7-nbpp.json
# -rw-rwx---+  3 rpd302 bigdata   990099798 2018-04-06 11:12 /user/bigdata/nyc_open_data/bvi5-pdi9.json
# -rw-rwx---+  3 rpd302 bigdata       47688 2018-04-06 11:12 /user/bigdata/nyc_open_data/bvna-6j7v.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:12 /user/bigdata/nyc_open_data/bw8v-wzdr.json
# -rw-rwx---+  3 rpd302 bigdata     2998660 2018-04-06 11:13 /user/bigdata/nyc_open_data/bwhw-9jek.json
# -rw-rwx---+  3 rpd302 bigdata        8838 2018-04-06 11:13 /user/bigdata/nyc_open_data/bws2-q2sb.json
# -rw-rwx---+  3 rpd302 bigdata      465599 2018-04-06 11:13 /user/bigdata/nyc_open_data/by6m-6zpb.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:13 /user/bigdata/nyc_open_data/bymk-vktx.json
# -rw-rwx---+  3 rpd302 bigdata       16608 2018-04-06 11:13 /user/bigdata/nyc_open_data/bzjf-rmtp.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:13 /user/bigdata/nyc_open_data/bzri-pz9j.json
# -rw-rwx---+  3 rpd302 bigdata  5913856681 2018-04-06 11:13 /user/bigdata/nyc_open_data/c284-tqph.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:13 /user/bigdata/nyc_open_data/c2g8-ercv.json
# -rw-rwx---+  3 rpd302 bigdata       16130 2018-04-06 11:13 /user/bigdata/nyc_open_data/c2v8-zzjq.json
# -rw-rwx---+  3 rpd302 bigdata    13350238 2018-04-06 11:13 /user/bigdata/nyc_open_data/c39u-es35.json
# -rw-rwx---+  3 rpd302 bigdata      747405 2018-04-06 11:13 /user/bigdata/nyc_open_data/c3uy-2p5r.json
# -rw-rwx---+  3 rpd302 bigdata     8061405 2018-04-06 11:13 /user/bigdata/nyc_open_data/c3v8-5x25.json
# -rw-rwx---+  3 rpd302 bigdata      583396 2018-04-06 11:13 /user/bigdata/nyc_open_data/c3ya-2ywy.json
# -rw-rwx---+  3 rpd302 bigdata       31409 2018-04-06 11:13 /user/bigdata/nyc_open_data/c49b-3kmd.json
# -rw-rwx---+  3 rpd302 bigdata 13733776559 2018-04-06 11:15 /user/bigdata/nyc_open_data/c4dx-tk4d.json
# -rw-rwx---+  3 rpd302 bigdata       23627 2018-04-06 11:15 /user/bigdata/nyc_open_data/c4pu-cif5.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/c5dk-m6ea.json
# -rw-rwx---+  3 rpd302 bigdata       19713 2018-04-06 11:15 /user/bigdata/nyc_open_data/c5mf-k73g.json
# -rw-rwx---+  3 rpd302 bigdata       41564 2018-04-06 11:15 /user/bigdata/nyc_open_data/c5sh-m8tb.json
# -rw-rwx---+  3 rpd302 bigdata      748374 2018-04-06 11:15 /user/bigdata/nyc_open_data/c5up-ki6j.json
# -rw-rwx---+  3 rpd302 bigdata    13934154 2018-04-06 11:15 /user/bigdata/nyc_open_data/c72z-kzbi.json
# -rw-rwx---+  3 rpd302 bigdata       12414 2018-04-06 11:15 /user/bigdata/nyc_open_data/c87b-2j3i.json
# -rw-rwx---+  3 rpd302 bigdata     4091215 2018-04-06 11:15 /user/bigdata/nyc_open_data/caav-grv8.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/cbn4-bn4p.json
# -rw-rwx---+  3 rpd302 bigdata       27135 2018-04-06 11:15 /user/bigdata/nyc_open_data/ccab-jb4k.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/ce34-mm33.json
# -rw-rwx---+  3 rpd302 bigdata       18979 2018-04-06 11:15 /user/bigdata/nyc_open_data/cete-9g3v.json
# -rw-rwx---+  3 rpd302 bigdata      163552 2018-04-06 11:15 /user/bigdata/nyc_open_data/cfzn-4iza.json
# -rw-rwx---+  3 rpd302 bigdata      569584 2018-04-06 11:15 /user/bigdata/nyc_open_data/cgz5-877h.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/ch5p-r223.json
# -rw-rwx---+  3 rpd302 bigdata      314100 2018-04-06 11:15 /user/bigdata/nyc_open_data/chv4-k4fa.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/chzg-3b9u.json
# -rw-rwx---+  3 rpd302 bigdata     6905200 2018-04-06 11:15 /user/bigdata/nyc_open_data/ci93-uc8s.json
# -rw-rwx---+  3 rpd302 bigdata        9874 2018-04-06 11:15 /user/bigdata/nyc_open_data/cj5g-iwxb.json
# -rw-rwx---+  3 rpd302 bigdata     9549609 2018-04-06 11:15 /user/bigdata/nyc_open_data/ck4n-5h6x.json
# -rw-rwx---+  3 rpd302 bigdata     2371510 2018-04-06 11:15 /user/bigdata/nyc_open_data/ckue-grzy.json
# -rw-rwx---+  3 rpd302 bigdata     2661681 2018-04-06 11:15 /user/bigdata/nyc_open_data/cma4-zi8m.json
# -rw-rwx---+  3 rpd302 bigdata     7112430 2018-04-06 11:15 /user/bigdata/nyc_open_data/cp6j-7bjj.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/cpcf-tcxs.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/cpf4-rkhq.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/cqds-77ys.json
# -rw-rwx---+  3 rpd302 bigdata       19995 2018-04-06 11:15 /user/bigdata/nyc_open_data/cqhy-d5cj.json
# -rw-rwx---+  3 rpd302 bigdata      140536 2018-04-06 11:15 /user/bigdata/nyc_open_data/cr93-x2xf.json
# -rw-rwx---+  3 rpd302 bigdata      291785 2018-04-06 11:15 /user/bigdata/nyc_open_data/crbs-vur7.json
# -rw-rwx---+  3 rpd302 bigdata      288751 2018-04-06 11:15 /user/bigdata/nyc_open_data/crns-fw6u.json
# -rw-rwx---+  3 rpd302 bigdata       47618 2018-04-06 11:15 /user/bigdata/nyc_open_data/cs9m-cz6f.json
# -rw-rwx---+  3 rpd302 bigdata   110955268 2018-04-06 11:15 /user/bigdata/nyc_open_data/cspg-yi7g.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/cteu-mj4k.json
# -rw-rwx---+  3 rpd302 bigdata       16390 2018-04-06 11:15 /user/bigdata/nyc_open_data/cu8c-kkz7.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/cu9u-3r5e.json
# -rw-rwx---+  3 rpd302 bigdata      324621 2018-04-06 11:15 /user/bigdata/nyc_open_data/cw88-qpsr.json
# -rw-rwx---+  3 rpd302 bigdata     1104266 2018-04-06 11:15 /user/bigdata/nyc_open_data/cwg5-cqkm.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/cwiz-gcty.json
# -rw-rwx---+  3 rpd302 bigdata       18766 2018-04-06 11:15 /user/bigdata/nyc_open_data/cwjt-kigp.json
# -rw-rwx---+  3 rpd302 bigdata      380162 2018-04-06 11:15 /user/bigdata/nyc_open_data/cwjy-rrh3.json
# -rw-rwx---+  3 rpd302 bigdata       36630 2018-04-06 11:15 /user/bigdata/nyc_open_data/cwqt-nvfg.json
# -rw-rwx---+  3 rpd302 bigdata     3185719 2018-04-06 11:15 /user/bigdata/nyc_open_data/cwx7-agsh.json
# -rw-rwx---+  3 rpd302 bigdata       16438 2018-04-06 11:15 /user/bigdata/nyc_open_data/cxcv-mgtn.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/cxrn-zyvb.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/cxyq-uhvk.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/cxzk-qz9w.json
# -rw-rwx---+  3 rpd302 bigdata      100089 2018-04-06 11:15 /user/bigdata/nyc_open_data/cyfw-hfqk.json
# -rw-rwx---+  3 rpd302 bigdata     1245956 2018-04-06 11:15 /user/bigdata/nyc_open_data/cz36-mpdq.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/d2bw-3fid.json
# -rw-rwx---+  3 rpd302 bigdata       89979 2018-04-06 11:15 /user/bigdata/nyc_open_data/d33y-i2m7.json
# -rw-rwx---+  3 rpd302 bigdata     6313979 2018-04-06 11:15 /user/bigdata/nyc_open_data/d3ge-anaz.json
# -rw-rwx---+  3 rpd302 bigdata      235039 2018-04-06 11:15 /user/bigdata/nyc_open_data/d4iy-9uh7.json
# -rw-rwx---+  3 rpd302 bigdata        8525 2018-04-06 11:15 /user/bigdata/nyc_open_data/d4uz-6jaw.json
# -rw-rwx---+  3 rpd302 bigdata     9353554 2018-04-06 11:15 /user/bigdata/nyc_open_data/d5zb-ragj.json
# -rw-rwx---+  3 rpd302 bigdata      436570 2018-04-06 11:15 /user/bigdata/nyc_open_data/d68p-5js9.json
# -rw-rwx---+  3 rpd302 bigdata       61899 2018-04-06 11:15 /user/bigdata/nyc_open_data/d6ee-k2sh.json
# -rw-rwx---+  3 rpd302 bigdata       47544 2018-04-06 11:15 /user/bigdata/nyc_open_data/d72n-ivax.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/d7n3-sf2d.json
# -rw-rwx---+  3 rpd302 bigdata       19513 2018-04-06 11:15 /user/bigdata/nyc_open_data/d84z-5kap.json
# -rw-rwx---+  3 rpd302 bigdata       14553 2018-04-06 11:15 /user/bigdata/nyc_open_data/d8cz-kh5x.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/d9z4-v86m.json
# -rw-rwx---+  3 rpd302 bigdata      429216 2018-04-06 11:15 /user/bigdata/nyc_open_data/da9u-wz3r.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/dapf-z62e.json
# -rw-rwx---+  3 rpd302 bigdata      286443 2018-04-06 11:15 /user/bigdata/nyc_open_data/dbs9-fgqs.json
# -rw-rwx---+  3 rpd302 bigdata     9238272 2018-04-06 11:15 /user/bigdata/nyc_open_data/dd6w-hnq9.json
# -rw-rwx---+  3 rpd302 bigdata      415829 2018-04-06 11:15 /user/bigdata/nyc_open_data/ddpx-u5dz.json
# -rw-rwx---+  3 rpd302 bigdata      349278 2018-04-06 11:15 /user/bigdata/nyc_open_data/de8q-estm.json
# -rw-rwx---+  3 rpd302 bigdata       11407 2018-04-06 11:15 /user/bigdata/nyc_open_data/dfad-fpwf.json
# -rw-rwx---+  3 rpd302 bigdata       23167 2018-04-06 11:15 /user/bigdata/nyc_open_data/dftr-3bf5.json
# -rw-rwx---+  3 rpd302 bigdata     4901256 2018-04-06 11:15 /user/bigdata/nyc_open_data/dg7a-jiz2.json
# -rw-rwx---+  3 rpd302 bigdata   311947408 2018-04-06 11:15 /user/bigdata/nyc_open_data/dg92-zbpx.json
# -rw-rwx---+  3 rpd302 bigdata        9459 2018-04-06 11:15 /user/bigdata/nyc_open_data/dgg9-jkx8.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/dgm3-gggb.json
# -rw-rwx---+  3 rpd302 bigdata      313339 2018-04-06 11:15 /user/bigdata/nyc_open_data/dhs7-q59e.json
# -rw-rwx---+  3 rpd302 bigdata       77491 2018-04-06 11:15 /user/bigdata/nyc_open_data/di8r-g5w9.json
# -rw-rwx---+  3 rpd302 bigdata     7307211 2018-04-06 11:15 /user/bigdata/nyc_open_data/did2-qzw3.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/dies-sqgi.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/ding-39n6.json
# -rw-rwx---+  3 rpd302 bigdata      548650 2018-04-06 11:15 /user/bigdata/nyc_open_data/dj4e-3xrn.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/dja4-zgtf.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/djze-f4qi.json
# -rw-rwx---+  3 rpd302 bigdata       37462 2018-04-06 11:15 /user/bigdata/nyc_open_data/dk7q-942i.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/dmue-3nqk.json
# -rw-rwx---+  3 rpd302 bigdata       10958 2018-04-06 11:15 /user/bigdata/nyc_open_data/dn64-92ub.json
# -rw-rwx---+  3 rpd302 bigdata       49521 2018-04-06 11:15 /user/bigdata/nyc_open_data/dp2s-vccd.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/dpc8-z3jc.json
# -rw-rwx---+  3 rpd302 bigdata     2277794 2018-04-06 11:15 /user/bigdata/nyc_open_data/dpec-ucu7.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/dqkt-8x6u.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/drex-xx56.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/drh3-e2fd.json
# -rw-rwx---+  3 rpd302 bigdata    43388873 2018-04-06 11:15 /user/bigdata/nyc_open_data/dsg6-ifza.json
# -rw-rwx---+  3 rpd302 bigdata       65199 2018-04-06 11:15 /user/bigdata/nyc_open_data/dt2z-amuf.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/dte3-kvx7.json
# -rw-rwx---+  3 rpd302 bigdata      123230 2018-04-06 11:15 /user/bigdata/nyc_open_data/dtfq-bfpc.json
# -rw-rwx---+  3 rpd302 bigdata      724508 2018-04-06 11:15 /user/bigdata/nyc_open_data/ducj-28wv.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/dv6z-emb2.json
# -rw-rwx---+  3 rpd302 bigdata     5736882 2018-04-06 11:15 /user/bigdata/nyc_open_data/dvaj-b7yx.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/dve9-92na.json
# -rw-rwx---+  3 rpd302 bigdata     1396727 2018-04-06 11:15 /user/bigdata/nyc_open_data/dvzp-h4k9.json
# -rw-rwx---+  3 rpd302 bigdata     1716293 2018-04-06 11:15 /user/bigdata/nyc_open_data/dxnu-p2qd.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/dy62-2n2g.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/dy9m-dvf2.json
# -rw-rwx---+  3 rpd302 bigdata      567734 2018-04-06 11:15 /user/bigdata/nyc_open_data/dzgh-ja44.json
# -rw-rwx---+  3 rpd302 bigdata    42869632 2018-04-06 11:15 /user/bigdata/nyc_open_data/e25p-jzfy.json
# -rw-rwx---+  3 rpd302 bigdata       11446 2018-04-06 11:15 /user/bigdata/nyc_open_data/e266-vpg7.json
# -rw-rwx---+  3 rpd302 bigdata       70737 2018-04-06 11:15 /user/bigdata/nyc_open_data/e2ey-aicw.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/e2f7-cs7i.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/e33f-d2gn.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/e3uq-vht9.json
# -rw-rwx---+  3 rpd302 bigdata      156399 2018-04-06 11:15 /user/bigdata/nyc_open_data/e4ej-j6hn.json
# -rw-rwx---+  3 rpd302 bigdata     2583285 2018-04-06 11:15 /user/bigdata/nyc_open_data/e4p3-6ecr.json
# -rw-rwx---+  3 rpd302 bigdata       18916 2018-04-06 11:15 /user/bigdata/nyc_open_data/e4ss-s2zn.json
# -rw-rwx---+  3 rpd302 bigdata     1028843 2018-04-06 11:15 /user/bigdata/nyc_open_data/e544-259w.json
# -rw-rwx---+  3 rpd302 bigdata      158906 2018-04-06 11:15 /user/bigdata/nyc_open_data/e649-r223.json
# -rw-rwx---+  3 rpd302 bigdata      233384 2018-04-06 11:15 /user/bigdata/nyc_open_data/e64w-ctmw.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/e76w-s8gb.json
# -rw-rwx---+  3 rpd302 bigdata       58913 2018-04-06 11:15 /user/bigdata/nyc_open_data/e7rh-dmb4.json
# -rw-rwx---+  3 rpd302 bigdata   304535224 2018-04-06 11:15 /user/bigdata/nyc_open_data/e8jc-rs3b.json
# -rw-rwx---+  3 rpd302 bigdata    26762838 2018-04-06 11:15 /user/bigdata/nyc_open_data/e98g-f8hy.json
# -rw-rwx---+  3 rpd302 bigdata   379753750 2018-04-06 11:15 /user/bigdata/nyc_open_data/eabe-havv.json
# -rw-rwx---+  3 rpd302 bigdata    29650793 2018-04-06 11:15 /user/bigdata/nyc_open_data/easq-ubfe.json
# -rw-rwx---+  3 rpd302 bigdata      536493 2018-04-06 11:15 /user/bigdata/nyc_open_data/ebb7-mvp5.json
# -rw-rwx---+  3 rpd302 bigdata      393096 2018-04-06 11:15 /user/bigdata/nyc_open_data/eccv-9dzr.json
# -rw-rwx---+  3 rpd302 bigdata       38738 2018-04-06 11:15 /user/bigdata/nyc_open_data/ect6-rj3p.json
# -rw-rwx---+  3 rpd302 bigdata      448845 2018-04-06 11:15 /user/bigdata/nyc_open_data/ecvp-uumu.json
# -rw-rwx---+  3 rpd302 bigdata     6479455 2018-04-06 11:15 /user/bigdata/nyc_open_data/eddp-3v5g.json
# -rw-rwx---+  3 rpd302 bigdata      355726 2018-04-06 11:15 /user/bigdata/nyc_open_data/edx9-hxi8.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/efsz-uj8v.json
# -rw-rwx---+  3 rpd302 bigdata      301239 2018-04-06 11:15 /user/bigdata/nyc_open_data/eg59-gdqu.json
# -rw-rwx---+  3 rpd302 bigdata      263830 2018-04-06 11:15 /user/bigdata/nyc_open_data/eg75-mh9k.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/egch-abu9.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/egea-b8r5.json
# -rw-rwx---+  3 rpd302 bigdata       23456 2018-04-06 11:15 /user/bigdata/nyc_open_data/egiq-kmr5.json
# -rw-rwx---+  3 rpd302 bigdata       23352 2018-04-06 11:15 /user/bigdata/nyc_open_data/eivx-q94q.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/eizi-ujye.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/ejxk-d93y.json
# -rw-rwx---+  3 rpd302 bigdata       62415 2018-04-06 11:15 /user/bigdata/nyc_open_data/ek5y-zcyf.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/ekax-ky3z.json
# -rw-rwx---+  3 rpd302 bigdata     1490027 2018-04-06 11:15 /user/bigdata/nyc_open_data/emnd-d8ba.json
# -rw-rwx---+  3 rpd302 bigdata   147064956 2018-04-06 11:15 /user/bigdata/nyc_open_data/emrz-5p35.json
# -rw-rwx---+  3 rpd302 bigdata      143717 2018-04-06 11:15 /user/bigdata/nyc_open_data/en2c-j6tw.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/ens7-ac7e.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:15 /user/bigdata/nyc_open_data/epfh-qbp5.json
# -rw-rwx---+  3 rpd302 bigdata  9567648663 2018-04-06 11:16 /user/bigdata/nyc_open_data/erm2-nwe9.json
# -rw-rwx---+  3 rpd302 bigdata      337152 2018-04-06 11:16 /user/bigdata/nyc_open_data/erra-pzy8.json
# -rw-rwx---+  3 rpd302 bigdata       68390 2018-04-06 11:16 /user/bigdata/nyc_open_data/erts-eyf6.json
# -rw-rwx---+  3 rpd302 bigdata      830431 2018-04-06 11:16 /user/bigdata/nyc_open_data/esep-hmvs.json
# -rw-rwx---+  3 rpd302 bigdata     1194256 2018-04-06 11:16 /user/bigdata/nyc_open_data/esmb-8zkm.json
# -rw-rwx---+  3 rpd302 bigdata       49225 2018-04-06 11:16 /user/bigdata/nyc_open_data/esw6-z4id.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:16 /user/bigdata/nyc_open_data/evdj-a5z2.json
# -rw-rwx---+  3 rpd302 bigdata      280588 2018-04-06 11:16 /user/bigdata/nyc_open_data/evjd-dqpz.json
# -rw-rwx---+  3 rpd302 bigdata  2787687946 2018-04-06 11:17 /user/bigdata/nyc_open_data/evp6-d8e7.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:17 /user/bigdata/nyc_open_data/eweh-h793.json
# -rw-rwx---+  3 rpd302 bigdata      584793 2018-04-06 11:17 /user/bigdata/nyc_open_data/ewg2-2vyd.json
# -rw-rwx---+  3 rpd302 bigdata       57479 2018-04-06 11:17 /user/bigdata/nyc_open_data/ewmy-2fww.json
# -rw-rwx---+  3 rpd302 bigdata     2556257 2018-04-06 11:17 /user/bigdata/nyc_open_data/ex6k-ym48.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:17 /user/bigdata/nyc_open_data/exjm-f27b.json
# -rw-rwx---+  3 rpd302 bigdata      286449 2018-04-06 11:17 /user/bigdata/nyc_open_data/eyk3-bhe9.json
# -rw-rwx---+  3 rpd302 bigdata    83630847 2018-04-06 11:17 /user/bigdata/nyc_open_data/ez4e-fazm.json
# -rw-rwx---+  3 rpd302 bigdata     4302222 2018-04-06 11:17 /user/bigdata/nyc_open_data/ezaf-3uhs.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:17 /user/bigdata/nyc_open_data/ezds-sqp6.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:17 /user/bigdata/nyc_open_data/ezfn-5dsb.json
# -rw-rwx---+  3 rpd302 bigdata       46089 2018-04-06 11:17 /user/bigdata/nyc_open_data/f2cz-q2ik.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:17 /user/bigdata/nyc_open_data/f2kq-825w.json
# -rw-rwx---+  3 rpd302 bigdata  1094815409 2018-04-06 11:17 /user/bigdata/nyc_open_data/f364-y3pv.json
# -rw-rwx---+  3 rpd302 bigdata    13572813 2018-04-06 11:17 /user/bigdata/nyc_open_data/f3u3-q8ea.json
# -rw-rwx---+  3 rpd302 bigdata     1094360 2018-04-06 11:17 /user/bigdata/nyc_open_data/f42p-xqaa.json
# -rw-rwx---+  3 rpd302 bigdata    40092358 2018-04-06 11:17 /user/bigdata/nyc_open_data/f4rp-2kvy.json
# -rw-rwx---+  3 rpd302 bigdata     1809620 2018-04-06 11:17 /user/bigdata/nyc_open_data/f4yq-wry5.json
# -rw-rwx---+  3 rpd302 bigdata     6037788 2018-04-06 11:17 /user/bigdata/nyc_open_data/f5zq-eacn.json
# -rw-rwx---+  3 rpd302 bigdata        9127 2018-04-06 11:17 /user/bigdata/nyc_open_data/f64t-5yiv.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:17 /user/bigdata/nyc_open_data/f6an-2v46.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:17 /user/bigdata/nyc_open_data/f6st-pb23.json
# -rw-rwx---+  3 rpd302 bigdata       78008 2018-04-06 11:17 /user/bigdata/nyc_open_data/f7b6-v6v3.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:17 /user/bigdata/nyc_open_data/f7ta-5e24.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:17 /user/bigdata/nyc_open_data/f888-ni5f.json
# -rw-rwx---+  3 rpd302 bigdata       96131 2018-04-06 11:17 /user/bigdata/nyc_open_data/f9a8-4jby.json
# -rw-rwx---+  3 rpd302 bigdata      103072 2018-04-06 11:17 /user/bigdata/nyc_open_data/f9bf-2cp4.json
# -rw-rwx---+  3 rpd302 bigdata      201461 2018-04-06 11:17 /user/bigdata/nyc_open_data/fa9x-pfzm.json
# -rw-rwx---+  3 rpd302 bigdata      137206 2018-04-06 11:17 /user/bigdata/nyc_open_data/fb26-34vu.json
# -rw-rwx---+  3 rpd302 bigdata     7534194 2018-04-06 11:17 /user/bigdata/nyc_open_data/fbaw-uq4e.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:17 /user/bigdata/nyc_open_data/fbmg-vwgd.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:17 /user/bigdata/nyc_open_data/fbqm-ihfd.json
# -rw-rwx---+  3 rpd302 bigdata       10463 2018-04-06 11:17 /user/bigdata/nyc_open_data/fbsa-93dh.json
# -rw-rwx---+  3 rpd302 bigdata       30094 2018-04-06 11:17 /user/bigdata/nyc_open_data/fcau-jc6k.json
# -rw-rwx---+  3 rpd302 bigdata 60915859527 2018-04-06 11:24 /user/bigdata/nyc_open_data/fd5y-xikb.json
# -rw-rwx---+  3 rpd302 bigdata   175103508 2018-04-06 11:24 /user/bigdata/nyc_open_data/fdkv-4t4z.json
# -rw-rwx---+  3 rpd302 bigdata       32130 2018-04-06 11:24 /user/bigdata/nyc_open_data/fdx7-6jsr.json
# -rw-rwx---+  3 rpd302 bigdata   168860936 2018-04-06 11:24 /user/bigdata/nyc_open_data/feu5-w2e2.json
# -rw-rwx---+  3 rpd302 bigdata       18145 2018-04-06 11:24 /user/bigdata/nyc_open_data/ff9v-9yzg.json
# -rw-rwx---+  3 rpd302 bigdata       16316 2018-04-06 11:24 /user/bigdata/nyc_open_data/ffgt-jimk.json
# -rw-rwx---+  3 rpd302 bigdata      475897 2018-04-06 11:24 /user/bigdata/nyc_open_data/ffnc-f3aa.json
# -rw-rwx---+  3 rpd302 bigdata      634083 2018-04-06 11:24 /user/bigdata/nyc_open_data/ffzt-rdkr.json
# -rw-rwx---+  3 rpd302 bigdata       16739 2018-04-06 11:24 /user/bigdata/nyc_open_data/fgb7-3q7d.json
# -rw-rwx---+  3 rpd302 bigdata     1247431 2018-04-06 11:24 /user/bigdata/nyc_open_data/fgq8-am2v.json
# -rw-rwx---+  3 rpd302 bigdata    10258503 2018-04-06 11:24 /user/bigdata/nyc_open_data/fgqh-vfzz.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:24 /user/bigdata/nyc_open_data/fhj3-55ah.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:24 /user/bigdata/nyc_open_data/fhs8-jstc.json
# -rw-rwx---+  3 rpd302 bigdata       22583 2018-04-06 11:24 /user/bigdata/nyc_open_data/fics-ewaq.json
# -rw-rwx---+  3 rpd302 bigdata       74073 2018-04-06 11:24 /user/bigdata/nyc_open_data/fijd-wye8.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:24 /user/bigdata/nyc_open_data/fkwx-g3zf.json
# -rw-rwx---+  3 rpd302 bigdata      299012 2018-04-06 11:24 /user/bigdata/nyc_open_data/fm6n-5jvy.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:24 /user/bigdata/nyc_open_data/fmhd-mfkw.json
# -rw-rwx---+  3 rpd302 bigdata       13874 2018-04-06 11:24 /user/bigdata/nyc_open_data/fmzx-suji.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:24 /user/bigdata/nyc_open_data/fpuh-f5mr.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:24 /user/bigdata/nyc_open_data/fpz8-jqf4.json
# -rw-rwx---+  3 rpd302 bigdata       55211 2018-04-06 11:24 /user/bigdata/nyc_open_data/fqcv-e9sg.json
# -rw-rwx---+  3 rpd302 bigdata       18035 2018-04-06 11:24 /user/bigdata/nyc_open_data/fr6n-f337.json
# -rw-rwx---+  3 rpd302 bigdata       17954 2018-04-06 11:24 /user/bigdata/nyc_open_data/fsis-j6x5.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:24 /user/bigdata/nyc_open_data/ft4n-yqee.json
# -rw-rwx---+  3 rpd302 bigdata      352474 2018-04-06 11:24 /user/bigdata/nyc_open_data/ftpm-ey3k.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:24 /user/bigdata/nyc_open_data/ftxv-d5ix.json
# -rw-rwx---+  3 rpd302 bigdata       94740 2018-04-06 11:24 /user/bigdata/nyc_open_data/fu34-wamz.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:24 /user/bigdata/nyc_open_data/fum3-ejky.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:24 /user/bigdata/nyc_open_data/fupk-24im.json
# -rw-rwx---+  3 rpd302 bigdata       52619 2018-04-06 11:24 /user/bigdata/nyc_open_data/fuvx-wqd7.json
# -rw-rwx---+  3 rpd302 bigdata     1130042 2018-04-06 11:24 /user/bigdata/nyc_open_data/fuzb-9jre.json
# -rw-rwx---+  3 rpd302 bigdata   125339108 2018-04-06 11:24 /user/bigdata/nyc_open_data/fuzi-5ks9.json
# -rw-rwx---+  3 rpd302 bigdata       37354 2018-04-06 11:24 /user/bigdata/nyc_open_data/fve3-eee8.json
# -rw-rwx---+  3 rpd302 bigdata  8131504463 2018-04-06 11:25 /user/bigdata/nyc_open_data/fvrb-kbbt.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:25 /user/bigdata/nyc_open_data/fw3w-apxs.json
# -rw-rwx---+  3 rpd302 bigdata  1851573326 2018-04-06 11:25 /user/bigdata/nyc_open_data/fw4n-6ehm.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:25 /user/bigdata/nyc_open_data/fw5m-2rb3.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:25 /user/bigdata/nyc_open_data/fx7a-24mf.json
# -rw-rwx---+  3 rpd302 bigdata      428924 2018-04-06 11:25 /user/bigdata/nyc_open_data/fxdy-q85h.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:25 /user/bigdata/nyc_open_data/fxpq-c8ku.json
# -rw-rwx---+  3 rpd302 bigdata     1666690 2018-04-06 11:25 /user/bigdata/nyc_open_data/fxs2-faah.json
# -rw-rwx---+  3 rpd302 bigdata       31848 2018-04-06 11:25 /user/bigdata/nyc_open_data/fxwm-3t4n.json
# -rw-rwx---+  3 rpd302 bigdata      320550 2018-04-06 11:25 /user/bigdata/nyc_open_data/fyf4-hrcu.json
# -rw-rwx---+  3 rpd302 bigdata       32990 2018-04-06 11:25 /user/bigdata/nyc_open_data/fzk8-3ynb.json
# -rw-rwx---+  3 rpd302 bigdata      355870 2018-04-06 11:25 /user/bigdata/nyc_open_data/fzv4-jan3.json
# -rw-rwx---+  3 rpd302 bigdata       76493 2018-04-06 11:25 /user/bigdata/nyc_open_data/g3vh-kbnw.json
# -rw-rwx---+  3 rpd302 bigdata      163235 2018-04-06 11:25 /user/bigdata/nyc_open_data/g63j-swsd.json
# -rw-rwx---+  3 rpd302 bigdata       45388 2018-04-06 11:25 /user/bigdata/nyc_open_data/g6f6-qpfi.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:25 /user/bigdata/nyc_open_data/g6pj-hd8k.json
# -rw-rwx---+  3 rpd302 bigdata       18221 2018-04-06 11:25 /user/bigdata/nyc_open_data/g7ee-832z.json
# -rw-rwx---+  3 rpd302 bigdata       17036 2018-04-06 11:25 /user/bigdata/nyc_open_data/g7ir-4pf8.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:25 /user/bigdata/nyc_open_data/g84h-jbjm.json
# -rw-rwx---+  3 rpd302 bigdata    26702338 2018-04-06 11:25 /user/bigdata/nyc_open_data/g8e6-y4ax.json
# -rw-rwx---+  3 rpd302 bigdata       23278 2018-04-06 11:25 /user/bigdata/nyc_open_data/g8v5-qeu5.json
# -rw-rwx---+  3 rpd302 bigdata       15807 2018-04-06 11:25 /user/bigdata/nyc_open_data/g993-cbry.json
# -rw-rwx---+  3 rpd302 bigdata      107364 2018-04-06 11:25 /user/bigdata/nyc_open_data/g9ub-hrve.json
# -rw-rwx---+  3 rpd302 bigdata       28722 2018-04-06 11:25 /user/bigdata/nyc_open_data/g9wv-7n2m.json
# -rw-rwx---+  3 rpd302 bigdata      534162 2018-04-06 11:25 /user/bigdata/nyc_open_data/gahm-hu5h.json
# -rw-rwx---+  3 rpd302 bigdata       53520 2018-04-06 11:25 /user/bigdata/nyc_open_data/gakf-suji.json
# -rw-rwx---+  3 rpd302 bigdata       33319 2018-04-06 11:25 /user/bigdata/nyc_open_data/gaq9-z3hz.json
# -rw-rwx---+  3 rpd302 bigdata      195173 2018-04-06 11:25 /user/bigdata/nyc_open_data/gbgg-xjuf.json
# -rw-rwx---+  3 rpd302 bigdata    48945153 2018-04-06 11:25 /user/bigdata/nyc_open_data/gcvr-n8qw.json
# -rw-rwx---+  3 rpd302 bigdata   135355475 2018-04-06 11:25 /user/bigdata/nyc_open_data/gcys-vvnq.json
# -rw-rwx---+  3 rpd302 bigdata       13849 2018-04-06 11:25 /user/bigdata/nyc_open_data/gd6m-k9v9.json
# -rw-rwx---+  3 rpd302 bigdata      482636 2018-04-06 11:25 /user/bigdata/nyc_open_data/ge8j-uqbf.json
# -rw-rwx---+  3 rpd302 bigdata       87493 2018-04-06 11:25 /user/bigdata/nyc_open_data/gepv-dxc2.json
# -rw-rwx---+  3 rpd302 bigdata     4549219 2018-04-06 11:25 /user/bigdata/nyc_open_data/gezn-7mgk.json
# -rw-rwx---+  3 rpd302 bigdata       15881 2018-04-06 11:25 /user/bigdata/nyc_open_data/gffu-ps8j.json
# -rw-rwx---+  3 rpd302 bigdata   398392370 2018-04-06 11:25 /user/bigdata/nyc_open_data/ghpb-fpea.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:25 /user/bigdata/nyc_open_data/ghq4-ydq4.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:25 /user/bigdata/nyc_open_data/ghse-r5nk.json
# -rw-rwx---+  3 rpd302 bigdata       46457 2018-04-06 11:25 /user/bigdata/nyc_open_data/gi3h-3i8t.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:25 /user/bigdata/nyc_open_data/gi7d-8gt5.json
# -rw-rwx---+  3 rpd302 bigdata   922484369 2018-04-06 11:25 /user/bigdata/nyc_open_data/gi8d-wdg5.json
# -rw-rwx---+  3 rpd302 bigdata     1288614 2018-04-06 11:25 /user/bigdata/nyc_open_data/gk83-aa6y.json
# -rw-rwx---+  3 rpd302 bigdata       12653 2018-04-06 11:25 /user/bigdata/nyc_open_data/gk9u-c3tv.json
# -rw-rwx---+  3 rpd302 bigdata     2189674 2018-04-06 11:25 /user/bigdata/nyc_open_data/gkd7-3vk7.json
# -rw-rwx---+  3 rpd302 bigdata      107968 2018-04-06 11:25 /user/bigdata/nyc_open_data/gmi7-62cd.json
# -rw-rwx---+  3 rpd302 bigdata 18657931357 2018-04-06 11:27 /user/bigdata/nyc_open_data/gn7m-em8n.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:27 /user/bigdata/nyc_open_data/gnpd-qabs.json
# -rw-rwx---+  3 rpd302 bigdata     5755026 2018-04-06 11:27 /user/bigdata/nyc_open_data/gpwd-npar.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:27 /user/bigdata/nyc_open_data/gpxw-bq7a.json
# -rw-rwx---+  3 rpd302 bigdata      173920 2018-04-06 11:27 /user/bigdata/nyc_open_data/grbs-nm2g.json
# -rw-rwx---+  3 rpd302 bigdata     1289173 2018-04-06 11:27 /user/bigdata/nyc_open_data/grnn-mvqe.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:27 /user/bigdata/nyc_open_data/gs56-euca.json
# -rw-rwx---+  3 rpd302 bigdata      571055 2018-04-06 11:27 /user/bigdata/nyc_open_data/gsak-mt7t.json
# -rw-rwx---+  3 rpd302 bigdata      213730 2018-04-06 11:27 /user/bigdata/nyc_open_data/gshi-yqza.json
# -rw-rwx---+  3 rpd302 bigdata      435554 2018-04-06 11:27 /user/bigdata/nyc_open_data/gsr2-xq9e.json
# -rw-rwx---+  3 rpd302 bigdata       35506 2018-04-06 11:27 /user/bigdata/nyc_open_data/gt5i-dmde.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:27 /user/bigdata/nyc_open_data/gua4-p9wg.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:27 /user/bigdata/nyc_open_data/gx5n-2nma.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:27 /user/bigdata/nyc_open_data/gx7x-82rk.json
# -rw-rwx---+  3 rpd302 bigdata      347191 2018-04-06 11:27 /user/bigdata/nyc_open_data/gyaz-82xj.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:27 /user/bigdata/nyc_open_data/gyhq-r8du.json
# -rw-rwx---+  3 rpd302 bigdata     8436126 2018-04-06 11:27 /user/bigdata/nyc_open_data/gysc-yn4h.json
# -rw-rwx---+  3 rpd302 bigdata      358432 2018-04-06 11:27 /user/bigdata/nyc_open_data/gysw-j2f3.json
# -rw-rwx---+  3 rpd302 bigdata      101854 2018-04-06 11:27 /user/bigdata/nyc_open_data/gzdv-qiga.json
# -rw-rwx---+  3 rpd302 bigdata     1932207 2018-04-06 11:27 /user/bigdata/nyc_open_data/gzfs-3h4m.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:27 /user/bigdata/nyc_open_data/gzk5-mux8.json
# -rw-rwx---+  3 rpd302 bigdata     2211068 2018-04-06 11:27 /user/bigdata/nyc_open_data/gzvm-na49.json
# -rw-rwx---+  3 rpd302 bigdata      627937 2018-04-06 11:27 /user/bigdata/nyc_open_data/h2mm-eazk.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:27 /user/bigdata/nyc_open_data/h2n3-98hq.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:27 /user/bigdata/nyc_open_data/h3ke-x25q.json
# -rw-rwx---+  3 rpd302 bigdata      159254 2018-04-06 11:27 /user/bigdata/nyc_open_data/h3qk-ybvt.json
# -rw-rwx---+  3 rpd302 bigdata      140277 2018-04-06 11:27 /user/bigdata/nyc_open_data/h3zm-ta5h.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:27 /user/bigdata/nyc_open_data/h424-4zbv.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:27 /user/bigdata/nyc_open_data/h49x-6v6r.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:27 /user/bigdata/nyc_open_data/h4i2-acfi.json
# -rw-rwx---+  3 rpd302 bigdata       19555 2018-04-06 11:27 /user/bigdata/nyc_open_data/h4jn-x3ty.json
# -rw-rwx---+  3 rpd302 bigdata       37401 2018-04-06 11:27 /user/bigdata/nyc_open_data/h4jy-7dv7.json
# -rw-rwx---+  3 rpd302 bigdata      123015 2018-04-06 11:27 /user/bigdata/nyc_open_data/h5de-ndty.json
# -rw-rwx---+  3 rpd302 bigdata      105721 2018-04-06 11:27 /user/bigdata/nyc_open_data/h5nh-eqde.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:27 /user/bigdata/nyc_open_data/h682-ywyg.json
# -rw-rwx---+  3 rpd302 bigdata       11197 2018-04-06 11:27 /user/bigdata/nyc_open_data/h7mf-hrsw.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:27 /user/bigdata/nyc_open_data/h7zy-iq3d.json
# -rw-rwx---+  3 rpd302 bigdata       36877 2018-04-06 11:27 /user/bigdata/nyc_open_data/h8eh-b25q.json
# -rw-rwx---+  3 rpd302 bigdata   580998003 2018-04-06 11:27 /user/bigdata/nyc_open_data/h9gi-nx95.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:27 /user/bigdata/nyc_open_data/h9sf-7bej.json
# -rw-rwx---+  3 rpd302 bigdata       66526 2018-04-06 11:27 /user/bigdata/nyc_open_data/hb7y-b986.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:27 /user/bigdata/nyc_open_data/hbw8-2bah.json
# -rw-rwx---+  3 rpd302 bigdata       93404 2018-04-06 11:27 /user/bigdata/nyc_open_data/hc8x-tcnd.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:27 /user/bigdata/nyc_open_data/hc9t-g6wa.json
# -rw-rwx---+  3 rpd302 bigdata      125714 2018-04-06 11:27 /user/bigdata/nyc_open_data/hcf7-jp2y.json
# -rw-rwx---+  3 rpd302 bigdata       54843 2018-04-06 11:27 /user/bigdata/nyc_open_data/hcv4-fhfs.json
# -rw-rwx---+  3 rpd302 bigdata       63684 2018-04-06 11:27 /user/bigdata/nyc_open_data/hdnu-nbrh.json
# -rw-rwx---+  3 rpd302 bigdata       18518 2018-04-06 11:27 /user/bigdata/nyc_open_data/hdu7-ujt4.json
# -rw-rwx---+  3 rpd302 bigdata       66824 2018-04-06 11:27 /user/bigdata/nyc_open_data/he5b-24yw.json
# -rw-rwx---+  3 rpd302 bigdata  1755607617 2018-04-06 11:28 /user/bigdata/nyc_open_data/hemm-82xw.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:28 /user/bigdata/nyc_open_data/hfa3-euj3.json
# -rw-rwx---+  3 rpd302 bigdata       12718 2018-04-06 11:28 /user/bigdata/nyc_open_data/hfac-j85r.json
# -rw-rwx---+  3 rpd302 bigdata     4177832 2018-04-06 11:28 /user/bigdata/nyc_open_data/hg3c-2jsy.json
# -rw-rwx---+  3 rpd302 bigdata        6746 2018-04-06 11:28 /user/bigdata/nyc_open_data/hg3k-2w6h.json
# -rw-rwx---+  3 rpd302 bigdata     1479386 2018-04-06 11:28 /user/bigdata/nyc_open_data/hg8x-zxpr.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:28 /user/bigdata/nyc_open_data/hgue-hj96.json
# -rw-rwx---+  3 rpd302 bigdata       39245 2018-04-06 11:28 /user/bigdata/nyc_open_data/hi3x-y76v.json
# -rw-rwx---+  3 rpd302 bigdata       64495 2018-04-06 11:28 /user/bigdata/nyc_open_data/hiik-hmf3.json
# -rw-rwx---+  3 rpd302 bigdata      422054 2018-04-06 11:28 /user/bigdata/nyc_open_data/him9-7gri.json
# -rw-rwx---+  3 rpd302 bigdata      139748 2018-04-06 11:28 /user/bigdata/nyc_open_data/hjae-yuav.json
# -rw-rwx---+  3 rpd302 bigdata       39477 2018-04-06 11:28 /user/bigdata/nyc_open_data/hjnm-89hx.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:28 /user/bigdata/nyc_open_data/hkpx-aaxc.json
# -rw-rwx---+  3 rpd302 bigdata     8074273 2018-04-06 11:28 /user/bigdata/nyc_open_data/hm4n-kxfu.json
# -rw-rwx---+  3 rpd302 bigdata        8577 2018-04-06 11:28 /user/bigdata/nyc_open_data/hm7r-w4y9.json
# -rw-rwx---+  3 rpd302 bigdata      114263 2018-04-06 11:28 /user/bigdata/nyc_open_data/hmw8-8is3.json
# -rw-rwx---+  3 rpd302 bigdata   380452153 2018-04-06 11:28 /user/bigdata/nyc_open_data/hn5i-inap.json
# -rw-rwx---+  3 rpd302 bigdata      110848 2018-04-06 11:28 /user/bigdata/nyc_open_data/hnf2-ds4u.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:28 /user/bigdata/nyc_open_data/hnxz-kkn5.json
# -rw-rwx---+  3 rpd302 bigdata      568004 2018-04-06 11:28 /user/bigdata/nyc_open_data/hpid-63r5.json
# -rw-rwx---+  3 rpd302 bigdata      419084 2018-04-06 11:28 /user/bigdata/nyc_open_data/hq68-rnsi.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:28 /user/bigdata/nyc_open_data/hr2s-xdcw.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:28 /user/bigdata/nyc_open_data/hrii-hezj.json
# -rw-rwx---+  3 rpd302 bigdata    11756536 2018-04-06 11:28 /user/bigdata/nyc_open_data/hrsu-3w2q.json
# -rw-rwx---+  3 rpd302 bigdata     1298536 2018-04-06 11:28 /user/bigdata/nyc_open_data/ht4t-wzcm.json
# -rw-rwx---+  3 rpd302 bigdata      567746 2018-04-06 11:28 /user/bigdata/nyc_open_data/hti8-xb6u.json
# -rw-rwx---+  3 rpd302 bigdata      636061 2018-04-06 11:28 /user/bigdata/nyc_open_data/htkc-b6ea.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:28 /user/bigdata/nyc_open_data/htur-iwux.json
# -rw-rwx---+  3 rpd302 bigdata      695158 2018-04-06 11:28 /user/bigdata/nyc_open_data/hu6m-9cfi.json
# -rw-rwx---+  3 rpd302 bigdata       93615 2018-04-06 11:28 /user/bigdata/nyc_open_data/hukm-snmq.json
# -rw-rwx---+  3 rpd302 bigdata      319279 2018-04-06 11:28 /user/bigdata/nyc_open_data/huq7-iui5.json
# -rw-rwx---+  3 rpd302 bigdata       39895 2018-04-06 11:28 /user/bigdata/nyc_open_data/hv77-qnda.json
# -rw-rwx---+  3 rpd302 bigdata        9009 2018-04-06 11:28 /user/bigdata/nyc_open_data/hve5-8z68.json
# -rw-rwx---+  3 rpd302 bigdata    25460369 2018-04-06 11:28 /user/bigdata/nyc_open_data/hvrh-b6nb.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:28 /user/bigdata/nyc_open_data/hxay-3qcw.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:28 /user/bigdata/nyc_open_data/hxff-kzzc.json
# -rw-rwx---+  3 rpd302 bigdata  1471919071 2018-04-06 11:28 /user/bigdata/nyc_open_data/hy4q-igkk.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:28 /user/bigdata/nyc_open_data/hybb-af8n.json
# -rw-rwx---+  3 rpd302 bigdata    12659787 2018-04-06 11:28 /user/bigdata/nyc_open_data/hypw-js3b.json
# -rw-rwx---+  3 rpd302 bigdata     1355619 2018-04-06 11:28 /user/bigdata/nyc_open_data/hyur-qpyf.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:28 /user/bigdata/nyc_open_data/hyuz-tij8.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:28 /user/bigdata/nyc_open_data/hz79-96hi.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:28 /user/bigdata/nyc_open_data/hzb8-928j.json
# -rw-rwx---+  3 rpd302 bigdata   200384638 2018-04-06 11:28 /user/bigdata/nyc_open_data/i296-73x5.json
# -rw-rwx---+  3 rpd302 bigdata     5044472 2018-04-06 11:28 /user/bigdata/nyc_open_data/i37z-2ty9.json
# -rw-rwx---+  3 rpd302 bigdata      793263 2018-04-06 11:28 /user/bigdata/nyc_open_data/i3a3-qxkf.json
# -rw-rwx---+  3 rpd302 bigdata      475699 2018-04-06 11:28 /user/bigdata/nyc_open_data/i3ez-z58g.json
# -rw-rwx---+  3 rpd302 bigdata        9261 2018-04-06 11:28 /user/bigdata/nyc_open_data/i447-i5u3.json
# -rw-rwx---+  3 rpd302 bigdata     1678546 2018-04-06 11:28 /user/bigdata/nyc_open_data/i4ni-6qin.json
# -rw-rwx---+  3 rpd302 bigdata  2889406832 2018-04-06 11:28 /user/bigdata/nyc_open_data/i4p3-pe6a.json
# -rw-rwx---+  3 rpd302 bigdata      170727 2018-04-06 11:28 /user/bigdata/nyc_open_data/i6as-kc83.json
# -rw-rwx---+  3 rpd302 bigdata     5729956 2018-04-06 11:28 /user/bigdata/nyc_open_data/i6b5-j7bu.json
# -rw-rwx---+  3 rpd302 bigdata      137247 2018-04-06 11:28 /user/bigdata/nyc_open_data/i6bk-bwyv.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:28 /user/bigdata/nyc_open_data/i762-rk6i.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:28 /user/bigdata/nyc_open_data/i7a5-bsik.json
# -rw-rwx---+  3 rpd302 bigdata       38209 2018-04-06 11:28 /user/bigdata/nyc_open_data/i7jz-e2db.json
# -rw-rwx---+  3 rpd302 bigdata       21048 2018-04-06 11:28 /user/bigdata/nyc_open_data/i7zn-7njs.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:28 /user/bigdata/nyc_open_data/i8d5-5ciu.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:28 /user/bigdata/nyc_open_data/i8f4-bu5r.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:28 /user/bigdata/nyc_open_data/i8iw-xf4u.json
# -rw-rwx---+  3 rpd302 bigdata      418066 2018-04-06 11:28 /user/bigdata/nyc_open_data/i8ua-bnkj.json
# -rw-rwx---+  3 rpd302 bigdata     3821508 2018-04-06 11:28 /user/bigdata/nyc_open_data/i8ys-e4pm.json
# -rw-rwx---+  3 rpd302 bigdata    14190492 2018-04-06 11:28 /user/bigdata/nyc_open_data/i99z-ad8n.json
# -rw-rwx---+  3 rpd302 bigdata      863438 2018-04-06 11:28 /user/bigdata/nyc_open_data/i9pf-sj7c.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:28 /user/bigdata/nyc_open_data/i9rv-hdr5.json
# -rw-rwx---+  3 rpd302 bigdata       18698 2018-04-06 11:28 /user/bigdata/nyc_open_data/ia2d-e54m.json
# -rw-rwx---+  3 rpd302 bigdata       83734 2018-04-06 11:28 /user/bigdata/nyc_open_data/ia9u-k3t3.json
# -rw-rwx---+  3 rpd302 bigdata       31380 2018-04-06 11:28 /user/bigdata/nyc_open_data/ibs4-k445.json
# -rw-rwx---+  3 rpd302 bigdata       99834 2018-04-06 11:28 /user/bigdata/nyc_open_data/ic2k-etms.json
# -rw-rwx---+  3 rpd302 bigdata  1666902291 2018-04-06 11:29 /user/bigdata/nyc_open_data/ic3t-wcy2.json
# -rw-rwx---+  3 rpd302 bigdata     4244887 2018-04-06 11:29 /user/bigdata/nyc_open_data/icps-nwdu.json
# -rw-rwx---+  3 rpd302 bigdata       22786 2018-04-06 11:29 /user/bigdata/nyc_open_data/idfb-y78n.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:29 /user/bigdata/nyc_open_data/ie6s-t87j.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:29 /user/bigdata/nyc_open_data/ieyi-rqsn.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:29 /user/bigdata/nyc_open_data/ige5-v6sk.json
# -rw-rwx---+  3 rpd302 bigdata     4038968 2018-04-06 11:29 /user/bigdata/nyc_open_data/ihfw-zy9j.json
# -rw-rwx---+  3 rpd302 bigdata      255364 2018-04-06 11:29 /user/bigdata/nyc_open_data/ihup-vdhf.json
# -rw-rwx---+  3 rpd302 bigdata       15860 2018-04-06 11:29 /user/bigdata/nyc_open_data/ihvw-cp8d.json
# -rw-rwx---+  3 rpd302 bigdata       18023 2018-04-06 11:29 /user/bigdata/nyc_open_data/ii73-cgb4.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:29 /user/bigdata/nyc_open_data/iiv7-jaj9.json
# -rw-rwx---+  3 rpd302 bigdata      884875 2018-04-06 11:29 /user/bigdata/nyc_open_data/ikqj-pyhc.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:29 /user/bigdata/nyc_open_data/ikvd-dex8.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:29 /user/bigdata/nyc_open_data/im58-6hb9.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:29 /user/bigdata/nyc_open_data/infj-99i7.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:29 /user/bigdata/nyc_open_data/ipbu-mtcs.json
# -rw-rwx---+  3 rpd302 bigdata       14861 2018-04-06 11:29 /user/bigdata/nyc_open_data/ipc3-2nbm.json
# -rw-rwx---+  3 rpd302 bigdata       37573 2018-04-06 11:29 /user/bigdata/nyc_open_data/ipsj-8mer.json
# -rw-rwx---+  3 rpd302 bigdata  2470022799 2018-04-06 11:29 /user/bigdata/nyc_open_data/ipu4-2q9a.json
# -rw-rwx---+  3 rpd302 bigdata      837383 2018-04-06 11:29 /user/bigdata/nyc_open_data/irhv-jqz7.json
# -rw-rwx---+  3 rpd302 bigdata       16058 2018-04-06 11:29 /user/bigdata/nyc_open_data/ismp-xffj.json
# -rw-rwx---+  3 rpd302 bigdata       31138 2018-04-06 11:29 /user/bigdata/nyc_open_data/isn9-aw8z.json
# -rw-rwx---+  3 rpd302 bigdata    65484979 2018-04-06 11:29 /user/bigdata/nyc_open_data/it56-eyq4.json
# -rw-rwx---+  3 rpd302 bigdata      540540 2018-04-06 11:29 /user/bigdata/nyc_open_data/it9k-rtx5.json
# -rw-rwx---+  3 rpd302 bigdata       19878 2018-04-06 11:29 /user/bigdata/nyc_open_data/ita7-8em7.json
# -rw-rwx---+  3 rpd302 bigdata    40093472 2018-04-06 11:29 /user/bigdata/nyc_open_data/itd7-gx3g.json
# -rw-rwx---+  3 rpd302 bigdata       64002 2018-04-06 11:29 /user/bigdata/nyc_open_data/itfs-ms3e.json
# -rw-rwx---+  3 rpd302 bigdata      718957 2018-04-06 11:29 /user/bigdata/nyc_open_data/iuvu-z276.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:29 /user/bigdata/nyc_open_data/ivb7-t7a7.json
# -rw-rwx---+  3 rpd302 bigdata       13205 2018-04-06 11:29 /user/bigdata/nyc_open_data/ivbu-e2q7.json
# -rw-rwx---+  3 rpd302 bigdata    12851174 2018-04-06 11:29 /user/bigdata/nyc_open_data/ivix-m77e.json
# -rw-rwx---+  3 rpd302 bigdata      232918 2018-04-06 11:29 /user/bigdata/nyc_open_data/iwdd-99mu.json
# -rw-rwx---+  3 rpd302 bigdata     6948459 2018-04-06 11:29 /user/bigdata/nyc_open_data/iz2q-9x8d.json
# -rw-rwx---+  3 rpd302 bigdata     4757584 2018-04-06 11:29 /user/bigdata/nyc_open_data/izav-3bhy.json
# -rw-rwx---+  3 rpd302 bigdata       39734 2018-04-06 11:29 /user/bigdata/nyc_open_data/j2iz-mwzu.json
# -rw-rwx---+  3 rpd302 bigdata       30469 2018-04-06 11:29 /user/bigdata/nyc_open_data/j2sr-pm3b.json
# -rw-rwx---+  3 rpd302 bigdata      752063 2018-04-06 11:29 /user/bigdata/nyc_open_data/j34j-vqvt.json
# -rw-rwx---+  3 rpd302 bigdata      451103 2018-04-06 11:29 /user/bigdata/nyc_open_data/j39j-zq32.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:29 /user/bigdata/nyc_open_data/j49e-erz3.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:29 /user/bigdata/nyc_open_data/j4t9-dyts.json
# -rw-rwx---+  3 rpd302 bigdata       13575 2018-04-06 11:29 /user/bigdata/nyc_open_data/j7gw-gcxi.json
# -rw-rwx---+  3 rpd302 bigdata       22983 2018-04-06 11:29 /user/bigdata/nyc_open_data/j7wp-ax4x.json
# -rw-rwx---+  3 rpd302 bigdata       40330 2018-04-06 11:29 /user/bigdata/nyc_open_data/j7wr-gf2w.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:29 /user/bigdata/nyc_open_data/j7ww-5ipv.json
# -rw-rwx---+  3 rpd302 bigdata       54214 2018-04-06 11:29 /user/bigdata/nyc_open_data/j7yn-nvq9.json
# -rw-rwx---+  3 rpd302 bigdata      194603 2018-04-06 11:29 /user/bigdata/nyc_open_data/j86k-5i43.json
# -rw-rwx---+  3 rpd302 bigdata       52470 2018-04-06 11:29 /user/bigdata/nyc_open_data/j8gx-kc43.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:29 /user/bigdata/nyc_open_data/j8nm-zs7q.json
# -rw-rwx---+  3 rpd302 bigdata      158772 2018-04-06 11:29 /user/bigdata/nyc_open_data/j8p3-8ufc.json
# -rw-rwx---+  3 rpd302 bigdata       11291 2018-04-06 11:29 /user/bigdata/nyc_open_data/jabk-zf7i.json
# -rw-rwx---+  3 rpd302 bigdata       46697 2018-04-06 11:29 /user/bigdata/nyc_open_data/jat2-irw9.json
# -rw-rwx---+  3 rpd302 bigdata    38934788 2018-04-06 11:29 /user/bigdata/nyc_open_data/jb3k-j3gp.json
# -rw-rwx---+  3 rpd302 bigdata      247632 2018-04-06 11:29 /user/bigdata/nyc_open_data/jb7j-dtam.json
# -rw-rwx---+  3 rpd302 bigdata      469658 2018-04-06 11:29 /user/bigdata/nyc_open_data/jcih-dj9q.json
# -rw-rwx---+  3 rpd302 bigdata       16812 2018-04-06 11:29 /user/bigdata/nyc_open_data/jdmi-whyn.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:29 /user/bigdata/nyc_open_data/jfju-ynrr.json
# -rw-rwx---+  3 rpd302 bigdata       23051 2018-04-06 11:29 /user/bigdata/nyc_open_data/jgjk-h2bn.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:29 /user/bigdata/nyc_open_data/jgqm-ccbd.json
# -rw-rwx---+  3 rpd302 bigdata   211797468 2018-04-06 11:29 /user/bigdata/nyc_open_data/jgtb-hmpg.json
# -rw-rwx---+  3 rpd302 bigdata      346480 2018-04-06 11:29 /user/bigdata/nyc_open_data/jhjm-vsp8.json
# -rw-rwx---+  3 rpd302 bigdata       32535 2018-04-06 11:29 /user/bigdata/nyc_open_data/jhn3-4vdj.json
# -rw-rwx---+  3 rpd302 bigdata       18730 2018-04-06 11:29 /user/bigdata/nyc_open_data/jhq9-vaec.json
# -rw-rwx---+  3 rpd302 bigdata    43210804 2018-04-06 11:29 /user/bigdata/nyc_open_data/ji82-xba5.json
# -rw-rwx---+  3 rpd302 bigdata       35893 2018-04-06 11:29 /user/bigdata/nyc_open_data/jign-uhe6.json
# -rw-rwx---+  3 rpd302 bigdata       89252 2018-04-06 11:29 /user/bigdata/nyc_open_data/jjvq-4t2v.json
# -rw-rwx---+  3 rpd302 bigdata    48960658 2018-04-06 11:29 /user/bigdata/nyc_open_data/jk35-yh5p.json
# -rw-rwx---+  3 rpd302 bigdata       44194 2018-04-06 11:29 /user/bigdata/nyc_open_data/jkiz-wt49.json
# -rw-rwx---+  3 rpd302 bigdata       38345 2018-04-06 11:29 /user/bigdata/nyc_open_data/jmr8-fdbz.json
# -rw-rwx---+  3 rpd302 bigdata       15211 2018-04-06 11:29 /user/bigdata/nyc_open_data/jp7y-czvr.json
# -rw-rwx---+  3 rpd302 bigdata       88522 2018-04-06 11:29 /user/bigdata/nyc_open_data/jphp-xt7k.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:29 /user/bigdata/nyc_open_data/jpib-dv6s.json
# -rw-rwx---+  3 rpd302 bigdata       84912 2018-04-06 11:29 /user/bigdata/nyc_open_data/jqy3-ybjq.json
# -rw-rwx---+  3 rpd302 bigdata   119420115 2018-04-06 11:29 /user/bigdata/nyc_open_data/jr24-e7cr.json
# -rw-rwx---+  3 rpd302 bigdata       33913 2018-04-06 11:29 /user/bigdata/nyc_open_data/jr3e-jwne.json
# -rw-rwx---+  3 rpd302 bigdata  1241334139 2018-04-06 11:30 /user/bigdata/nyc_open_data/jr6k-xwua.json
# -rw-rwx---+  3 rpd302 bigdata       19712 2018-04-06 11:30 /user/bigdata/nyc_open_data/js82-9nvz.json
# -rw-rwx---+  3 rpd302 bigdata  4239383897 2018-04-06 11:30 /user/bigdata/nyc_open_data/jt7v-77mi.json
# -rw-rwx---+  3 rpd302 bigdata       14524 2018-04-06 11:30 /user/bigdata/nyc_open_data/jt9i-9gxr.json
# -rw-rwx---+  3 rpd302 bigdata    74708755 2018-04-06 11:30 /user/bigdata/nyc_open_data/ju3b-rwpy.json
# -rw-rwx---+  3 rpd302 bigdata     6791654 2018-04-06 11:30 /user/bigdata/nyc_open_data/jufi-gzgp.json
# -rw-rwx---+  3 rpd302 bigdata       81025 2018-04-06 11:30 /user/bigdata/nyc_open_data/jvce-szsb.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:30 /user/bigdata/nyc_open_data/jvnx-z9de.json
# -rw-rwx---+  3 rpd302 bigdata       31911 2018-04-06 11:30 /user/bigdata/nyc_open_data/jvqn-dyef.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:30 /user/bigdata/nyc_open_data/jwvp-gyiq.json
# -rw-rwx---+  3 rpd302 bigdata       72385 2018-04-06 11:30 /user/bigdata/nyc_open_data/jxdc-hnze.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:30 /user/bigdata/nyc_open_data/jxmq-5dde.json
# -rw-rwx---+  3 rpd302 bigdata     2722349 2018-04-06 11:30 /user/bigdata/nyc_open_data/jxyc-rxiv.json
# -rw-rwx---+  3 rpd302 bigdata 12406204542 2018-04-06 11:31 /user/bigdata/nyc_open_data/jz4z-kudi.json
# -rw-rwx---+  3 rpd302 bigdata      100931 2018-04-06 11:31 /user/bigdata/nyc_open_data/jzdn-258f.json
# -rw-rwx---+  3 rpd302 bigdata    65415313 2018-04-06 11:31 /user/bigdata/nyc_open_data/jzhd-m6uv.json
# -rw-rwx---+  3 rpd302 bigdata     8159682 2018-04-06 11:31 /user/bigdata/nyc_open_data/jzst-u7j8.json
# -rw-rwx---+  3 rpd302 bigdata      119811 2018-04-06 11:31 /user/bigdata/nyc_open_data/k233-bk49.json
# -rw-rwx---+  3 rpd302 bigdata      361611 2018-04-06 11:31 /user/bigdata/nyc_open_data/k26i-s5bd.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:31 /user/bigdata/nyc_open_data/k2bb-k6p8.json
# -rw-rwx---+  3 rpd302 bigdata     5561054 2018-04-06 11:31 /user/bigdata/nyc_open_data/k2tc-bipg.json
# -rw-rwx---+  3 rpd302 bigdata       37264 2018-04-06 11:31 /user/bigdata/nyc_open_data/k2ye-5mmh.json
# -rw-rwx---+  3 rpd302 bigdata   789683700 2018-04-06 11:32 /user/bigdata/nyc_open_data/k397-673e.json
# -rw-rwx---+  3 rpd302 bigdata    36026219 2018-04-06 11:32 /user/bigdata/nyc_open_data/k3cd-yu9d.json
# -rw-rwx---+  3 rpd302 bigdata       53528 2018-04-06 11:32 /user/bigdata/nyc_open_data/k3e2-emsq.json
# -rw-rwx---+  3 rpd302 bigdata       45593 2018-04-06 11:32 /user/bigdata/nyc_open_data/k3qa-jvkc.json
# -rw-rwx---+  3 rpd302 bigdata      410826 2018-04-06 11:32 /user/bigdata/nyc_open_data/k46n-sa2m.json
# -rw-rwx---+  3 rpd302 bigdata       16366 2018-04-06 11:32 /user/bigdata/nyc_open_data/k4u8-p5ux.json
# -rw-rwx---+  3 rpd302 bigdata      111325 2018-04-06 11:32 /user/bigdata/nyc_open_data/k4xi-fxp5.json
# -rw-rwx---+  3 rpd302 bigdata     1704599 2018-04-06 11:32 /user/bigdata/nyc_open_data/k548-32d3.json
# -rw-rwx---+  3 rpd302 bigdata     2575402 2018-04-06 11:32 /user/bigdata/nyc_open_data/k5us-nav4.json
# -rw-rwx---+  3 rpd302 bigdata       88282 2018-04-06 11:32 /user/bigdata/nyc_open_data/k5ws-xbkn.json
# -rw-rwx---+  3 rpd302 bigdata      102116 2018-04-06 11:32 /user/bigdata/nyc_open_data/k5xr-vi4c.json
# -rw-rwx---+  3 rpd302 bigdata    19433894 2018-04-06 11:32 /user/bigdata/nyc_open_data/k63t-h76x.json
# -rw-rwx---+  3 rpd302 bigdata       28763 2018-04-06 11:32 /user/bigdata/nyc_open_data/k659-gwja.json
# -rw-rwx---+  3 rpd302 bigdata 14821657927 2018-04-06 11:33 /user/bigdata/nyc_open_data/k67s-dv2t.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:33 /user/bigdata/nyc_open_data/k6b6-sdbz.json
# -rw-rwx---+  3 rpd302 bigdata       31807 2018-04-06 11:33 /user/bigdata/nyc_open_data/k72f-2ytm.json
# -rw-rwx---+  3 rpd302 bigdata  7118488246 2018-04-06 11:34 /user/bigdata/nyc_open_data/k7b3-4y4m.json
# -rw-rwx---+  3 rpd302 bigdata      102545 2018-04-06 11:34 /user/bigdata/nyc_open_data/k84j-firu.json
# -rw-rwx---+  3 rpd302 bigdata     1091457 2018-04-06 11:34 /user/bigdata/nyc_open_data/k8hv-56d7.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:34 /user/bigdata/nyc_open_data/k9k7-3cje.json
# -rw-rwx---+  3 rpd302 bigdata       33769 2018-04-06 11:34 /user/bigdata/nyc_open_data/ka27-qx5k.json
# -rw-rwx---+  3 rpd302 bigdata       16098 2018-04-06 11:34 /user/bigdata/nyc_open_data/ka3k-93z7.json
# -rw-rwx---+  3 rpd302 bigdata       35745 2018-04-06 11:34 /user/bigdata/nyc_open_data/kcgr-4dqx.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:34 /user/bigdata/nyc_open_data/kcrm-j9hh.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:34 /user/bigdata/nyc_open_data/kdig-pewd.json
# -rw-rwx---+  3 rpd302 bigdata     6299503 2018-04-06 11:34 /user/bigdata/nyc_open_data/kdm9-vp7d.json
# -rw-rwx---+  3 rpd302 bigdata       45404 2018-04-06 11:34 /user/bigdata/nyc_open_data/kdpk-qekk.json
# -rw-rwx---+  3 rpd302 bigdata     2210187 2018-04-06 11:34 /user/bigdata/nyc_open_data/kdqv-qs7p.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:34 /user/bigdata/nyc_open_data/kdu2-865w.json
# -rw-rwx---+  3 rpd302 bigdata       53451 2018-04-06 11:34 /user/bigdata/nyc_open_data/kewa-q4dq.json
# -rw-rwx---+  3 rpd302 bigdata     2950249 2018-04-06 11:34 /user/bigdata/nyc_open_data/kf2b-aeh5.json
# -rw-rwx---+  3 rpd302 bigdata    51544101 2018-04-06 11:34 /user/bigdata/nyc_open_data/kfgh-h6re.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:34 /user/bigdata/nyc_open_data/kfum-nzw3.json
# -rw-rwx---+  3 rpd302 bigdata      190366 2018-04-06 11:34 /user/bigdata/nyc_open_data/kh2m-kcyz.json
# -rw-rwx---+  3 rpd302 bigdata       87131 2018-04-06 11:34 /user/bigdata/nyc_open_data/kh3d-xhq7.json
# -rw-rwx---+  3 rpd302 bigdata     6277046 2018-04-06 11:34 /user/bigdata/nyc_open_data/kha6-7i9i.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:34 /user/bigdata/nyc_open_data/khkb-h6hx.json
# -rw-rwx---+  3 rpd302 bigdata     5246136 2018-04-06 11:34 /user/bigdata/nyc_open_data/khqi-x3p3.json
# -rw-rwx---+  3 rpd302 bigdata  4978869578 2018-04-06 11:35 /user/bigdata/nyc_open_data/kiv2-tbus.json
# -rw-rwx---+  3 rpd302 bigdata     2276824 2018-04-06 11:35 /user/bigdata/nyc_open_data/kivi-tmb3.json
# -rw-rwx---+  3 rpd302 bigdata      997893 2018-04-06 11:35 /user/bigdata/nyc_open_data/kiyv-ks3f.json
# -rw-rwx---+  3 rpd302 bigdata    98121561 2018-04-06 11:35 /user/bigdata/nyc_open_data/kj4p-ruqc.json
# -rw-rwx---+  3 rpd302 bigdata      184898 2018-04-06 11:35 /user/bigdata/nyc_open_data/kjey-zuvr.json
# -rw-rwx---+  3 rpd302 bigdata      209020 2018-04-06 11:35 /user/bigdata/nyc_open_data/kjgh-ywbx.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:35 /user/bigdata/nyc_open_data/kjk4-7tzy.json
# -rw-rwx---+  3 rpd302 bigdata     1012016 2018-04-06 11:35 /user/bigdata/nyc_open_data/kjpz-79mu.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:35 /user/bigdata/nyc_open_data/kjtf-e6kp.json
# -rw-rwx---+  3 rpd302 bigdata       64804 2018-04-06 11:35 /user/bigdata/nyc_open_data/kjxa-7ccf.json
# -rw-rwx---+  3 rpd302 bigdata       19813 2018-04-06 11:35 /user/bigdata/nyc_open_data/kk22-kcb6.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:35 /user/bigdata/nyc_open_data/kkjw-ny95.json
# -rw-rwx---+  3 rpd302 bigdata      151959 2018-04-06 11:35 /user/bigdata/nyc_open_data/kku6-nxdu.json
# -rw-rwx---+  3 rpd302 bigdata       15321 2018-04-06 11:35 /user/bigdata/nyc_open_data/kkwv-djnk.json
# -rw-rwx---+  3 rpd302 bigdata     5489737 2018-04-06 11:35 /user/bigdata/nyc_open_data/kmix-7hhj.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:35 /user/bigdata/nyc_open_data/kmt4-jkta.json
# -rw-rwx---+  3 rpd302 bigdata     4358239 2018-04-06 11:35 /user/bigdata/nyc_open_data/kn9i-9q8m.json
# -rw-rwx---+  3 rpd302 bigdata   137889336 2018-04-06 11:35 /user/bigdata/nyc_open_data/knik-dax9.json
# -rw-rwx---+  3 rpd302 bigdata    18647449 2018-04-06 11:35 /user/bigdata/nyc_open_data/kpav-sd4t.json
# -rw-rwx---+  3 rpd302 bigdata      134688 2018-04-06 11:35 /user/bigdata/nyc_open_data/kpjg-ubxi.json
# -rw-rwx---+  3 rpd302 bigdata       15997 2018-04-06 11:35 /user/bigdata/nyc_open_data/kq8c-w9ag.json
# -rw-rwx---+  3 rpd302 bigdata      283799 2018-04-06 11:35 /user/bigdata/nyc_open_data/kquf-ewd9.json
# -rw-rwx---+  3 rpd302 bigdata       56650 2018-04-06 11:35 /user/bigdata/nyc_open_data/krwf-eng6.json
# -rw-rwx---+  3 rpd302 bigdata     7005026 2018-04-06 11:35 /user/bigdata/nyc_open_data/krx7-u82t.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:35 /user/bigdata/nyc_open_data/ks56-wyey.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:35 /user/bigdata/nyc_open_data/ksfe-nc8x.json
# -rw-rwx---+  3 rpd302 bigdata      120470 2018-04-06 11:35 /user/bigdata/nyc_open_data/kt29-ab5k.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:35 /user/bigdata/nyc_open_data/kubx-z7zd.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:35 /user/bigdata/nyc_open_data/kvfi-kxcq.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:35 /user/bigdata/nyc_open_data/kvuc-fg9b.json
# -rw-rwx---+  3 rpd302 bigdata    66257116 2018-04-06 11:35 /user/bigdata/nyc_open_data/kw9y-h36n.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:35 /user/bigdata/nyc_open_data/kwk4-6u9e.json
# -rw-rwx---+  3 rpd302 bigdata    28872442 2018-04-06 11:35 /user/bigdata/nyc_open_data/kwmq-dbub.json
# -rw-rwx---+  3 rpd302 bigdata   831963378 2018-04-06 11:35 /user/bigdata/nyc_open_data/kwte-dppd.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:35 /user/bigdata/nyc_open_data/kxg8-856s.json
# -rw-rwx---+  3 rpd302 bigdata   251035280 2018-04-06 11:35 /user/bigdata/nyc_open_data/kyad-zm4j.json
# -rw-rwx---+  3 rpd302 bigdata       19960 2018-04-06 11:35 /user/bigdata/nyc_open_data/kydh-ijhc.json
# -rw-rwx---+  3 rpd302 bigdata    37692301 2018-04-06 11:35 /user/bigdata/nyc_open_data/kyvb-rbwd.json
# -rw-rwx---+  3 rpd302 bigdata    13000131 2018-04-06 11:35 /user/bigdata/nyc_open_data/m3fi-rt3k.json
# -rw-rwx---+  3 rpd302 bigdata       39654 2018-04-06 11:35 /user/bigdata/nyc_open_data/m48u-yjt8.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:35 /user/bigdata/nyc_open_data/m4mp-ji5y.json
# -rw-rwx---+  3 rpd302 bigdata     2903080 2018-04-06 11:35 /user/bigdata/nyc_open_data/m56g-jpua.json
# -rw-rwx---+  3 rpd302 bigdata      357542 2018-04-06 11:35 /user/bigdata/nyc_open_data/m59i-mqex.json
# -rw-rwx---+  3 rpd302 bigdata       57304 2018-04-06 11:35 /user/bigdata/nyc_open_data/m64p-r9hk.json
# -rw-rwx---+  3 rpd302 bigdata   139878456 2018-04-06 11:35 /user/bigdata/nyc_open_data/m666-sf2m.json
# -rw-rwx---+  3 rpd302 bigdata       61121 2018-04-06 11:35 /user/bigdata/nyc_open_data/m6ap-zcwi.json
# -rw-rwx---+  3 rpd302 bigdata        8887 2018-04-06 11:35 /user/bigdata/nyc_open_data/m6nh-ye6v.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:35 /user/bigdata/nyc_open_data/m7f5-x3k4.json
# -rw-rwx---+  3 rpd302 bigdata       19111 2018-04-06 11:35 /user/bigdata/nyc_open_data/m7m9-uyrn.json
# -rw-rwx---+  3 rpd302 bigdata    12105590 2018-04-06 11:35 /user/bigdata/nyc_open_data/m8nr-4ivu.json
# -rw-rwx---+  3 rpd302 bigdata      262144 2018-04-06 11:35 /user/bigdata/nyc_open_data/ma5g-2458.json
# -rw-rwx---+  3 rpd302 bigdata   115530015 2018-04-06 11:35 /user/bigdata/nyc_open_data/madj-gkhr.json
# -rw-rwx---+  3 rpd302 bigdata       28842 2018-04-06 11:35 /user/bigdata/nyc_open_data/mai7-g3fm.json
# -rw-rwx---+  3 rpd302 bigdata      930453 2018-04-06 11:35 /user/bigdata/nyc_open_data/mbd7-jfnc.json
# -rw-rwx---+  3 rpd302 bigdata       60743 2018-04-06 11:35 /user/bigdata/nyc_open_data/mbym-vp3s.json
# -rw-rwx---+  3 rpd302 bigdata   188983026 2018-04-06 11:35 /user/bigdata/nyc_open_data/mdbu-nrqn.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:35 /user/bigdata/nyc_open_data/mdcr-pn8p.json
# -rw-rwx---+  3 rpd302 bigdata     1963440 2018-04-06 11:35 /user/bigdata/nyc_open_data/mdcw-n682.json
# -rw-rwx---+  3 rpd302 bigdata      147524 2018-04-06 11:35 /user/bigdata/nyc_open_data/memx-xuna.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:35 /user/bigdata/nyc_open_data/meug-f4mb.json
# -rw-rwx---+  3 rpd302 bigdata       62382 2018-04-06 11:35 /user/bigdata/nyc_open_data/mfmf-gtvc.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:35 /user/bigdata/nyc_open_data/mg79-yih5.json
# -rw-rwx---+  3 rpd302 bigdata        8649 2018-04-06 11:35 /user/bigdata/nyc_open_data/mgjt-zuui.json
# -rw-rwx---+  3 rpd302 bigdata       65986 2018-04-06 11:35 /user/bigdata/nyc_open_data/mi8r-ff2q.json
# -rw-rwx---+  3 rpd302 bigdata    13832688 2018-04-06 11:35 /user/bigdata/nyc_open_data/mib5-bwqy.json
# -rw-rwx---+  3 rpd302 bigdata      582460 2018-04-06 11:35 /user/bigdata/nyc_open_data/mifw-tguq.json
# -rw-rwx---+  3 rpd302 bigdata       15890 2018-04-06 11:35 /user/bigdata/nyc_open_data/miqs-rvtb.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:35 /user/bigdata/nyc_open_data/miz8-534t.json
# -rw-rwx---+  3 rpd302 bigdata       18501 2018-04-06 11:35 /user/bigdata/nyc_open_data/mkxg-y5uc.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:35 /user/bigdata/nyc_open_data/mm69-vrje.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:35 /user/bigdata/nyc_open_data/mmu8-8w8b.json
# -rw-rwx---+  3 rpd302 bigdata     2592813 2018-04-06 11:35 /user/bigdata/nyc_open_data/mmvm-mvi3.json
# -rw-rwx---+  3 rpd302 bigdata       28806 2018-04-06 11:35 /user/bigdata/nyc_open_data/mnqg-rcee.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:35 /user/bigdata/nyc_open_data/mnz3-dyi8.json
# -rw-rwx---+  3 rpd302 bigdata       14730 2018-04-06 11:35 /user/bigdata/nyc_open_data/mpg8-b8s5.json
# -rw-rwx---+  3 rpd302 bigdata     4890785 2018-04-06 11:35 /user/bigdata/nyc_open_data/mpk5-48av.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:35 /user/bigdata/nyc_open_data/mpmk-b5ed.json
# -rw-rwx---+  3 rpd302 bigdata        9310 2018-04-06 11:35 /user/bigdata/nyc_open_data/mpqk-skis.json
# -rw-rwx---+  3 rpd302 bigdata      254481 2018-04-06 11:35 /user/bigdata/nyc_open_data/mq6n-s45c.json
# -rw-rwx---+  3 rpd302 bigdata       96587 2018-04-06 11:35 /user/bigdata/nyc_open_data/mqd6-mvf7.json
# -rw-rwx---+  3 rpd302 bigdata      883006 2018-04-06 11:35 /user/bigdata/nyc_open_data/mqdy-gu73.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:35 /user/bigdata/nyc_open_data/mran-v46w.json
# -rw-rwx---+  3 rpd302 bigdata      114267 2018-04-06 11:35 /user/bigdata/nyc_open_data/mrxb-9w9v.json
# -rw-rwx---+  3 rpd302 bigdata       39200 2018-04-06 11:35 /user/bigdata/nyc_open_data/ms66-xjfq.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:35 /user/bigdata/nyc_open_data/mshx-yvwq.json
# -rw-rwx---+  3 rpd302 bigdata       37932 2018-04-06 11:35 /user/bigdata/nyc_open_data/mtfg-8ayp.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:35 /user/bigdata/nyc_open_data/mthv-t59m.json
# -rw-rwx---+  3 rpd302 bigdata       38091 2018-04-06 11:35 /user/bigdata/nyc_open_data/mu2n-2qpd.json
# -rw-rwx---+  3 rpd302 bigdata   251468275 2018-04-06 11:35 /user/bigdata/nyc_open_data/mu46-p9is.json
# -rw-rwx---+  3 rpd302 bigdata       17986 2018-04-06 11:35 /user/bigdata/nyc_open_data/mumm-6t9n.json
# -rw-rwx---+  3 rpd302 bigdata        9829 2018-04-06 11:35 /user/bigdata/nyc_open_data/mvhn-ypfv.json
# -rw-rwx---+  3 rpd302 bigdata   284735496 2018-04-06 11:35 /user/bigdata/nyc_open_data/mwbr-9zz9.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:35 /user/bigdata/nyc_open_data/mwxp-krtu.json
# -rw-rwx---+  3 rpd302 bigdata    76307509 2018-04-06 11:35 /user/bigdata/nyc_open_data/mwzb-yiwb.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:35 /user/bigdata/nyc_open_data/mx2v-5myb.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:35 /user/bigdata/nyc_open_data/mxbm-493w.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:35 /user/bigdata/nyc_open_data/mxwn-eh3b.json
# -rw-rwx---+  3 rpd302 bigdata      715584 2018-04-06 11:35 /user/bigdata/nyc_open_data/my4g-bvvs.json
# -rw-rwx---+  3 rpd302 bigdata       49913 2018-04-06 11:35 /user/bigdata/nyc_open_data/myn9-hwsy.json
# -rw-rwx---+  3 rpd302 bigdata    28017422 2018-04-06 11:35 /user/bigdata/nyc_open_data/myrj-umam.json
# -rw-rwx---+  3 rpd302 bigdata     2019501 2018-04-06 11:35 /user/bigdata/nyc_open_data/myrx-addi.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:35 /user/bigdata/nyc_open_data/mzbd-kucq.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:35 /user/bigdata/nyc_open_data/mzpm-a6vd.json
# -rw-rwx---+  3 rpd302 bigdata       65662 2018-04-06 11:35 /user/bigdata/nyc_open_data/mzrr-g56e.json
# -rw-rwx---+  3 rpd302 bigdata       18229 2018-04-06 11:35 /user/bigdata/nyc_open_data/mzy5-smmw.json
# -rw-rwx---+  3 rpd302 bigdata       43707 2018-04-06 11:35 /user/bigdata/nyc_open_data/n246-cev5.json
# -rw-rwx---+  3 rpd302 bigdata      118335 2018-04-06 11:35 /user/bigdata/nyc_open_data/n2s5-fumm.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:35 /user/bigdata/nyc_open_data/n3et-mfjw.json
# -rw-rwx---+  3 rpd302 bigdata     1684190 2018-04-06 11:35 /user/bigdata/nyc_open_data/n3p6-zve2.json
# -rw-rwx---+  3 rpd302 bigdata  2173423621 2018-04-06 11:36 /user/bigdata/nyc_open_data/n4kn-dy2y.json
# -rw-rwx---+  3 rpd302 bigdata      459147 2018-04-06 11:36 /user/bigdata/nyc_open_data/n4tc-j6kh.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:36 /user/bigdata/nyc_open_data/n5e5-z493.json
# -rw-rwx---+  3 rpd302 bigdata     7929882 2018-04-06 11:36 /user/bigdata/nyc_open_data/n5mv-nfpy.json
# -rw-rwx---+  3 rpd302 bigdata       64261 2018-04-06 11:36 /user/bigdata/nyc_open_data/n5xc-7jfa.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:36 /user/bigdata/nyc_open_data/n7nh-rhic.json
# -rw-rwx---+  3 rpd302 bigdata       12396 2018-04-06 11:36 /user/bigdata/nyc_open_data/n7ta-pz8k.json
# -rw-rwx---+  3 rpd302 bigdata   122459338 2018-04-06 11:36 /user/bigdata/nyc_open_data/n8p9-7jxp.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:36 /user/bigdata/nyc_open_data/n927-2nn8.json
# -rw-rwx---+  3 rpd302 bigdata      352500 2018-04-06 11:36 /user/bigdata/nyc_open_data/n9yn-6q3f.json
# -rw-rwx---+  3 rpd302 bigdata     1027686 2018-04-06 11:36 /user/bigdata/nyc_open_data/narn-kyx4.json
# -rw-rwx---+  3 rpd302 bigdata  2350933812 2018-04-06 11:36 /user/bigdata/nyc_open_data/nbbg-wtuz.json
# -rw-rwx---+  3 rpd302 bigdata      614328 2018-04-06 11:36 /user/bigdata/nyc_open_data/nbgq-j9jt.json
# -rw-rwx---+  3 rpd302 bigdata       56816 2018-04-06 11:36 /user/bigdata/nyc_open_data/nbun-a9vi.json
# -rw-rwx---+  3 rpd302 bigdata 10994276799 2018-04-06 11:37 /user/bigdata/nyc_open_data/nc67-uf89.json
# -rw-rwx---+  3 rpd302 bigdata       32588 2018-04-06 11:37 /user/bigdata/nyc_open_data/ncbg-6agr.json
# -rw-rwx---+  3 rpd302 bigdata       28673 2018-04-06 11:37 /user/bigdata/nyc_open_data/nd82-bi9f.json
# -rw-rwx---+  3 rpd302 bigdata       80308 2018-04-06 11:37 /user/bigdata/nyc_open_data/ne9f-g6k4.json
# -rw-rwx---+  3 rpd302 bigdata       75208 2018-04-06 11:37 /user/bigdata/nyc_open_data/ne9z-skhf.json
# -rw-rwx---+  3 rpd302 bigdata     2278914 2018-04-06 11:37 /user/bigdata/nyc_open_data/nekg-b6tw.json
# -rw-rwx---+  3 rpd302 bigdata     1553481 2018-04-06 11:37 /user/bigdata/nyc_open_data/nfkx-wd79.json
# -rw-rwx---+  3 rpd302 bigdata       42107 2018-04-06 11:37 /user/bigdata/nyc_open_data/nfz9-tzba.json
# -rw-rwx---+  3 rpd302 bigdata       47366 2018-04-06 11:37 /user/bigdata/nyc_open_data/ngbi-cq85.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:37 /user/bigdata/nyc_open_data/ngew-r755.json
# -rw-rwx---+  3 rpd302 bigdata       11847 2018-04-06 11:37 /user/bigdata/nyc_open_data/ngf9-zejg.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:37 /user/bigdata/nyc_open_data/nieh-77cs.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:37 /user/bigdata/nyc_open_data/niuh-hrin.json
# -rw-rwx---+  3 rpd302 bigdata     2735683 2018-04-06 11:37 /user/bigdata/nyc_open_data/niy5-4j7q.json
# -rw-rwx---+  3 rpd302 bigdata       15092 2018-04-06 11:37 /user/bigdata/nyc_open_data/niyd-ckq3.json
# -rw-rwx---+  3 rpd302 bigdata   104239345 2018-04-06 11:37 /user/bigdata/nyc_open_data/nj5b-z2hw.json
# -rw-rwx---+  3 rpd302 bigdata       51716 2018-04-06 11:37 /user/bigdata/nyc_open_data/nja7-3m37.json
# -rw-rwx---+  3 rpd302 bigdata      305281 2018-04-06 11:37 /user/bigdata/nyc_open_data/nk42-j6hc.json
# -rw-rwx---+  3 rpd302 bigdata       26125 2018-04-06 11:37 /user/bigdata/nyc_open_data/nkn9-ge6x.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:37 /user/bigdata/nyc_open_data/nmqv-xfsc.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:37 /user/bigdata/nyc_open_data/nn5y-wmuj.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:37 /user/bigdata/nyc_open_data/nn83-afrt.json
# -rw-rwx---+  3 rpd302 bigdata    10254702 2018-04-06 11:37 /user/bigdata/nyc_open_data/np9k-hd4i.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:37 /user/bigdata/nyc_open_data/nqwf-w8eh.json
# -rw-rwx---+  3 rpd302 bigdata       32545 2018-04-06 11:37 /user/bigdata/nyc_open_data/nr9n-yqxr.json
# -rw-rwx---+  3 rpd302 bigdata     1346095 2018-04-06 11:37 /user/bigdata/nyc_open_data/nre2-6m2s.json
# -rw-rwx---+  3 rpd302 bigdata       12999 2018-04-06 11:37 /user/bigdata/nyc_open_data/ns22-2dcm.json
# -rw-rwx---+  3 rpd302 bigdata       38698 2018-04-06 11:37 /user/bigdata/nyc_open_data/nstm-kb7u.json
# -rw-rwx---+  3 rpd302 bigdata       45952 2018-04-06 11:37 /user/bigdata/nyc_open_data/ntbr-wib6.json
# -rw-rwx---+  3 rpd302 bigdata       45660 2018-04-06 11:37 /user/bigdata/nyc_open_data/ntcm-2w4k.json
# -rw-rwx---+  3 rpd302 bigdata       17637 2018-04-06 11:37 /user/bigdata/nyc_open_data/nthg-fsts.json
# -rw-rwx---+  3 rpd302 bigdata    34970892 2018-04-06 11:37 /user/bigdata/nyc_open_data/nu7n-tubp.json
# -rw-rwx---+  3 rpd302 bigdata       27782 2018-04-06 11:37 /user/bigdata/nyc_open_data/nufv-bxfc.json
# -rw-rwx---+  3 rpd302 bigdata     2494977 2018-04-06 11:37 /user/bigdata/nyc_open_data/nurr-mhyi.json
# -rw-rwx---+  3 rpd302 bigdata       21762 2018-04-06 11:37 /user/bigdata/nyc_open_data/nuxu-5fjs.json
# -rw-rwx---+  3 rpd302 bigdata    16683348 2018-04-06 11:37 /user/bigdata/nyc_open_data/nvgj-hbht.json
# -rw-rwx---+  3 rpd302 bigdata       36884 2018-04-06 11:37 /user/bigdata/nyc_open_data/nvm3-w2i6.json
# -rw-rwx---+  3 rpd302 bigdata      343296 2018-04-06 11:37 /user/bigdata/nyc_open_data/nvqd-aa32.json
# -rw-rwx---+  3 rpd302 bigdata        8972 2018-04-06 11:37 /user/bigdata/nyc_open_data/nwet-nc6h.json
# -rw-rwx---+  3 rpd302 bigdata      273653 2018-04-06 11:37 /user/bigdata/nyc_open_data/nwrb-z58j.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:37 /user/bigdata/nyc_open_data/nx9f-wn3a.json
# -rw-rwx---+  3 rpd302 bigdata      123403 2018-04-06 11:37 /user/bigdata/nyc_open_data/ny8v-zzzb.json
# -rw-rwx---+  3 rpd302 bigdata    17905038 2018-04-06 11:37 /user/bigdata/nyc_open_data/nyis-y4yr.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:37 /user/bigdata/nyc_open_data/nzih-r6xb.json
# -rw-rwx---+  3 rpd302 bigdata     2268601 2018-04-06 11:37 /user/bigdata/nyc_open_data/nzjr-3966.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:37 /user/bigdata/nyc_open_data/nzvw-cjc2.json
# -rw-rwx---+  3 rpd302 bigdata       13087 2018-04-06 11:37 /user/bigdata/nyc_open_data/p26e-k6k9.json
# -rw-rwx---+  3 rpd302 bigdata       26060 2018-04-06 11:37 /user/bigdata/nyc_open_data/p2q7-at72.json
# -rw-rwx---+  3 rpd302 bigdata      137025 2018-04-06 11:37 /user/bigdata/nyc_open_data/p2x5-udz8.json
# -rw-rwx---+  3 rpd302 bigdata    24851411 2018-04-06 11:37 /user/bigdata/nyc_open_data/p32s-yqxq.json
# -rw-rwx---+  3 rpd302 bigdata      251958 2018-04-06 11:37 /user/bigdata/nyc_open_data/p39r-nm7f.json
# -rw-rwx---+  3 rpd302 bigdata    15526630 2018-04-06 11:37 /user/bigdata/nyc_open_data/p3r6-jdne.json
# -rw-rwx---+  3 rpd302 bigdata     2713970 2018-04-06 11:37 /user/bigdata/nyc_open_data/p424-amsu.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:37 /user/bigdata/nyc_open_data/p4pf-fyc4.json
# -rw-rwx---+  3 rpd302 bigdata      149789 2018-04-06 11:37 /user/bigdata/nyc_open_data/p5v2-fwzn.json
# -rw-rwx---+  3 rpd302 bigdata       72410 2018-04-06 11:37 /user/bigdata/nyc_open_data/p5w7-g72z.json
# -rw-rwx---+  3 rpd302 bigdata      404281 2018-04-06 11:37 /user/bigdata/nyc_open_data/p6bh-gqsg.json
# -rw-rwx---+  3 rpd302 bigdata     1662053 2018-04-06 11:37 /user/bigdata/nyc_open_data/p6h4-mpyy.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:37 /user/bigdata/nyc_open_data/p84r-8kqf.json
# -rw-rwx---+  3 rpd302 bigdata       15761 2018-04-06 11:37 /user/bigdata/nyc_open_data/p8e4-uwuv.json
# -rw-rwx---+  3 rpd302 bigdata   622412292 2018-04-06 11:37 /user/bigdata/nyc_open_data/p937-wjvj.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:37 /user/bigdata/nyc_open_data/p94q-8hxh.json
# -rw-rwx---+  3 rpd302 bigdata      825695 2018-04-06 11:37 /user/bigdata/nyc_open_data/p9cr-nt9j.json
# -rw-rwx---+  3 rpd302 bigdata       15553 2018-04-06 11:38 /user/bigdata/nyc_open_data/pa5t-ktd3.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:38 /user/bigdata/nyc_open_data/pask-bcmz.json
# -rw-rwx---+  3 rpd302 bigdata     1709898 2018-04-06 11:38 /user/bigdata/nyc_open_data/pasr-j7fb.json
# -rw-rwx---+  3 rpd302 bigdata     8623066 2018-04-06 11:38 /user/bigdata/nyc_open_data/pba9-2xiu.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:38 /user/bigdata/nyc_open_data/pbi9-jd5i.json
# -rw-rwx---+  3 rpd302 bigdata       71546 2018-04-06 11:38 /user/bigdata/nyc_open_data/pc34-d3sx.json
# -rw-rwx---+  3 rpd302 bigdata       18199 2018-04-06 11:38 /user/bigdata/nyc_open_data/pc4g-yqvf.json
# -rw-rwx---+  3 rpd302 bigdata       39252 2018-04-06 11:38 /user/bigdata/nyc_open_data/pcgw-s47c.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:38 /user/bigdata/nyc_open_data/pckb-8r2z.json
# -rw-rwx---+  3 rpd302 bigdata       54606 2018-04-06 11:38 /user/bigdata/nyc_open_data/pd5h-92mc.json
# -rw-rwx---+  3 rpd302 bigdata     2400359 2018-04-06 11:38 /user/bigdata/nyc_open_data/pdiy-9ae5.json
# -rw-rwx---+  3 rpd302 bigdata       63289 2018-04-06 11:38 /user/bigdata/nyc_open_data/pe54-wf39.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:38 /user/bigdata/nyc_open_data/pf5b-73bw.json
# -rw-rwx---+  3 rpd302 bigdata        8189 2018-04-06 11:38 /user/bigdata/nyc_open_data/pf7i-ims3.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:38 /user/bigdata/nyc_open_data/pf9y-ef2p.json
# -rw-rwx---+  3 rpd302 bigdata       20412 2018-04-06 11:38 /user/bigdata/nyc_open_data/pfbw-d97h.json
# -rw-rwx---+  3 rpd302 bigdata   145786529 2018-04-06 11:38 /user/bigdata/nyc_open_data/pffu-gbfi.json
# -rw-rwx---+  3 rpd302 bigdata       51539 2018-04-06 11:38 /user/bigdata/nyc_open_data/pfn4-vjwr.json
# -rw-rwx---+  3 rpd302 bigdata       55905 2018-04-06 11:38 /user/bigdata/nyc_open_data/pfys-fabf.json
# -rw-rwx---+  3 rpd302 bigdata     1250195 2018-04-06 11:38 /user/bigdata/nyc_open_data/pgrs-2cjd.json
# -rw-rwx---+  3 rpd302 bigdata      897160 2018-04-06 11:38 /user/bigdata/nyc_open_data/pgun-i6u7.json
# -rw-rwx---+  3 rpd302 bigdata       17993 2018-04-06 11:38 /user/bigdata/nyc_open_data/ph29-5mxy.json
# -rw-rwx---+  3 rpd302 bigdata       41074 2018-04-06 11:38 /user/bigdata/nyc_open_data/ph5g-sr3v.json
# -rw-rwx---+  3 rpd302 bigdata      276342 2018-04-06 11:38 /user/bigdata/nyc_open_data/ph76-k6qa.json
# -rw-rwx---+  3 rpd302 bigdata      737885 2018-04-06 11:38 /user/bigdata/nyc_open_data/ph7v-u5f3.json
# -rw-rwx---+  3 rpd302 bigdata    14121232 2018-04-06 11:38 /user/bigdata/nyc_open_data/phth-xf25.json
# -rw-rwx---+  3 rpd302 bigdata       13047 2018-04-06 11:38 /user/bigdata/nyc_open_data/pi4j-9c8t.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:38 /user/bigdata/nyc_open_data/pi5s-9p35.json
# -rw-rwx---+  3 rpd302 bigdata      647438 2018-04-06 11:38 /user/bigdata/nyc_open_data/piri-jns7.json
# -rw-rwx---+  3 rpd302 bigdata     2359133 2018-04-06 11:38 /user/bigdata/nyc_open_data/pknx-dgka.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:38 /user/bigdata/nyc_open_data/pn7c-bqri.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:38 /user/bigdata/nyc_open_data/pnij-y7y6.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:38 /user/bigdata/nyc_open_data/pnru-8qsf.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:38 /user/bigdata/nyc_open_data/pp5b-95kq.json
# -rw-rwx---+  3 rpd302 bigdata    78183531 2018-04-06 11:38 /user/bigdata/nyc_open_data/pq5i-thsu.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:38 /user/bigdata/nyc_open_data/pqb7-6q2k.json
# -rw-rwx---+  3 rpd302 bigdata       36575 2018-04-06 11:38 /user/bigdata/nyc_open_data/pqbh-p6xe.json
# -rw-rwx---+  3 rpd302 bigdata     1262673 2018-04-06 11:38 /user/bigdata/nyc_open_data/pqg4-dm6b.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:38 /user/bigdata/nyc_open_data/pr5n-ucgi.json
# -rw-rwx---+  3 rpd302 bigdata    12130874 2018-04-06 1


# # 04-06 11:38 /user/bigdata/nyc_open_data/piri-jns7.json
# # -rw-rwx---+  3 rpd302 bigdata     2359133 2018-04-06 11:38 /user/bigdata/nyc_open_data/pknx-dgka.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:38 /user/bigdata/nyc_open_data/pn7c-bqri.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:38 /user/bigdata/nyc_open_data/pnij-y7y6.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:38 /user/bigdata/nyc_open_data/pnru-8qsf.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:38 /user/bigdata/nyc_open_data/pp5b-95kq.json
# # -rw-rwx---+  3 rpd302 bigdata    78183531 2018-04-06 11:38 /user/bigdata/nyc_open_data/pq5i-thsu.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:38 /user/bigdata/nyc_open_data/pqb7-6q2k.json
# # -rw-rwx---+  3 rpd302 bigdata       36575 2018-04-06 11:38 /user/bigdata/nyc_open_data/pqbh-p6xe.json
# # -rw-rwx---+  3 rpd302 bigdata     1262673 2018-04-06 11:38 /user/bigdata/nyc_open_data/pqg4-dm6b.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:38 /user/bigdata/nyc_open_data/pr5n-ucgi.json
# # -rw-rwx---+  3 rpd302 bigdata    12130874 2018-04-06 11:38 /user/bigdata/nyc_open_data/pra5-xxvj.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:38 /user/bigdata/nyc_open_data/psde-rqze.json
# # -rw-rwx---+  3 rpd302 bigdata       17980 2018-04-06 11:38 /user/bigdata/nyc_open_data/psmp-cmuu.json
# # -rw-rwx---+  3 rpd302 bigdata  1077097254 2018-04-06 11:38 /user/bigdata/nyc_open_data/psqs-brte.json
# # -rw-rwx---+  3 rpd302 bigdata    92548708 2018-04-06 11:38 /user/bigdata/nyc_open_data/ptev-4hud.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:38 /user/bigdata/nyc_open_data/pv8j-5ywy.json
# # -rw-rwx---+  3 rpd302 bigdata  5524280015 2018-04-06 11:38 /user/bigdata/nyc_open_data/pvkv-25ck.json
# # -rw-rwx---+  3 rpd302 bigdata  3580291472 2018-04-06 11:39 /user/bigdata/nyc_open_data/pvqr-7yc4.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:39 /user/bigdata/nyc_open_data/pwhj-ikym.json
# # -rw-rwx---+  3 rpd302 bigdata  1284365572 2018-04-06 11:39 /user/bigdata/nyc_open_data/pwkr-dpni.json
# # -rw-rwx---+  3 rpd302 bigdata    13999244 2018-04-06 11:39 /user/bigdata/nyc_open_data/pxfd-dpcz.json
# # -rw-rwx---+  3 rpd302 bigdata       58862 2018-04-06 11:39 /user/bigdata/nyc_open_data/pyif-r8qe.json
# # -rw-rwx---+  3 rpd302 bigdata       33326 2018-04-06 11:39 /user/bigdata/nyc_open_data/pzqy-pk76.json
# # -rw-rwx---+  3 rpd302 bigdata      997604 2018-04-06 11:39 /user/bigdata/nyc_open_data/pzt3-tne9.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:39 /user/bigdata/nyc_open_data/pzz2-ca2q.json
# # -rw-rwx---+  3 rpd302 bigdata    21353645 2018-04-06 11:39 /user/bigdata/nyc_open_data/q2ni-ztsb.json
# # -rw-rwx---+  3 rpd302 bigdata     1601864 2018-04-06 11:39 /user/bigdata/nyc_open_data/q39e-7gbs.json
# # -rw-rwx---+  3 rpd302 bigdata    11764823 2018-04-06 11:39 /user/bigdata/nyc_open_data/q5hp-72f8.json
# # -rw-rwx---+  3 rpd302 bigdata       86789 2018-04-06 11:39 /user/bigdata/nyc_open_data/q5x3-7piv.json
# # -rw-rwx---+  3 rpd302 bigdata      408163 2018-04-06 11:39 /user/bigdata/nyc_open_data/q5za-zqz7.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:39 /user/bigdata/nyc_open_data/q663-gvx6.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:39 /user/bigdata/nyc_open_data/q68s-8qxv.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:39 /user/bigdata/nyc_open_data/q6ei-tvmg.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:39 /user/bigdata/nyc_open_data/q6p5-m7xb.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:39 /user/bigdata/nyc_open_data/q7kr-hyux.json
# # -rw-rwx---+  3 rpd302 bigdata      315341 2018-04-06 11:39 /user/bigdata/nyc_open_data/q7r2-64fm.json
# # -rw-rwx---+  3 rpd302 bigdata      233323 2018-04-06 11:39 /user/bigdata/nyc_open_data/q7ra-ebu4.json
# # -rw-rwx---+  3 rpd302 bigdata      103583 2018-04-06 11:39 /user/bigdata/nyc_open_data/q8fg-j5sk.json
# # -rw-rwx---+  3 rpd302 bigdata      182646 2018-04-06 11:39 /user/bigdata/nyc_open_data/q974-2uuf.json
# # -rw-rwx---+  3 rpd302 bigdata        9293 2018-04-06 11:39 /user/bigdata/nyc_open_data/q9kp-jvxv.json
# # -rw-rwx---+  3 rpd302 bigdata      143438 2018-04-06 11:39 /user/bigdata/nyc_open_data/q9mx-gjyn.json
# # -rw-rwx---+  3 rpd302 bigdata       77099 2018-04-06 11:39 /user/bigdata/nyc_open_data/q9rw-qihz.json
# # -rw-rwx---+  3 rpd302 bigdata      295059 2018-04-06 11:39 /user/bigdata/nyc_open_data/qa4d-xc73.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:39 /user/bigdata/nyc_open_data/qafz-7myz.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:39 /user/bigdata/nyc_open_data/qb3k-n8mm.json
# # -rw-rwx---+  3 rpd302 bigdata      142588 2018-04-06 11:39 /user/bigdata/nyc_open_data/qb86-fg8z.json
# # -rw-rwx---+  3 rpd302 bigdata      534674 2018-04-06 11:39 /user/bigdata/nyc_open_data/qbce-2kcu.json
# # -rw-rwx---+  3 rpd302 bigdata      105052 2018-04-06 11:39 /user/bigdata/nyc_open_data/qbjq-atxv.json
# # -rw-rwx---+  3 rpd302 bigdata       94189 2018-04-06 11:39 /user/bigdata/nyc_open_data/qbvv-9nzz.json
# # -rw-rwx---+  3 rpd302 bigdata       28500 2018-04-06 11:39 /user/bigdata/nyc_open_data/qc6h-hbw3.json
# # -rw-rwx---+  3 rpd302 bigdata     1367967 2018-04-06 11:39 /user/bigdata/nyc_open_data/qcdj-rwhu.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:39 /user/bigdata/nyc_open_data/qd3c-zuu7.json
# # -rw-rwx---+  3 rpd302 bigdata      307111 2018-04-06 11:39 /user/bigdata/nyc_open_data/qd93-w582.json
# # -rw-rwx---+  3 rpd302 bigdata     2281985 2018-04-06 11:39 /user/bigdata/nyc_open_data/qd9w-yz23.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:39 /user/bigdata/nyc_open_data/qf28-yqqv.json
# # -rw-rwx---+  3 rpd302 bigdata       37106 2018-04-06 11:39 /user/bigdata/nyc_open_data/qf2v-7dbv.json
# # -rw-rwx---+  3 rpd302 bigdata       46306 2018-04-06 11:39 /user/bigdata/nyc_open_data/qf92-qkjm.json
# # -rw-rwx---+  3 rpd302 bigdata     8061652 2018-04-06 11:39 /user/bigdata/nyc_open_data/qfe3-6dkn.json
# # -rw-rwx---+  3 rpd302 bigdata     3822084 2018-04-06 11:39 /user/bigdata/nyc_open_data/qfk7-6ens.json
# # -rw-rwx---+  3 rpd302 bigdata       84466 2018-04-06 11:39 /user/bigdata/nyc_open_data/qfs9-xn8t.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:39 /user/bigdata/nyc_open_data/qfxy-c6k3.json
# # -rw-rwx---+  3 rpd302 bigdata  2767519753 2018-04-06 11:39 /user/bigdata/nyc_open_data/qgea-i56i.json
# # -rw-rwx---+  3 rpd302 bigdata       46066 2018-04-06 11:39 /user/bigdata/nyc_open_data/qgga-62ej.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:39 /user/bigdata/nyc_open_data/qh62-9utz.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:39 /user/bigdata/nyc_open_data/qhen-5rve.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:39 /user/bigdata/nyc_open_data/qirg-qbv8.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:39 /user/bigdata/nyc_open_data/qiwj-i2jk.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:39 /user/bigdata/nyc_open_data/qiwn-t99b.json
# # -rw-rwx---+  3 rpd302 bigdata       41523 2018-04-06 11:39 /user/bigdata/nyc_open_data/qj9s-yv6v.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:39 /user/bigdata/nyc_open_data/qjqq-8zh3.json
# # -rw-rwx---+  3 rpd302 bigdata       66078 2018-04-06 11:39 /user/bigdata/nyc_open_data/qjx7-9mep.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:39 /user/bigdata/nyc_open_data/qk6i-zcht.json
# # -rw-rwx---+  3 rpd302 bigdata      175912 2018-04-06 11:39 /user/bigdata/nyc_open_data/qk7d-gecv.json
# # -rw-rwx---+  3 rpd302 bigdata      249423 2018-04-06 11:39 /user/bigdata/nyc_open_data/qkez-i8mv.json
# # -rw-rwx---+  3 rpd302 bigdata  1093571181 2018-04-06 11:40 /user/bigdata/nyc_open_data/qkm5-nuaq.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:40 /user/bigdata/nyc_open_data/qm58-9mub.json
# # -rw-rwx---+  3 rpd302 bigdata       83592 2018-04-06 11:40 /user/bigdata/nyc_open_data/qnuk-aubm.json
# # -rw-rwx---+  3 rpd302 bigdata       16403 2018-04-06 11:40 /user/bigdata/nyc_open_data/qnwe-j5my.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:40 /user/bigdata/nyc_open_data/qpbf-g2yx.json
# # -rw-rwx---+  3 rpd302 bigdata      728567 2018-04-06 11:40 /user/bigdata/nyc_open_data/qphc-zrtc.json
# # -rw-rwx---+  3 rpd302 bigdata      120051 2018-04-06 11:40 /user/bigdata/nyc_open_data/qpm9-j523.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:40 /user/bigdata/nyc_open_data/qpsp-bm9z.json
# # -rw-rwx---+  3 rpd302 bigdata       88818 2018-04-06 11:40 /user/bigdata/nyc_open_data/qrb4-aqtx.json
# # -rw-rwx---+  3 rpd302 bigdata      326724 2018-04-06 11:40 /user/bigdata/nyc_open_data/qrz6-23fw.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:40 /user/bigdata/nyc_open_data/qs4p-vs2w.json
# # -rw-rwx---+  3 rpd302 bigdata      111004 2018-04-06 11:40 /user/bigdata/nyc_open_data/qs5h-jhhg.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:40 /user/bigdata/nyc_open_data/qsa5-iezm.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:40 /user/bigdata/nyc_open_data/qsuf-mgjh.json
# # -rw-rwx---+  3 rpd302 bigdata        9985 2018-04-06 11:40 /user/bigdata/nyc_open_data/qt4e-9a97.json
# # -rw-rwx---+  3 rpd302 bigdata        9834 2018-04-06 11:40 /user/bigdata/nyc_open_data/qt67-786k.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:40 /user/bigdata/nyc_open_data/qtma-k4hh.json
# # -rw-rwx---+  3 rpd302 bigdata       49664 2018-04-06 11:40 /user/bigdata/nyc_open_data/qtrj-g3nm.json
# # -rw-rwx---+  3 rpd302 bigdata    57892962 2018-04-06 11:40 /user/bigdata/nyc_open_data/qu8g-sxqf.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:40 /user/bigdata/nyc_open_data/quix-kfbk.json
# # -rw-rwx---+  3 rpd302 bigdata      141089 2018-04-06 11:40 /user/bigdata/nyc_open_data/qvir-knu3.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:40 /user/bigdata/nyc_open_data/qvr4-94sr.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:40 /user/bigdata/nyc_open_data/qvtg-k2hn.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:40 /user/bigdata/nyc_open_data/qwca-zqw3.json
# # -rw-rwx---+  3 rpd302 bigdata       28502 2018-04-06 11:40 /user/bigdata/nyc_open_data/qwi9-6tzj.json
# # -rw-rwx---+  3 rpd302 bigdata     1383969 2018-04-06 11:40 /user/bigdata/nyc_open_data/qy7q-cb9e.json
# # -rw-rwx---+  3 rpd302 bigdata     3929319 2018-04-06 11:40 /user/bigdata/nyc_open_data/qybk-bjjc.json
# # -rw-rwx---+  3 rpd302 bigdata    28250820 2018-04-06 11:40 /user/bigdata/nyc_open_data/qyyg-4tf5.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:40 /user/bigdata/nyc_open_data/r2ig-3im3.json
# # -rw-rwx---+  3 rpd302 bigdata   935933255 2018-04-06 11:40 /user/bigdata/nyc_open_data/r4c5-ndkx.json
# # -rw-rwx---+  3 rpd302 bigdata      112570 2018-04-06 11:40 /user/bigdata/nyc_open_data/r4dz-wduq.json
# # -rw-rwx---+  3 rpd302 bigdata     1088640 2018-04-06 11:40 /user/bigdata/nyc_open_data/r4s5-tb2g.json
# # -rw-rwx---+  3 rpd302 bigdata       25058 2018-04-06 11:40 /user/bigdata/nyc_open_data/r528-jcks.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:40 /user/bigdata/nyc_open_data/r5j3-b762.json
# # -rw-rwx---+  3 rpd302 bigdata       10816 2018-04-06 11:40 /user/bigdata/nyc_open_data/r69u-62nw.json
# # -rw-rwx---+  3 rpd302 bigdata       84826 2018-04-06 11:40 /user/bigdata/nyc_open_data/r75y-8qe7.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:40 /user/bigdata/nyc_open_data/r7rr-2vqh.json
# # -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:40 /user/bigdata/nyc_open_data/r8nu-ymqj.json
# # -rw-rwx---+  3 rpd302 bigdata      126528 2018-04-06 11:40 /user/bigdata/nyc_open_data/rafb-6xry.json
# # -rw-rwx---+  3 rpd302 bigdata       27732 2018-04-06 11:40 /user/bigdata/nyc_open_data/rb2h-bgai.json
# -rw-rwx---+  3 rpd302 bigdata       72562 2018-04-06 11:40 /user/bigdata/nyc_open_data/rb93-tisp.json
# -rw-rwx---+  3 rpd302 bigdata        8065 2018-04-06 11:40 /user/bigdata/nyc_open_data/rbrz-iagc.json
# -rw-rwx---+  3 rpd302 bigdata       57816 2018-04-06 11:40 /user/bigdata/nyc_open_data/rbvx-jqnh.json
# -rw-rwx---+  3 rpd302 bigdata       17698 2018-04-06 11:40 /user/bigdata/nyc_open_data/rbwv-5abg.json
# -rw-rwx---+  3 rpd302 bigdata     5078397 2018-04-06 11:40 /user/bigdata/nyc_open_data/rbx6-tga4.json
# -rw-rwx---+  3 rpd302 bigdata     2857321 2018-04-06 11:40 /user/bigdata/nyc_open_data/rdxc-q253.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:40 /user/bigdata/nyc_open_data/rek2-fjft.json
# -rw-rwx---+  3 rpd302 bigdata      232177 2018-04-06 11:40 /user/bigdata/nyc_open_data/reri-chf8.json
# -rw-rwx---+  3 rpd302 bigdata       16128 2018-04-06 11:40 /user/bigdata/nyc_open_data/rfpq-hs49.json
# -rw-rwx---+  3 rpd302 bigdata       12651 2018-04-06 11:40 /user/bigdata/nyc_open_data/rfu3-4gsz.json
# -rw-rwx---+  3 rpd302 bigdata      181669 2018-04-06 11:40 /user/bigdata/nyc_open_data/rfu7-paqe.json
# -rw-rwx---+  3 rpd302 bigdata     7964959 2018-04-06 11:40 /user/bigdata/nyc_open_data/rgfe-8y2z.json
# -rw-rwx---+  3 rpd302 bigdata       11887 2018-04-06 11:40 /user/bigdata/nyc_open_data/rgqc-ddc4.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:40 /user/bigdata/nyc_open_data/rgy2-tti8.json
# -rw-rwx---+  3 rpd302 bigdata  2022322075 2018-04-06 11:40 /user/bigdata/nyc_open_data/rhe8-mgbb.json
# -rw-rwx---+  3 rpd302 bigdata      124717 2018-04-06 11:40 /user/bigdata/nyc_open_data/rhtj-vttz.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:40 /user/bigdata/nyc_open_data/rjaj-zgq7.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:40 /user/bigdata/nyc_open_data/rjqi-t95z.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:40 /user/bigdata/nyc_open_data/rm4p-5usz.json
# -rw-rwx---+  3 rpd302 bigdata      475781 2018-04-06 11:40 /user/bigdata/nyc_open_data/rmv8-86p4.json
# -rw-rwx---+  3 rpd302 bigdata       42512 2018-04-06 11:40 /user/bigdata/nyc_open_data/rn5p-vhac.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:40 /user/bigdata/nyc_open_data/rn6h-i66u.json
# -rw-rwx---+  3 rpd302 bigdata     8968283 2018-04-06 11:40 /user/bigdata/nyc_open_data/rn6p-xvjd.json
# -rw-rwx---+  3 rpd302 bigdata        8124 2018-04-06 11:40 /user/bigdata/nyc_open_data/rnf5-jwk6.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:40 /user/bigdata/nyc_open_data/rnjn-x48k.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:40 /user/bigdata/nyc_open_data/rnnj-5mmi.json
# -rw-rwx---+  3 rpd302 bigdata       56875 2018-04-06 11:40 /user/bigdata/nyc_open_data/rnsn-acs2.json
# -rw-rwx---+  3 rpd302 bigdata       45174 2018-04-06 11:40 /user/bigdata/nyc_open_data/rp8m-vm93.json
# -rw-rwx---+  3 rpd302 bigdata      719908 2018-04-06 11:40 /user/bigdata/nyc_open_data/rq2f-42ua.json
# -rw-rwx---+  3 rpd302 bigdata       76701 2018-04-06 11:40 /user/bigdata/nyc_open_data/rqhp-hivt.json
# -rw-rwx---+  3 rpd302 bigdata    13730126 2018-04-06 11:40 /user/bigdata/nyc_open_data/rqjq-29wc.json
# -rw-rwx---+  3 rpd302 bigdata       61544 2018-04-06 11:40 /user/bigdata/nyc_open_data/rqx9-kktd.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:40 /user/bigdata/nyc_open_data/rqzz-2ajy.json
# -rw-rwx---+  3 rpd302 bigdata    42496412 2018-04-06 11:40 /user/bigdata/nyc_open_data/rs6k-p7g6.json
# -rw-rwx---+  3 rpd302 bigdata      155143 2018-04-06 11:40 /user/bigdata/nyc_open_data/rskq-5bfv.json
# -rw-rwx---+  3 rpd302 bigdata      251969 2018-04-06 11:40 /user/bigdata/nyc_open_data/rsnd-bbih.json
# -rw-rwx---+  3 rpd302 bigdata       73187 2018-04-06 11:40 /user/bigdata/nyc_open_data/rstd-gm72.json
# -rw-rwx---+  3 rpd302 bigdata      255689 2018-04-06 11:40 /user/bigdata/nyc_open_data/rtws-c2ai.json
# -rw-rwx---+  3 rpd302 bigdata      109196 2018-04-06 11:40 /user/bigdata/nyc_open_data/ru7m-mpyz.json
# -rw-rwx---+  3 rpd302 bigdata     8307689 2018-04-06 11:40 /user/bigdata/nyc_open_data/ruce-cnp6.json
# -rw-rwx---+  3 rpd302 bigdata     1500214 2018-04-06 11:40 /user/bigdata/nyc_open_data/rukc-mmqu.json
# -rw-rwx---+  3 rpd302 bigdata       18100 2018-04-06 11:40 /user/bigdata/nyc_open_data/rv3z-jq34.json
# -rw-rwx---+  3 rpd302 bigdata      317356 2018-04-06 11:40 /user/bigdata/nyc_open_data/rwa3-b3wr.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:40 /user/bigdata/nyc_open_data/rxuy-2muj.json
# -rw-rwx---+  3 rpd302 bigdata 64572958619 2018-04-06 11:47 /user/bigdata/nyc_open_data/ry9a-ubra.json
# -rw-rwx---+  3 rpd302 bigdata    17753760 2018-04-06 11:47 /user/bigdata/nyc_open_data/rzd6-qsmn.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:47 /user/bigdata/nyc_open_data/s2d8-h5fg.json
# -rw-rwx---+  3 rpd302 bigdata       10226 2018-04-06 11:47 /user/bigdata/nyc_open_data/s2zm-f47y.json
# -rw-rwx---+  3 rpd302 bigdata     3092562 2018-04-06 11:47 /user/bigdata/nyc_open_data/s3k6-pzi2.json
# -rw-rwx---+  3 rpd302 bigdata      326809 2018-04-06 11:47 /user/bigdata/nyc_open_data/s3zn-tf7c.json
# -rw-rwx---+  3 rpd302 bigdata      745398 2018-04-06 11:47 /user/bigdata/nyc_open_data/s4kf-3yrf.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:47 /user/bigdata/nyc_open_data/s5c9-5mja.json
# -rw-rwx---+  3 rpd302 bigdata       19243 2018-04-06 11:47 /user/bigdata/nyc_open_data/s5ne-bpvg.json
# -rw-rwx---+  3 rpd302 bigdata      255208 2018-04-06 11:47 /user/bigdata/nyc_open_data/s5q4-7ezf.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:47 /user/bigdata/nyc_open_data/s5zg-yzea.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:47 /user/bigdata/nyc_open_data/s65f-sqe8.json
# -rw-rwx---+  3 rpd302 bigdata    18753770 2018-04-06 11:47 /user/bigdata/nyc_open_data/s79c-jgrm.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:47 /user/bigdata/nyc_open_data/s7k9-vr5b.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:47 /user/bigdata/nyc_open_data/s8jv-f44n.json
# -rw-rwx---+  3 rpd302 bigdata      331948 2018-04-06 11:47 /user/bigdata/nyc_open_data/s9xf-ztqu.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:47 /user/bigdata/nyc_open_data/sage-tgxd.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:47 /user/bigdata/nyc_open_data/sah3-jw2y.json
# -rw-rwx---+  3 rpd302 bigdata      147580 2018-04-06 11:47 /user/bigdata/nyc_open_data/sapz-4gsi.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:47 /user/bigdata/nyc_open_data/sban-vuz2.json
# -rw-rwx---+  3 rpd302 bigdata    52668892 2018-04-06 11:47 /user/bigdata/nyc_open_data/sbnd-xujn.json
# -rw-rwx---+  3 rpd302 bigdata      286879 2018-04-06 11:47 /user/bigdata/nyc_open_data/scfi-iv96.json
# -rw-rwx---+  3 rpd302 bigdata       10851 2018-04-06 11:47 /user/bigdata/nyc_open_data/sci4-yqgk.json
# -rw-rwx---+  3 rpd302 bigdata       17866 2018-04-06 11:47 /user/bigdata/nyc_open_data/scqk-i7ht.json
# -rw-rwx---+  3 rpd302 bigdata        8694 2018-04-06 11:47 /user/bigdata/nyc_open_data/sd9s-b3hd.json
# -rw-rwx---+  3 rpd302 bigdata       33164 2018-04-06 11:47 /user/bigdata/nyc_open_data/sefr-5pmx.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:47 /user/bigdata/nyc_open_data/sf3b-xntp.json
# -rw-rwx---+  3 rpd302 bigdata       41309 2018-04-06 11:47 /user/bigdata/nyc_open_data/sgvu-nui7.json
# -rw-rwx---+  3 rpd302 bigdata    13515082 2018-04-06 11:47 /user/bigdata/nyc_open_data/sibt-hnvk.json
# -rw-rwx---+  3 rpd302 bigdata      715431 2018-04-06 11:47 /user/bigdata/nyc_open_data/siju-6isf.json
# -rw-rwx---+  3 rpd302 bigdata     1149456 2018-04-06 11:47 /user/bigdata/nyc_open_data/sjpy-4cc9.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:47 /user/bigdata/nyc_open_data/sjy3-nf9e.json
# -rw-rwx---+  3 rpd302 bigdata       22812 2018-04-06 11:47 /user/bigdata/nyc_open_data/sjyc-3up2.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:47 /user/bigdata/nyc_open_data/sknu-4f6s.json
# -rw-rwx---+  3 rpd302 bigdata     1393800 2018-04-06 11:47 /user/bigdata/nyc_open_data/smdw-73pj.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:47 /user/bigdata/nyc_open_data/smk3-tmxj.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:47 /user/bigdata/nyc_open_data/sms6-sm5p.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:47 /user/bigdata/nyc_open_data/sn25-9xqk.json
# -rw-rwx---+  3 rpd302 bigdata       15969 2018-04-06 11:47 /user/bigdata/nyc_open_data/sn5i-xuny.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:47 /user/bigdata/nyc_open_data/sngu-yqq8.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:47 /user/bigdata/nyc_open_data/snt7-jkiu.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:47 /user/bigdata/nyc_open_data/sntb-k5vj.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:47 /user/bigdata/nyc_open_data/sp9a-cd2a.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:47 /user/bigdata/nyc_open_data/spax-mybh.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:47 /user/bigdata/nyc_open_data/spjh-pz7h.json
# -rw-rwx---+  3 rpd302 bigdata      108542 2018-04-06 11:47 /user/bigdata/nyc_open_data/sqb7-p8nz.json
# -rw-rwx---+  3 rpd302 bigdata   915592916 2018-04-06 11:47 /user/bigdata/nyc_open_data/sqcr-6mww.json
# -rw-rwx---+  3 rpd302 bigdata     1185474 2018-04-06 11:47 /user/bigdata/nyc_open_data/sqmu-2ixd.json
# -rw-rwx---+  3 rpd302 bigdata   153537072 2018-04-06 11:47 /user/bigdata/nyc_open_data/ssq6-fkht.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:47 /user/bigdata/nyc_open_data/stv3-xtpf.json
# -rw-rwx---+  3 rpd302 bigdata       11829 2018-04-06 11:47 /user/bigdata/nyc_open_data/su6u-afcg.json
# -rw-rwx---+  3 rpd302 bigdata       21660 2018-04-06 11:47 /user/bigdata/nyc_open_data/sv6e-j8t9.json
# -rw-rwx---+  3 rpd302 bigdata  1115735086 2018-04-06 11:47 /user/bigdata/nyc_open_data/sv7x-dduq.json
# -rw-rwx---+  3 rpd302 bigdata       13110 2018-04-06 11:47 /user/bigdata/nyc_open_data/svyi-maaj.json
# -rw-rwx---+  3 rpd302 bigdata       81223 2018-04-06 11:47 /user/bigdata/nyc_open_data/swpk-hqdp.json
# -rw-rwx---+  3 rpd302 bigdata       87701 2018-04-06 11:47 /user/bigdata/nyc_open_data/swsf-ed7j.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:47 /user/bigdata/nyc_open_data/sx4q-k6ay.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:47 /user/bigdata/nyc_open_data/sxe3-hucm.json
# -rw-rwx---+  3 rpd302 bigdata       20175 2018-04-06 11:47 /user/bigdata/nyc_open_data/sxh6-h6ph.json
# -rw-rwx---+  3 rpd302 bigdata  1473207790 2018-04-06 11:48 /user/bigdata/nyc_open_data/sxmw-f24h.json
# -rw-rwx---+  3 rpd302 bigdata      128467 2018-04-06 11:48 /user/bigdata/nyc_open_data/sxx4-xhzg.json
# -rw-rwx---+  3 rpd302 bigdata       19040 2018-04-06 11:48 /user/bigdata/nyc_open_data/sxxc-x9gg.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:48 /user/bigdata/nyc_open_data/szbc-ua9b.json
# -rw-rwx---+  3 rpd302 bigdata     1965501 2018-04-06 11:48 /user/bigdata/nyc_open_data/szkz-syh6.json
# -rw-rwx---+  3 rpd302 bigdata      249104 2018-04-06 11:48 /user/bigdata/nyc_open_data/szn6-bbuk.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:48 /user/bigdata/nyc_open_data/szwg-xci6.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:48 /user/bigdata/nyc_open_data/t22b-cmty.json
# -rw-rwx---+  3 rpd302 bigdata      443567 2018-04-06 11:48 /user/bigdata/nyc_open_data/t446-jbtd.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:48 /user/bigdata/nyc_open_data/t4s6-khpm.json
# -rw-rwx---+  3 rpd302 bigdata      195554 2018-04-06 11:48 /user/bigdata/nyc_open_data/t5w8-y8xf.json
# -rw-rwx---+  3 rpd302 bigdata        7320 2018-04-06 11:48 /user/bigdata/nyc_open_data/t6g4-rw7k.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:48 /user/bigdata/nyc_open_data/t6ia-5tin.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:48 /user/bigdata/nyc_open_data/t7sx-id53.json
# -rw-rwx---+  3 rpd302 bigdata    27865943 2018-04-06 11:48 /user/bigdata/nyc_open_data/t8hj-ruu2.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:48 /user/bigdata/nyc_open_data/t9jy-gfev.json
# -rw-rwx---+  3 rpd302 bigdata      686351 2018-04-06 11:48 /user/bigdata/nyc_open_data/t9nw-j73k.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:48 /user/bigdata/nyc_open_data/tar7-vww3.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:48 /user/bigdata/nyc_open_data/tars-scr5.json
# -rw-rwx---+  3 rpd302 bigdata       27707 2018-04-06 11:48 /user/bigdata/nyc_open_data/tavr-zknk.json
# -rw-rwx---+  3 rpd302 bigdata     1462168 2018-04-06 11:48 /user/bigdata/nyc_open_data/tb8q-a3ar.json
# -rw-rwx---+  3 rpd302 bigdata       12023 2018-04-06 11:48 /user/bigdata/nyc_open_data/tbf6-u8ea.json
# -rw-rwx---+  3 rpd302 bigdata     1277126 2018-04-06 11:48 /user/bigdata/nyc_open_data/tbgj-tdd6.json
# -rw-rwx---+  3 rpd302 bigdata      708659 2018-04-06 11:48 /user/bigdata/nyc_open_data/tbvj-mbps.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:48 /user/bigdata/nyc_open_data/tbvn-fzud.json
# -rw-rwx---+  3 rpd302 bigdata       36124 2018-04-06 11:48 /user/bigdata/nyc_open_data/tc6u-8rnp.json
# -rw-rwx---+  3 rpd302 bigdata      197962 2018-04-06 11:48 /user/bigdata/nyc_open_data/tczk-5sa2.json
# -rw-rwx---+  3 rpd302 bigdata  3773747154 2018-04-06 11:48 /user/bigdata/nyc_open_data/td5q-ry6d.json
# -rw-rwx---+  3 rpd302 bigdata  7607971459 2018-04-06 11:49 /user/bigdata/nyc_open_data/tdd6-3ysr.json
# -rw-rwx---+  3 rpd302 bigdata    47449538 2018-04-06 11:49 /user/bigdata/nyc_open_data/tesw-yqqr.json
# -rw-rwx---+  3 rpd302 bigdata       47483 2018-04-06 11:49 /user/bigdata/nyc_open_data/tesz-9suw.json
# -rw-rwx---+  3 rpd302 bigdata       31175 2018-04-06 11:49 /user/bigdata/nyc_open_data/tfbb-gszk.json
# -rw-rwx---+  3 rpd302 bigdata    25699361 2018-04-06 11:49 /user/bigdata/nyc_open_data/tg4x-b46p.json
# -rw-rwx---+  3 rpd302 bigdata       35817 2018-04-06 11:49 /user/bigdata/nyc_open_data/tgqn-na2n.json
# -rw-rwx---+  3 rpd302 bigdata      744556 2018-04-06 11:49 /user/bigdata/nyc_open_data/tgrn-h24f.json
# -rw-rwx---+  3 rpd302 bigdata        9081 2018-04-06 11:49 /user/bigdata/nyc_open_data/tgvi-w9ww.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:49 /user/bigdata/nyc_open_data/tgyc-r5jh.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:49 /user/bigdata/nyc_open_data/thbt-gfu9.json
# -rw-rwx---+  3 rpd302 bigdata      402249 2018-04-06 11:49 /user/bigdata/nyc_open_data/thjb-fm53.json
# -rw-rwx---+  3 rpd302 bigdata      303045 2018-04-06 11:49 /user/bigdata/nyc_open_data/thqd-deec.json
# -rw-rwx---+  3 rpd302 bigdata       55096 2018-04-06 11:49 /user/bigdata/nyc_open_data/thrx-b6bc.json
# -rw-rwx---+  3 rpd302 bigdata    13597620 2018-04-06 11:49 /user/bigdata/nyc_open_data/thxi-frp3.json
# -rw-rwx---+  3 rpd302 bigdata      133930 2018-04-06 11:49 /user/bigdata/nyc_open_data/tkdy-59zg.json
# -rw-rwx---+  3 rpd302 bigdata       42636 2018-04-06 11:49 /user/bigdata/nyc_open_data/tm5c-buy3.json
# -rw-rwx---+  3 rpd302 bigdata   686674156 2018-04-06 11:49 /user/bigdata/nyc_open_data/tm6d-hbzd.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:49 /user/bigdata/nyc_open_data/tmtb-gcc6.json
# -rw-rwx---+  3 rpd302 bigdata   251035935 2018-04-06 11:49 /user/bigdata/nyc_open_data/tn4g-ski5.json
# -rw-rwx---+  3 rpd302 bigdata    25088766 2018-04-06 11:49 /user/bigdata/nyc_open_data/tn5h-i3e8.json
# -rw-rwx---+  3 rpd302 bigdata       67205 2018-04-06 11:49 /user/bigdata/nyc_open_data/tncb-agv4.json
# -rw-rwx---+  3 rpd302 bigdata       15849 2018-04-06 11:49 /user/bigdata/nyc_open_data/tngj-drbu.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:49 /user/bigdata/nyc_open_data/tnru-abg2.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:49 /user/bigdata/nyc_open_data/tpe4-3w5y.json
# -rw-rwx---+  3 rpd302 bigdata      188384 2018-04-06 11:49 /user/bigdata/nyc_open_data/tph5-57et.json
# -rw-rwx---+  3 rpd302 bigdata      845068 2018-04-06 11:49 /user/bigdata/nyc_open_data/tphb-2tdm.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:49 /user/bigdata/nyc_open_data/tpix-uwie.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:49 /user/bigdata/nyc_open_data/tq7f-w2f5.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:49 /user/bigdata/nyc_open_data/tqh4-y786.json
# -rw-rwx---+  3 rpd302 bigdata       87740 2018-04-06 11:49 /user/bigdata/nyc_open_data/tqkr-fgym.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:49 /user/bigdata/nyc_open_data/tqmj-j8zm.json
# -rw-rwx---+  3 rpd302 bigdata      118760 2018-04-06 11:49 /user/bigdata/nyc_open_data/tsak-vtv3.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:49 /user/bigdata/nyc_open_data/tsny-wwsu.json
# -rw-rwx---+  3 rpd302 bigdata       24855 2018-04-06 11:49 /user/bigdata/nyc_open_data/tsy7-gcm8.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:49 /user/bigdata/nyc_open_data/tv64-9x69.json
# -rw-rwx---+  3 rpd302 bigdata     2182399 2018-04-06 11:49 /user/bigdata/nyc_open_data/tvfr-dhen.json
# -rw-rwx---+  3 rpd302 bigdata      755518 2018-04-06 11:49 /user/bigdata/nyc_open_data/tvpp-9vvx.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:49 /user/bigdata/nyc_open_data/tvy2-e7mm.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:49 /user/bigdata/nyc_open_data/tw25-qwub.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:49 /user/bigdata/nyc_open_data/twim-r7xp.json
# -rw-rwx---+  3 rpd302 bigdata     2157062 2018-04-06 11:49 /user/bigdata/nyc_open_data/twu4-tp2g.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:49 /user/bigdata/nyc_open_data/txxa-5nhg.json
# -rw-rwx---+  3 rpd302 bigdata    26842714 2018-04-06 11:49 /user/bigdata/nyc_open_data/ty7c-8rmq.json
# -rw-rwx---+  3 rpd302 bigdata  2653687707 2018-04-06 11:50 /user/bigdata/nyc_open_data/ty85-y26w.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:50 /user/bigdata/nyc_open_data/ty8z-v9d2.json
# -rw-rwx---+  3 rpd302 bigdata     1079890 2018-04-06 11:50 /user/bigdata/nyc_open_data/tyfh-9h2y.json
# -rw-rwx---+  3 rpd302 bigdata       90395 2018-04-06 11:50 /user/bigdata/nyc_open_data/tyjc-nqc2.json
# -rw-rwx---+  3 rpd302 bigdata       25484 2018-04-06 11:50 /user/bigdata/nyc_open_data/tzwr-vksx.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:50 /user/bigdata/nyc_open_data/u2m4-wh3s.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:50 /user/bigdata/nyc_open_data/u32x-nkau.json
# -rw-rwx---+  3 rpd302 bigdata      640887 2018-04-06 11:50 /user/bigdata/nyc_open_data/u35m-9t32.json
# -rw-rwx---+  3 rpd302 bigdata      310080 2018-04-06 11:50 /user/bigdata/nyc_open_data/u4ef-3s9d.json
# -rw-rwx---+  3 rpd302 bigdata       21236 2018-04-06 11:50 /user/bigdata/nyc_open_data/u4uz-edhr.json
# -rw-rwx---+  3 rpd302 bigdata     1637942 2018-04-06 11:50 /user/bigdata/nyc_open_data/u553-m549.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:50 /user/bigdata/nyc_open_data/u6fv-5dqe.json
# -rw-rwx---+  3 rpd302 bigdata       91589 2018-04-06 11:50 /user/bigdata/nyc_open_data/u6gg-xejf.json
# -rw-rwx---+  3 rpd302 bigdata       23145 2018-04-06 11:50 /user/bigdata/nyc_open_data/u6p4-fsey.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:50 /user/bigdata/nyc_open_data/u6su-4fpt.json
# -rw-rwx---+  3 rpd302 bigdata 40388283670 2018-04-06 11:54 /user/bigdata/nyc_open_data/uacg-pexx.json
# -rw-rwx---+  3 rpd302 bigdata      114768 2018-04-06 11:54 /user/bigdata/nyc_open_data/uaj7-9szf.json
# -rw-rwx---+  3 rpd302 bigdata   609449842 2018-04-06 11:54 /user/bigdata/nyc_open_data/ub9z-gccp.json
# -rw-rwx---+  3 rpd302 bigdata       49965 2018-04-06 11:54 /user/bigdata/nyc_open_data/ubdi-jgw2.json
# -rw-rwx---+  3 rpd302 bigdata       48209 2018-04-06 11:54 /user/bigdata/nyc_open_data/ubv8-6n5w.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:54 /user/bigdata/nyc_open_data/uc6u-xsrr.json
# -rw-rwx---+  3 rpd302 bigdata      194416 2018-04-06 11:54 /user/bigdata/nyc_open_data/ucdy-byxd.json
# -rw-rwx---+  3 rpd302 bigdata      264238 2018-04-06 11:54 /user/bigdata/nyc_open_data/uchs-jqh4.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:54 /user/bigdata/nyc_open_data/ud5r-z5ws.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:54 /user/bigdata/nyc_open_data/udt3-taj7.json
# -rw-rwx---+  3 rpd302 bigdata      303870 2018-04-06 11:54 /user/bigdata/nyc_open_data/uedp-fegm.json
# -rw-rwx---+  3 rpd302 bigdata       36576 2018-04-06 11:54 /user/bigdata/nyc_open_data/uf8p-ervp.json
# -rw-rwx---+  3 rpd302 bigdata       47275 2018-04-06 11:54 /user/bigdata/nyc_open_data/ufu7-zp25.json
# -rw-rwx---+  3 rpd302 bigdata       18335 2018-04-06 11:54 /user/bigdata/nyc_open_data/ugc2-6t2g.json
# -rw-rwx---+  3 rpd302 bigdata       21723 2018-04-06 11:54 /user/bigdata/nyc_open_data/uggy-myiz.json
# -rw-rwx---+  3 rpd302 bigdata     4770021 2018-04-06 11:54 /user/bigdata/nyc_open_data/ugzk-a6x4.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:54 /user/bigdata/nyc_open_data/uh7r-6nya.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:54 /user/bigdata/nyc_open_data/uhb2-uqfs.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:54 /user/bigdata/nyc_open_data/uhim-nea2.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:54 /user/bigdata/nyc_open_data/uihr-hn7s.json
# -rw-rwx---+  3 rpd302 bigdata       17427 2018-04-06 11:54 /user/bigdata/nyc_open_data/uiz5-pwzg.json
# -rw-rwx---+  3 rpd302 bigdata       24901 2018-04-06 11:54 /user/bigdata/nyc_open_data/ujdf-5byz.json
# -rw-rwx---+  3 rpd302 bigdata       43555 2018-04-06 11:54 /user/bigdata/nyc_open_data/ujsc-un6m.json
# -rw-rwx---+  3 rpd302 bigdata   377615452 2018-04-06 11:54 /user/bigdata/nyc_open_data/umvu-uw78.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:54 /user/bigdata/nyc_open_data/un72-4nix.json
# -rw-rwx---+  3 rpd302 bigdata     1641196 2018-04-06 11:54 /user/bigdata/nyc_open_data/un8d-rbed.json
# -rw-rwx---+  3 rpd302 bigdata       23284 2018-04-06 11:54 /user/bigdata/nyc_open_data/unw7-yyit.json
# -rw-rwx---+  3 rpd302 bigdata      479236 2018-04-06 11:54 /user/bigdata/nyc_open_data/upwt-zvh3.json
# -rw-rwx---+  3 rpd302 bigdata   749636408 2018-04-06 11:54 /user/bigdata/nyc_open_data/uqqa-hym2.json
# -rw-rwx---+  3 rpd302 bigdata       82322 2018-04-06 11:54 /user/bigdata/nyc_open_data/urvc-2kdr.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:54 /user/bigdata/nyc_open_data/urxm-vzzk.json
# -rw-rwx---+  3 rpd302 bigdata     7009436 2018-04-06 11:54 /user/bigdata/nyc_open_data/urz7-pzb3.json
# -rw-rwx---+  3 rpd302 bigdata      431791 2018-04-06 11:54 /user/bigdata/nyc_open_data/us4j-b5zt.json
# -rw-rwx---+  3 rpd302 bigdata       18500 2018-04-06 11:54 /user/bigdata/nyc_open_data/us5j-esyf.json
# -rw-rwx---+  3 rpd302 bigdata     1407702 2018-04-06 11:54 /user/bigdata/nyc_open_data/usap-qc7e.json
# -rw-rwx---+  3 rpd302 bigdata      137378 2018-04-06 11:54 /user/bigdata/nyc_open_data/ut9y-2ptp.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:54 /user/bigdata/nyc_open_data/utnf-u4xf.json
# -rw-rwx---+  3 rpd302 bigdata      582810 2018-04-06 11:54 /user/bigdata/nyc_open_data/utqd-4534.json
# -rw-rwx---+  3 rpd302 bigdata       74566 2018-04-06 11:54 /user/bigdata/nyc_open_data/uv67-wxba.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:54 /user/bigdata/nyc_open_data/uvbr-fk6w.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:54 /user/bigdata/nyc_open_data/uvgd-xsc8.json
# -rw-rwx---+  3 rpd302 bigdata      398476 2018-04-06 11:54 /user/bigdata/nyc_open_data/uvks-tn5n.json
# -rw-rwx---+  3 rpd302 bigdata   394954414 2018-04-06 11:54 /user/bigdata/nyc_open_data/uvpi-gqnh.json
# -rw-rwx---+  3 rpd302 bigdata       16675 2018-04-06 11:54 /user/bigdata/nyc_open_data/uvw5-9znb.json
# -rw-rwx---+  3 rpd302 bigdata   364536281 2018-04-06 11:54 /user/bigdata/nyc_open_data/uwyv-629c.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:54 /user/bigdata/nyc_open_data/ux7j-iww6.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:54 /user/bigdata/nyc_open_data/uxpt-rzip.json
# -rw-rwx---+  3 rpd302 bigdata    10253525 2018-04-06 11:54 /user/bigdata/nyc_open_data/uyiw-98i7.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:54 /user/bigdata/nyc_open_data/uyj8-7rv5.json
# -rw-rwx---+  3 rpd302 bigdata  1551823563 2018-04-06 11:54 /user/bigdata/nyc_open_data/uzcy-9puk.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:54 /user/bigdata/nyc_open_data/uzf5-f8n2.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:54 /user/bigdata/nyc_open_data/uzgy-xh4j.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:54 /user/bigdata/nyc_open_data/v2h8-6mxf.json
# -rw-rwx---+  3 rpd302 bigdata       48231 2018-04-06 11:54 /user/bigdata/nyc_open_data/v2kq-qrx6.json
# -rw-rwx---+  3 rpd302 bigdata       16753 2018-04-06 11:54 /user/bigdata/nyc_open_data/v3a6-muuw.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:54 /user/bigdata/nyc_open_data/v3am-k46r.json
# -rw-rwx---+  3 rpd302 bigdata       20298 2018-04-06 11:54 /user/bigdata/nyc_open_data/v3f6-2e7z.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:54 /user/bigdata/nyc_open_data/v3zf-nci8.json
# -rw-rwx---+  3 rpd302 bigdata      182416 2018-04-06 11:54 /user/bigdata/nyc_open_data/v475-8jcj.json
# -rw-rwx---+  3 rpd302 bigdata     6276337 2018-04-06 11:54 /user/bigdata/nyc_open_data/v575-87iz.json
# -rw-rwx---+  3 rpd302 bigdata      552080 2018-04-06 11:54 /user/bigdata/nyc_open_data/v5b9-t7fc.json
# -rw-rwx---+  3 rpd302 bigdata   243193532 2018-04-06 11:54 /user/bigdata/nyc_open_data/v6j6-k9uc.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:54 /user/bigdata/nyc_open_data/v6vm-bucj.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:54 /user/bigdata/nyc_open_data/v7f4-yzyg.json
# -rw-rwx---+  3 rpd302 bigdata       44262 2018-04-06 11:54 /user/bigdata/nyc_open_data/v8qe-fx6p.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:54 /user/bigdata/nyc_open_data/v9xd-tt3e.json
# -rw-rwx---+  3 rpd302 bigdata       18172 2018-04-06 11:54 /user/bigdata/nyc_open_data/vbgf-ket3.json
# -rw-rwx---+  3 rpd302 bigdata    13808180 2018-04-06 11:54 /user/bigdata/nyc_open_data/vdbc-pyc9.json
# -rw-rwx---+  3 rpd302 bigdata       88823 2018-04-06 11:54 /user/bigdata/nyc_open_data/vdem-2i66.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:54 /user/bigdata/nyc_open_data/vdgp-ddvg.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:54 /user/bigdata/nyc_open_data/vdkk-sqws.json
# -rw-rwx---+  3 rpd302 bigdata      596527 2018-04-06 11:54 /user/bigdata/nyc_open_data/ven4-h25u.json
# -rw-rwx---+  3 rpd302 bigdata     1401796 2018-04-06 11:54 /user/bigdata/nyc_open_data/vf4p-p8ui.json
# -rw-rwx---+  3 rpd302 bigdata      552066 2018-04-06 11:54 /user/bigdata/nyc_open_data/vfdq-dvkf.json
# -rw-rwx---+  3 rpd302 bigdata      141889 2018-04-06 11:54 /user/bigdata/nyc_open_data/vfk9-3uwk.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:54 /user/bigdata/nyc_open_data/vfx9-tbb6.json
# -rw-rwx---+  3 rpd302 bigdata    31155942 2018-04-06 11:54 /user/bigdata/nyc_open_data/vg63-xw6u.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:54 /user/bigdata/nyc_open_data/vghm-gmwr.json
# -rw-rwx---+  3 rpd302 bigdata      825469 2018-04-06 11:54 /user/bigdata/nyc_open_data/vgmz-py3h.json
# -rw-rwx---+  3 rpd302 bigdata    10481211 2018-04-06 11:54 /user/bigdata/nyc_open_data/vh2h-md7a.json
# -rw-rwx---+  3 rpd302 bigdata       17683 2018-04-06 11:54 /user/bigdata/nyc_open_data/vhtt-kpwy.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:54 /user/bigdata/nyc_open_data/vihk-m25f.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:54 /user/bigdata/nyc_open_data/vijr-8gr7.json
# -rw-rwx---+  3 rpd302 bigdata      292749 2018-04-06 11:54 /user/bigdata/nyc_open_data/vimb-anc6.json
# -rw-rwx---+  3 rpd302 bigdata       12063 2018-04-06 11:54 /user/bigdata/nyc_open_data/vk9f-gvzq.json
# -rw-rwx---+  3 rpd302 bigdata      121812 2018-04-06 11:54 /user/bigdata/nyc_open_data/vn2t-jh2b.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:54 /user/bigdata/nyc_open_data/vnwz-ihnf.json
# -rw-rwx---+  3 rpd302 bigdata       14276 2018-04-06 11:54 /user/bigdata/nyc_open_data/vpb3-uf7s.json
# -rw-rwx---+  3 rpd302 bigdata      115335 2018-04-06 11:54 /user/bigdata/nyc_open_data/vpdq-ktpr.json
# -rw-rwx---+  3 rpd302 bigdata     6060290 2018-04-06 11:54 /user/bigdata/nyc_open_data/vq35-j9qm.json
# -rw-rwx---+  3 rpd302 bigdata     1402307 2018-04-06 11:55 /user/bigdata/nyc_open_data/vqix-8bak.json
# -rw-rwx---+  3 rpd302 bigdata        8013 2018-04-06 11:55 /user/bigdata/nyc_open_data/vr2i-c3qq.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:55 /user/bigdata/nyc_open_data/vr8g-vfny.json
# -rw-rwx---+  3 rpd302 bigdata    21039742 2018-04-06 11:55 /user/bigdata/nyc_open_data/vr8p-8shw.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:55 /user/bigdata/nyc_open_data/vrfr-9k4d.json
# -rw-rwx---+  3 rpd302 bigdata      532316 2018-04-06 11:55 /user/bigdata/nyc_open_data/vrn4-2abs.json
# -rw-rwx---+  3 rpd302 bigdata      524433 2018-04-06 11:55 /user/bigdata/nyc_open_data/vrs9-g7kz.json
# -rw-rwx---+  3 rpd302 bigdata   626536325 2018-04-06 11:55 /user/bigdata/nyc_open_data/vsfz-uqxv.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:55 /user/bigdata/nyc_open_data/vsnr-94wk.json
# -rw-rwx---+  3 rpd302 bigdata       29398 2018-04-06 11:55 /user/bigdata/nyc_open_data/vspn-8tzq.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:55 /user/bigdata/nyc_open_data/vtzg-7562.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:55 /user/bigdata/nyc_open_data/vu7w-gbbe.json
# -rw-rwx---+  3 rpd302 bigdata     7373976 2018-04-06 11:55 /user/bigdata/nyc_open_data/vuae-w6cg.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:55 /user/bigdata/nyc_open_data/vvdx-b56i.json
# -rw-rwx---+  3 rpd302 bigdata       72518 2018-04-06 11:55 /user/bigdata/nyc_open_data/vve2-26rs.json
# -rw-rwx---+  3 rpd302 bigdata     1172628 2018-04-06 11:55 /user/bigdata/nyc_open_data/vvj6-d5qx.json
# -rw-rwx---+  3 rpd302 bigdata       28823 2018-04-06 11:55 /user/bigdata/nyc_open_data/vvym-pu7g.json
# -rw-rwx---+  3 rpd302 bigdata     3230956 2018-04-06 11:55 /user/bigdata/nyc_open_data/vw9i-7mzq.json
# -rw-rwx---+  3 rpd302 bigdata  1605644674 2018-04-06 11:55 /user/bigdata/nyc_open_data/vwpc-kje2.json
# -rw-rwx---+  3 rpd302 bigdata   141739674 2018-04-06 11:55 /user/bigdata/nyc_open_data/vx8i-nprf.json
# -rw-rwx---+  3 rpd302 bigdata      446031 2018-04-06 11:55 /user/bigdata/nyc_open_data/vxxs-iyt2.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:55 /user/bigdata/nyc_open_data/vy67-bzq3.json
# -rw-rwx---+  3 rpd302 bigdata       59844 2018-04-06 11:55 /user/bigdata/nyc_open_data/vyxt-abab.json
# -rw-rwx---+  3 rpd302 bigdata      177680 2018-04-06 11:55 /user/bigdata/nyc_open_data/vz7h-p6wa.json
# -rw-rwx---+  3 rpd302 bigdata       32376 2018-04-06 11:55 /user/bigdata/nyc_open_data/vz8c-29aj.json
# -rw-rwx---+  3 rpd302 bigdata      649156 2018-04-06 11:55 /user/bigdata/nyc_open_data/vza7-n6vi.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:55 /user/bigdata/nyc_open_data/w2sw-2dqb.json
# -rw-rwx---+  3 rpd302 bigdata       18835 2018-04-06 11:55 /user/bigdata/nyc_open_data/w38c-pyzq.json
# -rw-rwx---+  3 rpd302 bigdata       87446 2018-04-06 11:55 /user/bigdata/nyc_open_data/w3c6-35wg.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:55 /user/bigdata/nyc_open_data/w3g3-3ai7.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:55 /user/bigdata/nyc_open_data/w3wp-dpdi.json
# -rw-rwx---+  3 rpd302 bigdata       18984 2018-04-06 11:55 /user/bigdata/nyc_open_data/w449-f4d7.json
# -rw-rwx---+  3 rpd302 bigdata       21509 2018-04-06 11:55 /user/bigdata/nyc_open_data/w49k-mmkh.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:55 /user/bigdata/nyc_open_data/w4v2-rv6b.json
# -rw-rwx---+  3 rpd302 bigdata       40982 2018-04-06 11:55 /user/bigdata/nyc_open_data/w4v6-3sdt.json
# -rw-rwx---+  3 rpd302 bigdata       13637 2018-04-06 11:55 /user/bigdata/nyc_open_data/w5he-u64t.json
# -rw-rwx---+  3 rpd302 bigdata      143140 2018-04-06 11:55 /user/bigdata/nyc_open_data/w5y2-8cs3.json
# -rw-rwx---+  3 rpd302 bigdata      365945 2018-04-06 11:55 /user/bigdata/nyc_open_data/w6yt-hctp.json
# -rw-rwx---+  3 rpd302 bigdata    63237127 2018-04-06 11:55 /user/bigdata/nyc_open_data/w7w3-xahh.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:55 /user/bigdata/nyc_open_data/w83z-2kf9.json
# -rw-rwx---+  3 rpd302 bigdata       21285 2018-04-06 11:55 /user/bigdata/nyc_open_data/w8dz-xpjh.json
# -rw-rwx---+  3 rpd302 bigdata     4558571 2018-04-06 11:55 /user/bigdata/nyc_open_data/w9ak-ipjd.json
# -rw-rwx---+  3 rpd302 bigdata      100965 2018-04-06 11:55 /user/bigdata/nyc_open_data/w9cy-nnma.json
# -rw-rwx---+  3 rpd302 bigdata       29460 2018-04-06 11:55 /user/bigdata/nyc_open_data/w9du-8cu6.json
# -rw-rwx---+  3 rpd302 bigdata      626993 2018-04-06 11:55 /user/bigdata/nyc_open_data/w9ei-idxz.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:55 /user/bigdata/nyc_open_data/w9uz-8epq.json
# -rw-rwx---+  3 rpd302 bigdata    63570592 2018-04-06 11:55 /user/bigdata/nyc_open_data/wavz-fkw8.json
# -rw-rwx---+  3 rpd302 bigdata      530337 2018-04-06 11:55 /user/bigdata/nyc_open_data/wbtw-zkex.json
# -rw-rwx---+  3 rpd302 bigdata      104881 2018-04-06 11:55 /user/bigdata/nyc_open_data/weaz-wxw9.json
# -rw-rwx---+  3 rpd302 bigdata    84139907 2018-04-06 11:55 /user/bigdata/nyc_open_data/wed3-5i35.json
# -rw-rwx---+  3 rpd302 bigdata      352520 2018-04-06 11:55 /user/bigdata/nyc_open_data/weg5-33pj.json
# -rw-rwx---+  3 rpd302 bigdata       24768 2018-04-06 11:55 /user/bigdata/nyc_open_data/wffy-3iyg.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:55 /user/bigdata/nyc_open_data/wg68-84sr.json
# -rw-rwx---+  3 rpd302 bigdata       28708 2018-04-06 11:55 /user/bigdata/nyc_open_data/wgsy-wbzx.json
# -rw-rwx---+  3 rpd302 bigdata       20513 2018-04-06 11:55 /user/bigdata/nyc_open_data/wha7-46h5.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:55 /user/bigdata/nyc_open_data/wha9-m3tq.json
# -rw-rwx---+  3 rpd302 bigdata       45143 2018-04-06 11:55 /user/bigdata/nyc_open_data/whux-iuiu.json
# -rw-rwx---+  3 rpd302 bigdata       40024 2018-04-06 11:55 /user/bigdata/nyc_open_data/wibz-uqui.json
# -rw-rwx---+  3 rpd302 bigdata       23063 2018-04-06 11:55 /user/bigdata/nyc_open_data/wip6-ytad.json
# -rw-rwx---+  3 rpd302 bigdata       66937 2018-04-06 11:55 /user/bigdata/nyc_open_data/wjtn-s4z7.json
# -rw-rwx---+  3 rpd302 bigdata       27866 2018-04-06 11:55 /user/bigdata/nyc_open_data/wkaa-8g8b.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:55 /user/bigdata/nyc_open_data/wm9y-vrt8.json
# -rw-rwx---+  3 rpd302 bigdata      531667 2018-04-06 11:55 /user/bigdata/nyc_open_data/wmi7-dkwa.json
# -rw-rwx---+  3 rpd302 bigdata     1525743 2018-04-06 11:55 /user/bigdata/nyc_open_data/wng2-85mv.json
# -rw-rwx---+  3 rpd302 bigdata   141425699 2018-04-06 11:55 /user/bigdata/nyc_open_data/wpqj-3buw.json
# -rw-rwx---+  3 rpd302 bigdata       14173 2018-04-06 11:55 /user/bigdata/nyc_open_data/wqr5-zmgj.json
# -rw-rwx---+  3 rpd302 bigdata    15285202 2018-04-06 11:55 /user/bigdata/nyc_open_data/wr4r-bue7.json
# -rw-rwx---+  3 rpd302 bigdata     7661558 2018-04-06 11:55 /user/bigdata/nyc_open_data/wrhz-w8mn.json
# -rw-rwx---+  3 rpd302 bigdata     1215995 2018-04-06 11:55 /user/bigdata/nyc_open_data/ws4c-4g69.json
# -rw-rwx---+  3 rpd302 bigdata      103721 2018-04-06 11:55 /user/bigdata/nyc_open_data/wstu-wcnw.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:55 /user/bigdata/nyc_open_data/wt4d-p43d.json
# -rw-rwx---+  3 rpd302 bigdata      184942 2018-04-06 11:55 /user/bigdata/nyc_open_data/wtqm-fd2z.json
# -rw-rwx---+  3 rpd302 bigdata        9466 2018-04-06 11:55 /user/bigdata/nyc_open_data/wudr-qbgm.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:55 /user/bigdata/nyc_open_data/wue3-68ab.json
# -rw-rwx---+  3 rpd302 bigdata       79452 2018-04-06 11:55 /user/bigdata/nyc_open_data/wv4q-e75v.json
# -rw-rwx---+  3 rpd302 bigdata  3497917559 2018-04-06 11:55 /user/bigdata/nyc_open_data/wvxf-dwi5.json
# -rw-rwx---+  3 rpd302 bigdata      729310 2018-04-06 11:55 /user/bigdata/nyc_open_data/wwhr-5ven.json
# -rw-rwx---+  3 rpd302 bigdata       16723 2018-04-06 11:55 /user/bigdata/nyc_open_data/wwsa-q2dq.json
# -rw-rwx---+  3 rpd302 bigdata       19248 2018-04-06 11:55 /user/bigdata/nyc_open_data/wyca-yviy.json
# -rw-rwx---+  3 rpd302 bigdata      431110 2018-04-06 11:55 /user/bigdata/nyc_open_data/wye7-nyek.json
# -rw-rwx---+  3 rpd302 bigdata      499468 2018-04-06 11:55 /user/bigdata/nyc_open_data/wz5f-jajk.json
# -rw-rwx---+  3 rpd302 bigdata       65286 2018-04-06 11:55 /user/bigdata/nyc_open_data/wzur-rhz9.json
# -rw-rwx---+  3 rpd302 bigdata    21141163 2018-04-06 11:55 /user/bigdata/nyc_open_data/x273-tgv9.json
# -rw-rwx---+  3 rpd302 bigdata      183441 2018-04-06 11:55 /user/bigdata/nyc_open_data/x2hp-8ukt.json
# -rw-rwx---+  3 rpd302 bigdata       87688 2018-04-06 11:55 /user/bigdata/nyc_open_data/x2s6-6d2j.json
# -rw-rwx---+  3 rpd302 bigdata      261768 2018-04-06 11:55 /user/bigdata/nyc_open_data/x3kb-2vbv.json
# -rw-rwx---+  3 rpd302 bigdata    12061202 2018-04-06 11:55 /user/bigdata/nyc_open_data/x4ai-kstz.json
# -rw-rwx---+  3 rpd302 bigdata      370850 2018-04-06 11:55 /user/bigdata/nyc_open_data/x4sg-2jca.json
# -rw-rwx---+  3 rpd302 bigdata       49465 2018-04-06 11:55 /user/bigdata/nyc_open_data/x4ud-jhxu.json
# -rw-rwx---+  3 rpd302 bigdata       12092 2018-04-06 11:55 /user/bigdata/nyc_open_data/x56h-7iwp.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:55 /user/bigdata/nyc_open_data/x57r-az25.json
# -rw-rwx---+  3 rpd302 bigdata     1385926 2018-04-06 11:55 /user/bigdata/nyc_open_data/x5tk-fa54.json
# -rw-rwx---+  3 rpd302 bigdata      173659 2018-04-06 11:55 /user/bigdata/nyc_open_data/x84u-rirx.json
# -rw-rwx---+  3 rpd302 bigdata       20219 2018-04-06 11:55 /user/bigdata/nyc_open_data/x8rc-3utf.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:55 /user/bigdata/nyc_open_data/x9ia-3cjh.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:55 /user/bigdata/nyc_open_data/x9uq-u3qs.json
# -rw-rwx---+  3 rpd302 bigdata       34129 2018-04-06 11:55 /user/bigdata/nyc_open_data/xagh-idmf.json
# -rw-rwx---+  3 rpd302 bigdata       18366 2018-04-06 11:55 /user/bigdata/nyc_open_data/xah7-gu5w.json
# -rw-rwx---+  3 rpd302 bigdata      128745 2018-04-06 11:55 /user/bigdata/nyc_open_data/xahu-rkwn.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:55 /user/bigdata/nyc_open_data/xbvj-gfnw.json
# -rw-rwx---+  3 rpd302 bigdata      101864 2018-04-06 11:55 /user/bigdata/nyc_open_data/xcah-6evp.json
# -rw-rwx---+  3 rpd302 bigdata     1980076 2018-04-06 11:56 /user/bigdata/nyc_open_data/xck4-5xd5.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:56 /user/bigdata/nyc_open_data/xd8h-7j2h.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:56 /user/bigdata/nyc_open_data/xdkk-pvdv.json
# -rw-rwx---+  3 rpd302 bigdata       35810 2018-04-06 11:56 /user/bigdata/nyc_open_data/xdqu-utzq.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:56 /user/bigdata/nyc_open_data/xdsd-mmyu.json
# -rw-rwx---+  3 rpd302 bigdata      478916 2018-04-06 11:56 /user/bigdata/nyc_open_data/xefy-6ent.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:56 /user/bigdata/nyc_open_data/xfhz-rhsk.json
# -rw-rwx---+  3 rpd302 bigdata  2129462962 2018-04-06 11:56 /user/bigdata/nyc_open_data/xfyi-uyt5.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:56 /user/bigdata/nyc_open_data/xg3x-h3g7.json
# -rw-rwx---+  3 rpd302 bigdata       21665 2018-04-06 11:56 /user/bigdata/nyc_open_data/xggi-kgx9.json
# -rw-rwx---+  3 rpd302 bigdata       39355 2018-04-06 11:56 /user/bigdata/nyc_open_data/xgse-vmv6.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:56 /user/bigdata/nyc_open_data/xgwd-7vhd.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:56 /user/bigdata/nyc_open_data/xi5z-cgq7.json
# -rw-rwx---+  3 rpd302 bigdata       30430 2018-04-06 11:56 /user/bigdata/nyc_open_data/xi7c-iiu2.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:56 /user/bigdata/nyc_open_data/xiyt-f6tz.json
# -rw-rwx---+  3 rpd302 bigdata       23634 2018-04-06 11:56 /user/bigdata/nyc_open_data/xj6i-rnxp.json
# -rw-rwx---+  3 rpd302 bigdata      231593 2018-04-06 11:56 /user/bigdata/nyc_open_data/xjcm-e5uy.json
# -rw-rwx---+  3 rpd302 bigdata    40550937 2018-04-06 11:56 /user/bigdata/nyc_open_data/xjfq-wh2d.json
# -rw-rwx---+  3 rpd302 bigdata       82622 2018-04-06 11:56 /user/bigdata/nyc_open_data/xjur-zbxw.json
# -rw-rwx---+  3 rpd302 bigdata       99113 2018-04-06 11:56 /user/bigdata/nyc_open_data/xk6g-r83g.json
# -rw-rwx---+  3 rpd302 bigdata      115324 2018-04-06 11:56 /user/bigdata/nyc_open_data/xkkx-md5q.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:56 /user/bigdata/nyc_open_data/xkzc-675v.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:56 /user/bigdata/nyc_open_data/xmzf-uf2w.json
# -rw-rwx---+  3 rpd302 bigdata       19705 2018-04-06 11:56 /user/bigdata/nyc_open_data/xnje-s6zf.json
# -rw-rwx---+  3 rpd302 bigdata       17664 2018-04-06 11:56 /user/bigdata/nyc_open_data/xnpc-vebg.json
# -rw-rwx---+  3 rpd302 bigdata      155044 2018-04-06 11:56 /user/bigdata/nyc_open_data/xp25-gxux.json
# -rw-rwx---+  3 rpd302 bigdata       18922 2018-04-06 11:56 /user/bigdata/nyc_open_data/xpcf-tg2m.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:56 /user/bigdata/nyc_open_data/xphm-ebrs.json
# -rw-rwx---+  3 rpd302 bigdata     1852386 2018-04-06 11:56 /user/bigdata/nyc_open_data/xqmg-7z3j.json
# -rw-rwx---+  3 rpd302 bigdata    11278077 2018-04-06 11:56 /user/bigdata/nyc_open_data/xsmd-g5j6.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:56 /user/bigdata/nyc_open_data/xswq-wnv9.json
# -rw-rwx---+  3 rpd302 bigdata       16147 2018-04-06 11:56 /user/bigdata/nyc_open_data/xt3u-h44z.json
# -rw-rwx---+  3 rpd302 bigdata    24623462 2018-04-06 11:56 /user/bigdata/nyc_open_data/xubg-57si.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:56 /user/bigdata/nyc_open_data/xuek-2su9.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:56 /user/bigdata/nyc_open_data/xuk2-nczf.json
# -rw-rwx---+  3 rpd302 bigdata      568378 2018-04-06 11:56 /user/bigdata/nyc_open_data/xw3c-8982.json
# -rw-rwx---+  3 rpd302 bigdata   137199745 2018-04-06 11:56 /user/bigdata/nyc_open_data/xwxx-rnki.json
# -rw-rwx---+  3 rpd302 bigdata       64339 2018-04-06 11:56 /user/bigdata/nyc_open_data/xx2p-4jnq.json
# -rw-rwx---+  3 rpd302 bigdata   210883522 2018-04-06 11:56 /user/bigdata/nyc_open_data/xx67-kt59.json
# -rw-rwx---+  3 rpd302 bigdata    21024962 2018-04-06 11:56 /user/bigdata/nyc_open_data/xx92-6788.json
# -rw-rwx---+  3 rpd302 bigdata       43606 2018-04-06 11:56 /user/bigdata/nyc_open_data/xxf6-krb6.json
# -rw-rwx---+  3 rpd302 bigdata       30633 2018-04-06 11:56 /user/bigdata/nyc_open_data/xxjs-y9yk.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:56 /user/bigdata/nyc_open_data/xy43-qc25.json
# -rw-rwx---+  3 rpd302 bigdata       28680 2018-04-06 11:56 /user/bigdata/nyc_open_data/xywu-7bv9.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:56 /user/bigdata/nyc_open_data/xz57-5ygp.json
# -rw-rwx---+  3 rpd302 bigdata   355320978 2018-04-06 11:56 /user/bigdata/nyc_open_data/xzj8-i3jk.json
# -rw-rwx---+  3 rpd302 bigdata      160761 2018-04-06 11:56 /user/bigdata/nyc_open_data/xzy8-qqgf.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:56 /user/bigdata/nyc_open_data/y237-iita.json
# -rw-rwx---+  3 rpd302 bigdata      426096 2018-04-06 11:56 /user/bigdata/nyc_open_data/y3ea-en4q.json
# -rw-rwx---+  3 rpd302 bigdata       29452 2018-04-06 11:56 /user/bigdata/nyc_open_data/y3gq-zv28.json
# -rw-rwx---+  3 rpd302 bigdata      255546 2018-04-06 11:56 /user/bigdata/nyc_open_data/y43c-5n92.json
# -rw-rwx---+  3 rpd302 bigdata     2919725 2018-04-06 11:56 /user/bigdata/nyc_open_data/y4fw-iqfr.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:56 /user/bigdata/nyc_open_data/y4xu-dcu3.json
# -rw-rwx---+  3 rpd302 bigdata        6856 2018-04-06 11:56 /user/bigdata/nyc_open_data/y4yc-78a4.json
# -rw-rwx---+  3 rpd302 bigdata      225352 2018-04-06 11:56 /user/bigdata/nyc_open_data/y52e-hp89.json
# -rw-rwx---+  3 rpd302 bigdata      916079 2018-04-06 11:56 /user/bigdata/nyc_open_data/y6fv-k6p7.json
# -rw-rwx---+  3 rpd302 bigdata       37223 2018-04-06 11:56 /user/bigdata/nyc_open_data/y7z5-rhh5.json
# -rw-rwx---+  3 rpd302 bigdata    13858338 2018-04-06 11:56 /user/bigdata/nyc_open_data/y8bm-tzs3.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:56 /user/bigdata/nyc_open_data/y8tr-23bj.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:56 /user/bigdata/nyc_open_data/yann-8etk.json
# -rw-rwx---+  3 rpd302 bigdata       17153 2018-04-06 11:56 /user/bigdata/nyc_open_data/yanz-4hj5.json
# -rw-rwx---+  3 rpd302 bigdata      500317 2018-04-06 11:56 /user/bigdata/nyc_open_data/yayv-apxh.json
# -rw-rwx---+  3 rpd302 bigdata    11960055 2018-04-06 11:56 /user/bigdata/nyc_open_data/ybcb-4665.json
# -rw-rwx---+  3 rpd302 bigdata       57129 2018-04-06 11:56 /user/bigdata/nyc_open_data/yczb-msz7.json
# -rw-rwx---+  3 rpd302 bigdata      116178 2018-04-06 11:56 /user/bigdata/nyc_open_data/ydbx-4ufw.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:56 /user/bigdata/nyc_open_data/ydj7-rk56.json
# -rw-rwx---+  3 rpd302 bigdata   111156356 2018-04-06 11:56 /user/bigdata/nyc_open_data/ye3c-m4ga.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:56 /user/bigdata/nyc_open_data/ye4j-rp7z.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:56 /user/bigdata/nyc_open_data/ye4r-qpmp.json
# -rw-rwx---+  3 rpd302 bigdata     2522077 2018-04-06 11:56 /user/bigdata/nyc_open_data/yeba-ynb5.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:56 /user/bigdata/nyc_open_data/yfnk-k7r4.json
# -rw-rwx---+  3 rpd302 bigdata       19110 2018-04-06 11:56 /user/bigdata/nyc_open_data/yggg-xf4b.json
# -rw-rwx---+  3 rpd302 bigdata       60695 2018-04-06 11:56 /user/bigdata/nyc_open_data/yhdx-itry.json
# -rw-rwx---+  3 rpd302 bigdata      385037 2018-04-06 11:56 /user/bigdata/nyc_open_data/yhfh-vyns.json
# -rw-rwx---+  3 rpd302 bigdata     3173045 2018-04-06 11:56 /user/bigdata/nyc_open_data/yhuu-4pt3.json
# -rw-rwx---+  3 rpd302 bigdata       35787 2018-04-06 11:56 /user/bigdata/nyc_open_data/yid9-y2bb.json
# -rw-rwx---+  3 rpd302 bigdata      111592 2018-04-06 11:56 /user/bigdata/nyc_open_data/yiet-hu2w.json
# -rw-rwx---+  3 rpd302 bigdata      353270 2018-04-06 11:56 /user/bigdata/nyc_open_data/yig9-9zum.json
# -rw-rwx---+  3 rpd302 bigdata      540672 2018-04-06 11:56 /user/bigdata/nyc_open_data/yini-w76t.json
# -rw-rwx---+  3 rpd302 bigdata       22758 2018-04-06 11:56 /user/bigdata/nyc_open_data/yiqb-mq9h.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:56 /user/bigdata/nyc_open_data/yitc-zzrc.json
# -rw-rwx---+  3 rpd302 bigdata       10418 2018-04-06 11:56 /user/bigdata/nyc_open_data/yizy-365y.json
# -rw-rwx---+  3 rpd302 bigdata       26961 2018-04-06 11:56 /user/bigdata/nyc_open_data/yj3u-pw36.json
# -rw-rwx---+  3 rpd302 bigdata       26757 2018-04-06 11:56 /user/bigdata/nyc_open_data/yjbz-vif8.json
# -rw-rwx---+  3 rpd302 bigdata        6131 2018-04-06 11:56 /user/bigdata/nyc_open_data/yjnr-kh6n.json
# -rw-rwx---+  3 rpd302 bigdata       40945 2018-04-06 11:56 /user/bigdata/nyc_open_data/yjsf-89ae.json
# -rw-rwx---+  3 rpd302 bigdata     2154994 2018-04-06 11:56 /user/bigdata/nyc_open_data/yjub-udmw.json
# -rw-rwx---+  3 rpd302 bigdata       17070 2018-04-06 11:56 /user/bigdata/nyc_open_data/yk6f-pa7p.json
# -rw-rwx---+  3 rpd302 bigdata      592477 2018-04-06 11:56 /user/bigdata/nyc_open_data/ykvb-493p.json
# -rw-rwx---+  3 rpd302 bigdata     1105665 2018-04-06 11:56 /user/bigdata/nyc_open_data/ykx2-pdw8.json
# -rw-rwx---+  3 rpd302 bigdata   261653515 2018-04-06 11:56 /user/bigdata/nyc_open_data/ym2h-u9dt.json
# -rw-rwx---+  3 rpd302 bigdata       78482 2018-04-06 11:56 /user/bigdata/nyc_open_data/ymhw-9cz9.json
# -rw-rwx---+  3 rpd302 bigdata       41640 2018-04-06 11:56 /user/bigdata/nyc_open_data/ymvu-4x4s.json
# -rw-rwx---+  3 rpd302 bigdata    21061908 2018-04-06 11:56 /user/bigdata/nyc_open_data/ynau-kwze.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:56 /user/bigdata/nyc_open_data/yne3-pqfu.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:56 /user/bigdata/nyc_open_data/ynsf-rr5f.json
# -rw-rwx---+  3 rpd302 bigdata       61222 2018-04-06 11:56 /user/bigdata/nyc_open_data/ypbd-r4kg.json
# -rw-rwx---+  3 rpd302 bigdata      230731 2018-04-06 11:56 /user/bigdata/nyc_open_data/ypm7-drwf.json
# -rw-rwx---+  3 rpd302 bigdata      132351 2018-04-06 11:56 /user/bigdata/nyc_open_data/yqkf-i7a4.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:56 /user/bigdata/nyc_open_data/yqz9-aduk.json
# -rw-rwx---+  3 rpd302 bigdata      540098 2018-04-06 11:56 /user/bigdata/nyc_open_data/yrf7-4wry.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:56 /user/bigdata/nyc_open_data/ysjj-vb9j.json
# -rw-rwx---+  3 rpd302 bigdata     6772357 2018-04-06 11:56 /user/bigdata/nyc_open_data/yu9n-iqyk.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:56 /user/bigdata/nyc_open_data/yupw-u2ax.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:56 /user/bigdata/nyc_open_data/yusd-j4xi.json
# -rw-rwx---+  3 rpd302 bigdata    14857490 2018-04-06 11:56 /user/bigdata/nyc_open_data/yuzm-c784.json
# -rw-rwx---+  3 rpd302 bigdata       93258 2018-04-06 11:56 /user/bigdata/nyc_open_data/yv6j-r66f.json
# -rw-rwx---+  3 rpd302 bigdata      639329 2018-04-06 11:56 /user/bigdata/nyc_open_data/yz7z-iupz.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:56 /user/bigdata/nyc_open_data/z42n-hfkv.json
# -rw-rwx---+  3 rpd302 bigdata       43543 2018-04-06 11:56 /user/bigdata/nyc_open_data/z4hj-p6bi.json
# -rw-rwx---+  3 rpd302 bigdata       12205 2018-04-06 11:56 /user/bigdata/nyc_open_data/zcqs-4wtn.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:56 /user/bigdata/nyc_open_data/zhrf-jnt6.json
# -rw-rwx---+  3 rpd302 bigdata     1170725 2018-04-06 11:56 /user/bigdata/nyc_open_data/zkky-n5j3.json
# -rw-rwx---+  3 rpd302 bigdata       88477 2018-04-06 11:56 /user/bigdata/nyc_open_data/zmut-au2w.json
# -rw-rwx---+  3 rpd302 bigdata      121250 2018-04-06 11:56 /user/bigdata/nyc_open_data/zpd4-gad8.json
# -rw-rwx---+  3 rpd302 bigdata    13810754 2018-04-06 11:56 /user/bigdata/nyc_open_data/zs4w-c9cd.json
# -rw-rwx---+  3 rpd302 bigdata      106612 2018-04-06 11:56 /user/bigdata/nyc_open_data/zt9s-n5aj.json
# -rw-rwx---+  3 rpd302 bigdata       18234 2018-04-06 11:56 /user/bigdata/nyc_open_data/zwt9-6u9n.json
# -rw-rwx---+  3 rpd302 bigdata           0 2018-04-06 11:56 /user/bigdata/nyc_open_data/zyf6-z3xt.json




#################
#  nycopendata  #
#################

# 2t2c-qih9.json
# +----+--------------------+---------+-----------+-------------+-----------+-------------+-----+----------------+-------------+--------------------+-----------+-------------------+-------------------+-----------------------+------------------------------------------------+---------------------+--------------------+-------------------+----------------------+-----+
# |:sid|                 :id|:position|:created_at|:created_meta|:updated_at|:updated_meta|:meta|publication_date|agency_number|         agency_name|fiscal_year|personnel_type_code|personnel_type_name|code_for_full_time_ftes|full_time_full_time_equivalents_ft_fte_positions|city_funded_headcount|ifa_funded_headcount|cd_funded_headcount|other_funded_headcount|total|
# +----+--------------------+---------+-----------+-------------+-----------+-------------+-----+----------------+-------------+--------------------+-----------+-------------------+-------------------+-----------------------+------------------------------------------------+---------------------+--------------------+-------------------+----------------------+-----+

# 2t32-hbca.json
# --------+-----+--------------------+------------------+------------+--------------+----------+------------+--------------------+----------------------+------------------+--------------------+----------------------+------------------------+---------------------+-----------------------+---------------------+-----------------------+------------------------+--------------------------+------------------------+--------------------------+------------------------+--------------------------+---------------------+-----------------------+-----------------------+-------------------------+---------------------+-----------------------+------------------------------+--------------------------------+----------------+------------------+--------------------------+----------------------------+----------------------------+------------------------------+--------------------------+----------------------------+--------------------------------+----------------------------------+---------------------------------+-----------------------------------+-------------------------------+---------------------------------+-----------------------------+-------------------------------+
# |:sid|                 :id|:position|:created_at|:created_meta|:updated_at|:updated_meta|:meta|   jurisdiction_name|count_participants|count_female|percent_female|count_male|percent_male|count_gender_unknown|percent_gender_unknown|count_gender_total|percent_gender_total|count_pacific_islander|percent_pacific_islander|count_hispanic_latino|percent_hispanic_latino|count_american_indian|percent_american_indian|count_asian_non_hispanic|percent_asian_non_hispanic|count_white_non_hispanic|percent_white_non_hispanic|count_black_non_hispanic|percent_black_non_hispanic|count_other_ethnicity|percent_other_ethnicity|count_ethnicity_unknown|percent_ethnicity_unknown|count_ethnicity_total|percent_ethnicity_total|count_permanent_resident_alien|percent_permanent_resident_alien|count_us_citizen|percent_us_citizen|count_other_citizen_status|percent_other_citizen_status|count_citizen_status_unknown|percent_citizen_status_unknown|count_citizen_status_total|percent_citizen_status_total|count_receives_public_assistance|percent_receives_public_assistance|count_nreceives_public_assistance|percent_nreceives_public_assistance|count_public_assistance_unknown|percent_public_assistance_unknown|count_public_assistance_total|percent_public_assistance_total|
# +----+--------------------+---------+-----------+-------------+-----------+-------------+-----+--------------------+------------------+------------+--------------+----------+------------+--------------------+----------------------+------------------+--------------------+----------------------+------------------------+---------------------+-----------------------+---------------------+-----------------------+------------------------+--------------------------+------------------------+--------------------------+------------------------+--------------------------+---------------------+-----------------------+-----------------------+-------------------------+---------------------+-----------------------+------------------------------+--------------------------------+----------------+------------------+--------------------------+----------------------------+----------------------------+------------------------------+--------------------------+----------------------------+--------------------------------+----------------------------------+---------------------------------+-----------------------------------+-------------------------------+---------------------------------+-----------------------------+-------------------------------+

# 2uk5-v8da.json
# +----+--------------------+---------+-----------+-------------+-----------+-------------+-----+-----+----+-----------+-------------+----------------+--------+-------+--------+-------+--------+-------+--------+-------+----------+---------+
# |:sid|                 :id|:position|:created_at|:created_meta|:updated_at|:updated_meta|:meta|grade|year|   category|number_tested|mean_scale_score|level1_n|level1_|level2_n|level2_|level3_n|level3_|level4_n|level4_|level3_4_n|level3_4_|
# +----+--------------------+---------+-----------+-------------+-----------+-------------+-----+-----+----+-----------+-------------+----------------+--------+-------+--------+-------+--------+-------+--------+-------+----------+---------+

# 2v9c-2k7f.json
# +--------+--------------------+---------+-----------+-------------+-----------+-------------+-----+-------------------+-----------+--------------------+------------------+-----+-----------+-------------------+-------------------+----------------------+-------------------------+
# |    :sid|                 :id|:position|:created_at|:created_meta|:updated_at|:updated_meta|:meta|base_license_number|wave_number|           base_name|               dba|years|week_number|  pickup_start_date|    pickup_end_date|total_dispatched_trips|unique_dispatched_vehicle|
# +--------+--------------------+---------+-----------+-------------+-----------+-------------+-----+-------------------+-----------+--------------------+------------------+-----+-----------+-------------------+-------------------+----------------------+-------------------------+

# 22zm-qrtq.json
#[':sid', ':id', ':position', ':created_at', ':created_meta', ':updated_at', ':updated_meta', ':meta', 'age_of_case_in_months', '_2005_number_of_cases', '_2005_percent_of_docket', '_2006_number_of_cases', '_2006_percent_of_docket', '_2007_number_of_cases', '_2007_percent_of_docket', '_2008_number_of_cases', '_2008_percent_of_docket', '_2009_number_of_cases', '_2009_percent_of_docket']

# 23rb-xz43.json
# [':sid', ':id', ':position', ':created_at', ':created_meta', ':updated_at', ':updated_meta', ':meta', 'manhattan_north', '_2005', '_2006', '_2007', '_2008', '_2009', 'total']

# 24nr-gahi.json
# [':sid', ':id', ':position', ':created_at', ':created_meta', ':updated_at', ':updated_meta', ':meta', 'category', 'subcategory', 'work_type', 'fy15', 'fy16', 'fy17', 'fy18', 'fy19', 'total']

# 25aa-q86c.json
# [':sid', ':id', ':position', ':created_at', ':created_meta', ':updated_at', ':updated_meta', ':meta', 'dbn', 'school_name', 'category', 'year', 'total_enrollment', 'grade_k', 'grade_1', 'grade_2', 'grade_3', 'grade_4', 'grade_5', 'grade_6', 'grade_7', 'grade_8', 'female_1', 'female_2', 'male_1', 'male_2', 'asian_1', 'asian_2', 'black_1', 'black_2', 'hispanic_1', 'hispanic_2', 'other_1', 'other_2', 'white_1', 'white_2', 'ell_spanish_1', 'ell_spanish_2', 'ell_chinese_1', 'ell_chinese_2', 'ell_bengali_1', 'ell_bengali_2', 'ell_arabic_1', 'ell_arabic_2', 'ell_haitian_creole_1', 'ell_haitian_creole_2', 'ell_french_1', 'ell_french_2', 'ell_russian_1', 'ell_russian_2', 'ell_korean_1', 'ell_korean_2', 'ell_urdu_1', 'ell_urdu_2', 'ell_other_1', 'ell_other_2', 'ela_test_takers', 'ela_level_1_1', 'ela_level_1_2', 'ela_level_2_1', 'ela_level_2_2', 'ela_level_3_1', 'ela_level_3_2', 'ela_level_4_1', 'ela_level_4_2', 'ela_l3_l4_1', 'ela_l3_l4_2', 'math_test_takers', 'math_level_1_1', 'math_level_1_2', 'math_level_2_1', 'math_level_2_2', 'math_level_3_1', 'math_level_3_2', 'math_level_4_1', 'math_level_4_2', 'math_l3_l4_1', 'math_l3_l4_2']

# 25cx-4jug.json
# [':sid', ':id', ':position', ':created_at', ':created_meta', ':updated_at', ':updated_meta', ':meta', 'agency', 'mmr_goal', 'critical', 'performance_indicator', 'fy13', 'fy14', 'fy15', 'fy16', 'fy17', 'tgt17', 'tgt18', '_5_yr_trend', 'desired_direction']

# 25th-nujf.json
# [':sid', ':id', ':position', ':created_at', ':created_meta', ':updated_at', ':updated_meta', ':meta', 'brth_yr', 'gndr', 'ethcty', 'nm', 'cnt', 'rnk']

# 26kp-bgdh.json
# [':sid', ':id', ':position', ':created_at', ':created_meta', ':updated_at', ':updated_meta', ':meta', 'grade', 'year', 'category', 'number_tested', 'mean_scale_score', 'level_1_1', 'level_1_2', 'level_2_1', 'level_2_2', 'level_3_1', 'level_3_2', 'level_4_1', 'level_4_2', 'level_3_4_1', 'level_3_4_2']

# 26ze-s5bx.json
# [':sid', ':id', ':position', ':created_at', ':created_meta', ':updated_at', ':updated_meta', ':meta', 'fiscal_year', 'inmate_population']
# 2vha-97jm.json
# [':sid', ':id', ':position', ':created_at', ':created_meta', ':updated_at', ':updated_meta', ':meta', 'district', 'grade_level', 'category', 'average_frequency', 'average_minutes', 'of_students_who_are_receiving_the_required_amount_of_physical_education_instruction_1', 'of_students_who_are_receiving_the_required_amount_of_physical_education_instruction_2', 'of_students_who_are_receiving_less_than_the_required_amount_of_physical_education_instruction_1', 'of_students_who_are_receiving_less_than_the_required_amount_of_physical_education_instruction_2', 'of_students_who_have_an_iep_that_recommends_adaptive_physical_education_1', 'of_students_who_have_an_iep_that_recommends_adaptive_physical_education_2']
# 2x8v-d8nh.json
# [':sid', ':id', ':position', ':created_at', ':created_meta', ':updated_at', ':updated_meta', ':meta', 'dbn', 'location_name', 'location_category', 'administrative_district', 'american_indian_alaskan_native_removals', 'american_indian_alaskan_native_principal', 'american_indian_alaskan_native_superintendent', 'american_indian_alaskan_native_expulsions', 'asian_removals', 'asian_principal', 'asian_superintendent', 'asian_expulsions', 'black_removals', 'black_principal', 'black_superintendent', 'black_expulsions', 'hispanic_removals', 'hispanic_principal', 'hispanic_superintendent', 'hispanic_expulsions', 'white_removals', 'white_principal', 'white_superintendent', 'white_expulsions', 'multi_racial_removals', 'multi_racial_principal', 'multi_racial_superintendent', 'multi_racial_expulsions', 'unknown_removals', 'unknown_principal', 'unknown_superintendent', 'unknown_expulsions']
# 3pzk-fyqp.json
# [':sid', ':id', ':position', ':created_at', ':created_meta', ':updated_at', ':updated_meta', ':meta', 'city_council_district', 'of_teachers_assigned_to_teach_health']
# 3qfc-4tta.json
# [':sid', ':id', ':position', ':created_at', ':created_meta', ':updated_at', ':updated_meta', ':meta', 'bronx_condominiums_comparable_properties_boro_block_lot', 'bronx_condominiums_comparable_properties_condo_section', 'bronx_condominiums_comparable_properties_address', 'borough', 'postcode', 'latitude', 'longitude', 'community_board', 'council_district', 'census_tract', 'bin', 'bbl', 'nta', 'bronx_condominiums_comparable_properties_neighborhood', 'bronx_condominiums_comparable_properties_building_classification', 'bronx_condominiums_comparable_properties_total_units', 'bronx_condominiums_comparable_properties_year_built', 'bronx_condominiums_comparable_properties_gross_sqft', 'bronx_condominiums_comparable_properties_estimated_gross_income', 'bronx_condominiums_comparable_properties_gross_income_per_sqft', 'bronx_condominiums_comparable_properties_estimated_expense', 'bronx_condominiums_comparable_properties_expense_per_sqft', 'bronx_condominiums_comparable_properties_net_operating_income', 'bronx_condominiums_comparable_properties_full_market_value', 'bronx_condominiums_comparable_properties_market_value_per_sqft', 'comparable_rental_1_boro_block_lot', 'comparable_rental_1_address', 'comparable_rental_1_neighborhood', 'comparable_rental_1_building_classification', 'comparable_rental_1_total_units', 'comparable_rental_1_year_built', 'comparable_rental_1_gross_sqft', 'comparable_rental_1_estimated_gross_income', 'comparable_rental_1_gross_income_per_sqft', 'comparable_rental_1_estimated_expense', 'comparable_rental_1_expense_per_sqft', 'comparable_rental_1_net_operating_income', 'comparable_rental_1_full_market_value', 'comparable_rental_1_market_value_per_sqft', 'comparable_rental_1_distance_from_condo_in_miles', 'comparable_rental_2_boro_block_lot', 'comparable_rental_2_address', 'comparable_rental_2_neighborhood', 'comparable_rental_2_building_classification', 'comparable_rental_2_total_units', 'comparable_rental_2_year_built', 'comparable_rental_2_gross_sqft', 'comparable_rental_2_estimated_gross_income', 'comparable_rental_2_gross_income_per_sqft', 'comparable_rental_2_estimated_expense', 'comparable_rental_2_expense_per_sqft', 'comparable_rental_2_net_operating_income', 'comparable_rental_2_full_market_value', 'comparable_rental_2_market_value_per_sqft', 'comparable_rental_2_distance_from_condo_in_miles', 'comparable_rental_3_boro_block_lot', 'comparable_rental_3_address', 'comparable_rental_3_neighborhood', 'comparable_rental_3_building_classification', 'comparable_rental_3_total_units', 'comparable_rental_3_year_built', 'comparable_rental_3_gross_sqft', 'comparable_rental_3_estimated_gross_income', 'comparable_rental_3_gross_income_per_sqft', 'comparable_rental_3_estimated_expense', 'comparable_rental_3_expense_per_sqft', 'comparable_rental_3_net_operating_income', 'comparable_rental_3_full_market_value', 'comparable_rental_3_market_value_per_sqft', 'comparable_rental_3_distance_from_condo_in_miles']
# 3qty-g4aq.json
# [':sid', ':id', ':position', ':created_at', ':created_meta', ':updated_at', ':updated_meta', ':meta', 'survey', 'question', 'year', 'prevalence', 'lower95_ci', 'upper95_ci']

# 4tqt-y424.json
# [':sid', ':id', ':position', ':created_at', ':created_meta', ':updated_at', ':updated_meta', ':meta', 'school_year', 'vendor_name', 'type_of_service', 'active_employees', 'job_type']

# 4vsa-fhnm.json
# [':sid', ':id', ':position', ':created_at', ':created_meta', ':updated_at', ':updated_meta', ':meta', 'type_of_encounter', '_number_1', '_percent_of_total_1', '_number_2', '_percent_of_total_2', '_number_3', '_percent_of_total_3', '_number_4', '_percent_of_total_4', '_number_5', '_percent_of_total_5']
# 4wf2-7kdu.json
# [':sid', ':id', ':position', ':created_at', ':created_meta', ':updated_at', ':updated_meta', ':meta', 'cb_link_id', 'link_site_id', 'street_address', 'cross_street_1', 'cross_street_2', 'borough', 'zip_code', 'community_board', 'council_district', 'site_in_bid', 'bid', 'zoning', 'neighborhood_tabulation_area_nta', 'census_tract_ct', 'building_identification_number_bin', 'borough_block_lot_bbl', 'latitude', 'longitude', 'doitt_ntp_issued_a', 'doitt_ntp_expiration_date', 'in_progress_suspended', 'project_status', 'location_1']

# 5r5y-pvs3.json
# [':sid', ':id', ':position', ':created_at', ':created_meta', ':updated_at', ':updated_meta', ':meta', 'program', 'statecity_section8_flag', 'white_families', 'black_families', 'hispanic_families', 'asian_families', 'other_races_families', 'total_families', 'white_female_headed_families', 'black_female_headed_families', 'hispanic_female_headed_families', 'asian_female_headed_families', 'other_races_female_headed_families', 'total_female_headed_families', 'white_male_headed_families', 'black_male_headed_families', 'hispanic_male_headed_families', 'asian_male_headed_families', 'other_races_male_headed_families', 'total_male_headed_families', 'white_population', 'black_population', 'hispanic_population', 'asian_population', 'other_races_population', 'total_population', 'average_white_family_size', 'average_black_family_size', 'average_hispanic_family_size', 'average_asian_family_size', 'average_other_races_family_size', 'average_family_size', 'white_minors_under_18', 'black_minors_under_18', 'hispanic_minors_under_18', 'asian_minors_under_18', 'other_races_minors_under_18', 'total_minors_under_18', 'average_minors_per_white_family', 'average_minors_per_black_family', 'average_minors_per_hispanic_family', 'average_minors_per_asian_family', 'average_minors_per_other_races_family', 'average_minors_per_family', 'white_minors_as_percent_of_population', 'black_minors_as_percent_of_population', 'hispanic_minors_as_percent_of_population', 'asian_minors_as_percent_of_population', 'other_races_minors_as_percent_of_population', 'total_minors_as_percent_of_population', 'white_average_total_gross_income', 'black_average_total_gross_income', 'hispanic_average_total_gross_income', 'asian_average_total_gross_income', 'other_races_average_total_gross_income', 'all_average_total_gross_income', 'white_average_gross_rent', 'black_average_gross_rent', 'hispanic_average_gross_rent', 'asian_average_gross_rent', 'other_races_average_gross_rent', 'all_average_gross_rent', 'white_hoh_62_years_and_over', 'black_hoh_62_years_and_over', 'hispanic_hoh_62_years_and_over', 'asian_hoh_62_years_and_over', 'other_races_hoh_62_years_and_over', 'total_hoh_62_years_and_over', 'white_hoh_62_years_and_over_as_percent_of_families', 'black_hoh_62_years_and_over_as_percent_of_families', 'hispanic_hoh_62_years_and_over_as_percent_of_families', 'asian_hoh_62_years_and_over_as_percent_of_families', 'other_races_hoh_62_years_and_over_as_percent_of_families', 'total_hoh_62_years_and_over_as_percent_of_families', 'white_female_headed_hoh_62_years_and_over', 'black_female_headed_hoh_62_years_and_over', 'hispanic_female_headed_hoh_62_years_and_over', 'asian_female_headed_hoh_62_years_and_over', 'other_races_female_headed_hoh_62_years_and_over', 'total_female_headed_hoh_62_years_and_over', 'white_male_headed_hoh_62_years_and_over', 'black_male_headed_hoh_62_years_and_over', 'hispanic_male_headed_hoh_62_years_and_over', 'asian_male_headed_hoh_62_years_and_over', 'other_races_male_headed_hoh_62_years_and_over', 'total_male_headed_hoh_62_years_and_over', 'white_elderly_single_person_families', 'black_elderly_single_person_families', 'hispanic_elderly_single_person_families', 'asian_elderly_single_person_families', 'other_races_elderly_single_person_families', 'total_elderly_single_person_families', 'white_elderly_population', 'black_elderly_population', 'hispanic_elderly_population', 'asian_elderly_population', 'other_races_elderly_population', 'total_elderly_population', 'white_62_years_and_over_as_percent_of_population', 'black_62_years_and_over_as_percent_of_population', 'hispanic_62_years_and_over_as_percent_of_population', 'asian_62_years_and_over_as_percent_of_population', 'other_races_62_years_and_over_as_percent_of_population', 'total_62_years_and_over_as_percent_of_population', 'white_families_on_welfare', 'black_families_on_welfare', 'hispanic_families_on_welfare', 'asian_families_on_welfare', 'other_races_families_on_welfare', 'total_families_on_welfare', 'white_families_on_welfare_and_hoh_elderly', 'black_families_on_welfare_and_hoh_elderly', 'hispanic_families_on_welfare_and_hoh_elderly', 'asian_families_on_welfare_and_hoh_elderly', 'other_races_families_on_welfare_and_hoh_elderly', 'total_families_on_welfare_and_hoh_elderly', 'white_families_on_full_welfare', 'black_families_on_full_welfare', 'hispanic_families_on_full_welfare', 'asian_families_on_full_welfare', 'other_races_families_on_full_welfare', 'total_families_on_full_welfare', 'white_families_on_welfare_as_percent_of_families', 'black_families_on_welfare_as_percent_of_families', 'hispanic_families_on_welfare_as_percent_of_families', 'asian_families_on_welfare_as_percent_of_families', 'other_races_families_on_welfare_as_percent_of_families', 'total_families_on_welfare_as_percent_of_families', 'white_single_parent_grandparent_with_minors', 'black_single_parent_grandparent_with_minors', 'hispanic_single_parent_grandparent_with_minors', 'asian_single_parent_grandparent_families_with_minors', 'other_races_single_parent_grandparent_with_minors', 'total_single_parent_grandparent_families_with_minors', 'white_female_headed_single_parent_grandparent_with_minors', 'black_female_headed_single_parent_grandparent_with_minors', 'hispanic_female_headed_single_parent_grandparent_with_minors', 'asian_female_headed_single_parent_grandparent_with_minors', 'other_races_female_headed_single_parent_grandparent_with_minors', 'total_female_headed_single_parent_grandparent_with_minors', 'white_male_headed_single_parent_grandparent_with_minors', 'black_male_headed_single_parent_grandparent_with_minors', 'hispanic_male_headed_single_parent_grandparent_with_minors', 'asian_male_headed_single_parent_grandparent_with_minors', 'other_races_male_headed_single_parent_grandparent_with_minors', 'total_male_headed_single_parent_grandparent_with_minors', 'white_single_parent_grandparent_families_on_welfare', 'black_single_parent_grandparent_families_on_welfare', 'hispanic_single_parent_grandparent_families_on_welfare', 'asian_single_parent_grandparent_families_on_welfare', 'other_races_single_parent_grandparent_families_on_welfare', 'total_single_parent_grandparent_families_on_welfare', 'white_single_parent_grandparent_with_minors_as_of_families', 'black_single_parent_grandparent_with_minors_as_of_families', 'hispanic_single_parent_grandparent_with_minors_as_of_families', 'asian_single_parent_grandparent_with_minors_as_of_families', 'other_races_single_parent_grandpare_with_minors_as_of_families', 'total_single_parent_grandparent_with_minors_as_of_families', 'white_families_1_or_more_employed', 'black_families_1_or_more_employed', 'hispanic_families_1_or_more_employed', 'asian_families_1_or_more_employed', 'other_races_families_1_or_more_employed', 'total_families_1_or_more_employed', 'white_families_1_or_more_employed_as_percent_of_families', 'black_families_1_or_more_employed_as_percent_of_families', 'hispanic_families_1_or_more_employed_of_families', 'asian_families_1_or_more_employed_as_percent_of_families', 'other_races_families_1_or_more_employed_of_families', 'total_families_1_or_more_employed_as_percent_of_families', 'white_families_2nd_adult_employed', 'black_families_2nd_adult_employed', 'hispanic_families_2nd_adult_employed', 'asian_families_2nd_adult_employed', 'other_races_families_2nd_adult_employed', 'total_families_2nd_adult_employed', 'white_families_average_years_in_public_housing', 'black_families_average_years_in_public_housing', 'hispanic_families_average_years_in_public_housing', 'asian_families_average_years_in_public_housing', 'other_races_families_average_years_in_public_housing', 'all_families_average_years_in_public_housing', 'residents_under_4', 'residents_4_to_5', 'residents_6_to_9', 'residents_10_to_13', 'residents_14_to_17', 'residents_18_to_20', 'residents_21_to_49', 'residents_50_to_61']
# 5rsf-y7wv.json
# [':sid', ':id', ':position', ':created_at', ':created_meta', ':updated_at', ':updated_meta', ':meta', 'unique_key', 'created_date', 'closed_date', 'agency', 'agency_name', 'complaint_type', 'descriptor', 'location_type', 'incident_zip', 'incident_address', 'street_name', 'cross_street_1', 'cross_street_2', 'intersection_street_1', 'intersection_street_2', 'address_type', 'city', 'landmark', 'facility_type', 'status', 'due_date', 'resolution_action_updated_date', 'community_board', 'borough', 'x_coordinate_state_plane_', 'y_coordinate_state_plane_', 'park_facility_name', 'park_borough', 'school_name', 'school_number', 'school_region', 'school_code', 'school_phone_number', 'school_address', 'school_city', 'school_state', 'school_zip', 'school_not_found', 'school_or_citywide_complaint', 'vehicle_type', 'taxi_company_borough', 'taxi_pick_up_location', 'bridge_highway_name', 'bridge_highway_direction', 'road_ramp', 'bridge_highway_segment', 'garage_lot_name', 'ferry_direction', 'ferry_terminal_name', 'latitude', 'longitude', 'location']


# 5t4n-d72c.json
# [':sid', ':id', ':position', ':created_at', ':created_meta', ':updated_at', ':updated_meta', ':meta', 'year', 'area', 'homeless_estimates']
# 5tub-eh45.json
# [':sid', ':id', ':position', ':created_at', ':created_meta', ':updated_at', ':updated_meta', ':meta', 'license_number', 'name', 'status_code', 'status_description', 'expiration_date', 'last_update_date', 'last_update_time']
# 5uac-w243.json
# [':sid', ':id', ':position', ':created_at', ':created_meta', ':updated_at', ':updated_meta', ':meta', 'cmplnt_num', 'cmplnt_fr_dt', 'cmplnt_fr_tm', 'cmplnt_to_dt', 'cmplnt_to_tm', 'rpt_dt', 'ky_cd', 'ofns_desc', 'pd_cd', 'pd_desc', 'crm_atpt_cptd_cd', 'law_cat_cd', 'juris_desc', 'boro_nm', 'addr_pct_cd', 'loc_of_occur_desc', 'prem_typ_desc', 'parks_nm', 'hadevelopt', 'x_coord_cd', 'y_coord_cd', 'latitude', 'longitude', 'lat_lon']