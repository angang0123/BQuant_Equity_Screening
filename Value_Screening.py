'''
This screening allows us to define factors for a security universe and then screen out the securities that 
do not meet a specified threshold for those factors. For this first screening example, we'll perform screening 
using three factors:

*Price to Book Value
*2-Year Average Return on Equity =  (ROEFY−1+ROEFY−2/2)(ROEFY−1+ROEFY−2/2) 
*Cashflow from Operations / Total Assets

Example Code: Creating and Executing the BQL Request for the Screening Factors
We'll define our security universe and request the data for our screening factors. 
Then, we'll rank securities in the FTSE 100 index by these factors and screen out the worst 10% among the securities in each factor.
'''

# Import the required libraries
import bql
import pandas as pd
from collections import OrderedDict

# Instantiate an object to interface with the BQL service
bq = bql.Service()

# Create our screening universe - in this case FTSE 100 Index
bq_univ = bq.univ.members('UKX Index')

# Define BQL data items for price to book ratio
bq_px_to_book = bq.data.px_last(fill='PREV',currency='GBP')/ bq.data.book_val_per_sh(fa_period_type='LTM',currency='GBP')

# Define a composite BQL data item with each BQL Item component of the 2-year average ROE
bq_avg_roe_2y = (bq.data.return_com_eqy(fa_period_offset='-1') 
                 + bq.data.return_com_eqy(fa_period_offset='-2')) / 2

# Define a BQL data item for trailing twelve-month operating cash flow and total assets
cash_from_oper = bq.data.cf_cash_from_oper(fa_period_type='LTM')
tot_asset = bq.data.bs_tot_asset(fa_period_type='LTM')

# Define the factor by using the defined data items
bq_cash_per_asset = cash_from_oper / tot_asset

# Request the number of the index members using BQL count function
id_count = bq.data.id().group().count()
bq_res = bq.execute(bql.Request(bq_univ, {'COUNT': id_count}))
num_of_members = bq_res[0].df()['COUNT']

# Define the threshold rank value which is equvalent to the percentile rank of 80%
threshold_percentage = 0.80
threshold_rank = int(threshold_percentage * num_of_members)

# Define a function to calculate the rank of BQL item
def rank_func(factor):
      return factor.group().znav().rank().ungroup().applyPreferences(Currencycheck="ignore")


# Define the rank of the factor by using the custom rank function
factor_ranks = [rank_func(bq_avg_roe_2y),
                rank_func(bq_px_to_book),
                rank_func(bq_cash_per_asset)]

# Define a BQL criteria item for the factor rank
# This will be used to screen out securities for which 
# the factor rank is less than 20%
criteria = [factor_rank <= threshold_rank for factor_rank in factor_ranks]

# Combine the three criteria items with AND clause
criteria_final = criteria[0]    
for i in range(1, len(criteria)): criteria_final = bq.func.and_(criteria_final, criteria[i])        

# Define a filtered universe by passing the security universe and the criteria
filtered_univ = bq.univ.filter(bq_univ, criteria_final)

# Define an ordered Python dictionary
items_ordered_dict = OrderedDict()

# Populate the dictionary with our screening factors and custom header labels 
items_ordered_dict['AVE_ROE_2Y'] = bq_avg_roe_2y
items_ordered_dict['PX_BOOK_VALUE'] = bq_px_to_book
items_ordered_dict['CASH_PER_ASSET'] = bq_cash_per_asset



# Generate the request using the security universe and dictionary of factors
bq_request = bql.Request(filtered_univ, items_ordered_dict, with_params={"mode": "cached"})

# Execute the request
bq_res = bq.execute(bq_request)

# Define a new DataFrame using custom function
bq_result_df = pd.concat([sir.df()[sir.name] for sir in bq_res], axis=1)

# Display the first five rows to verify the output
bq_result_df.head(5)

