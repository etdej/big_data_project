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
        #print(dfData.show())
        print(datasets_path)
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
                inter = inter.intersect(elements)
	
            print(inter.show(100))


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
    cs = Column_selecter([  '5t4n-d72c.json', '5tub-eh45.json', '5uac-w243.json' , '5unr-w4sc.json'])
    #print(cs.get_columns(withword=1, without='23'))
    #cs.propose_similar_columns(1, 2)
    #cs.get_intersection([(0, ':created_at'), (0, ':created_at')])
#spark.clearActiveSession()
#spark.clearDefaultSession()


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