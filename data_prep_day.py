import pandas as pd
import matplotlib.pyplot as plt

all_merged_data = []

# Read stations.csv
station_data = pd.read_csv("/Users/misak/Documents/Master/10_Visualisation in Data Science/Data/stations.csv")

# Loop through files from 2001 to 2018
for year in range(2001, 2019):
    file_name = f"/Users/misak/Documents/Master/10_Visualisation in Data Science/Data/madrid_{year}.csv"
    
    # Read the year's data
    yearly_data = pd.read_csv(file_name)

    # Merge on 'id'
    merged_data = pd.merge(yearly_data, station_data, left_on="station", right_on="id", how="left")
    
    #print(merged_data)
    all_merged_data.append(merged_data)

combined_data = pd.concat(all_merged_data, ignore_index=True)

# Convert the 'date' column to datetime format in the combined_data DataFrame
combined_data['date'] = pd.to_datetime(combined_data['date'])

combined_data['day'] = combined_data['date'].dt.date
combined_data['year'] = combined_data['date'].dt.year
combined_data['month'] = combined_data['date'].dt.month

# Group by 'station' to calculate averages for numeric columns
averaged_data = combined_data.groupby(['name', 'day', 'year', 'month']).mean(numeric_only=True)
# Convert PM25 to cigarette equivalents per day
averaged_data['Cigarettes'] = averaged_data['PM25'] / 22

averaged_data.to_csv("/Users/misak/Documents/Master/10_Visualisation in Data Science/Data/avg_data_day.csv", index=True)  # Exclude row indices
