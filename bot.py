import requests, json, re, os, mysql.connector, uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from mysql.connector import Error
from datetime import datetime

app = FastAPI() #API service
load_dotenv() #Load credentials

API_TOKEN = os.getenv('API_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

# Database credentials
HOST = os.getenv('HOST')
DATABASE = os.getenv('DATABASE')
USER = os.getenv('USER')
PASSWORD = os.getenv('PASSWORD')

def compare_ranks(asin, cat_rank, subcat_rank, cat_rank_int, subcat_rank_int): # get last record from db and compare
    connection, cursor = db_conn()

    get_last_record_query = f"""
    SELECT time, cat_rank, subcat_rank from {asin} 
    ORDER BY time DESC LIMIT 1;
    """

    cursor.execute(get_last_record_query)

    results = cursor.fetchone() 
    print(results[1])

    if results[1]==str(cat_rank_int):
        return f'ASIN: {asin} ✅\n{cat_rank} \n{subcat_rank}'
    elif results[1]<str(cat_rank_int):
        return f'ASIN: {asin} 🔼\n{cat_rank} \n{subcat_rank}'
    else:
        return f'ASIN: {asin} 🔽\n{cat_rank} \n{subcat_rank}'

def api_rank(asin): # get ranks from the API
    api = f'http://localhost:8000/rank?asin={asin}'
    res = requests.get(api)
    data = json.loads(res.text)

    asin_p = data["asin"]
    cat_rank = data["category_rank"] # with category names
    subcat_rank = data["sub_category_rank"] # with category names

    cat_rank_int = re.search(r'\d{1,3}(,\d{3})*',cat_rank).group() # extracting numbers alone
    subcat_rank_int = re.search(r'\d{1,3}(,\d{3})*',subcat_rank).group() # extracting numbers alone

    insert_table(asin, cat_rank_int , subcat_rank_int) #insert to db after removing un-wanted texts
    
    #message = f'ASIN: {asin_p} \n{cat_rank} \n{subcat_rank}'
    message = compare_ranks(asin, cat_rank, subcat_rank, cat_rank_int, subcat_rank_int)
    #send_msg(message)
    return message

def send_msg(asin): # send message to telegram group
    url = f'https://api.telegram.org/bot{API_TOKEN}/sendMessage'

    payload = {
        'chat_id': CHAT_ID,
        'text': api_rank(asin)
    }

    response = requests.post(url, data=payload)
    return(response.json())

def db_conn(): # Establish db connection
    try:
        connection = mysql.connector.connect(
            host=HOST,
            database=DATABASE,
            user=USER,
            password=PASSWORD
        )
        if connection.is_connected():
            print("Successfully connected to the database!")

            # Create a cursor object
            cursor = connection.cursor()
            return connection, cursor
    except Error as e:
        return(f"Error: {e}")

def db_close(connection, cursor): # Close db connection
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("Database connection closed.")
    
def create_table_asin(asin): # Create a table
    connection, cursor = db_conn()
    
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {asin} (
        time DATETIME,
        cat_rank VARCHAR(10),
        subcat_rank VARCHAR(10)
    );
    """
    cursor.execute(create_table_query)
    print("Table created successfully!")
    db_close(connection, cursor)

def insert_table(asin, cat_rank, subcat_rank): # Insert into db
    connection, cursor = db_conn()

    # Get the current date and time
    dtime = datetime.now()
    #datetime = "2025-01-24 00:25:52.561803"

    # Print the current date and time
    print("Current Date and Time:", datetime)

    # Create a table
    insert_query = f"""
    INSERT INTO {asin} VALUES ('{dtime}', 
        '{cat_rank}', 
        '{subcat_rank}'
    );
    """
    print(insert_query)
    cursor.execute(insert_query)
    connection.commit()
    print("Data inserted successfully!")        

    db_close(connection, cursor) 

# listenting for api
@app.get("/asin")
async def get_asin(
    asin: str = Query(..., description="Amazon Standard Identification Number (ASIN)")
    ):
    # Extract ASIN from URL
    asin_match = re.search(r'dp/([A-Z0-9]+)', asin)
    if asin_match:
        asin = asin_match.group(1)
    create_table_asin(asin) # creates tables
    send_msg(asin) # sends message

# main function where asin is passed
if __name__ == "__main__":
    print(db_conn())
    uvicorn.run(app, host="0.0.0.0", port=9000)
