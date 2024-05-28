# -*- coding: utf-8 -*-
"""lz_sybil_detection.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1EsqsFbAfqhAFqkbdB4Vz91Jq_BqzbqFb

# Unpacking file
"""

from google.colab import drive
drive.mount('/content/drive')

# Commented out IPython magic to ensure Python compatibility.
# %cd /content/drive/My Drive/

import pickle
import glob
import requests
import pandas as pd

"""Due to the lack of RAM, it was not possible to open the entire dataset via read_csv. The dataset was unpacked in chunks and saved to pickle files. Then the first half of all pickle files was loaded, from which all rows containing addresses from the list of Sybil addresses were removed. Additionally, rows with duplicates in the SOURCE_TRANSACTION_HASH field were removed (in preliminary research, it was found that there are duplicates in this field). Fields that are not used in the analysis (SOURCE_CONTRACT, DESTINATION_TRANSACTION_HASH, DESTINATION_CONTRACT) were also removed. The first half was saved to a new csv file.

The same procedure was then performed for the second half of the pickle files, and the result was saved to a second csv file.

All processes were then reset, and the two prepared csv files were loaded.

## Splitting into pickle files
"""

file_name = '2024-05-15-snapshot1_transactions.csv.gz'

in_path = file_name
out_path = ""
chunk_size = 400000
separator = ","

reader = pd.read_csv(in_path,sep=separator,chunksize=chunk_size,
                    low_memory=False)


for i, chunk in enumerate(reader):
    out_file = out_path + "/data_{}.pkl".format(i+1)
    with open(out_file, "wb") as f:
        pickle.dump(chunk,f,pickle.HIGHEST_PROTOCOL)

"""## Loading the list of Sybils







"""

response = requests.get('https://raw.githubusercontent.com/LayerZero-Labs/sybil-report/main/initialList.txt')

banned_wallets_list = [address for address in response.text.split('\n')]

len(banned_wallets_list)

"""## Loading pickle files in parts"""

pickle_path = ""
data_p_files=[]
for name in glob.glob(pickle_path + "/data_*.pkl"):
   data_p_files.append(name)

len(data_p_files) / 2

"""### Pt 1"""

df = pd.DataFrame([])

for i in range(len(data_p_files[:161])):
   tmp_df = pd.read_pickle(data_p_files[i])
   df = pd.concat([df, tmp_df], ignore_index=True)
   del tmp_df

filtered_by_banned_wallets = df[~df['SENDER_WALLET'].isin(banned_wallets_list)]

(filtered_by_banned_wallets.drop(columns=['SOURCE_CONTRACT',
                                          'DESTINATION_TRANSACTION_HASH',
                                          'DESTINATION_CONTRACT'],
                                 inplace=True)
)

filtered_by_banned_wallets.drop_duplicates(subset=['SOURCE_TRANSACTION_HASH'], inplace=True)

filtered_by_banned_wallets.to_csv('Lz_txns_base_pt1.csv', index=False)

"""## Pt 2"""

df = pd.DataFrame([])

for i in range(161, len(data_p_files)):
  tmp_df = pd.read_pickle(data_p_files[i])
  df = pd.concat([df, tmp_df], ignore_index=True)
  del tmp_df

df.shape

filtered_by_banned_wallets = df[~df['SENDER_WALLET'].isin(banned_wallets_list)]

filtered_by_banned_wallets.shape

(filtered_by_banned_wallets.drop(columns=['SOURCE_CONTRACT',
                                          'DESTINATION_TRANSACTION_HASH',
                                          'DESTINATION_CONTRACT'],
                                 inplace=True)
)

filtered_by_banned_wallets.drop_duplicates(subset=['SOURCE_TRANSACTION_HASH'], inplace=True)

filtered_by_banned_wallets.shape

filtered_by_banned_wallets.to_csv('Lz_txns_base_pt2.csv', index=False)

"""# Loading CSV files







"""

import gc

from datetime import datetime, timedelta

import pandas as pd
import matplotlib.pyplot as plt

pt_1 = pd.read_csv('Lz_txns_base_pt1.csv')

pt_2 = pd.read_csv('Lz_txns_base_pt2.csv')

pt_1.shape

pt_2.shape

gc.collect()

df = pd.concat([pt_1, pt_2], ignore_index=True)

del pt_1

del pt_2

gc.collect()

"""# Data Preprocessing"""

df.info()

