"""Read-only clients for vetted public data endpoints; no trading credentials."""
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def session():
    client=requests.Session()
    client.headers['User-Agent']='RegimeAtlas-Research/1.0'
    client.mount('https://',HTTPAdapter(max_retries=Retry(total=2,backoff_factor=.5,
        status_forcelist=[429,500,502,503,504],allowed_methods=['GET'])))
    return client

def get_json(client,url,**params):
    response=client.get(url,params=params,timeout=(5,20))
    response.raise_for_status()
    payload=response.json()
    if 'error' in payload:
        raise ValueError(f'Public data source returned an error: {payload["error"]}')
    return payload
