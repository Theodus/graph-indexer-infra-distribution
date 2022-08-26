import ipinfo
import json
import matplotlib.pyplot as plt
import os
import pandas
import requests
import socket
from urllib.parse import urlparse

network_subgraph = 'https://gateway.thegraph.com/network'
ipinfo_token = os.environ['IPINFO_TOKEN']

def query_indexer_urls():
    response_data = []
    page_len = 100
    index = 0
    while True:
        filters = f"first:{page_len},skip:{page_len * index},where:{{allocatedTokens_gt:0}}"
        response = requests.post(
            network_subgraph,
            json = { "query": f"{{ indexers({filters}) {{ id url }} }}" }
        )
        page = json.loads(response.text)['data']['indexers']
        if len(page) == 0: break
        response_data.extend(page)
        index += 1

    return response_data

print('Loading data from network subgraph...')

records = query_indexer_urls()

print('Fetching IP info...')

for record in records:
    try:
        record['ip'] = socket.gethostbyname(urlparse(record['url']).netloc)
    except:
        record['ip'] = 'unknown'

ipinfo_handler = ipinfo.getHandler(ipinfo_token)
info = ipinfo_handler.getBatchDetails([r['ip'] for r in records if r['ip'] != 'unknown'])

for record in records:
    try:
        record['country'] = info[record['ip']]['country']
        record['org'] = info[record['ip']]['org']
    except:
        record['country'] = 'unknown'
        record['org'] = 'unknown'

data = pandas.DataFrame.from_records(records)

print(data)

print('Saving figure...')

fig, axes = plt.subplots(2, 1, figsize = (14, 10))

for (i, col) in enumerate(['country', 'org']):
    axes[i].set_title(f"Indexers by {col}")
    grouped = data.groupby([col])['id'].count().sort_values(ascending = False)
    print(grouped)
    axes[i].barh(grouped.index, grouped)
    axes[i].invert_yaxis()

fig.tight_layout()
plt.savefig('plot.png')
