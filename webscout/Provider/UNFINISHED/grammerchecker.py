from curl_cffi.requests import Session


def create_grammar_check_job(text: str):
    url = 'https://api.aigrammarchecker.io/api/ai-check-grammar/create-job'
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,en-IN;q=0.8',
        'dnt': '1',
        'origin': 'https://aigrammarchecker.io',
        'priority': 'u=1, i',
        'product-code': '067003',
        'product-serial': '6a4836a29e756bd24a74ebed31e405da',
        'referer': 'https://aigrammarchecker.io/',
        'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="120", "Microsoft Edge";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'sec-gpc': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
    }

    files = {
        'features': (None, 'check_grammar'),
        'entertext': (None, text),
        'translate_language': (None, 'English'),
    }

    session = Session()
    response = session.post(url, headers=headers, files=files)
    return response.json()

if __name__ == "__main__":
    from rich import print as cprint
    cprint(create_grammar_check_job("she gg to school"))
