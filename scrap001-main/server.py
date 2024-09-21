from flask import Flask, request, jsonify,render_template
import subprocess
from bs4 import BeautifulSoup
import pandas as pd
import time
app = Flask(__name__)
import time

def fetch_html(url):
    try:
        result = subprocess.run(
            ['node', 'fetchAndExtract.js', url],
            capture_output=True, text=True, encoding='utf-8'
        )
        if result.returncode == 0:
            return result.stdout
        else:
            print("Error executing the JavaScript code:", result.stderr)
            return None
    except Exception as e:

        print("Exception occurred:", e)
        return None
    


import execjs

js_code = """
function decodeEmail(encodedString) {
    var email = '',
        r = parseInt(encodedString.substr(0, 2), 16),
        n, i;
    for (n = 2; encodedString.length - n; n += 2) {
        i = parseInt(encodedString.substr(n, 2), 16) ^ r;   
        email += String.fromCharCode(i);
    }
    return email;
}
"""

            


def extractCompanyDetails(table):
    table_data = []
    for row in table.find_all('tr'):
        columns = row.find_all(['td', 'th'])
        row_data = [col.get_text(strip=True) for col in columns]
        if row_data[0]=="Activity":
          row_data[1]=row_data[1][:-59]
        table_data.append(row_data)
    return table_data

def extractShareCapital(table):
    table_data = []
    for row in table.find_all('tr'):
        columns = row.find_all(['td', 'th'])
        row_data = [col.get_text(strip=True) for col in columns]
        if row_data[1]=="Login to view":
          continue
        row_data[1] = ''.join([char for char in row_data[1] if char.isnumeric()])
        table_data.append(row_data)
    return table_data


def extractAnnualCompliance(table):
    table_data = []
    for row in table.find_all('tr'):
        columns = row.find_all(['td', 'th'])
        row_data = [col.get_text(strip=True) for col in columns]
        table_data.append(row_data)
    return table_data


@app.route('/ason', methods=['POST'])
def ason():
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    try:
        trial = 4
        while 1:
            sn = request.json.get('SN')
            html_content = fetch_html(url)
            dict= {}
            dict["SN"] = sn
            soup = BeautifulSoup(html_content, 'html.parser')
            div_element = soup.find('div', style="vertical-align: bottom; float:left; width:45%;")
            as_on_value = None
            if div_element:
                b_element = div_element.find('b')
                if b_element:
                    full_text = b_element.get_text(strip=True)
                    if full_text.startswith("As on:"):
                        as_on_value = full_text.replace("As on:", "").strip()
            if as_on_value:
                dict['As_on'] = as_on_value
            if trial == 0 or 'As_on' in dict:
                return jsonify(dict)
            else:
                trial = trial - 1
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@app.route('/scrape', methods=['POST'])
def scrape():
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    try:
        if url.startswith("https://www.zaubacorp.com/company-list/"):
            html_content = fetch_html(url)
            soup = BeautifulSoup(html_content, 'html.parser')
            tbody = soup.find('table', {'id': 'table'})
            if tbody is None:
                raise ValueError("No tbody found in table")
            rows = tbody.find_all('tr')[1:]
            data = []
            headers = ['CIN','Company','RoC','Status']
            headers.append('URL')
            for row in rows:
                cells = row.find_all('td')
                cin = cells[0].text.strip()
                company_name_tag = cells[1].find('a')
                company_name = company_name_tag.text.strip() if company_name_tag else cells[1].text.strip()
                company_url = company_name_tag['href'] if company_name_tag else ''
                roc = cells[2].text.strip()
                status = cells[3].text.strip()
                data.append([cin, company_name, roc, status, company_url])
            df = pd.DataFrame(data, columns=headers)
            df_json = df.to_json(orient='records')
            return df_json
        else:    
            trial = 3
            while 1:
                sn = request.json.get('SN')
                html_content = fetch_html(url)
                dict= {}
                dict["SN"] = sn
                soup = BeautifulSoup(html_content, 'html.parser')
                target_div = soup.find('h4', string="Company Details")
                if target_div:
                    parent_div = target_div.find_parent('div', class_="col-lg-12 col-md-12 col-sm-12 col-xs-12")
                    if parent_div:
                        table = parent_div.find('table')
                        if table:
                            table_data = extractCompanyDetails(table)
                            for row in table_data:
                                key, value = row
                                dict[key] = value
    
                target_div = soup.find('h4', string=lambda text: 'Share Capital & Number of Employees' in text)
                if target_div:
                    parent_div = target_div.find_parent('div', class_="col-lg-12 col-md-12 col-sm-12 col-xs-12")
                    if parent_div:
                        table = parent_div.find('table')
                        if table:
                            table_data = extractShareCapital(table)
                            for row in table_data:
                                key, value = row
                                dict[key] = value
    
    
                target_div = soup.find('h4', string=lambda text: 'Listing and Annual Compliance Details' in text)
                if target_div:
                    parent_div = target_div.find_parent('div', class_="col-lg-12 col-md-12 col-sm-12 col-xs-12")
                    if parent_div:
                        table = parent_div.find('table')
                        if table:
                            table_data = extractAnnualCompliance(table)
                            for row in table_data:
                                key, value = row
                                dict[key] = value
                
                
                
                Ason_element = soup.find('div', style="vertical-align: bottom; float:left; width:45%;")
                as_on_value = None
                if Ason_element:
                    b_element = Ason_element.find('b')
                    if b_element:
                        full_text = b_element.get_text(strip=True)
                        if full_text.startswith("As on:"):
                            as_on_value = full_text.replace("As on:", "").strip()
                if as_on_value:
                    dict['As_on'] = as_on_value
                email_tag = soup.find('a', class_='__cf_email__')
                email_data = email_tag['data-cfemail'] if email_tag else None
                ctx = execjs.compile(js_code)
                email_id = ctx.call("decodeEmail", email_data) if email_data else ""
                address_tag = soup.find('p', string=lambda text: text and 'Address:' in text)
                address = address_tag.find_next('p').get_text().strip() if address_tag else ""
    
                dict["Email ID"] = email_id
                dict["Address"] = address
                dict["Url"] = url
                rows = soup.find_all('tr', class_='accordion-toggle main-row')
                data = []
                for row in rows:
                    cols = row.find_all('td')
                    cols = [col.text.strip() for col in cols]
                    cols.insert(0, sn) 
                    data.append(cols[:-1])
                df = pd.DataFrame(data, columns=['SN','DIN', 'Director_Name', 'Designation', 'Appointment_Date'])
                df_json = df.to_dict(orient='records')
                if trial == 0 or ('Company Status' in dict and 'As_on' in dict):
                    return jsonify({"result_dict": dict, "dataframe": df_json})
                else:
                    trial = trial - 1

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ping', methods=['GET'])
def ping():
    return "Zorojuro!", 200
@app.route('/success')
def home():
    return render_template('index.html')
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
