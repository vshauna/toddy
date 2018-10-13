import json
import requests
#import logging

def read_old_catalog(board):
    catalog_fn = '{}-catalog.json'.format(board)
    try:
        with open(catalog_fn, 'r') as f:
            old_catalog = json.loads(f.read())
            return old_catalog
    except:
#        logging.info('no old catalog')
        pass

def get_and_save_catalog(board):
    catalog_fn = '{}-catalog.json'.format(board)
    catalog_url = 'https://8ch.net/{}/catalog.json'.format(board)

    r = requests.get(catalog_url)
    try:
        catalog = r.json()
    except Exception as e:
        with open('error_file', 'w') as f:
            f.write(r.text)
        raise
        
    with open(catalog_fn, 'w') as f:
        f.write(json.dumps(catalog))
    return catalog

def catalog_threads(catalog):
    threads = {}
    for page in catalog:
        for thread in page['threads']:
            threads[thread['no']] = thread
    return threads

def find_new_threads(catalog, old_catalog):
    threads = catalog_threads(catalog)
    old_threads = catalog_threads(old_catalog)
    new_threads_ids = (set(threads.keys())
                      -set(old_threads.keys()))
    new_threads = {thread_id: threads[thread_id]
                   for thread_id in new_threads_ids}
    return new_threads
