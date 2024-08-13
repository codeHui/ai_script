import requests  
import json  
import concurrent.futures  
import threading  
import time  
from tabulate import tabulate  
  
# Define the configurations  
number_of_requests_list = [1, 2, 4]  

world_count_list = [25, 50, 100, 200, 400, 800]  
  
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
            command = "tell a story in " + str(world_count) + " words: "  
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
