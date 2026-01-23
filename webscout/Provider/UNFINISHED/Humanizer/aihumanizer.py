import uuid

import requests
from rich import print

from webscout.litagent import LitAgent

url = 'https://aihumanizer.work/api/v1/text/rewriter'

headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-US,en;q=0.9,en-IN;q=0.8',
    'content-type': 'application/json; charset=UTF-8',
    'dnt': '1',
    'origin': 'https://aihumanizer.work',
    'priority': 'u=1, i',
    'referer': 'https://aihumanizer.work/?via=topaitools',
    'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Microsoft Edge";v="144"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'sec-gpc': '1',
    'user-agent': LitAgent().random(),
}

cookies = {
    '_ga': 'GA1.1.830684681.1766055491',
    '_ga_14V82CGVQ2': 'GS2.1.s1766055490$o1$g0$t1766055490$j90$l0$h0',
    'anonymous_user_id': str(uuid.uuid4()),
}

json_data = {
    'text': 'You are an Large Thinking and Reasoning Model (LTRM) called Dhanishtha-MAX by HelpingAI. Your purpose is to think deeply and reason carefully before answering user questions. You must follow the guidelines below strictly in every response.',
    'tone': 0,
}

response = requests.post(url, headers=headers, cookies=cookies, json=json_data)

print(response.json()['data']['humanizer_text'])
