from flask import Flask, request, jsonify, render_template
import mysql.connector
from mysql.connector import Error
from flask_wtf.csrf import CSRFProtect, generate_csrf
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with your actual secret key
csrf = CSRFProtect(app)

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
    'database': 'back_up',
    'port': 3306,
}


def generate_query_from_name(col, input_string,is_id):
    invalid_chars = ['\\', "'"]
    if is_id and any(char in input_string for char in invalid_chars):
        raise ValueError("don't use character like \\ and \' as they are not in any CIN and DIN")
    query = ' '
    s = ""
    i = 0
    bracket_closed = False
    params = []
    if col!='CIN':
        while i < len(input_string):
            # print(input_string[i])
            char = input_string[i]
            if char not in ['+', '\\', '|', ' ', '~']:
                s += char
            elif char == '+' and not s and bracket_closed:
                query += ' AND '
                bracket_closed = False
                if i+1<len(input_string) and input_string[i+1]==' ':
                    i+=1
            elif char == '|' and not s.strip() and bracket_closed:
                query += ' or '
                bracket_closed = False
                if i+1<len(input_string) and input_string[i+1]==' ':
                    i+=1
            elif (char == '+' or '|') and s.strip() and bracket_closed:
                    raise ValueError("can not use direct query after ) withoout using + or | operator.")
            elif char == '+' :
                if s.strip():
                    params.append(s)
                    query += f"{col} LIKE %s AND "
                    s = ""
                    if i+1<len(input_string) and input_string[i+1]==' ':
                        i+=1
            elif char == '|':
                if s.strip():
                    params.append(s)
                    query += f"{col} LIKE %s OR "
                    s = ""
                    if i+1<len(input_string) and input_string[i+1]==' ':
                        i+=1
            elif char == ' ':
                next_char = input_string[i + 1] if i + 1 < len(input_string) else ''
                # ( (i+1) < len(input_string) ) and s[i+1] not in ['+', '|', '(', ')']
                if next_char not in ['+', '|'] and (i+1 != len(input_string)) and ( i<=1 or (i>1 and input_string[i-1]!='(' and input_string[i-2]!='\\') ):
                    s += char

       
            elif char == '\\':
                i += 1
                if i < len(input_string):
                    char = input_string[i]
                    if char == '(':
                        if s.strip() == "":
                            query += " ( "
                            s = ""
                            if i+1<len(input_string) and input_string[i+1]==' ':
                                i+=1
                        else:
                            raise ValueError("Unexpected characters before '('.")
                    elif char == ')':
                        if s.strip():
                            params.append(s)
                            query += f"{col} LIKE %s"
                            s = ""
                            query += " ) "
                            bracket_closed = True
                            if i+1<len(input_string) and input_string[i+1]==' ':
                                i+=1
                        else:
                            raise ValueError("Unexpected characters before ')'.")
                    else:
                        s += input_string[i]
            elif char == '~':
                if not s.strip():
                    query += " NOT "
                    s = ""
            i += 1
        
        if s.strip():
            params.append(s)
            query += f"{col} LIKE %s"
        
        if query.endswith(' AND '):
            query = query[:-5]
        elif query.endswith(' OR '):
            query = query[:-4]
        return query, params
    else:
        # this is special case for making query to search via CIN as in full details there are 2 more column which have
        # this idetinfication number LLP_Identification_Number and Foreign_Company_Registration_Number
        while i < len(input_string):
            char = input_string[i]
            
            if char not in ['+', '\\', '|', ' ', '(', ')', '~']:
                s += char
            elif char == '+' and not s.strip() and bracket_closed:
                query += ' AND '
                bracket_closed = False
                if i+1<len(input_string) and input_string[i+1]==' ':
                    i+=1
            elif char == '|' and not s.strip() and bracket_closed:
                query += ' or '
                bracket_closed = False
                if i+1<len(input_string) and input_string[i+1]==' ':
                    i+=1
            elif (char == '+' or '|') and s.strip() and bracket_closed:
                    raise ValueError("can not use direct query after ) withoout using + or | operator.")
            elif char == '+':
                if s.strip():
                    params.append(s)
                    params.append(s)
                    params.append(s)
                    query += f" ( COALESCE(CIN, '') LIKE %s or COALESCE(LLP_Identification_Number, '') LIKE %s or COALESCE(Foreign_Company_Registration_Number, '') LIKE %s )  AND "
                    s = ""
                    if i+1<len(input_string) and input_string[i+1]==' ':
                        i+=1
            elif char == '|':
                if s.strip():
                    params.append(s)
                    params.append(s)
                    params.append(s)
                    query += f" ( COALESCE(CIN, '') LIKE %s or COALESCE(LLP_Identification_Number, '') LIKE %s or COALESCE(Foreign_Company_Registration_Number, '') LIKE %s )  OR "
                    s = ""
                    if i+1<len(input_string) and input_string[i+1]==' ':
                        i+=1
            elif char == ' ':
                next_char = input_string[i + 1] if i + 1 < len(input_string) else ''
                if next_char not in ['+', '|'] and (i+1 != len(input_string)) and ( i<=1 or (i>1 and input_string[i-1]!='(' and input_string[i-2]!='\\') ):
                    s += char
            
       
            elif char == '\\':
                i += 1
                if i < len(input_string):
                    char = input_string[i]
                    if char == '(':
                        if s.strip() == "":
                            query += " ( "
                            s = ""
                            if i+1<len(input_string) and input_string[i+1]==' ':
                                i+=1
                        else:
                            raise ValueError("Unexpected characters before '('.")
                    elif char == ')':
                        if s.strip():
                            params.append(s)
                            params.append(s)
                            params.append(s)
                            query += f" ( COALESCE(CIN, '') LIKE %s or COALESCE(LLP_Identification_Number, '') LIKE %s or COALESCE(Foreign_Company_Registration_Number, '') LIKE %s ) "
                            s = ""
                            query += " ) "
                            bracket_closed = True
                            if i+1<len(input_string) and input_string[i+1]==' ':
                                i+=1
                        else:
                            raise ValueError("Unexpected characters before ')'.")
                    else:
                    
                        s += input_string[i]
            elif char == '~':
                if not s.strip():
                    query += " NOT "
                    s = ""
            i += 1
        
        if s.strip():
            params.append(s)
            params.append(s)
            params.append(s)
            query += f" ( COALESCE(CIN, '') LIKE %s or COALESCE(LLP_Identification_Number, '') LIKE %s or COALESCE(Foreign_Company_Registration_Number, '') LIKE %s ) "
        
       

        if query.endswith(' AND '):
            query = query[:-5]
        elif query.endswith(' OR '):
            query = query[:-4]
        return query, params
        

