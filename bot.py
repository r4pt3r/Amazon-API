import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

API_TOKEN = os.getenv('API_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
#MESSAGE = 'Hello, Group! This is a test message from my bot.'


def get_rank(asin):
    api = f'http://localhost:8000/rank/{asin}'
    res = requests.get(api)
    data = json.loads(res.text)

    asin_p = data["asin"]
    cat_rank = data["category_rank"]
    subcat_rank = data["sub_category_rank"]
    
    return f'ASIN: {asin_p} \n{cat_rank} \n{subcat_rank}'


def send_msg(API_TOKEN, CHAT_ID, asin):
    url = f'https://api.telegram.org/bot{API_TOKEN}/sendMessage'

    payload = {
        'chat_id': CHAT_ID,
        'text': get_rank(asin)
    }

    response = requests.post(url, data=payload)
    print(response.json())

if __name__ == "__main__":
    send_msg(API_TOKEN, CHAT_ID,'B0CH1DMVBQ')