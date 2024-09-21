
import subprocess

url='https://www.zaubacorp.com/company-list'
try:
    result = subprocess.run(
        ['node', 'fetchAndExtract.js', url],
        capture_output=True, text=True, encoding='utf-8'
    )
    if result.returncode == 0:
        with open("list.html", "w") as file:
            file.write(result.stdout)
        # print(result.stdout)
    else:
        print("Error executing the JavaScript code:", result.stderr)
        None
except Exception as e:
    print("Exception occurred:", e)
    None