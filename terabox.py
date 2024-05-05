import re
from urllib.parse import parse_qs, urlparse
import random
import requests
from config import COOKIE
from tools import get_formatted_size
from typing import Union 

def check_url_patterns(url):
    patterns = [
        r"ww\.mirrobox\.com",
        r"www\.nephobox\.com",
        r"freeterabox\.com",
        r"www\.freeterabox\.com",
        r"1024tera\.com",
        r"4funbox\.co",
        r"www\.4funbox\.com",
        r"mirrobox\.com",
        r"nephobox\.com",
        r"terabox\.app",
        r"terabox\.com",
        r"www\.terabox\.ap",
        r"www\.terabox\.com",
        r"www\.1024tera\.co",
        r"www\.momerybox\.com",
        r"teraboxapp\.com",
        r"momerybox\.com",
        r"tibibox\.com",
        r"www\.tibibox\.com",
        r"www\.teraboxapp\.com",
    ]

    for pattern in patterns:
        if re.search(pattern, url):
            return True

    return False

def get_urls_from_string(string: str) -> list[str]:
    pattern = r"(https?://\S+)"
    urls = re.findall(pattern, string)
    urls = [url for url in urls if check_url_patterns(url)]
    return urls

def extract_surl_from_url(url: str) -> str or None:
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    surl = query_params.get("surl", None)

    if surl:
        return surl[0]
    else:
        return None

def generate_random_headers():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
        # Add more user agents as needed
    ]
    accept_encodings = ["gzip, deflate, br", "deflate, gzip", "gzip", ""]
    accept_languages = ["en-US,en;q=0.9,hi;q=0.8", "en-US,en;q=0.9", "en-US,en;q=0.8"]
    connection = ["keep-alive", "close"]
    headersList = {
        "User-Agent": random.choice(user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": random.choice(accept_encodings),
        "Accept-Language": random.choice(accept_languages),
        "Connection": random.choice(connection),
        "Cookie": COOKIE,
        "DNT": "1",
        "Host": "www.terabox.app",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "sec-ch-ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }
    return headersList

def get_data(url: str):
    headersList = generate_random_headers()

    with requests.Session() as r:
        response = r.get(url, headers=headersList)
        response = r.get(response.url, headers=headersList)
        logid = find_between(response.text, "dp-logid=", "&")
        jsToken = find_between(response.text, "fn%28%22", "%22%29")
        bdstoken = find_between(response.text, 'bdstoken":"', '"')
        shorturl = extract_surl_from_url(response.url)
        if not shorturl:
            return False

        reqUrl = f"https://www.terabox.app/share/list?app_id=250528&web=1&channel=0&jsToken={jsToken}&dp-logid={logid}&page=1&num=20&by=name&order=asc&site_referer=&shorturl={shorturl}&root=1"

        response = r.get(reqUrl, headers=headersList)

        if not response.status_code == 200:
            return False
        r_j = response.json()
        if r_j.get("errno"):
            return False
        if not ("list" in r_j and r_j["list"]):
            return False

        response = r.head(r_j["list"][0]["dlink"], headers=headersList)
        direct_link = response.headers.get("location")
        data = {
            "file_name": r_j["list"][0]["server_filename"],
            "link": r_j["list"][0]["dlink"],
            "direct_link": direct_link,
            "thumb": r_j["list"][0]["thumbs"]["url3"],
            "size": get_formatted_size(int(r_j["list"][0]["size"])),
            "sizebytes": int(r_j["list"][0]["size"]),
        }
        return data

def find_between(data: str, first: str, last: str) -> str or None:
    try:
        start = data.index(first) + len(first)
        end = data.index(last, start)
        return data[start:end]
    except ValueError:
        return None