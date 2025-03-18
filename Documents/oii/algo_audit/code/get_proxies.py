from typing import Dict, Optional
from requests_html import HTML, HTMLSession
import requests
import os
from pathlib import Path
import pandas as pd
import time
import numpy as np
import random
import socket
import argparse

def get_args_from_command_line():
    """Parse the command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=str)
    parser.add_argument("--is_hause", type=str, default='0')
    args = parser.parse_args()
    return args

def get_proxies(proxy_key, date, test_proxies=True, n_proxies=-1):
    """
    Get proxies from webshare.
    Call the function at the top of script to get proxies.
    Returns a list of formatted proxies.
    """
    proxy_file_name = f'proxies_{date}.txt'
    if args.is_hause == "1":
        proxies_path = Path(f"proxies/{proxy_file_name}")
    else:
        proxies_path = Path(f"/scratch/spf248/twitter_social_cohesion/proxies/{proxy_file_name}")
        # proxies_path = Path('/scratch/spf248/twitter_social_cohesion/proxies_26062023_bis.txt')
    if not proxies_path.exists():
        print(f"Retrieving proxies and saving as {proxy_file_name}")
        # get proxies
        resp = requests.get(
            "https://proxy.webshare.io/api/proxy/list/",
            headers={"Authorization": f"Token {proxy_key}"},
        )
        proxies = list()
        proxies += resp.json()["results"]
        while 'next' in resp.json():
            if resp.json()['next']:
                next_token = resp.json()['next']
                resp = requests.get(
                    f"https://proxy.webshare.io{next_token}",
                    headers={"Authorization": f"Token {proxy_key}"}
                )
                proxies += resp.json()["results"]
                print(len(proxies))
            else:
                break
        if n_proxies > 0:
            proxies = proxies[:n_proxies]
        for prox_idx, p in enumerate(proxies):
            prox = f"http://{p['username']}:{p['password']}@{p['proxy_address']}:{p['ports']['http']}"
            p["proxy"] = prox
            p["delete"] = 'no'
            if test_proxies:
                print(f"testing proxy {prox_idx + 1} of {len(proxies)}: {prox}")
                try:
                    status = requests.get("http://httpbin.org/ip", proxies={"http": prox, "https": prox})
                except Exception as e:
                    p["delete"] = 'yes'
                    continue
                if status.status_code == 200:
                    print(status.json())
                    p["delete"] = 'no'
                else:
                    print(f'remove proxy {prox}')
                    p["delete"] = 'yes'

        proxies = pd.DataFrame(proxies).query("delete == 'no'")["proxy"].to_list()
        proxies_path.write_text("\n".join(proxies))
    else:
        print(f"Using cached proxy list {proxy_file_name}")
        proxies = proxies_path.read_text().split("\n")
    print(f"Number of valid proxies: {len(proxies)}")
    return proxies

if __name__ == '__main__':
    args = get_args_from_command_line()
    path_to_data = os.path.join('/', os.getcwd().split('/')[1], 'spf248', 'twitter_social_cohesion', 'data')
    with open(os.path.join(path_to_data, 'data_collection', 'keys', 'proxies', 'proxy_key')) as f:
        proxy_key = f.readlines()[0].strip('\n|"')
    proxies = get_proxies(proxy_key, args.date)