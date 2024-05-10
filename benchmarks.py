import glob
import re
import os
import subprocess
from utils import *

def get_gcups_from_command(command, numIter):
    GCUPS = []
    try:
        for i in range(numIter):
            # Run the command and capture its output
            result = subprocess.run(command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # Check if the command was successful (return code 0)
            if result.returncode == 0:
                # Search for the line containing "GCUPS: <number>"
                match = re.search(r'(\d+\.\d+)', result.stdout)
                if match:
                    gcups = float(match.group(1))
                    gcups = 1.0/gcups
                    GCUPS.append(gcups)
                else:
                    return None  # No matching line found
            else:
                # Command failed, return None
                return None
        return compute_mean_and_filter(GCUPS)
    except Exception as e:
        # Handle exceptions, e.g., command not found or other errors
        print(f"An error occurred: {str(e)}")
        return None
    
def count_instructions_in_directory(directory):
    # Initialize a dictionary to store instruction frequencies
    instruction_count = {}

    # Initialize a variable to store the overall number of instructions
    total_instructions = 0

    try:
        # Iterate through all files in the directory
        for filename in os.listdir(directory):
            if filename.endswith(".s"):
                file_path = os.path.join(directory, filename)

                with open(file_path, 'r') as file:
                    for line in file:
                        # Remove leading and trailing whitespace and split the line into words
                        words = line.strip().split()

                        # Check if the line starts with a dot (.) or is empty
                        if not words or words[0].startswith('.') or words[0][-1]==':':
                            continue  # Ignore this line

                        # Extract the first word (instruction) from the line
                        instruction = words[0]

                        # Update the instruction count dictionary
                        if instruction in instruction_count:
                            instruction_count[instruction] += 1
                        else:
                            instruction_count[instruction] = 1

                        # Increment the overall instruction count
                        total_instructions += 1

        # Return the instruction count dictionary and total number of instructions
        return instruction_count, total_instructions

    except FileNotFoundError:
        print(f"Directory '{directory}' not found.")
        return {}, 0

def get_asm_info(input_directory):
    throughput_dict = {}

    # Find all "*.s" files in the input directory
    s_files = glob.glob(input_directory + "/*.s")
    #s_files = ['./SWAVX_256_Func_SeqToSeq_SubMat.s']
    
    for s_file in s_files:
        command = f"llvm-mca {s_file}"
        
        try:
            output = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            print(f"Error running the command for {s_file}: {e}")
            continue

        #pattern = r"Total Cycles:\s+(\d+)"
        pattern = r"Total Cycles:\s+(\d+)"
        match = re.search(pattern, output)

        if match:
            throughput = int(match.group(1))
            throughput_dict[s_file] = throughput
        else:
            print(f"Pattern not found in the command output for {s_file}")

    return list(throughput_dict.values())

def get_size_info(binary_name):
    command = f"du -b {binary_name}"
        
    try:
        output = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print(f"Error running the command for {binary_name}: {e}")
    
    '''
    #pattern = r"Total Cycles:\s+(\d+)"
    pattern = r'\s+caad\s+(\d+)\s+Sep\s+'
    match = re.search(pattern, output)

    try match:
        Size = int(match.group(1))
        return Size
    else:
        print(f"Pattern not found in the command output for {binary_name}")
    '''
    try:
        return int(output.split()[0])
    except:
        print(f"Pattern not found in the command output for {binary_name}")
