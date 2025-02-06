import os
from base64 import b64encode
from random import choice, random, randrange
from time import sleep
from urllib.parse import quote
from cloudscraper import create_scraper
from urllib3 import disable_warnings
from Krito import SHORTEN_KEY

shorteners_list = []

def load_shorteners_from_config():
    if SHORTEN_KEY:
        for entry in SHORTEN_KEY.split(','):
            temp = entry.strip().split()
            if len(temp) == 2:
                shorteners_list.append({'domain': temp[0], 'api_key': temp[1]})

load_shorteners_from_config()

def shorten_url(longurl):
    if not shorteners_list:
        return longurl
    i = 0 if len(shorteners_list) == 1 else randrange(len(shorteners_list))
    _shorten_dict = shorteners_list[i]
    _shortener = _shorten_dict['domain']
    _shortener_api =  _shorten_dict['api_key']
    cget = create_scraper().request
    disable_warnings()
    try:
        if "shorte.st" in _shortener:
            headers = {'public-api-token': _shortener_api}
            data = {'urlToShorten': quote(longurl)}
            return cget('PUT', 'https://api.shorte.st/v1/data/url', headers=headers, data=data).json()['shortenedUrl']
        elif "linkvertise" in _shortener:
            url = quote(b64encode(longurl.encode("utf-8")))
            linkvertise = [
                f"https://link-to.net/{_shortener_api}/{random() * 1000}/dynamic?r={url}",
                f"https://up-to-down.net/{_shortener_api}/{random() * 1000}/dynamic?r={url}",
                f"https://direct-link.net/{_shortener_api}/{random() * 1000}/dynamic?r={url}",
                f"https://file-link.net/{_shortener_api}/{random() * 1000}/dynamic?r={url}"]
            return choice(linkvertise)
        elif "bitly.com" in _shortener:
            headers = {"Authorization": f"Bearer {_shortener_api}"}
            return cget('POST', "https://api-ssl.bit.ly/v4/shorten", json={"long_url": longurl}, headers=headers).json()["link"]
        elif "ouo.io" in _shortener:
            return cget('GET', f'http://ouo.io/api/{_shortener_api}?s={longurl}', verify=False).text
        elif "cutt.ly" in _shortener:
            return cget('GET', f'http://cutt.ly/api/api.php?key={_shortener_api}&short={longurl}', verify=False).json()['url']['shortLink']
        else:
            res = cget('GET', f'https://{_shortener}/api?api={_shortener_api}&url={quote(longurl)}').json()
            shorted = res['shortenedUrl']
            if not shorted:
                shrtco_res = cget('GET', f'https://api.shrtco.de/v2/shorten?url={quote(longurl)}').json()
                shrtco_link = shrtco_res['result']['full_short_link']
                res = cget('GET', f'https://{_shortener}/api?api={_shortener_api}&url={shrtco_link}').json()
                shorted = res['shortenedUrl']
            if not shorted:
                shorted = longurl
            return shorted
    except Exception as e:
        print(f"Error occurred in shortener.py: {e}")
        sleep(1)
        return None
