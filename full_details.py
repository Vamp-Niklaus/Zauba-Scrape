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

from datetime import timedelta

batch = 50
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
        self.runtime_dict = {}  
        self._populate_runtime_dict()
        # self.details_SN = self.total_in_details()

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

    def _shorten_column_name(self, column, is_rec=0):
        if len(column) > 64 or is_rec:
            hash_suffix = hashlib.md5(column.encode()).hexdigest()[:8]  # Generate an 8-character hash suffix
            shortened_column = column[:55] + "_" + hash_suffix  # Ensure the total length is 64 characters
            if shortened_column not in self.runtime_dict.values():
                return shortened_column
            else:
                # If there's a collision, modify the original column slightly and retry
                return self._shorten_column_name(shortened_column, 1)
        else:
            return column

    def _add_to_shorted_table(self, original, shortened):
        cursor = self.get_db().cursor()
        insert_query = "INSERT INTO Shorted (Original, Edited) VALUES (%s, %s)"
        cursor.execute(insert_query, (original, shortened))
        self.get_db().commit()
        cursor.close()

    def _populate_runtime_dict(self):
        cursor = self.get_db().cursor()
        cursor.execute("SELECT Original, Edited FROM Shorted")
        shorted_mappings = cursor.fetchall()
        cursor.close()
        for original, edited in shorted_mappings:
            self.runtime_dict[original] = edited

    def _get_shortened_column_name(self, original_column):
        if original_column in self.runtime_dict:
            return self.runtime_dict[original_column]

        # Generate a unique shortened name and ensure it doesn't collide with existing columns
        shortened_column = self._shorten_column_name(original_column)

        # Update the runtime dictionary and SQL table
        self.runtime_dict[original_column] = shortened_column
        self._add_to_shorted_table(original_column, shortened_column)

        return shortened_column

    def add_entry_to_full_detail(self, entry):
        db = self.get_db()
        if db is None:
            log("Database connection failed.")
            return

        cursor = db.cursor()
        base_query = "INSERT INTO Full_Details ({columns}) VALUES ({values})"
        
        columns = []
        values = []
        for key, value in entry.items():
            original_column = key.replace(' ', '_')
            if len(original_column) > 64:
                column = self._get_shortened_column_name(original_column)
            else:
                column = original_column
            columns.append(column)
            values.append(value)
        
        columns_str = ", ".join(columns)
        placeholders_str = ", ".join(["%s"] * len(values))
        query = base_query.format(columns=columns_str, values=placeholders_str)
        success = False
        while True:
            try:
                cursor.execute(query, values)
                db.commit()
                success = True
                break
            except mysql.connector.Error as e:
                if "Unknown column" in str(e):
                    missing_column = str(e).split("'")[1]
                    alter_query = f"ALTER TABLE Full_Details ADD {missing_column} VARCHAR(700) DEFAULT NULL"
                    cursor.execute(alter_query)
                    log(f"unknown column {missing_column}")
                elif "Duplicate entry" in str(e):
                    log(f"Duplicate entry for SN {entry['SN']}. Skipping this entry.")
                    success = True
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
                        value_index = columns.index(column_name)
                        value_length = len(values[value_index])
                        new_length = value_length + 10  # Increase the length by 10
                        alter_query = f"ALTER TABLE Full_Details MODIFY {column_name} VARCHAR({new_length})"
                        cursor.execute(alter_query)
                    else:
                        log("Unable to determine the column name causing the error.")
                        break
                else:
                    log(f"An error occurred: {e}")
                    break
        cursor.close()
        return success


    def add_directors_from_dataframe(self, df: pd.DataFrame):
        db = self.get_db()
        if db is None:
            print("Database connection failed.")
            return False

        cursor = db.cursor()
        base_query = "INSERT INTO Director (SN, DIN, Director_Name, Designation, Appointment_Date) VALUES (%s, %s, %s, %s, %s)"
        success = True
        for index, row in df.iterrows():
            while True:
                try:
                    cursor.execute(base_query, (row['SN'], row['DIN'], row['Director_Name'], row['Designation'], row['Appointment_Date']))
                    db.commit()
                    break
                except mysql.connector.Error as e:
                    if "Duplicate entry" in str(e):
                        print(f"Duplicate entry for SN {row['SN']} and DIN {row['DIN']}. Skipping this entry.")
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
                            alter_query = f"ALTER TABLE Director MODIFY {column_name} VARCHAR({new_length})"
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

    def get_urls(self, low_limit, high_limit):
        db = self.get_db()
        if db is None or not db.is_connected():
            print("No connection to the database.")
            return None

        query = """
        SELECT SN, url 
        FROM details
        WHERE SN BETWEEN %s AND %s
        """
        params = (low_limit, high_limit)

        try:
            df = pd.read_sql(query, db, params=params)
            return df
        except Error as e:
            print(f"Error fetching data: {e}")
            return None
    
    def total_in_full_details(self):
        db = self.get_db()
        if db is None or not db.is_connected():
            print("No connection to the database.")
            return None

        query = """
            SELECT count(*) FROM zauba.full_details;	
        """
        params = ()
        try:
            last = pd.read_sql(query, db, params=params)
            return (list(last['count(*)']))[0]
        except Error as e:
            print(f"Error getting last: {e}")
            return None

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
            return (list(last['count(*)']))[0]
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

Last = db_conn.total_in_details()
already_done = db_conn.total_in_full_details()

if already_done is not None:
    i = ((already_done//batch)*batch)+1
    j=i
    t0=time.time()
    log(f"starting from {i}")
    good = True

    while i <= Last and good:
        low = i
        high = min(i + batch - 1, Last)
        log(f"Fetching URLs from {low} to {high}")

        df = db_conn.get_urls(low, high)
        log(f"Fetched {len(df)} URLs")

        retries = 0
        max_retries = 15

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
                        log(f"{row['SN']} generated an exception: {exc}")
                        good = False
                        break
            fetch_time = f"{time.time() - start_time:.2f}"
            log(f"Requests completed in {fetch_time} seconds")

            # Check if all results are valid
            all_data_valid = all(result is not None and result[0] is not None and result[1] is not None for _, result in results)

            if all_data_valid:
                for row, result in results:
                    result_dict, dataframe = result
                    if not db_conn.add_entry_to_full_detail(result_dict):
                        log("error in full details")
                        good = False
                        break
                    if not db_conn.add_directors_from_dataframe(dataframe):
                        log("error in full director")
                        good = False
                        break
                    print(f"{row['SN']} done")
                
                log(f"fetch time was {fetch_time}")
                log(f"Batch processing completed in {time.time() - start_time:.2f} seconds")
                if high>j:
                    print(f"{high*100/Last:.2f}% work is done and  {timedelta(seconds = int(((Last-high) * (time.time()-t0))  / (high-j)))} time remain ")
                else:
                    print("work is done.")
                break
            else:
                retries += 1
                if retries < max_retries:
                    log(f"Error: Not all results were valid, retrying batch in 1 minute... (Attempt {retries}/{max_retries})")
                    time.sleep(60*retries)
                else:
                    log("Error: Not all results were valid after 5 retries, halting the process.")
                    good = False
                    break
        log('*'*25 + "\n\n" +'*'*25 )
        i += batch

    log("finished")
    db_conn.close_db()
else:
    log("error in getting last point")
    db_conn.close_db()