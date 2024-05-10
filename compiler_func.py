import random
import subprocess
import re
import math

def parse_gcc_params(output, best_param, i, numIter, alpha=15, beta=30):
    params = {}
    param_pattern = r"--param=([\w-]+)=<(-?\d+),(-?\d+)>"
    exceptions_param = ['lazy-modules', 'logical-op-non-short-circuit', 'ranger-debug']
    for match in re.finditer(param_pattern, output):
        param_name = match.group(1)
        if param_name not in exceptions_param:
            a = int(match.group(2))
            b = int(match.group(3))
            # Initialize parameter with a random value within the specified range
            if param_name not in best_param or random.randint(0, 100)<(alpha*(random.random())) or i==0:
                params[param_name] = random.randint(a, b)
            else:
                value = random.randint(-1, 1)*math.floor(math.exp(-3*i/numIter)*(random.random())*(b-a)/beta) + best_param[param_name] 
                if value > a and value < b:
                    params[param_name] = value
                else:
                    params[param_name] = best_param[param_name] 

    # For parameters with a list of possible values, choose a random value from the list
    list_pattern = r"--param=([\w-]+)=\[((?:\w+\|)+\w+)\]?"
    for match in re.finditer(list_pattern, output):
        param_name = match.group(1)
        if param_name not in exceptions_param:
            possible_values = match.group(2).split('|')
            # Choose a random value from the list of possible values
            if param_name not in params:
                if param_name not in best_param or random.randint(0, 100)<math.floor(math.exp(-1.5*i/numIter)*(alpha)*(random.random()))  or i==0:
                    params[param_name] = random.choice(possible_values)
                else:
                    params[param_name] = best_param[param_name]


    # For parameters without specified ranges, assign a random value only if not in param_names
    default_pattern = r"--param=([\w-]+)="
    for match in re.finditer(default_pattern, output):
        param_name = match.group(1)
        if param_name not in exceptions_param:
            # Check if the parameter has already been assigned a value from param_pattern
            if param_name not in params:
                if param_name not in best_param or random.randint(0, 100)<(alpha*(random.random())) or i==0:
                    params[param_name] = random.randint(0, 100000)
                else:
                    if isinstance(best_param[param_name] , str):
                        print(best_param[param_name])
                    value = random.randint(-1, 1)*math.floor(math.exp(-3*i/numIter)*(random.random())*(100000)/beta) + best_param[param_name] 
                    if value > 0 and value < 100000:
                        params[param_name] = value
                    else:
                        params[param_name] = best_param[param_name] 

    return params

def compile_with_gcc(gcc_params, selected_indices, opt, i=-1, optTarget=2, output_binary="output", flto=0, compile_args=''):
    try:
        # Build the GCC command with parameters   
        param_cnt = 0
            
        if flto:
            gcc_command1 = ["gcc", opt, "-flto", "-fsave-optimization-record", "-o", output_binary]
        else:
            gcc_command1 = ["gcc", opt, "-o", output_binary]
            gcc_command2 = ["gcc", opt, "-S"]
        
        for cmd in compile_args.split():
            gcc_command1.append(cmd)
            if not flto:
                gcc_command2.append(cmd)
        
        for param_name, param_value in gcc_params.items():
            if param_cnt not in selected_indices:
                continue
            param_cnt += 1
            gcc_command1.append(f"--param={param_name}={param_value}")
            if not flto:
                gcc_command2.append(f"--param={param_name}={param_value}")
 
        #Run GCC to compile the program
        subprocess.check_call(gcc_command1)
        if not flto:
            subprocess.check_call(gcc_command2)

        if i<=-1: 
            print("Compilation successful. Binary SWAVX and assemblies generated.")
        return 1

    except subprocess.CalledProcessError as e:
        print(f"Error during compilation: {i}")
        print(e.output)
        return 0