"""## Converting the SOURCE_TIMESTAMP_UTC column to datetime format

"""

df['SOURCE_TIMESTAMP_UTC'] = pd.to_datetime(df['SOURCE_TIMESTAMP_UTC'])

df.info()

"""## Missing Values Search"""

df.isna().sum()

"""There is a large number of missing values in the fields NATIVE_DROP_USD and STARGATE_SWAP_USD. At this stage, I will not delete any rows with missing values.

## Duplicate Search

As a precaution, I will again check the SOURCE_TRANSACTION_HASH field; duplicates of this field were previously removed:
"""

df.duplicated(subset=['SOURCE_TRANSACTION_HASH']).sum()

"""349989 duplicated transactions.

Removing duplicates:
"""

df.drop_duplicates(subset=['SOURCE_TRANSACTION_HASH'], inplace=True)

df.shape

gc.collect()

"""# Dataset Reduction

## Counting the Number of Transactions per Wallet
"""

transaction_counts_by_wallet = (
    df.groupby('SENDER_WALLET')['SOURCE_TRANSACTION_HASH']
    .count().reset_index(name='TXNS_COUNT')
)

"""### Boxplot of the number of transactions made by users"""

with plt.style.context('fivethirtyeight'):
    transaction_counts_by_wallet.boxplot(column = 'TXNS_COUNT', figsize = (8, 8))
    plt.xticks(fontsize=18)
    plt.tight_layout()
    plt.savefig('TXNS_COUNT_1.png')

"""The main mass of values is not visible due to the presence of outliers - some users have made around 300 000, around 150 000, and around 50 000 transactions. The main cluster of values is somewhere below 5000 transactions.

Boxplot for wallets that have made fewer than 5000 transactions:
"""

with plt.style.context('fivethirtyeight'):
    (
    transaction_counts_by_wallet[transaction_counts_by_wallet['TXNS_COUNT']<5000]
        .boxplot(column = 'TXNS_COUNT', figsize = (8, 8))
    )
    plt.xticks(fontsize=18)
    plt.tight_layout()
    plt.savefig('TXNS_COUNT_2.png')

"""The main cluster of outliers is located from 1500 transactions, while the main sample is somewhere below.

Boxplot for wallets that have made fewer than 200 transactions:
"""

with plt.style.context('fivethirtyeight'):
    (
    transaction_counts_by_wallet[transaction_counts_by_wallet['TXNS_COUNT']<200]
        .boxplot(column = 'TXNS_COUNT', figsize = (8, 8))
    )
    plt.xticks(fontsize=18)
    plt.tight_layout()
    plt.savefig('TXNS_COUNT_3.png')

"""Even around 60 transactions are still considered outliers.

"""

with plt.style.context('fivethirtyeight'):
    (
    transaction_counts_by_wallet[transaction_counts_by_wallet['TXNS_COUNT']<60]
        .boxplot(column = 'TXNS_COUNT', figsize = (8, 8))
    )
    plt.xticks(fontsize=18)
    plt.tight_layout()
    plt.savefig('TXNS_COUNT_4.png')

transaction_counts_by_wallet['TXNS_COUNT'].median()

"""This graph represents a boxplot, a standardized way of displaying the distribution of data based on a five-number summary: minimum, first quartile (Q1), median, third quartile (Q3), and maximum.

- The yellow line (second quartile) is the median, which means 50% of users made 1-4 transactions.
-
From the yellow line to the end of the "box" (third quartile) represents the next 25% of users, who made more than 4 up to 17 transactions.

- The line ending with a black border (fourth quartile) represents the next 25% of users, who made from 17 to 41 transactions.

### How many is this in numbers:

1-4 transactions were made by 2,596,928 users:
"""

transaction_counts_by_wallet[transaction_counts_by_wallet['TXNS_COUNT']<=4]['SENDER_WALLET'].count()

"""more than 4 and less than 18 transactions were made by 843,630 users:"""

transaction_counts_by_wallet[(transaction_counts_by_wallet['TXNS_COUNT']>4)&
                            (transaction_counts_by_wallet['TXNS_COUNT']<=17)]['SENDER_WALLET'].count()

"""more than 17 and less than 42 transactions were made by 766,247 users:"""

transaction_counts_by_wallet[(transaction_counts_by_wallet['TXNS_COUNT']>17)&
                            (transaction_counts_by_wallet['TXNS_COUNT']<=41)]['SENDER_WALLET'].count()

