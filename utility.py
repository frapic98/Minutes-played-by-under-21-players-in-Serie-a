#import adfuller
from statsmodels.tsa.stattools import adfuller
import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import grangercausalitytests
import warnings
warnings.filterwarnings("ignore")


def adf_test(data_df):
    test_stat, p_val = [], []
    cv_1pct, cv_5pct, cv_10pct = [], [], []
    for c in data_df.columns: 
        adf_res = adfuller(data_df[c].dropna())
        test_stat.append(adf_res[0])
        p_val.append(adf_res[1])
        cv_1pct.append(adf_res[4]['1%'])
        cv_5pct.append(adf_res[4]['5%'])
        cv_10pct.append(adf_res[4]['10%'])
    adf_res_df = pd.DataFrame({'Test statistic': test_stat, 
                               'p-value': p_val, 
                               'Critical value - 1%': cv_1pct,
                               'Critical value - 5%': cv_5pct,
                               'Critical value - 10%': cv_10pct}, 
                             index=data_df.columns).T
    adf_res_df = adf_res_df.round(4)
    return adf_res_df


def get_all_teams():
    year_url = f"2022-2023"

    squads_actual=pd.read_excel(f"classifica\Classifica_{year_url}.xlsx")
    year_to_subtract = 55
    current_year=2021
    for i in range(year_to_subtract):
        # Calculate the year to use in the URL
        year_url = f"{current_year - i}-{current_year + 1 - i}"
        squads=pd.read_excel(f"classifica\Classifica_{year_url}.xlsx")
        #create a datafram with all the teams on each year
        squads_actual=pd.merge(squads_actual["Squadra"],squads["Squadra"],how="outer",on="Squadra")
        
    squads_actual.set_index("Squadra",inplace=True)
    all_teams=squads_actual.transpose()
    all_teams.columns.name = None
    return all_teams


#maxlag=4
def grangers_causation_matrix(data, variables, test='ssr_chi2test',lag=4, verbose=False):    
    """Check Granger Causality of all possible combinations of the Time series.
    The rows are the response variable, columns are predictors. 
    The values in the table are the P-Values. 
    P-Values lesser than the significance level (0.05), implies 
    the Null Hypothesis that the coefficients of the corresponding past values is 
    zero, that is, the X does not cause Y can be rejected.
    data      : pandas dataframe containing the time series variables
    variables : list containing names of the time series variables.
    """
    df = pd.DataFrame(np.zeros((len(variables), len(variables))), columns=variables, index=variables)
    for c in df.columns:
        for r in df.index:            
            test_result = grangercausalitytests(data[[r, c]], maxlag=lag,verbose=False)
            p_values = [round(test_result[i+1][0][test][1],4) for i in range(lag)]
            #if verbose: print(f'Y = {r}, X = {c}, P Values = {p_values}')
            min_p_value = np.min(p_values)
            df.loc[r, c] = min_p_value
    df.columns = [var + '_x' for var in variables]
    df.index = [var + '_y' for var in variables]
    return df

def granger_test(dataset,maxlag,s,input):    
    test_result=grangercausalitytests(dataset[2:-1],maxlag=5,verbose=False)
    test_result_df=pd.DataFrame(columns=['Lag','Test Statistic','P-value'])
    for i in range(s,maxlag+1):
        test_result_df.loc[i-1]=[i-1,test_result[i][0]['ssr_chi2test'][0],test_result[i][0]['ssr_chi2test'][1]]
    print("---------------------------------------------------------------------------------------------------------")
    print(f"Grenger Causality Test Results for: {input} ")
    print("---------------------------------------------------------------------------------------------------------")
    print(test_result_df)
    return 