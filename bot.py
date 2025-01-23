import requests
import json
import re
from dotenv import load_dotenv
import os
from fastapi import FastAPI, Query

app = FastAPI()

load_dotenv()

API_TOKEN = os.getenv('API_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
#MESSAGE = 'Hello, Group! This is a test message from my bot.'

# get ranks from the API
def api_rank(asin):
    api = f'http://localhost:8000/rank?asin={asin}'
    res = requests.get(api)
    data = json.loads(res.text)

    asin_p = data["asin"]
    cat_rank = data["category_rank"]
    subcat_rank = data["sub_category_rank"]
    
    return f'ASIN: {asin_p} \n{cat_rank} \n{subcat_rank}'

# send message to telegram group
#def send_msg(API_TOKEN, CHAT_ID, asin):
def send_msg(asin):
    url = f'https://api.telegram.org/bot{API_TOKEN}/sendMessage'

    payload = {
        'chat_id': CHAT_ID,
        'text': api_rank(asin)
    }

    response = requests.post(url, data=payload)
    return(response.json())

# listenting for api
@app.get("/asin")
async def get_asin(
    asin: str = Query(..., description="Amazon Standard Identification Number (ASIN)")
    ):
    # Extract ASIN from URL
    asin_match = re.search(r'dp/([A-Z0-9]+)', asin)
    if asin_match:
        asin = asin_match.group(1)
    #calling the send function
    return send_msg(asin)

# main function where asin is passed
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