"""More than 41 transactions were made by 809,162 users. This group is the most diverse, as all values are statistical outliers - there are those who made 41 transactions, and there are those who made more than 300,000:"""

transaction_counts_by_wallet[transaction_counts_by_wallet['TXNS_COUNT']>41]['SENDER_WALLET'].count()

"""For further analysis of user behavior to identify users who abuse the system, it is necessary to reduce the dataset. I think it would be reasonable to remove everyone up to the last segment of the boxplot - those who made 17 or fewer transactions. Of course, there may still be Sybils among them, but it is necessary to reduce the "noise" in the data to focus on those who have tried the most to manipulate the metrics."""

df = df.merge(transaction_counts_by_wallet, on='SENDER_WALLET', how='left')

df

del transaction_counts_by_wallet

filter_user_by_tx_number = df['TXNS_COUNT']<=17

df_ready = df[~(filter_user_by_tx_number)]

df_ready

del df

gc.collect()

"""# Analysis

I will split the time and date into different columns:
"""

df_ready['DATE'] = df_ready['SOURCE_TIMESTAMP_UTC'].dt.date

df_ready['TIME'] = df_ready['SOURCE_TIMESTAMP_UTC'].dt.time

"""Sorting the dataset by date:"""

df_ready.sort_values(by='SOURCE_TIMESTAMP_UTC', inplace=True)

df_ready['SOURCE_TIMESTAMP_UTC']

"""## 1. Searching for short "robotic" intervals between transactions

Counting the number of transactions users made each day:
"""

txns_within_day_by_wallet = (
    df_ready.groupby(['SENDER_WALLET', 'DATE'])['SOURCE_TRANSACTION_HASH'].count()
    .reset_index(name='TXNS_WITHIN_DAY_COUNT')
)

txns_within_day_by_wallet

"""Adding data to the overall dataset:"""

df_ready = df_ready.merge(txns_within_day_by_wallet, on=['SENDER_WALLET', 'DATE'], how='left')

df_ready

del txns_within_day_by_wallet

gc.collect()

"""Calculating the time in minutes between intervals, if there is 1 transaction per day, it will be NaN, also if the first iteration is for the day, it will be NaN, and then the time between intervals:"""

df_ready['INTERVAL_MINUTES'] = (
    df_ready.groupby(['SENDER_WALLET', 'DATE'])['SOURCE_TIMESTAMP_UTC']
    .diff().dt.total_seconds() / 60
)

df_ready.head()

df_ready.dropna(subset=['TXNS_COUNT', 'TXNS_WITHIN_DAY_COUNT'], inplace=True)

df_ready[['TXNS_COUNT', 'TXNS_WITHIN_DAY_COUNT']] = df_ready[['TXNS_COUNT', 'TXNS_WITHIN_DAY_COUNT']].astype(int)

"""Boxplot of the interval between transactions for users with more than 1 transaction per day:"""

with plt.style.context('fivethirtyeight'):
    (
    df_ready[df_ready['TXNS_WITHIN_DAY_COUNT']>1]
        .boxplot(column = 'INTERVAL_MINUTES', figsize = (8, 8))
    )
    plt.xticks(fontsize=18)
    plt.tight_layout()
    plt.savefig('INTERVAL_MINUTES_1.png')

"""There are many outliers, limiting INTERVAL_MINUTES to 80 minutes:

"""

with plt.style.context('fivethirtyeight'):
    (
    df_ready[(df_ready['TXNS_WITHIN_DAY_COUNT']>1)&
          (df_ready['INTERVAL_MINUTES']<80)]
        .boxplot(column = 'INTERVAL_MINUTES', figsize = (8, 8))
    )
    plt.xticks(fontsize=18)
    plt.tight_layout()
    plt.savefig('INTERVAL_MINUTES_2.png')

"""In the first quartile, there are users with intervals of approximately 1 minute.

More precisely in numbers, percentiles are chosen by 20%:
"""

(df_ready[(df_ready['TXNS_WITHIN_DAY_COUNT']>1)&(df_ready['INTERVAL_MINUTES']<80)]
['INTERVAL_MINUTES'].quantile([.2, .4, .6, .8]).to_dict())

"""In the first segment, users have intervals from 0 seconds to 60 seconds.

What is the distribution among those who have intervals less than 60 seconds:
"""

