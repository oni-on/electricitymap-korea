from datetime import datetime

import pandas as pd

# Based on https://www.tmrow.com/static/9ac35e5c7a5e8c445425664447e809a5/20def/merit-order-curve.png
SOURCE_PRIORITY = {
    1: ['solar', 'hydro', 'wind', 'biomass'],
    2: 'others',
    3: 'nuclear',
    4: 'coal',
    5: 'gas',
    6: 'oil'
    }


def estimate_split(hourly_consumption, capacity_split, source_priorities):
    """
    params:
        hourly_consumption: dataframe containing the columns ['month', 'datetime', total_consumption_average']
        capacity_split: dataframe containing the columns ['date', 'month', 'total_capacity'] and capacity per power source
        priority: dictionary, key = 1, 2, 3..., values = power source
    returns:
        data frame 
    """
    df = hourly_consumption.merge(capacity_split, on='month')
    
    energy_sources = sorted(list(source_priorities.values())[1:]+list(source_priorities.values())[0])

    prod_cols = ['power_production_'+source+'_avg' for source in energy_sources]
    
    df[prod_cols] = pd.DataFrame(columns=prod_cols)
    
    df = df.apply(production_split, axis=1)
    return df[['month','datetime', 'timestamp', 'zone_name', 'total_consumption_average']+prod_cols]


def production_split(row, source_priorities=SOURCE_PRIORITY):
    prio = 0
    production = 0
    consumption = row['total_consumption_average']
    while consumption > production:
        prio+=1
        sources = source_priorities[prio]
        if isinstance(sources, list):
            # the capacity of 1st priority sources (renewables) is very low, no need to check if any of them is marginal
            for source in sources:
                source_capacity = row.loc[source]
                production+=source_capacity
                row['power_production_'+source+'_avg'] = source_capacity
        else:
            source_capacity = row.loc[source_priorities[prio]]

            if consumption - production >= source_capacity:
                production+=source_capacity
                row['power_production_'+sources+'_avg'] = source_capacity
            else: 
                marginal = consumption - production
                row['power_production_'+sources+'_avg'] = marginal
                production+=marginal
    return row


def process_production(df):
    """Transforms the KR data to the right format"""
    # the row with index 2 will be used as column names
    rename_dict = dict(zip(df.columns[1:], df.iloc[2, 1:].values))
    # the first column is date (in korean)
    rename_dict[df.columns[0]] = 'date'
    df = df.rename(columns=rename_dict)
    
    # the first 3 rows contain null values and the column names
    df = df.drop(index=range(3))
    
    df['date'] = pd.to_datetime(df['date'])
    
    # convert all columns except for date to integers
    int_columns = [col for col in df.columns if col!='date']
    df[int_columns] = df[int_columns].astype(int)
    
    # change dataframe shape from wide to long 
    # one row per hour instead of 1 column per hour
    df = df.melt(id_vars='date', value_name='total_consumption_average', var_name='hour')
    
    # convert e.g. 1h to 1:00
    df.loc[df.hour=='24h', 'hour'] = '0h'
    df['hour'] = df['hour'].apply(lambda x: x[:(len(x))-1] + ':00')
    
    # create datetime from date and hour
    df['datetime'] = df['date'].astype(str) + " " + df['hour']
    df['datetime'] = df['datetime'].apply(lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M"))
    df['timestamp'] = df['datetime'].apply(lambda x: datetime.timestamp(x))
    
    df['zone_name'] = 'KR'
    
    df['month'] = df['datetime'].apply(lambda x: datetime.strftime(x, '%Y%m'))
    
    return df[['month', 'datetime', 'timestamp', 'zone_name', 'total_consumption_average']]
    
    
def process_fuel_types(df):
    """Transforms the fuel type data to the right format"""
    # use the first row as column names to fix nested structure
    rename_dict = dict(zip(df_fuel.columns[8:-2], df.loc[0, df_fuel.columns[8:-2]].values))
    df.rename(columns=rename_dict, inplace=True)
    df = df.drop(index=0)
    
    to_float_cols = df.iloc[:,2:].columns
    df[to_float_cols] = df[to_float_cols].astype(float).round(2)
    
    # data for 2019
    df = df.loc[df.Period.str.contains('2019')]
    
    # use the 1st of the month as the date
    df['date'] = pd.to_datetime(df.Period.apply(lambda x: x + '/01'))
    
    df = df.assign(
        coal = lambda x: x['Anthracite\ncoal']+x['Bituminous\ncoal'],
        hydro = lambda x: x['Pumped-Storage']+x['Hydro\nPower*'],
        
    )
    rename_cols = {
        'Nuclear': 'nuclear',
        'LNG': 'gas',
        'Wind\nPower': 'wind',
        'Solar\nPower': 'solar',
        'Oil': 'oil',
        'Bio\nEnergy*': 'biomass',
        'Total': 'total_capacity'
    }
    df = df.rename(columns=rename_cols)
    
    
    df = df[['date']+['coal', 'hydro']+list(rename_cols.values())]
    
    df.insert(df.shape[1]-1, 'others', df['total_capacity']-df.iloc[:,1:-1].sum(axis=1))
 
    df['month'] = df['date'].apply(lambda x: datetime.strftime(x, '%Y%m'))
    
    return df


if __name__ == "__main__":
    df_prod = pd.read_excel('./data/input/bidforecastgen_land_2019.xls')
    df_prod = process_production(df_prod)
    
    df_fuel = pd.read_csv('./data/input/GenerationCapacity_byFuel.csv')
    df_fuel = process_fuel_types(df_fuel)
    
    df_final = estimate_split(df_prod, df_fuel, SOURCE_PRIORITY)
    df_final.drop('month', inplace=True, axis=1)
    df_final = df_final.sort_values('timestamp')
    df_final.to_csv('./data/output/hourly_production_by_source_KR_2019.csv', index=False)