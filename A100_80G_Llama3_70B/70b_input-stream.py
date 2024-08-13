import requests  
import json  
import concurrent.futures  
import threading  
import time  
from tabulate import tabulate  
  
text ="""
A consortium of KKR Infrastructure and APG has exited the race for a controlling stake in Electricity North West, leaving Iberdrola and a team of Engie and CDPQ in the final stages of the process, several sources said.

The APG and KKR team filed non-binding offers and attended management presentations but did not file one of the final offers, which were submitted by bidders earlier this week, according to the sources.

The APG-KKR exit takes place amid a tight auction for ENW, which operates an electricity distribution network serving 5m people in the northwest of England.

Spanish energy group Iberdrola – said by sources to be a front-runner in the process –  and a recently formed consortium of Engie and CDPQ have just filed final bids for the asset, with a winner expected to be selected within days.

The French utility and the Canadian pension fund recently teamed up after separately filing non-binding offers, the sources added.

Abu Dhabi utility giant TAQA also filed an NBO although the sources were not clear whether it put in a final offer. TAQA and Spanish investment holding CriteriaCaixa in June abandoned plans to jointly take over Spain’s largest utility Naturgy.

KKR Infrastructure and APG might have exited given competitive pressure from lower cost of capital strategics in the auction as well as rising return expectations in the current high interest rate environment. They might “struggle to invest at the same rates they used to”, one of the sources said.

Equitix is looking to sell its 40% stake in ENW, while Japan’s Kansai Electric Power Corporation, which also holds 40%, and China’s CINC Corp, are also expected to sell at least part of their shares, with a controlling stake up for grabs. The sellers are being advised by Jefferies.

Iberdrola, which is being advised by BNP Paribas, owns via SP Energy Networks electricity transmission and distribution networks in central and southern Scotland that are adjacent to ENW, as well as a further electricity distribution network covering Merseyside, North Wales, and parts of Cheshire.

At a recent UK global investment summit, Iberdrola described the UK as a “main investment market” and at the centre of its GBP 12bn 2024-2028 investment roadmap.

Iberdrola said recently that it is set to benefit from the GBP 5bn needed to be invested into new electricity distribution projects in southern and central Scotland up to 2030.

Ofgem recently set for electricity distribution network operators a cost of equity of 5.23% and a cost of debt of 3.07%.

The last DNO to trade in the UK was Western Power Distribution, which was acquired by National Grid in 2021 for a 1.6x multiple of its regulatory asset base. ENW has a GBP 2.4bn RAB, and might fetch GBP 4bn or more in the event of a sale.

Equitix, Engie, Iberdrola, CDPQ, and KKR declined to comment. APG, TAQA, and BNP Paribas did not respond to requests for comment.
"""
# Define the configurations  
number_of_requests_list = [1, 2, 4]  

world_count_list = [10]  
# world_count_list = [25, 50, 100, 200, 400, 800]  
  
# URL and data template for the POST request  
url = "http://localhost:11434/api/chat"  
headers = {'Content-Type': 'application/json'}  
  
# Lock for thread-safe printing  
print_lock = threading.Lock()  
  
def count_speed(index, token_speed_map):  
    count = token_speed_map.get(index)  # Safely get the value with .get()  
    if count is None:  # Use 'is None' to check for NoneType  
        token_speed_map[index] = 1  
    else:  
        token_speed_map[index] = count + 1  
  
# Function to send a POST request and handle streaming response  
def send_request(index, data, token_speed_map, time_map):  
    print(f"Thread {index} started sending request.")  
      
    start_time = time.time()  # Start time for the thread  
  
    response = requests.post(url, data=json.dumps(data), headers=headers, stream=True)  
  
    # Process the streaming response  
    for line in response.iter_lines():  
        if line:  
            decoded_line = line.decode('utf-8')  
            # Assuming the server sends JSON lines  
            json_line = json.loads(decoded_line)  
            if 'message' in json_line:  
                count_speed(index, token_speed_map)  
            with print_lock:  
                print(f" {index} {json_line['message']['content']} |", end='', flush=True)  
  
    end_time = time.time()  # End time for the thread  
    time_map[index] = end_time - start_time  # Calculate and store the time taken  
  
    with print_lock:  
        print(f"\nThread {index} completed.")  
  
# Function to perform concurrent requests  
def perform_concurrent_requests(number_of_requests, data):  
    token_speed_map = {}  
    time_map = {}  
    with concurrent.futures.ThreadPoolExecutor(max_workers=number_of_requests) as executor:  
        futures = [executor.submit(send_request, i, data, token_speed_map, time_map) for i in range(number_of_requests)]  
        concurrent.futures.wait(futures)  
      
    # Calculate and return the results  
    total_tokens = sum(token_speed_map.values())  
    total_time = sum(time_map.values())  
    average_tokens = total_tokens / number_of_requests if number_of_requests > 0 else 0  
    average_time = total_time / number_of_requests if number_of_requests > 0 else 0  
    average_speed = average_tokens / average_time if average_time > 0 else 0  
      
    return average_tokens, average_time, average_speed  
  
if __name__ == "__main__":  
    results = []  
  
    for number_of_requests in number_of_requests_list:  
        for world_count in world_count_list:  
            command = "give a title for below text in " + str(world_count) + " words: "  +text
            data = {  
                "model": "llama3.1:70b",  
                "messages": [  
                    {  
                        "role": "user",  
                        "content": command  
                    }  
                ],  
                "stream": True  
            }  
            print(f"Testing with number_of_requests={number_of_requests}, world_count={world_count}")  
            avg_tokens, avg_time, avg_speed = perform_concurrent_requests(number_of_requests, data)  
            results.append([number_of_requests, world_count, avg_tokens, avg_time, avg_speed])  
  
    # Print the results in a table format  
    print(tabulate(results, headers=["Number of Requests", "World Count", "Average Tokens", "Average Time (s)", "Average Speed (tokens/s)"]))  