df_ready[df_ready['INTERVAL_MINUTES']<0.66]['INTERVAL_MINUTES'].quantile([.2, .4, .6, .8]).to_dict()

"""This means that among users with intervals up to 0,66 seconds, 20% have transactions with intervals up to 8 seconds, the next 20% from 8 to 0.21 seconds, the next from 21 to 35, the next from 35 to 50 seconds, and further more than 50 seconds. I think the shortest intervals should be the first 20% - from 0 seconds to 8 seconds. I will calculate how many such short transactions there are for users:"""

less_than_8_sec_interval = (df_ready[df_ready['INTERVAL_MINUTES']<=0.083]
                               .groupby(['SENDER_WALLET'])['INTERVAL_MINUTES']
                             .count()
                             .reset_index(name='LESS_8_SEC_COUNT'))

df_ready = df_ready.merge(less_than_8_sec_interval, on='SENDER_WALLET', how='left')

df_ready

del less_than_8_sec_interval

"""Let's consider these accounts from different angles.

Slice for users who made more than 1 transaction with an interval of 8 seconds or less. Percentiles 20%:
"""

(
    df_ready[df_ready['LESS_8_SEC_COUNT']>=1].groupby('SENDER_WALLET')
    ['LESS_8_SEC_COUNT'].first().reset_index()['LESS_8_SEC_COUNT']
    .quantile([.2, .4, .6, .8]).to_dict()

)

"""20% of the sample made 1 transaction with a short interval, the next 20% made 2 short transactions, the next 20% made between 2 to 4 short transactions, the next made between 4 to 10 short transactions, and the last 20% made more than 10 short transactions.

Quantitative count:
"""

(
    df_ready[df_ready['LESS_8_SEC_COUNT']>=1].groupby('SENDER_WALLET')
    ['LESS_8_SEC_COUNT'].first().reset_index()['LESS_8_SEC_COUNT'].value_counts()

)

"""72709 accounts made 1 transaction with a short interval, 28667 accounts made 2, 17813 accounts made 3, and so on. There are accounts that made 569 or 632 such transactions.

I think we can confidently include accounts with 3 or more such transactions in the Sybil list, but accounts with 2 such transactions raise questions. To make a decision, I will look at several examples.

Slice for accounts with 2 short transactions:
"""

df_ready[df_ready['LESS_8_SEC_COUNT'] == 2][['SENDER_WALLET', 'TXNS_COUNT']]

"""Example #1 from the list:

"""

(
    df_ready[df_ready['SENDER_WALLET'] == '0x784ca853277fe20b17c06c63958add91b047c166']
    [['SOURCE_CHAIN', 'DESTINATION_CHAIN', 'SOURCE_TIMESTAMP_UTC',
      'TXNS_WITHIN_DAY_COUNT', 'INTERVAL_MINUTES']].head(60)
)

"""This account made a total of 255 transactions. I didn't even get to the transactions with an interval of less than 8 seconds because at the very beginning of the list, there is a series of similar transactions with very short intervals.

Example #2 from the list:
"""

df_ready[df_ready['SENDER_WALLET'] == '0xbcd623d028b059a053fc397eb6674d835b5e3c9d']

"""3 transactions with intervals of 6 and 5 seconds, also with identical amounts in these transactions: Stargate - 49.922655 USD.

Example #3 from the list:
"""

df_ready[df_ready['SENDER_WALLET'] == '0x478a3565e474cb46e45312c08796a19541fe1859'].head(60)

"""13 transactions with very short intervals, some of which have 0 seconds intervals, from BNB Chain to Kava and Moonbeam through Merkly.

**I think all three examples taken from the list manually can be interpreted as Sybils, so accounts with 2 short intervals will be added to the list.**<br> Also, the last example inspired me to look at examples of accounts with 1 short transaction.

To be slightly more objective, I will add a count of the number of intervals from the second percentile - from 8 секунда minutes to 21 секунды:
"""

less_than_21_sec_interval = (df_ready[(df_ready['INTERVAL_MINUTES']>=0.08)&
                                   (df_ready['INTERVAL_MINUTES']<=0.21)]
                               .groupby(['SENDER_WALLET'])['INTERVAL_MINUTES']
                             .count()
                             .reset_index(name='LESS_21_SEC_COUNT'))

df_ready = df_ready.merge(less_than_21_sec_interval, on='SENDER_WALLET', how='left')

del less_than_21_sec_interval

