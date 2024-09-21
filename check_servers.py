import requests
import time
def log(message):
    timestamp = time.strftime("%H:%M:%S %p")
    s = f"{timestamp} - {message}\n"
    print(s)
    try:
        with open("server_log.txt", "a") as log_file:
            log_file.write(s)
    except FileNotFoundError:
        with open("server_log.txt", "w") as log_file:
            log_file.write(s)
            
def get_server(id):
    if id == 2:
        return "https://scrap002-vdvq.onrender.com/ping"
    return f"https://scrap{id:03}.onrender.com/ping"

def fetch_server_responses():
    for i in range(1, 101):
        url = get_server(i)
        try:
            response = requests.get(url)
            log(f"Server {i} returned: {response.text}")
        except requests.exceptions.RequestException as e:
            log(f"Server {i} could not be reached. Error: {e}")

if __name__ == "__main__":
    fetch_server_responses()
