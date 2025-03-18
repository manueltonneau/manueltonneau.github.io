from datetime import datetime
import re
from typing import Dict, Optional
from requests_html import HTMLSession
import socket
from dateutil import parser
import pytz
import os
from pathlib import Path
import numpy as np
import requests
import pandas as pd
import random
import argparse
import shutil
import time
# import datetime
utc=pytz.UTC

def sleep_random(short=False):
    if short:
        seconds = random.randint(1, 3)
    else:
        seconds = random.randint(3, 7)
    time.sleep(seconds)
    print(f"Slept for {seconds} seconds.")

def get_args_from_command_line():
    """Parse the command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=str)
    parser.add_argument("--is_hause", type=str, default='0')
    args = parser.parse_args()
    return args
def get_env_var(varname, default):
    if os.environ.get(varname) != None:
        var = int(os.environ.get(varname))
        print(varname, ':', var)
    else:
        var = default
        print(varname, ':', var, '(Default)')
    return var

def get_proxies(proxy_key, date):
    """
    Get proxies from webshare.
    Call the function at the top of script to get proxies.
    Returns a list of formatted proxies.
    """
    proxy_file_name = f'proxies_{date}.txt'
    if 'manuto' in socket.gethostname().lower():
        proxies_path = Path(f"/home/manuel/Documents/world_bank/nigeria/data/proxies/{proxy_file_name}")
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
        for p in proxies:
            prox = f"http://{p['username']}:{p['password']}@{p['proxy_address']}:{p['ports']['http']}"
            p["proxy"] = prox
        proxies = pd.DataFrame(proxies)["proxy"].to_list()
        proxies_path.write_text("\n".join(proxies))
    else:
        print(f"Using cached proxy list {proxy_file_name}")
        proxies = proxies_path.read_text().split("\n")
    return proxies

def select_proxy(proxylist, task_id=None, random=False):
    if random:
        task_id = random.randint(0,999)
    num_proxies = len(proxylist)
    proxy_index = task_id % num_proxies
    selected_proxy = proxylist[proxy_index]
    return selected_proxy

def save_to_txt(id, outfile):
    with open(outfile, 'a') as file:
        file.write('{}\n'.format(id))


if __name__ == '__main__':
    args = get_args_from_command_line()
    test=True
    # address = "https://nitter.net"
    # username = 'ManuelTonneau'
    # url = f"{address}/{username}/with_replies"
    if 'manuto' in socket.gethostname().lower():
        path_data = '/home/manuel/Documents/world_bank/scraping/data/users/input'
        SLURM_ARRAY_TASK_ID = 0
        SLURM_ARRAY_TASK_COUNT = 1
        SLURM_JOB_ID = 1000
    # elif args.is_hause == "1":
    #     path_data = ''
    #     #TODO add path to zip folder shared on Slack (obv unzip before)
    #     #TODO add env variables
    #     # SLURM_ARRAY_TASK_ID (index of worker in the job array; if only one worker, default to 0)
    #     # SLURM_ARRAY_TASK_COUNT (size of job array; if only one worker, default to 1)
    else:
        path_data = #TODO
        # path_data = '/scratch/mt4493/nigeria/data/hateful_users/nitter_collection/not_checked_14112023'
        # path_data = '/scratch/mt4493/nigeria/data/hateful_users/nitter_collection/err_to_check_15112023'
        SLURM_ARRAY_TASK_ID = get_env_var('SLURM_ARRAY_TASK_ID', 0)
        SLURM_ARRAY_TASK_COUNT = get_env_var('SLURM_ARRAY_TASK_COUNT', 1)
        SLURM_JOB_ID = get_env_var('SLURM_JOB_ID', 1)
    link_file_list = list(Path(path_data).glob('*.parquet'))
    path_to_links = list(np.array_split(link_file_list, SLURM_ARRAY_TASK_COUNT)[SLURM_ARRAY_TASK_ID])
    # date_today = datetime.today().strftime('%d%m%Y')
    if 'manuto' in socket.gethostname().lower():
        output_folder = #TODO
    else:
        output_folder = #TODO

    if not os.path.exists(output_folder):
        os.makedirs(output_folder, exist_ok=True)
    if not os.path.exists(os.path.join(output_folder, 'parquets')):
        os.makedirs(os.path.join(output_folder, 'parquets'), exist_ok=True)

    # pull_folder_name_list = os.listdir(output_folder)
    collected_count = 0
    error_count = 0
    # get proxy
    if 'manuto' in socket.gethostname().lower():
        path_proxy_key = '/home/manuel/Documents/world_bank/nigeria/data/proxy_key'
    else:
        path_to_data = os.path.join('/', os.getcwd().split('/')[1], 'spf248', 'twitter_social_cohesion', 'data')
        path_proxy_key = os.path.join(path_to_data, 'data_collection', 'keys', 'proxies', 'proxy_key')
    with open(path_proxy_key) as f:
        proxy_key = f.readlines()[0].strip('\n|"')
    proxies = get_proxies(proxy_key=proxy_key, date=output_folder.split('/')[-1])
    if 'manuto' in socket.gethostname().lower():
        proxy_list = proxies#[:50]
    else:
        proxy_list = list(np.array_split(proxies, SLURM_ARRAY_TASK_COUNT)[SLURM_ARRAY_TASK_ID])
    print(f'# proxies assigned to job: {len(proxy_list)}')
    # proxy = select_proxy(proxylist=proxies, random=True)
    # print(f'proxy: {proxy}')
    # proxy=None
    # check if instances still work
    print(f'original # links: {len(path_to_links)}')
    nitter_instances_list = list()
    proxy = proxy_list[0]
    for address in path_to_links:
        try:
            tweet_list, _ = get_tweets(username='ManuelTonneau',
                                   address=address,
                                   job_id=SLURM_JOB_ID,
                                   proxy=proxy,
                                   test=True
                                   )
            nitter_instances_list.append(address)
        except Exception as e:
            print(f'Exception: {e}; address: {address}')
            # nitter_instances_list.remove(address)
    