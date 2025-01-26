import requests, json, re, os, mysql.connector
from dotenv import load_dotenv
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

    get_last_record_query = f"""
        SELECT time, cat_rank, subcat_rank from {asin} 
        ORDER BY time DESC LIMIT 1; """
    cursor.execute(get_last_record_query)

    results = cursor.fetchone() 
        
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

    table = soup.find('div', {'id': 'productDetails_db_sections', 'class': 'a-section'})  # get the division of product detail rankings
    if not table:
        raise ValueError("No valid ASIN found!")
    
    span_comp = table.find_all("span") # filtered span with rank data

    cat_rank = span_comp[1].text.replace("(See Top 100 in Home & Kitchen)", "").strip() # seperate the rankings
    #cat_rank = re.sub(r"\(.*?\)", "", span_comp[1]).strip()
    subcat_rank = span_comp[2].text

    cat_rank_int = re.search(r'\d{1,3}(,\d{3})*',cat_rank).group() # extracting numbers alone
    subcat_rank_int = re.search(r'\d{1,3}(,\d{3})*',subcat_rank).group() # extracting numbers alone
    
    message = compare_ranks(asin, cat_rank, subcat_rank, cat_rank_int, subcat_rank_int)

    insert_table(asin, cat_rank_int , subcat_rank_int) #insert to db after removing un-wanted texts
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

def db_close(): # Close db connection
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("Database connection closed.")
    
def create_table_asin(asin): # Create a table    
    create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {asin} (
            time DATETIME,
            cat_rank VARCHAR(10),
            subcat_rank VARCHAR(10)
        ); """
    
    cursor.execute(create_table_query)
    print("Table created successfully!")
    send_msg(asin)

def insert_table(asin, cat_rank, subcat_rank): # Insert into db
    dtime = datetime.now()
    
    insert_query = f"""
        INSERT INTO {asin} VALUES ('{dtime}', 
            '{cat_rank}', 
            '{subcat_rank}'
        ); """
    
    cursor.execute(insert_query)
    connection.commit()
    print("Data inserted successfully!")        

def track_asin():
    select_query = f""" SELECT asin, sku, chat_id FROM track"""
    cursor.execute(select_query)
    results = cursor.fetchall()

    print(results)

    for row in results:
        asin = row[0]
        sku = row[1]
        chat_id = row[2]

        create_table_asin(asin)

connection, cursor = db_conn()
        
# main function where asin is passed
if __name__ == "__main__":
    track_asin()
    db_close()

