import requests
import requests
import json
import time
import pandas as pd
import pandas as pd
import mysql.connector
from mysql.connector import Error
import time
import hashlib
import concurrent.futures


batch = 50
from datetime import timedelta

def log(message):
    timestamp = time.strftime("%H:%M:%S %p")
    s = f"{timestamp} - {message}\n"
    print(s)
    try:
        with open("log.txt", "a") as log_file:
            log_file.write(s)
    except FileNotFoundError:
        with open("log.txt", "w") as log_file:
            log_file.write(s)
            
db_conn = None
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'R@k35h69',
    'database': 'zauba',
    'port': 3306,
}

class DBConnection:
    def __init__(self):
        self.g = {}
        self.details_SN = self.total_in_details()

    def get_db(self):
        if 'db' not in self.g:
            try:
                self.g['db'] = mysql.connector.connect(**db_config)
            except Error as e:
                log(f"Error: {e}")
                self.g['db'] = None
        return self.g['db']

    def close_db(self):
        db = self.g.pop('db', None)
        if db is not None:
            db.close()

 

    
    def add_new_urls_to_details(self, df: pd.DataFrame):
        db = self.get_db()
        if db is None:
            print("Database connection failed.")
            return False

        cursor = db.cursor()
        base_query = "INSERT INTO `zauba`.`details` (`SN`,`CIN`, `Company`,`roc`,`Status`,`Url`) VALUES (%s,%s, %s,%s,%s,%s);"
        success = True
        for index, row in df.iterrows():
            while True:
                try:
                    cursor.execute(base_query, (self.details_SN,row['CIN'], row['Company'], row['RoC'], row['Status'], row['URL']))
                    db.commit()
                    self.details_SN = self.details_SN+1
                    break
                except mysql.connector.Error as e:
                    if "Duplicate entry" in str(e):
                        break
                    elif "Data too long for column" in str(e):
                        column_name = None
                        for part in str(e).split("'"):
                            if "Data too long for column" in part:
                                continue
                            if part.strip().isidentifier():
                                column_name = part.strip()
                                break
                        if column_name:
                            value_length = len(row[column_name])
                            new_length = value_length + 10  # Increase the length by 10
                            alter_query = f"ALTER TABLE details MODIFY {column_name} VARCHAR({new_length})"
                            cursor.execute(alter_query)
                        else:
                            log("Unable to determine the column name causing the error.")
                            success = False
                            break
                    else:
                        print(f"An error occurred: {e}")
                        success = False
                        break
        cursor.close()
        return success

    
    def total_in_details(self):
        db = self.get_db()
        if db is None or not db.is_connected():
            print("No connection to the database.")
            return None

        query = """
            SELECT count(*) FROM zauba.details;
        """
        params = ()
        try:
            last = pd.read_sql(query, db, params=params)
            return (list(last['count(*)']))[0]+1
        except Error as e:
            print(f"Error getting last: {e}")
            return None

def get_server(id):
    if id == 2:
        return "https://scrap002-vdvq.onrender.com/scrape"
    return f"https://scrap{id:03}.onrender.com/scrape"

def send_request(row):
    url = get_server(1 + (int(row['SN']) - 1) % batch)
    payload = {
        "url": row['url']
    }
    if pd.notna(row['SN']):
        payload["SN"] = int(row['SN'])

    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        if response.status_code == 200:
            response_data = response.json()
            if row['url'].startswith("https://www.zaubacorp.com/company-list/"):
                dataframe = pd.DataFrame(response_data)
                return None, dataframe
            else:
                result_dict = response_data["result_dict"]
                dataframe = pd.DataFrame(response_data["dataframe"])
                return result_dict, dataframe
        else:
            log(f"Error: {response.status_code}, {response.text}")
            return None, None
    except Exception as e:
        log(f"Exception during request: {e}")
        return None, None





db_conn = DBConnection()




urls_1 = pd.read_csv('temp_urls.csv')
for index, row in urls_1.iterrows():
    
    start_point = 1
    Last = row['page']
    
    url = row['patterns']
    
    i = start_point
    j=i
    t0=time.time()
    log(f"starting from {i}")
    good = True
    
    while i <= Last and good:
        low = i
        high = min(i + batch -1, Last)
        log(f"Fetching URLs from page {low} to {high}")
        urls = [url.replace('{i}',str(i)) for i in range(low, high + 1)]
        df = pd.DataFrame(urls, columns=["url"])
        df["SN"] = range(low, high + 1)
        retries = 0
        max_retries = 5
        while retries < max_retries:
            start_time = time.time()
            results = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=batch) as executor:
                future_to_row = {executor.submit(send_request, row): row for index, row in df.iterrows()}
                for future in concurrent.futures.as_completed(future_to_row):
                    row = future_to_row[future]
                    try:
                        result = future.result()
                        results.append((row, result))
                    except Exception as exc:
                        log(f"{row['url']} generated an exception: {exc}")
                        good = False
                        break
            fetch_time = f"{time.time() - start_time:.2f}"
            log(f"Requests completed in {fetch_time} seconds")
            # Check if all results are valid
            all_data_valid = all(result is not None and result[1] is not None for _, result in results)
            if all_data_valid:
                for row, result in results:
                    dataframe = result[1]
       
           
                    if not db_conn.add_new_urls_to_details(dataframe):
                        log("error in full director")
                        good = False
                        break
                    log(f"{row['SN']} done")
                
                log(f"fetch time was {fetch_time}")
                log(f"Batch processing completed in {time.time() - start_time:.2f} seconds")
                if high>j:
                    print(f"for {index} {high*100/Last:.2f}% work is done and  {timedelta(seconds = int(((Last-high) * (time.time()-t0))  / (high-j)))} time remain ")
                else:
                    print("work is done. for {index}")
                break
            else:
                retries += 1
                if retries < max_retries:
                    log(f"Error: Not all results were valid, retrying batch in 1 minute... (Attempt {retries}/{max_retries})")
                    time.sleep(60)
                else:
                    log("Error: Not all results were valid after 5 retries, halting the process.")
                    good = False
                    break
        i += batch
    start_point = 1
log("finished")
db_conn.close_db()
