from utils import *
from compiler_func import *
from benchmarks import *

import multiprocessing
from tuner import tuner

import io
import sys

def capture_output(func ='', dir='./', compile_args='', optTarget=1, Par='', output_binary="tuned", flto=0, optPass='-O3', output_file='output.txt'):
    # Redirect stdout to a StringIO object
    stdout_capture = io.StringIO()
    sys.stdout = stdout_capture

    # Call the function
    tuner(func=func, dir=dir, compile_args=compile_args, optTarget=optTarget, Par=Par, output_binary=output_binary, flto=flto, optPass=optPass)

    # Get the printed output and write it to the file
    printed_output = stdout_capture.getvalue()
    with open(output_file, 'w') as file:
        file.write(printed_output)

    # Reset stdout
    sys.stdout = sys.__stdout__

if __name__ == "__main__":
    delete_files_with_extension('./', '.txt')
    numPar=255 
    numStop=5
    numIter=70
    numTest=5
    alpha=30
    beta=30
    Par_Val=0
    Par = [numPar, numStop, numIter, numTest, alpha, beta, Par_Val]

    optTarget=5
    output_binary="tuned_"
    flto=0
    optPass='-O3'

    processes = []
    create_or_clear_directory('results')
    dirResult = 'results'
    for root, dirs, files in os.walk('polybench-c-3.2/linear-algebra/kernels/'):
        #delete_files_with_extension('./', '.s')
        func = root.split('/')[-1]

        if func!='':

            try:
                output_file = f"{func}.txt"
                #output_binary + func + '.txt'
                
                compile_args = f"-I ../../polybench-c-3.2/utilities -I ../../polybench-c-3.2/linear-algebra/kernels/{func} ../../polybench-c-3.2/utilities/polybench.c ../../polybench-c-3.2/linear-algebra/kernels/{func}/{func}.c -DPOLYBENCH_TIME"
                if func == 'cholesky':
                    compile_args += ' -lm'
                dir = dirResult+'/'+func
                create_or_clear_directory(dir)
                process = multiprocessing.Process(target=capture_output, args=(func, dir, compile_args, optTarget, Par, output_binary+func, flto, optPass, output_file))
                process.start()
                processes.append(process)
                print(f"Thread {len(processes)} started!")
            except:
                print(f"Unable to optimize {func}")
    
    for process in processes:
        process.join()
    delete_files_with_extension('./', '.s')

