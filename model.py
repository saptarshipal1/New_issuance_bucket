import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import seaborn as sns
from datetime import date

df = pd.read_excel('new_issuance_bucket_ref_data_v_2.xlsx')
df1 = df.copy()

current_fixed_date = pd.to_datetime('2023-04-24',format = '%Y-%m-%d')

def time_standard(df1):
    df1['Dated Date'] = df1['Dated Date'].dt.normalize()
    df1['Maturity'] = df1['Maturity'].dt.normalize()


    df1['date_diff'] = df1['Dated Date']-current_fixed_date
    df1['date_diff'] = df1['date_diff'].values.astype('timedelta64[D]')
    df1['Old_forward_bond']= 0
    df1['Analysis'] = 0
    
    return df1

time_standard(df1)

def old_norm_fwd_bond(df1):
    
    old_bond_cutoff_date = pd.to_datetime('2023-04-17',format = '%Y-%m-%d')

    conditions =(
        (df1['Dated Date']<= old_bond_cutoff_date),
        (df1['date_diff']>= '90 days 00:00:00'),
        ((df1['Dated Date'] > old_bond_cutoff_date) & (df1['date_diff'] < '90 days 00:00:00'))
    )
    values = ['old bond','forward bond','normal bond']
    df1['Old_forward_bond'] = np.select(conditions,values)
    
    return df1

old_norm_fwd_bond(df1)

