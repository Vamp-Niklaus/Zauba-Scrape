import re
data = """
Agriculture, Hunting And ... (94,109)
Fishing... (5,746)
Mining And Quarrying... (23,820)
Manufacturing... (459,934)
Electricity, Gas And Wate... (26,707)
Construction... (188,403)
Wholesale And Retail Trad... (271,233)
Hotels And Restaurants... (46,691)
Transport , Storag And Co... (79,121)
Financial Intermediation... (135,952)
Real Estate, Renting And ... (807,636)
Public Administration And... (904)
Education... (43,123)
Health And Social Work... (61,702)
Other Community, Social A... (72,775)
Undifferentiated Producti... (511)
Extra Territorial Organiz... (40,389)
"""
pattern = r'\(([\d,]+)\)' 

matches = re.findall(pattern, data)

last_number_on_each_line = []
for line in data.splitlines():
    match = re.findall(pattern, line)
    if match:
        last_number_on_each_line.append(match[-1])

total_sum = sum(int(match.replace(',', '')) for match in last_number_on_each_line)

print(f"Total sum : {total_sum}")