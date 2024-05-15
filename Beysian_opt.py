import subprocess
import random
import ax
from ax import ParameterType, RangeParameter, ChoiceParameter
from ax.modelbridge import Models
import numpy as np
import re
from ax.service.ax_client import AxClient
from ax.service.ax_client import AxClient, ObjectiveProperties
import logging


from utils import *
from benchmarks import *

def parse_gcc_params():
    params = {}
    param_pattern = r"--param=([\w-]+)=<(-?\d+),(-?\d+)>"
    exceptions_param = ['lazy-modules', 'logical-op-non-short-circuit', 'ranger-debug', 'lto-min-partition', 'lto-max-partition', 'vect-max-peeling-for-alignment']
    output = subprocess.check_output(["gcc", "--help=params"], stderr=subprocess.STDOUT, universal_newlines=True)
    for match in re.finditer(param_pattern, output):
        param_name = match.group(1)
        if param_name not in exceptions_param:
            a = int(match.group(2))
            b = int(match.group(3))
            # Initialize parameter with a random value within the specified range
            params[param_name] = [a,b]

    # For parameters with a list of possible values, choose a random value from the list
    list_pattern = r"--param=([\w-]+)=\[((?:\w+\|)+\w+)\]?"
    for match in re.finditer(list_pattern, output):
        param_name = match.group(1)
        if param_name not in exceptions_param:
            possible_values = match.group(2).split('|')
            # Choose a random value from the list of possible values
            if param_name not in params:
                params[param_name] = possible_values


    # For parameters without specified ranges, assign a random value only if not in param_names
    default_pattern = r"--param=([\w-]+)="
    for match in re.finditer(default_pattern, output):
        param_name = match.group(1)
        if param_name not in exceptions_param:
            # Check if the parameter has already been assigned a value from param_pattern
            if param_name not in params:
                params[param_name] = [0,1e3]

    return params


# Function to compile the code with a set of parameters and return the runtime
def compile_and_evaluate(parameters, output_binary="tuned", numTest=20, compile_args='', optTarget=1, optPass='-O3'):
    #included_params = [param for param, include in parameters if include]
    
    # Build the compiler command with the selected parameters
    compiler_command = "gcc -o " + output_binary + ' ' + optPass + ' ' + compile_args

    i = 0
    for param_name, param_value in parameters.items():
        if i>255:
            break
        compiler_command += f" --param={param_name}={param_value}"
        i += 1
    
    # Compile the code and measure runtime
    try:
        subprocess.check_call(compiler_command.split())
    except subprocess.CalledProcessError as e:
        print(f"Error during compilation: {i}")
        print(e.output)
        return {"GCUPS": 1e7}#, "GCUPS": (-1e7, 1e7)}  # Return negative infinity in case of compilation failure
    
    # Measure runtime using your method
    if optTarget==1:
        GCUPS = get_gcups_from_command(f"./{output_binary}", numTest)
    else:
        GCUPS = get_size_info(output_binary)
    
    
    return {"GCUPS": GCUPS}#{"size": (size, 0.0)}#, "GCUPS": (GCUPS, 2)}


# Function to create random parameter settings with inclusion flags
def define_parameter_space(param_dict):
    parameters = []
    for param_name, param_range in param_dict.items():
        if not isinstance(param_range[0], int):
            parameters.append({"name":param_name, "type": "choice", "values":param_range, "value_type": "str", "is_ordered":False})
        else:
            parameters.append({"name":param_name, "type": "range", "bounds":param_range, "value_type": "int"})
    return parameters

# Function to optimize the compiler parameters
def optimize_compiler_parameters(numIter=10, output_binary="tuned", numTest=20, thresholds=[21104,5], compile_args='', optTarget=1, optPass='-O3'):
    # Define the parameter space
    param_dict = parse_gcc_params()
    parameters = define_parameter_space(param_dict)
    GCUPS_init = thresholds[0]#compile_and_evaluate({}, 'untuned', numTest=numTest)['GCUPS'][0]
    #the = GCUPS_init*0.95

    ax_client = AxClient(verbose_logging = False)
    ax_client.create_experiment(
        name="GCC hyperparameters tuning",
        parameters=parameters,
        objective_name="GCUPS",
        minimize=True,
        #num_initialization_trials = 20,
        #use_batch_trials=False,
        #max_initialization_trials = 20,
        
    )

    print("----------------------------------")
    for i in range(numIter):
        parameters, trial_index = ax_client.get_next_trial()
        ax_client.complete_trial(trial_index=trial_index, raw_data=compile_and_evaluate(parameters, output_binary=output_binary, numTest=numTest, compile_args=compile_args, optTarget=optTarget, optPass=optPass))
        percentile = (i+1)/numIter*100
        progress   = (i+1)/numIter*30
        print(f" In progress: {percentile:.2f}%\t[", end="")
        for j in range(30):
            if j<progress-1:
                print("#", end="")
            elif (j-1)<progress-1 and (i+1)!=numIter:
                print(">", end="")
            elif (i+1)==numIter:
                print("#", end="")
            else:
                print("-", end="")
        print("]", end="\r")
    print("\n----------------------------------")
    print("DONE!")
    best_parameters, metrics = ax_client.get_best_parameters()
    #paretos = ax_client.get_pareto_optimal_parameters()
    return best_parameters

# Number of optimization iterations
def Main(numIter=10, output_binary="tuned", numTest=1):
    compile_args = '-I polybench-c-3.2/utilities -I polybench-c-3.2/linear-algebra/kernels/atax polybench-c-3.2/utilities/polybench.c polybench-c-3.2/linear-algebra/kernels/atax/atax.c -DPOLYBENCH_TIME'
    evalInit = compile_and_evaluate({}, output_binary=output_binary+"_init", numTest=numTest, compile_args=compile_args)
    evalInit = compile_and_evaluate({}, output_binary=output_binary+"_init", numTest=numTest, compile_args=compile_args)
  #  print("GCUPS initial: ", evalInit['GCUPS'])
    print("GUCPS initial: ", evalInit['GCUPS'])
    best_parameters = optimize_compiler_parameters(numIter=numIter, output_binary=output_binary,  numTest=numTest, thresholds=[evalInit['GCUPS']], compile_args=compile_args)#, evalInit['GCUPS']])
    evalFinal = compile_and_evaluate(best_parameters, output_binary=output_binary, numTest=numTest, compile_args=compile_args)
   # print("GCUPS final: ", evalFinal['GCUPS'])
    print("GCUPS final: ", evalFinal['GCUPS'])


if __name__ == "__main__":
    Main(numIter=100, output_binary="tuned", numTest=100)