"""Taking a slice of users who have one interval between transactions less than 8 seconds, and also have more than 1 interval less than 21 seconds:"""

df_ready[(df_ready['LESS_8_SEC_COUNT'] == 1)&(df_ready['LESS_21_SEC_COUNT'] > 1)][['SENDER_WALLET', 'TXNS_COUNT']]

"""Example #1 from the list:"""

df_ready[df_ready['SENDER_WALLET'] == '0xbc61933d21ada45ba53044804cfd3e8b2831b531'].head(60)

"""A series of 25 transactions with very short intervals, including 0 seconds. All transactions are from different networks to different networks.

Example #2 from the list:
"""

df_ready[df_ready['SENDER_WALLET'] == '0x00286e56b210d91ecd0d0a3009c3c9ce2d111ac5'].head(60)

"""26 transactions per session with different intervals, including short intervals, including 0 seconds. Also, very similar amounts in transactions indicate weak randomization when using software.

**Based on 2 randomly selected examples, I conclude that the presence of short transactions up to 21 seconds and the presence of transactions from 0 to 21 seconds indicate the use of software in these accounts.**

### List formation

Accounts with 2 very short transactions:
"""

less_than_8_sec_list = (df_ready[df_ready['LESS_8_SEC_COUNT'] >= 2]['SENDER_WALLET'].unique().tolist())

len(less_than_8_sec_list)

"""Accounts that meet both conditions:

- Have one transaction with an interval up to 8 seconds.
- Have transactions with intervals from 8 to 21 seconds.
"""

list_less_8_sec_and_less_21sec = (df_ready[(df_ready['LESS_8_SEC_COUNT'] == 1)&
        (df_ready['LESS_21_SEC_COUNT'] > 1)]
 ['SENDER_WALLET'].unique().tolist())

len(list_less_8_sec_and_less_21sec)

less_than_8_sec_list.extend(list_less_8_sec_and_less_21sec)

list_of_sybils_with_short_intervals = less_than_8_sec_list

len(list_of_sybils_with_short_intervals)

with open('sybils_first_list.txt', 'w') as file:
    for item in list_of_sybils_with_short_intervals:
        file.write("%s\n" % item)

"""### Deleting transactions from these addresses from the overall dataset"""

df_after_filtering = df_ready[~df_ready['SENDER_WALLET'].isin(list_of_sybils_with_short_intervals)]

df_after_filtering

del df_ready

gc.collect()

"""## 2. Identifying weak randomization when using automation

The idea of this point is that accounts using software randomize the values of certain parameters, including:

- the number of transactions per session
- intervals between transactions<br>

The software uses something like the python random module and functions like randint() and choice(). We can try to find transactions where there was "weak" randomization, when the user set short ranges.

### How to do this

Calculate the median and mean of each parameter, and then divide the mean by the median. The closer the value is to 1, the weaker the randomization. Here's how it works:

- The median is a stable parameter that points exactly to the middle of all sorted values.
- The mean is subject to strong fluctuations; the greater the difference between the values, the more the mean will be "pulled" towards the outlier.<br>
<br>
The more similar the median and the mean, the less the values in the sample differ, i.e., the weaker the randomization.

To start, I will identify accounts that did not make multiple transactions in one day, i.e., 1 day - 1 transaction. In such accounts, it is not possible to determine randomization based on the number of transactions per session and the randomization of intervals between transactions.

The number of intervals between transactions, if there are 0 intervals, means that the user did not have multiple transactions on any day:
"""

txns_interval_count = (
    df_after_filtering.groupby('SENDER_WALLET')['INTERVAL_MINUTES']
    .count().reset_index(name='NUM_OF_INTERVALS')
)

df_after_filtering = df_after_filtering.merge(txns_interval_count, on='SENDER_WALLET', how='left')

del txns_interval_count

df_after_filtering = df_after_filtering[df_after_filtering['NUM_OF_INTERVALS'] != 0 ]

"""To better calculate the ratio of the median to the mean, it is necessary to limit the sample so that the median and mean values themselves are more objective.

Boxplot of the number of intervals:
"""

with plt.style.context('fivethirtyeight'):
    (
    df_after_filtering.boxplot(column = 'NUM_OF_INTERVALS', figsize = (8, 8))
    )
    plt.xticks(fontsize=18)
    plt.tight_layout()
    plt.savefig('NUM_OF_INTERVALS_1.png')

"""Limiting the dataset to 20 intervals:"""