class QueryError(Exception):
    """Custom exception for query errors."""
    pass

class DBConnection:
    def __init__(self):
        self.g = {}
    
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

@app.route('/')
def home():
    csrf_token = generate_csrf()
    return render_template('index.html', csrf_token=csrf_token)

@app.route('/search', methods=['POST'])
def search():
    companyQuery = request.json.get('company')
    directorQuery = request.json.get('director')
    result = request.json.get('format')
    num_pages = int(request.json.get('numPages'))
    page = int(request.json.get('page'))
    companyColumn = request.json.get('companyColumn')
    directorColumn = request.json.get('directorColumn')

    offset = (page - 1) * num_pages
    data = request.json
    print("Company:", companyQuery)
    print("Director:", directorQuery)
    print("Format:", result)
    print("Num Pages:", num_pages)
    print("Page:", page)
    print("company Column:", companyColumn)
    print("director Column:", directorColumn)
    # + goes for 'and' take intersection
    # | goes for 'or' take union
    # default it goes for SOP(sum of product) as here statements are like AB + C => can be goes as (A&B) U C. here + means as union.
    if not companyQuery and not directorQuery:
        return jsonify({'error': 'Both company and director cannot be empty.'}), 400
    
    base_query = "SELECT  f.CIN,  f.Company_Name, d.DIN, d.SN, d.Director_Name, d.Designation, d.Appointment_Date, f.Company_Status, f.ROC, f.LLP_Identification_Number, f.Registration_Number, f.Foreign_Company_Registration_Number,f.Company_Category, f.Company_Sub_Category, f.Class_of_Company, f.Date_of_Incorporation, f.Age_of_Company, f.Activity,f.Number_of_Members, f.Authorised_Capital, f.Paid_up_capital, f.Listing_status, f.Date_of_Last_Annual_General_Meeting,f.Date_of_Latest_Balance_Sheet, f.Email_ID, f.Address, f.Url,f.Date_of_last_financial_year_end_date_for_which_Annual_R_f1e09135,f.Date_of_last_financial_year_end_date_for_which_Statemen_d6a6f160, f.Description_of_main_division,f.Main_division_of_business_activity_to_be_carried_out_in_India, f.Number_Of_Partners, f.Number_of_Designated_Partners,f.Total_Obligation_of_Contribution, f.Country_of_Incorporation, f.Type_Of_Office, f.As_on "
    
    if  result == 'Company':
        base_query = "SELECT  f.CIN,  f.Company_Name, f.Company_Status, f.ROC, f.LLP_Identification_Number, f.Registration_Number, f.Foreign_Company_Registration_Number,f.Company_Category, f.Company_Sub_Category, f.Class_of_Company, f.Date_of_Incorporation, f.Age_of_Company, f.Activity, f.Number_of_Members, f.Authorised_Capital, f.Paid_up_capital, f.Listing_status, f.Date_of_Last_Annual_General_Meeting, f.Date_of_Latest_Balance_Sheet, f.Email_ID, f.Address, f.Url, f.Date_of_last_financial_year_end_date_for_which_Annual_R_f1e09135, f.Date_of_last_financial_year_end_date_for_which_Statemen_d6a6f160, f.Description_of_main_division, f.Main_division_of_business_activity_to_be_carried_out_in_India, f.Number_Of_Partners, f.Number_of_Designated_Partners, f.Total_Obligation_of_Contribution, f.Country_of_Incorporation, f.Type_Of_Office, f.As_on, f.SN "
        
    if result == 'Director':
        base_query = "SELECT d.DIN, d.SN , d.Director_Name, d.Designation, d.Appointment_Date "
    
    db_connection = DBConnection()
    
    try:
        if not directorQuery and result == 'Company' :
            base_query += " FROM sample_full_details as f where "
            try:
                sql_query, params = generate_query_from_name(f"f.{companyColumn}" , companyQuery,companyColumn == 'CIN')
                base_query+=sql_query
            except ValueError as e:
                raise QueryError(f"Invalid query: {e}")

        elif  not companyQuery and result == 'sample_Director' :
            base_query += " FROM director as d WHERE "
            try:
                sql_query, params = generate_query_from_name(directorColumn, directorQuery,directorColumn=='DIN')
                base_query+=sql_query
            except ValueError as e:
                raise QueryError(f"Invalid query: {e}")
        else:
            if result == 'Join':
                base_query += " FROM sample_full_details as f LEFT JOIN sample_director as d ON f.SN = d.SN where "
            else:
                base_query += " FROM sample_full_details as f INNER JOIN sample_director as d ON f.SN = d.SN where "
                
            try:
                params=[]
                if companyQuery:
                    sql_query_on_company, params_on_company = generate_query_from_name(f"f.{companyColumn}" , companyQuery,companyColumn == 'CIN')
                    base_query+=sql_query_on_company
                    params = params_on_company

                if companyQuery and directorQuery:
                    base_query+=" AND "
                    
                if directorQuery:
                    sql_query_on_director, params_on_director = generate_query_from_name(f"d.{directorColumn}" , directorQuery,directorColumn == 'DIN')
                    base_query+=sql_query_on_director
                    params = params + params_on_director
                

                
            except ValueError as e:
                raise QueryError(f"Invalid query: {e}")
            
        base_query += " LIMIT %s OFFSET %s;"
        params.append(num_pages)
        params.append(offset)
        params = tuple(params)
        
        print(base_query)
        print(params)
        
        
        db = db_connection.get_db()
        cursor = db.cursor()
        cursor.execute(base_query, params)
        data = cursor.fetchall()
        cursor.close()

        has_more = len(data) == num_pages

        return jsonify({
            'results': data,
            'hasMore': has_more
        })

    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except QueryError as qe:
        return jsonify({'error': str(qe)}), 400
    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred: ' + str(e)}), 500
  


if __name__ == '__main__':
    app.run(debug=True)
