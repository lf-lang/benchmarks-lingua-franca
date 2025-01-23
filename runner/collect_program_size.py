import sys
import os
import psutil
import time
import subprocess
import csv

# Function to run the `size` command and parse its output
def get_binary_size(binary_path):
    try:
        # Run the `size` command and capture the output
        result = subprocess.run(["size", "-G", binary_path],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        output = result.stdout.splitlines()
        
        # Parse the output of `size` command
        if len(output) < 2:
            raise ValueError(f"Unexpected output from `size` command for {binary_path}: {output}")

        # Extract the headers and values
        headers = output[0].split()[:-2]
        values = output[1].split()[:-2]

        # Ensure that headers and values are aligned
        if len(headers) != len(values):
            raise ValueError(f"Mismatch in headers and values for {binary_path}: {output}")

        # Create a dictionary of sizes
        size_dict = {headers[i]: int(values[i]) for i in range(len(headers))}
        return size_dict
    except Exception as e:
        print(f"Error processing {binary_path}: {e}")
        return None


def which_target(entry):
    file = os.path.join(entry.path, ".hydra/overrides.yaml")
    with open(file, "r") as f:
        for line in f:
            if "target" in line:
                target = line.split('=')[1].strip()
                break
    return target
        

# Main function to traverse directories and collect sizes
def collect_binary_sizes(base_path):
    results = [
        ['Benchmark', 'Target', 'text', 'data', 'bss', 'rss'],
    ]

    for entry in os.scandir(base_path):
        if entry.is_dir():
            target = which_target(entry)
            if target == "lf-ts":
                continue
            
            print(entry.name)

            binaryDir = os.path.join(entry.path, "bin")
            binary = os.scandir(binaryDir).__next__()

            res = get_binary_size(binary.path)

            if target == "lf-rust":
                if binary.name == "big":
                    continue

            memory_usage = measure_memory_usage(binary.path)

            bench = binary.name
            if target == "lf-rust":
                temp = binary.name.split("_")
                for i in range(len(temp)):
                    temp[i] = temp[i].capitalize()
                
                bench = "".join(temp)
                
            
            res = [bench, target, res["text"], res["data"], res["bss"], memory_usage]
            print(res)
            results.append(res)
            
            
    return results

def measure_memory_usage(binary_path):
    try:
        process = subprocess.Popen(binary_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        pid = process.pid
        ps_process = psutil.Process(pid)

        max_memory = 0

        while process.poll() is None:  # While the process is running
            memory_info = ps_process.memory_info()
            max_memory = max(max_memory, memory_info.rss)
            time.sleep(0.1)  # Poll every 100ms


        return max_memory
    except Exception as e:
        print(f"Error measuring memory usage for {binary_path}: {e}")
        return None


# Check for command-line argument
if len(sys.argv) < 3:
    print("Usage: python script.py <base_directory> <results_file>")
    sys.exit(1)

# Base directory to start searching
base_directory = sys.argv[1]
results_file = sys.argv[2]
results = collect_binary_sizes(base_directory)

# Print the collected sizes
print(results)

with open(results_file, 'w', newline='', encoding='utf-8') as csvfile:
    csvwriter = csv.writer(csvfile)
    
    # Write the rows to the file
    csvwriter.writerows(results)