with plt.style.context('fivethirtyeight'):
    (
    df_after_filtering[df_after_filtering['NUM_OF_INTERVALS']<20]
        .boxplot(column = 'NUM_OF_INTERVALS', figsize = (8, 8))
    )
    plt.xticks(fontsize=18)
    plt.tight_layout()
    plt.savefig('NUM_OF_INTERVALS_2.png')

"""I will take a slice based on whether the user has at least 9 intervals among all transactions:"""

df_after_filtering = df_after_filtering[df_after_filtering['NUM_OF_INTERVALS']>=9]

df_after_filtering

gc.collect()

"""### Calculating the median and mean for the number of transactions made each day

Median number of transactions made for all days:
"""

median_txns_num_within_session = (
    df_after_filtering.groupby(['SENDER_WALLET'])['TXNS_WITHIN_DAY_COUNT']
    .median().reset_index(name='MEDIAN_TXNS_NUM_WITHIN_SESSION')
)

df_after_filtering = df_after_filtering.merge(median_txns_num_within_session, on='SENDER_WALLET', how='left')

del median_txns_num_within_session

"""Mean number of transactions made for all days:"""

mean_txns_num_within_session = (
    df_after_filtering.groupby(['SENDER_WALLET'])['TXNS_WITHIN_DAY_COUNT']
    .mean().reset_index(name='MEAN_TXNS_NUM_WITHIN_SESSION')
)

df_after_filtering = df_after_filtering.merge(mean_txns_num_within_session, on='SENDER_WALLET', how='left')

del mean_txns_num_within_session

"""The ratio of the median to the mean:"""

df_after_filtering['TXN_NUM_MEDIAN_TO_MEAN_RATIO'] = (df_after_filtering['MEAN_TXNS_NUM_WITHIN_SESSION'] /
                                                      df_after_filtering['MEDIAN_TXNS_NUM_WITHIN_SESSION']
                                                    )

(
    df_after_filtering.drop(columns=['MEDIAN_TXNS_NUM_WITHIN_SESSION','MEAN_TXNS_NUM_WITHIN_SESSION'],
                       inplace=True)
                              )

"""### Calculating the median and mean for the intervals between transactions for each day

Median:
"""

median_interval_within_session = (
    df_after_filtering.groupby(['SENDER_WALLET'])['INTERVAL_MINUTES']
    .median().reset_index(name='MEDIAN_INTERVAL_WITHIN_SESSION')
)

df_after_filtering = df_after_filtering.merge(median_interval_within_session, on='SENDER_WALLET', how='left')

del median_interval_within_session

"""Mean:"""

mean_interval_within_session = (
    df_after_filtering.groupby(['SENDER_WALLET'])['INTERVAL_MINUTES']
    .mean().reset_index(name='MEAN_INTERVAL_WITHIN_SESSION')
)

df_after_filtering = df_after_filtering.merge(mean_interval_within_session, on='SENDER_WALLET', how='left')

del mean_interval_within_session

"""Ratio:"""

df_after_filtering['INTERVAL_MEDIAN_TO_MEAN_RATIO'] = (df_after_filtering['MEAN_INTERVAL_WITHIN_SESSION'] /
                                                       df_after_filtering['MEDIAN_INTERVAL_WITHIN_SESSION']
                                                    )

(
    df_after_filtering.drop(columns=['MEDIAN_INTERVAL_WITHIN_SESSION','MEAN_INTERVAL_WITHIN_SESSION'],
                       inplace=True)
                              )

df_after_filtering

"""#### Distribution based on calculated parameters"""

quintiles = (
    df_after_filtering[['TXN_NUM_MEDIAN_TO_MEAN_RATIO',
                     'INTERVAL_MEDIAN_TO_MEAN_RATIO']]
    .quantile([.2, .4, .6, .8]).to_dict()
)

quintiles

"""#### Creating a scoring system for segmentation

For example, accounts that are in the first percentile of 20% for the parameter TXN_NUM_MEDIAN_TO_MEAN_RATIO will receive a value of 1, accounts within the second percentile - 2, and so on.

TXN_NUM_MEDIAN_TO_MEAN_RATIO
"""

