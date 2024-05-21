from benchmarks import *
from Beysian_opt import optimize_compiler_parameters
import matplotlib.pyplot as plt

def normalize_and_plot(dictionary):
    # Normalize the dictionary values
    values = np.array(list(dictionary.values()))
    min_val = min(values)
    max_val = max(values)
    normalized_values = [(val - min_val) / (max_val - min_val) for val in values]
    
    # Sort the normalized values from highest to lowest
    sorted_values = sorted(normalized_values, reverse=True)
    threshold_dict = {key: normalized_value > 0.5 for key, normalized_value in zip(dictionary.keys(), normalized_values)}
    # Plot the sorted values
    plt.figure(figsize=(40, 5))
    plt.plot(sorted_values, marker='o', linestyle='-')
    plt.title('Normalized and Sorted Values')
    plt.xlabel('Index')
    plt.ylabel('Normalized Value')
    plt.grid(True)
    plt.savefig('out_val.png')
    return threshold_dict, zip(dictionary.keys(), normalized_values)

def process_and_sort_file(input_filename, output_filename, threshold):
    try:
        # Initialize an empty dictionary
        data_dict = {}
        
        # Open the input file for reading
        with open(input_filename, 'r') as infile:
            # Read lines from the file
            lines = infile.readlines()
            
            # Process each line
            for line in lines:
                # Check if the line starts with '-'
                if line.startswith('-'):
                    # Split into key and value, keeping the '-'
                    parts = line.strip().split()
                    if len(parts) == 2:
                        key, value = parts
                        try:
                            # Convert the value to a float
                            value = float(value)
                            # Store the key-value pair in the dictionary
                            data_dict[key] = value
                        except ValueError:
                            print(f"Skipping line with invalid float value: {line.strip()}")
                    else:
                        
                        try:
                            key = ' '.join(parts[0:-1])
                            value = parts[-1]
                            value = float(value)
                            data_dict[key] = value
                        except ValueError:
                            print(f"Skipping line with invalid float value: {line.strip()}")

        # Sort the dictionary by value in descending order
        _, norm_list = normalize_and_plot(data_dict)
        sorted_data = sorted(norm_list, key=lambda item: item[1], reverse=True)
        

        # Open the output file for writing
        with open(output_filename, 'w') as outfile:
            # Write the sorted dictionary entries to the file
            for key, value in sorted_data:
                outfile.write(f"{key} {value}\n")
        
        # Concatenate keys with values higher than the threshold
        concatenated_keys = ' '.join(key for key, value in sorted_data if value > threshold)
        
        print(f"Data successfully processed, sorted, and saved to {output_filename}")
        #print(f"{concatenated_keys}")
        
        return concatenated_keys
        
    except FileNotFoundError:
        print(f"The file {input_filename} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")


def compile_and_evaluate(parameters, output_binary="tuned", numTest=20, compile_args='', optTarget=1, optPass='', param_tune=False):
    #included_params = [param for param, include in parameters if include]
    
    # Build the compiler command with the selected parameters
    if param_tune:
        parameters = optimize_compiler_parameters(numIter=20, output_binary=output_binary,  numTest=numTest*5, compile_args=compile_args, optTarget=optTarget, optPass=optPass)

    compiler_command = "gcc -Werror -w "  + optPass + ' ' + compile_args

    i = 0
    for param_name, param_value in parameters.items():
        if i>255:
            break
        compiler_command += f" --param={param_name}={param_value}"
        i += 1
    
    # Compile the code and measure runtime
    try:
        subprocess.check_call((compiler_command+ ' -S').split())
        subprocess.check_call((compiler_command+' -o '  + output_binary+'.out').split())
    except subprocess.CalledProcessError as e:
        print(f"Error during compilation: {i}")
        print(e.output)
        return 1e7#, "GCUPS": (-1e7, 1e7)}  # Return negative infinity in case of compilation failure
    
    # Measure runtime using your method
    if optTarget == 0:
        if get_gcups_from_command(f"./{output_binary}", 1)<=0.001:
            return 1e7
        GCUPS = run_hyperfine_and_extract_time(output_binary+'.out')/1000.0
        if GCUPS == 0.0:
            return 1e7
    elif optTarget==1:
        GCUPS = get_gcups_from_command(f"./{output_binary+'.out'}", numTest)
    elif optTarget==2:
        GCUPS = sum(count_instructions_in_directory('./')[0].values())
    elif optTarget==3:
        GCUPS = sum(get_asm_info('./'))/1000.0
    else:
        GCUPS = get_size_info(output_binary+'.out')/1000.0
    
    
    return GCUPS#{"size": (size, 0.0)}#, "GCUPS": (GCUPS, 2)}

if __name__ == "__main__":
    concatenated_keys = process_and_sort_file('out.txt', 'out_processed.txt', 0.58)
    compile_args = '-I polybench-c-3.2/utilities -I polybench-c-3.2/linear-algebra/kernels/atax polybench-c-3.2/utilities/polybench.c polybench-c-3.2/linear-algebra/kernels/atax/atax.c -DPOLYBENCH_TIME'


    #print(concatenated_keys)
    print('-----------------------------------------------------------------------')
    init  = compile_and_evaluate({}, output_binary="tuned", numTest=20, compile_args=compile_args, optTarget=0, optPass='-Ofast', param_tune=False)*1000.0
    final = compile_and_evaluate({}, output_binary="tuned", numTest=20, compile_args=compile_args+' '+concatenated_keys, optTarget=0, optPass='', param_tune=False)*1000.0
    print('Init:', end=' ')
    print(init)
    print('Final:', end=' ')
    print(final)

