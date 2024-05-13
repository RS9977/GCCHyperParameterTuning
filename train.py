from utils import *
from compiler_func import *
from benchmarks import *
from tuner import tuner

if __name__ == "__main__":
    numPar=255 
    numStop=20
    numIter=20
    numTest=5
    alpha=30
    beta=30
    Par_Val=0
    Par = [numPar, numStop, numIter, numTest, alpha, beta, Par_Val]

    optTarget=1
    flto=0
    optPass='-O3'

    create_or_clear_directory('results')
    dirResult = 'results'
    for root, dirs, files in os.walk('polybench-c-3.2/datamining/'):
        func = root.split('/')[-1]
        if func!='':
            try:
                dir = dirResult+'/'+func
                create_or_clear_directory(dir)
                compile_args = f"-I ../../polybench-c-3.2/utilities -I ../../polybench-c-3.2/datamining/{func} ../../polybench-c-3.2/utilities/polybench.c ../../polybench-c-3.2/datamining/{func}/{func}.c -DPOLYBENCH_TIME"
                if func == 'correlation':
                    compile_args += ' -lm'
                tuner(func=func, compile_args=compile_args, dir=dir, optTarget=optTarget, Par=Par, output_binary="tuned_"+func, flto=flto, optPass=optPass)
                change_directory('../../')
            except:
                print(f"Unable to optimize {func}")

    for root, dirs, files in os.walk('polybench-c-3.2/medley/'):
        func = root.split('/')[-1]
        if func!='':
            try:
                dir = dirResult+'/'+func
                create_or_clear_directory(dir)
                compile_args = f"-I ../../polybench-c-3.2/utilities -I ../../polybench-c-3.2/medley/{func} ../../polybench-c-3.2/utilities/polybench.c ../../polybench-c-3.2/medley/{func}/{func}.c -DPOLYBENCH_TIME"
                
                tuner(func=func, compile_args=compile_args, dir=dir, optTarget=optTarget, Par=Par, output_binary="tuned_"+func, flto=flto, optPass=optPass)
                change_directory('../../')
            except:
                print(f"Unable to optimize {func}")

    for root, dirs, files in os.walk('polybench-c-3.2/stencils/'):
        func = root.split('/')[-1]
        if func!='':
            try:
                dir = dirResult+'/'+func
                create_or_clear_directory(dir)
                compile_args = f"-I ../../polybench-c-3.2/utilities -I ../../polybench-c-3.2/stencils/{func} ../../polybench-c-3.2/utilities/polybench.c ../../polybench-c-3.2/stencils/{func}/{func}.c -DPOLYBENCH_TIME"
                tuner(func=func, compile_args=compile_args, dir=dir, optTarget=optTarget, Par=Par, output_binary="tuned_"+func, flto=flto, optPass=optPass)
                change_directory('../../')
            except:
                print(f"Unable to optimize {func}")
                
    for root, dirs, files in os.walk('polybench-c-3.2/linear-algebra/solvers/'):
        func = root.split('/')[-1]
        if func!='':
            try:
                dir = dirResult+'/'+func
                create_or_clear_directory(dir)
                compile_args = f"-I ../../polybench-c-3.2/utilities -I ../../polybench-c-3.2/linear-algebra/solvers/{func} ../../polybench-c-3.2/utilities/polybench.c ../../polybench-c-3.2/linear-algebra/solvers/{func}/{func}.c -DPOLYBENCH_TIME"
                if func == 'gramschmidt':
                    compile_args += ' -lm'
                tuner(func=func, compile_args=compile_args, dir=dir, optTarget=optTarget, Par=Par, output_binary="tuned_"+func, flto=flto, optPass=optPass)
                change_directory('../../')
            except:
                print(f"Unable to optimize {func}")

    for root, dirs, files in os.walk('polybench-c-3.2/linear-algebra/kernels/'):
        func = root.split('/')[-1]
        if func!='':
            try:
                dir = dirResult+'/'+func
                create_or_clear_directory(dir)
                compile_args = f"-I ../../polybench-c-3.2/utilities -I ../../polybench-c-3.2/linear-algebra/kernels/{func} ../../polybench-c-3.2/utilities/polybench.c ../../polybench-c-3.2/linear-algebra/kernels/{func}/{func}.c -DPOLYBENCH_TIME"
                if func == 'cholesky':
                    compile_args += ' -lm'
                tuner(func=func, compile_args=compile_args, dir=dir, optTarget=optTarget, Par=Par, output_binary="tuned_"+func, flto=flto, optPass=optPass)
                change_directory('../../')
            except:
                print(f"Unable to optimize {func}")
    