def bond_categ_logics(df1):

    #Inactive Bonds
    df1.loc[(df1['Rating'] == 'Called') | (df1['Rating'] == 'Matured'),['Analysis']] = 'Bonds inactive pricing'

    # Taxable, New Pref/etm from rating column
    df1.loc[(df1['Rating'].isin(['Pre- refunded','Escrowed'])) & (df1['Bond Type'] == 'TAX'),['Analysis']] = 'Old Bond.New pref etm process.Send to Jan for pricing.'

    # Non Taxable, New Pref/etm from rating column
    df1.loc[(df1['Rating'].isin(['Pre- refunded','Escrowed'])) & (df1['Bond Type'].isin(['GO','REV'])),['Analysis']] = 'Old Bond.New pref etm process.'

    #Secondary Issuance
    df1.loc[(df1['Analysis'] == 0) & (df1['Old_forward_bond']=='old bond') & (df1['Prior Reason'] == 'Secondarily Insured') & (df1['Status Type']=='Active'),['Analysis']] = 'Old Bond.Secondary issuance process'

    #Partially Prerefunded where redemption type is Partially Prerefunded
    df1.loc[(df1['Analysis'] == 0) & (df1['Old_forward_bond']=='old bond') & (df1['Redemption Type'] == 'Partially Prerefunded') & (df1['Status Type']=='Active'),['Analysis']] = 'Old Bond.Partially Prerefunded process'

    #Old bond, new pref etm, not in rating, taxable
    df1.loc[(df1['Analysis'] == 0) & (df1['Old_forward_bond']=='old bond') & (df1['Bond Type']=='TAX') & (df1['Redemption Type'].isin(['Pre-Refunded','Escrowed'])) & (df1['Status Type']=='Active'),['Analysis']] = 'Old Bond.New pref etm process. Send to Jan for latest pricing'

    #Old bond, new pref etm, not in rating, non taxable
    df1.loc[(df1['Analysis'] == 0) & (df1['Old_forward_bond']=='old bond') & (df1['Bond Type'].isin(['GO','REV'])) & (df1['Redemption Type'].isin(['Pre-Refunded','Escrowed'])) & (df1['Status Type']=='Active'),['Analysis']] = 'Old Bond.New pref etm process.Price from latest Trades.'

    #Old bond, redemption type is null, prior reason refunding, prior cusip is not null.
    df1.loc[(df1['Analysis'] == 0) & (df1['Old_forward_bond']=='old bond') & (df1['Redemption Type'].isnull()) & (df1['Status Type']=='Active') & (df1['Prior Reason']=='Refunding') & (df1['Prior Cusip'].notnull()),['Analysis']] = 'Old Bond.Check original cusips redemption type. Most likely partially prerefunded.'

    #Old bond, redemption type is null, prior reason is null, prior cusip is null.
    df1.loc[(df1['Analysis'] == 0) & (df1['Old_forward_bond']=='old bond') & (df1['Redemption Type'].isnull()) & (df1['Status Type']=='Active') & (df1['Prior Reason'].isnull()) & (df1['Prior Cusip'].isnull()),['Analysis']] = 'Old Bond.If latest trade available do bucketing and turn bond on.No Trade info available, turn bond off. Recent trade info NA then bucket and ask analyst for price.'

    #TOBs
    df1.loc[(df1['Analysis'] == 0) & (df1['Old_forward_bond']=='normal bond') & (df1['Debt Type']=='Tender Option Bond'),['Analysis']] = 'Tobs'

    #Forward Bonds
    df1.loc[(df1['Analysis'] == 0) & (df1['Analysis'] == ' ') & (df1['Old_forward_bond']=='forward bond'),['Analysis']] = 'Forward Bond'

    #IG Taxable Bonds
    df1.loc[(df1['Analysis'] == 0) & (df1['Old_forward_bond']=='normal bond') & (df1['Rating'].isin(['A','A+','AA','AA+','AAA','A-','AA-'])) & (df1['Bond Type']=='TAX'),['Analysis']] = 'new issuance taxable'

    #IG MTEMS Bonds
    df1.loc[(df1['Analysis'] == 0) & (df1['Old_forward_bond']=='normal bond') & (df1['Bond Type'].isin(['GO','REV'])) & (df1['Rating'].isin(['A','A+','AA','AA+','AAA','A-','AA-'])) & (df1['Issue Discription'].isin(['Tax-Exempt Mortgage-Backed','Tax-exempt Mortgage-backed','TAX-EXEMPT MORTGAGE-BACKED','TEMS','Tax-Exempt Mortgage-Backed','Tax- Exempt Mortgage - Backed Securities','M-TEBS','Mortgage-Backed Securities'])),['Analysis']] = 'Tax Exempt Mortgage Back Securities Housing Bonds'

    #IG Zero coupon Bonds non callable
    df1.loc[(df1['Analysis'] == 0) & (df1['Old_forward_bond']=='normal bond') & (df1['Rating'].isin(['A','A+','AA','AA+','AAA','A-','AA-'])) & (df1['Coupon Code'] == 'ZERO_COUPON') & (df1['Callable'] == 'No'),['Analysis']] = 'Zero coupon'

    #IG Coupon code not Zero coupon, coupon is zero and Bonds callable
    df1.loc[(df1['Analysis'] == 0) & (df1['Old_forward_bond']=='normal bond') & (df1['Rating'].isin(['A','A+','AA','AA+','AAA','A-','AA-'])) & (df1['Coupon Code'] != 'ZERO_COUPON') & (df1['Coupon'] == 0) & (df1['Callable'] == 'Yes'),['Analysis']] = 'This may not be Zero coupon callable. Check with ref data.'

    #IG Coupon code not Zero coupon, coupon is zero and Bonds non callable
    df1.loc[(df1['Analysis'] == 0) & (df1['Old_forward_bond']=='normal bond') & (df1['Rating'].isin(['A','A+','AA','AA+','AAA','A-','AA-'])) & (df1['Coupon Code'] != 'ZERO_COUPON') & (df1['Coupon'] == 0) & (df1['Callable'] == 'No'),['Analysis']] = 'This may not be Zero coupon. Check with ref data.'

    #IG Zero coupon Bonds callable
    df1.loc[(df1['Analysis'] == 0) & (df1['Old_forward_bond']=='normal bond') & (df1['Rating'].isin(['A','A+','AA','AA+','AAA','A-','AA-'])) & (df1['Coupon Code'] == 'ZERO_COUPON') & (df1['Callable'] == 'Yes'),['Analysis']] = 'Zero coupon callable'

    #IG Variable Bonds
    df1.loc[(df1['Analysis'] == 0) & (df1['Old_forward_bond']=='normal bond') & (df1['Rating'].isin(['A','A+','AA','AA+','AAA','A-','AA-'])) & (df1['Coupon Code']== 'Floating: Floating'),['Analysis']] = 'Variable bonds'

    #IG Variable Index Bonds
    df1.loc[(df1['Analysis'] == 0) & (df1['Old_forward_bond']=='normal bond') & (df1['Rating'].isin(['A','A+','AA','AA+','AAA','A-','AA-'])) & (df1['Coupon Code']== 'Floating: Fixed Margin over Index'),['Analysis']] = 'Variable bonds. Alert Andy for index bonds.'

    #IG PAC Bonds
    df1.loc[(df1['Analysis'] == 0) & (df1['Old_forward_bond']=='normal bond') & (df1['Rating'].isin(['A','A+','AA','AA+','AAA','A-','AA-'])) & (df1['Uop'].str.contains('housing', case=False, regex=True)),['Analysis']] ='Check fo PAC bond.'

    #IG PUT Bonds
    df1.loc[(df1['Analysis'] == 0) & (df1['Old_forward_bond']=='normal bond') & (df1['Rating'].isin(['A','A+','AA','AA+','AAA','A-','AA-'])) & (df1['Put Type']== 'Y') & (df1['Puttable']== 'Yes'),['Analysis']] = 'Put bond'

    #IG Tobacco Settlement Bonds
    df1.loc[(df1['Analysis'] == 0) & (df1['Old_forward_bond']=='normal bond') & (df1['Rating'].isin(['A','A+','AA','AA+','AAA','A-','AA-'])) & (df1['Issue Discription'].str.contains('Tobacco', case=False, regex = True)),['Analysis']] = 'Put in JI Temp. Alert Jim'

    #IG AMT Bonds
    df1.loc[(df1['Analysis'] == 0) & (df1['Old_forward_bond']=='normal bond') & (df1['Rating'].isin(['A','A+','AA','AA+','AAA','A-','AA-'])) & (df1['Amt']== 'Y'),['Analysis']] = 'AMT REV all ratings'

    #IG COP Bonds
    df1.loc[(df1['Analysis'] == 0) & (df1['Old_forward_bond']=='normal bond') & (df1['Rating'].isin(['A','A+','AA','AA+','AAA','A-','AA-'])) & (df1['Cop']== 'Y'),['Analysis']] = 'COP REV all ratings'

    #IG GO BQ A Bonds
    df1.loc[(df1['Analysis'] == 0) & (df1['Old_forward_bond']=='normal bond') & (df1['Bond Type'] == 'GO') & (df1['Rating'].isin(['A'])) & (df1['Bq']== 'Y'),['Analysis']] = ' GO BQ A bonds'

    #IG GO BQ A+ Bonds
    df1.loc[(df1['Analysis'] == 0) & (df1['Old_forward_bond']=='normal bond') & (df1['Bond Type'] == 'GO') & (df1['Rating'].isin(['A+'])) & (df1['Bq']== 'Y'),['Analysis']] = ' GO BQ A+ bonds'

    #IG GO BQ AA Bonds
    df1.loc[(df1['Analysis'] == 0) & (df1['Old_forward_bond']=='normal bond') & (df1['Bond Type'] == 'GO') & (df1['Rating'].isin(['AA'])) & (df1['Bq']== 'Y'),['Analysis']] = ' GO BQ AA bonds'

    #IG GO BQ AA+ Bonds
    df1.loc[(df1['Analysis'] == 0) & (df1['Old_forward_bond']=='normal bond') & (df1['Bond Type'] == 'GO') & (df1['Rating'].isin(['AA+'])) & (df1['Bq']== 'Y'),['Analysis']] = ' GO BQ AA+ bonds'

    #IG GO BQ AAA Bonds
    df1.loc[(df1['Analysis'] == 0) & (df1['Old_forward_bond']=='normal bond') & (df1['Bond Type'] == 'GO') & (df1['Rating'].isin(['AAA'])) & (df1['Bq']== 'Y'),['Analysis']] = ' GO BQ AAA bonds'

    #IG GO BQ A- Bonds
    df1.loc[(df1['Analysis'] == 0) & (df1['Old_forward_bond']=='normal bond') & (df1['Bond Type'] == 'GO') & (df1['Rating'].isin(['A-'])) & (df1['Bq']== 'Y'),['Analysis']] = ' GO BQ A- bonds'

    #IG GO BQ AA- Bonds
    df1.loc[(df1['Analysis'] == 0) & (df1['Old_forward_bond']=='normal bond') & (df1['Bond Type'] == 'GO') & (df1['Rating'].isin(['AA-'])) & (df1['Bq']== 'Y'),['Analysis']] = ' GO BQ AA- bonds'

    #IG REV BQ Bonds
    df1.loc[(df1['Analysis'] == 0) & (df1['Old_forward_bond']=='normal bond') & (df1['Bond Type'] == 'REV') & (df1['Rating'].isin(['A','A+','AA','AA+','AAA','A-','AA-'])) & (df1['Bq']== 'Y'),['Analysis']] = ' REV BQ ALL RATINGS'

    #NR - high yield new issuances
    df1.loc[(df1['Analysis'] == 0) & (df1['Old_forward_bond']=='normal bond') & (df1['Rating'].isin(['BB-','BB+','BBB-','BBB+','BBB','BB','NR'])),['Analysis']] = 'NR - high yield new issuances'

    #Rebalance Cases
    df1.loc[(df1['Analysis'] == 0) & (df1['Old_forward_bond']=='normal bond') & (df1['Rating'].isin(['A','A+','AA','AA+','AAA','A-','AA-'])) & (df1['Amt']== 'N') & (df1['Cop']== 'N') & (df1['Bq']== 'N'),['Analysis']] = ' Rebalance Cases'
    
    return df1

bond_categ_logics(df1)

final_output = df1[['Dated Date', 'Maturity', 'Coupon', 'Coupon Code','Bond Type', 'Rating','Uop', 'Debt Type','Issue Discription','Put Date', 'Put Price'
                    ,'Status Type','Amt', 'Cop', 'Bq','Status Sub Type', 'Prior Cusip', 'Default Type', 'Avg Life Date','Orig Cusip', 'Orig Cusip Type'
                    , 'Prior Cusip.1', 'Prior Reason','Prior Date', 'Offering Price', 'Offering Yield', 'Redemption Date','Redemption Type'
                    , 'date_diff', 'Old_forward_bond', 'Analysis']]