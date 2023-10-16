# -*- coding: utf-8 -*-
#!/usr/bin/env python3

# Porduce scatter plots of relevant columns 

import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import pearsonr


old_data = pd.read_csv('/Users/willstrawson/Documents/PhD/repos/StateSpace/scratch/NPS_and_VPS_results_old.csv')
new_data = pd.read_csv('/Users/willstrawson/Documents/PhD/repos/StateSpace/scratch/pain_dotproduct_vps_2020_long.csv')

# clean old_data
# remove ' in cisc numbers 
old_data['SUB_ID']=old_data['SUB_ID'].str.strip("'")

# Filter columns with 'Unnamed' in their names
filtered_columns = [col for col in old_data.columns if 'Unnamed' not in col]
# Create a new DataFrame with the selected columns
old_data = old_data[filtered_columns]

# change SUB_ID 
old_data.rename(columns={'SUB_ID':'subject_id'}, inplace=True)

# remove whitespace
old_data.columns = old_data.columns.str.replace(' ', '_')

# transform new data to match old data 
# make task_name into columns
# Remove rows where 'canonical_map' contains 'General_vicarious_pain_pattern_unthresholded'
new_data = new_data[~new_data['canonical_map'].str.contains('General_vicarious_pain_pattern_unthresholded')]
# Pivot the DataFrame to create new columns from 'task_name'
pivoted_df = new_data.pivot(index = 'subject_id',columns='task_name', values='dotproduct').fillna(0)

# add pic infrot of these four columnns to match old data 
pivoted_df = pivoted_df.rename(columns={
    'foot_nopain':'pic_foot_nopain',
    'foot_pain':'pic_foot_pain',
    'hand_nopain':'pic_hand_nopain', 
    'hand_pain':'pic_hand_pain'})
pivoted_df.reset_index(inplace=True)

# keep only these columns in both dfs for simplicity 
new_data = pivoted_df[['subject_id','pic_foot_nopain','pic_foot_pain','pic_hand_nopain','pic_hand_pain']]
old_data = old_data[['subject_id','pic_foot_nopain','pic_foot_pain','pic_hand_nopain','pic_hand_pain']]

# Remove rows with NaN values in the 'subject_id' column
old_data = old_data.dropna(subset=['subject_id'])
new_data = new_data.dropna(subset=['subject_id'])

# Convert all columns to str
#old_data = df.astype(str)
#new_data = df.astype(str)

# remove CISC30803 sinnce empty values in old_data
old_data = old_data[~old_data['subject_id'].str.contains('CISC30803')]
new_data = new_data[~new_data['subject_id'].str.contains('CISC30803')]

# Create scatterplots for the same-named columns in both dataframes

fig, axes = plt.subplots(1, len(new_data.columns), figsize=(12, 4))

for i, column in enumerate(new_data.columns):
    print(f'Processing column: {column}')
    x = old_data[column]
    y = new_data[column]

    axes[i].scatter(x, y)
    axes[i].set_xlabel(f'Old Data ({column})')
    axes[i].set_ylabel(f'New Data ({column})')
    if column == 'subject_id':
        continue
    r, _ = pearsonr(x, y)
    axes[i].set_title(f'Scatterplot for {column}\nPearson\'s r = {r:.2f}')
    print(f'Pearson\'s r for {column}: {r:.2f}')

plt.tight_layout()
plt.show()


# Function to remove outliers using Z-score for specific columns while maintaining like-for-like basis
def remove_outliers_like_for_like(old_data, new_data, columns, threshold=3):
    old_data_no_outliers = old_data.copy()
    new_data_no_outliers = new_data.copy()
    for column in columns:
        z_scores_old = np.abs((old_data[column] - old_data[column].mean()) / old_data[column].std())
        z_scores_new = np.abs((new_data[column] - new_data[column].mean()) / new_data[column].std())
        outlier_indices = (z_scores_old >= threshold) | (z_scores_new >= threshold)
        old_data_no_outliers = old_data_no_outliers[~outlier_indices]
        new_data_no_outliers = new_data_no_outliers[~outlier_indices]
    return old_data_no_outliers, new_data_no_outliers

# List of columns for which to remove outliers
columns_to_remove_outliers = ['pic_foot_nopain', 'pic_foot_pain', 'pic_hand_nopain','pic_hand_pain']

# Remove outliers for both old_data and new_data while maintaining like-for-like basis
old_data_no_outliers, new_data_no_outliers = remove_outliers_like_for_like(old_data, new_data, columns_to_remove_outliers)

# Create scatterplots and calculate correlations for corresponding columns
fig, axes = plt.subplots(1, len(columns_to_remove_outliers), figsize=(12, 4))

for i, column in enumerate(columns_to_remove_outliers):
    x = old_data_no_outliers[column]
    y = new_data_no_outliers[column]

    axes[i].scatter(x, y)
    axes[i].set_xlabel(f'Old Data ({column})')
    axes[i].set_ylabel(f'New Data ({column})')
    r, _ = pearsonr(x, y)
    axes[i].set_title(f'Scatterplot for {column}\nPearson\'s r = {r:.2f}')

plt.tight_layout()
plt.show()