def t_score(x):
    if x <= quintiles['TXN_NUM_MEDIAN_TO_MEAN_RATIO'][.2]:
        return 1
    elif x <= quintiles['TXN_NUM_MEDIAN_TO_MEAN_RATIO'][.4]:
        return 2
    elif x <= quintiles['TXN_NUM_MEDIAN_TO_MEAN_RATIO'][.6]:
        return 3
    elif x <= quintiles['TXN_NUM_MEDIAN_TO_MEAN_RATIO'][.8]:
        return 4
    else:
        return 5

"""INTERVAL_MEDIAN_TO_MEAN_RATIO"""

def i_score(x):
    if x <= quintiles['INTERVAL_MEDIAN_TO_MEAN_RATIO'][.2]:
        return 1
    elif x <= quintiles['INTERVAL_MEDIAN_TO_MEAN_RATIO'][.4]:
        return 2
    elif x <= quintiles['INTERVAL_MEDIAN_TO_MEAN_RATIO'][.6]:
        return 3
    elif x <= quintiles['INTERVAL_MEDIAN_TO_MEAN_RATIO'][.8]:
        return 4
    else:
        return 5

df_after_filtering['T'] = df_after_filtering['TXN_NUM_MEDIAN_TO_MEAN_RATIO'].apply(lambda x: t_score(x))
df_after_filtering['I'] = df_after_filtering['INTERVAL_MEDIAN_TO_MEAN_RATIO'].apply(lambda x: i_score(x))

df_after_filtering['SCORE'] = (df_after_filtering['T'].map(str) +
                               df_after_filtering['I'].map(str)
                              )

(
    df_after_filtering.drop(columns=['T','I'],
                       inplace=True)
                              )

gc.collect()

df_after_filtering['SCORE'].value_counts()

"""From the entire list of segments obtained, I can highlight segments 11, 21 - segments with the lowest score based on the parameters. I will examine accounts from each segment.

### Segment №1 - score "11"
"""

df_after_filtering[df_after_filtering['SCORE'] == '11']['SENDER_WALLET'].unique()

(df_after_filtering[(df_after_filtering['SCORE'] == '11')&
                    (df_after_filtering['TXNS_COUNT'] >20)
                  ]['SENDER_WALLET'].unique())

"""Example #1 from the list:"""

df_after_filtering[df_after_filtering['SENDER_WALLET'] == '0x64f4575537244213160c713aeb1f8665dcb4e7ae'].head(60)

"""Very similar intervals, also note the weakly randomized amounts sent through Merkly.

Example #2 from the list:
"""

df_after_filtering[df_after_filtering['SENDER_WALLET'] == '0xa1fbe5012e1e5104d48378028d2324be8023f0dc'].head(60)

"""Small differences between intervals, also weakly randomized amounts sent through Stargate.

Example #3 from the list:
"""

df_after_filtering[df_after_filtering['SENDER_WALLET'] == '0x41f73454e42da24e267a3013ba044db259cb36ee'].head(60)

"""Very similar intervals with very similar small amounts, sent through different protocols.

I think it would not be a mistake to add the addresses from segment №1 with a score of "11" to the list.

### Segment №2 - score "21"
"""

df_after_filtering[df_after_filtering['SCORE'] == '21']['SENDER_WALLET'].unique()

"""Example #1 from the list:"""

df_after_filtering[df_after_filtering['SENDER_WALLET'] == '0x51edab02afb55fd7cd54b145983dc72835ad2605'].head(60)

"""Again, intervals close in value and almost identical amounts sent through Stargate.

Example #2 from the list:
"""

df_after_filtering[df_after_filtering['SENDER_WALLET'] == '0x1c910afe24e009468a66e3536d0e1e2f8437b078'].head(60)

"""Again, intervals close in value and almost identical amounts sent. There are short intervals - 50, 30 seconds, and others.

**I think it would not be a mistake to add the addresses from segment №1 with a score of "21" to the list.**

### List Formation

Accounts with randomization scoring "11":
"""

score_11 = df_after_filtering[df_after_filtering['SCORE'] == '11']['SENDER_WALLET'].unique().tolist()

len(score_11)

"""Accounts with randomization scoring "21":"""

score_21 = df_after_filtering[df_after_filtering['SCORE'] == '21']['SENDER_WALLET'].unique().tolist()

len(score_21)

score_11.extend(score_21)

list_of_sybils_with_weak_randomisation = score_11

len(list_of_sybils_with_weak_randomisation)

with open('sybils_second_list.txt', 'w') as file:
    for item in list_of_sybils_with_weak_randomisation:
        file.write("%s\n" % item)