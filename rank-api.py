from fastapi import FastAPI, HTTPException
import requests
from bs4 import BeautifulSoup
import re

app = FastAPI()

# get the rank function
def get_rank(asin):
    # product url with headers to not detect robot
    url = f'https://www.amazon.in/dp/{asin}'
    headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246"}

    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')

        # get the division of product detail rankings
        table = soup.find('div', {'id': 'productDetails_db_sections', 'class': 'a-section'})
        if not table:
            raise ValueError("No valid ASIN found!")
        
        # filtered span with rank data
        span_comp = table.find_all("span")

        # seperate the rankings
        cat_rank = span_comp[1].text
        subcat_rank = span_comp[2].text

        # return the data
        return {
            "asin": asin,
            "category_rank": cat_rank, 
            "sub_category_rank": subcat_rank
        }
    
    # handling exceptions
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Data extraction error: {ve}")

# listenting for api
@app.get("/rank/{asin}")
async def get_asin(asin: str):
    # Extract ASIN from URL
    asin_match = re.search(r'dp/([A-Z0-9]+)', asin)
    if asin_match:
        asin = asin_match.group(1)
    #calling the function
    return get_rank(asin)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
