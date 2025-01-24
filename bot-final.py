import requests, json, re, os, mysql.connector
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from mysql.connector import Error
from datetime import datetime
from bs4 import BeautifulSoup


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

def get_rank(asin): # get ranks from the API
    url = f'https://www.amazon.in/dp/{asin}'
    headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246"}

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    # get the division of product detail rankings
    table = soup.find('div', {'id': 'productDetails_db_sections', 'class': 'a-section'})
    if not table:
        raise ValueError("No valid ASIN found!")
    
    # filtered span with rank data
    span_comp = table.find_all("span")

    # seperate the rankings
    cat_rank = span_comp[1].text.replace("(See Top 100 in Home & Kitchen)", "").strip()
    #cat_rank = re.sub(r"\(.*?\)", "", span_comp[1]).strip()
    subcat_rank = span_comp[2].text

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
        'text': get_rank(asin)
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

# main function where asin is passed
if __name__ == "__main__":
    print(db_conn())
    asin = 'B09TSVL68H'
    create_table_asin(asin) # creates tables
    send_msg(asin) # sends message