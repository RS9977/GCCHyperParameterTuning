from utils import *
from compiler_func import *
from benchmarks import *

import multiprocessing

import threading
import io
import sys

def tuner(func='', dir='./', args='', compile_args='', optTarget=1, Par=[], output_binary = "tuned", flto=0, optPass='-O3'):
    change_directory(dir)
    print('#####################################################################################################')
    print(f"Optimizig: {func}")
    if len(Par)!=7:
        Par = [260, 3, 50, 5, 30, 50, 0]
    numPar=Par[0]
    numStop=Par[1]
    numIter=Par[2]
    numTest=Par[3]
    alpha=Par[4]
    beta=Par[5]
    Par_Val=Par[6]
    print(f"Result calculated for:\nalpha: {alpha},\tbeta: {beta},\tnumIter:{numIter},\tnumPar: {numPar},\tnumTest: {numTest},\tflto: {flto},\toptTarget: {optTarget},\toptPass: {optPass}")
    print("---------------------------------------------\n")
    
    try:                
        try:
            if Par_Val:
                [gcc_params_min,selected_indices_min, cycles_pre] = load_dictionary_from_file('Par_Val')
            else:
                selected_indices_min   = []
                gcc_params_min         = {}
                cycles_pre             = []
        except:
            selected_indices_min   = []
            gcc_params_min         = {}
            cycles_pre             = []
        output_binary_temp = output_binary
        output_binary = 'un'+output_binary
        compile_with_gcc(compile_args= compile_args, gcc_params=gcc_params_min, selected_indices=selected_indices_min, opt=optPass, i=-1, optTarget=optTarget, output_binary=output_binary, flto=flto)    
        GCUPS_max_main = get_gcups_from_command(f"./{output_binary} {args}", numTest*5)
        GCUPS_max = get_gcups_from_command(f"./{output_binary} {args}", numTest*10)
        GCUPS_max_main = get_gcups_from_command(f"./{output_binary} {args}", numTest*10)
        if not flto:
            cycles_min = get_asm_info('./')
            instruction_count, total_instructions_min = count_instructions_in_directory('./')
            cycles_min.append(total_instructions_min)     
        else:
            cycles = []
            preBinary, eq = are_files_equal(cycles, output_binary)      
        try:
            Size_min   = get_size_info(output_binary)
        except:
            print("Change the date and user in get_size_info")
            Size_min = 0
        
        output_binary = output_binary_temp
        print('Without Tuning:')
        print(f"Initial GCUPS : {GCUPS_max:.4f}")
        print(f"Initial GCUPS main: {GCUPS_max_main:.4f}")
        if not flto:
            print(f"Initial total Instructions: {total_instructions_min}")
            print(f"Initial cycles: {cycles_min}")
        print(f"Initial binary size: {Size_min}")
        print("---------------------------------------------\n")
        print("Tuning...")
        if not flto:
            cycles_min.append(total_instructions_min)
            if len(cycles_pre)==0:
                cycles_pre = [cycles_min]
            total_instructions_pre = total_instructions_min
        else:
            cycles_min = []
            total_instructions_pre = []
            binaries = [preBinary]

        same_cnt = 0
        #GCUPS_max = 0
        #gcc_command = ["gcc", "-Ofast", "-mavx2", "-D", "SUBMAT", "-D", "L8", "-lpthread", "SWAVX_utils.c", "SWAVX_SubMat.c", "SWAVX_TOP.c", "SWAVX_256_Func_SeqToSeq_SubMat.c", "-o", "SWAVX"]
        #subprocess.check_call(gcc_command)
        #GCUPS_max = get_gcups_from_command('./SWAVX',numTest)
        
        j = -1
        while same_cnt < numStop*numIter:
            j += 1
            if not flto:
                print(f"(j: {j}), Explored space: {len(cycles_pre)}, Repetitions: {same_cnt}", end="\r")
            else:
                print(f"(j: {j}), Explored space: {len(binaries)}, Repetitions: {same_cnt}", end="\r")
            if same_cnt < numIter:
                selected_indices_min   = []
                gcc_params_min         = {}
            for i in range(numIter):
                '''
                if j==numOutIter-1:
                    optTarget = 1
                '''
                # Run `gcc --help=params` and capture the output
                output = subprocess.check_output(["gcc", "--help=params"], stderr=subprocess.STDOUT, universal_newlines=True)
                # Parse the output to extract parameter names and descriptions
                
                gcc_params = parse_gcc_params(output, gcc_params_min, i, numIter, alpha=alpha, beta=beta)


                #for i in range(100):
                pool = multiprocessing.Pool(processes=1)
                selected_indices = random.sample(range(0, 270), numPar)
                selected_indices.sort()
                # Use apply_async to run the function in a separate process
                compile_with_gcc(gcc_params, selected_indices, optPass, i, optTarget, output_binary, flto, compile_args)
                result_value = True
                

                if result_value:
                    if optTarget == 1:
                        if not flto:
                            cycles = get_asm_info('./')
                            instruction_count, total_instructions = count_instructions_in_directory('./')
                            cycles.append(total_instructions)
                        else:
                            preBinary, eq = are_files_equal(binaries, output_binary)
                        same_cnt += 1
                        if ((not are_lists_identical(cycles,cycles_pre)) and not flto) or (flto and not eq):
                            same_cnt = 0
                            if not flto:
                                cycles_pre.append(cycles)
                            else:
                                binaries.append(preBinary)     
                            gcups = get_gcups_from_command(f"./{output_binary}  {args}", numTest)
                            if (GCUPS_max-gcups)/GCUPS_max>0.005:
                                gcups_main = get_gcups_from_command(f"./{output_binary}  {args}", numTest*10)
                                if  gcups_main < GCUPS_max_main:
                                    #gcups = get_gcups_from_command(f"./{output_binary} 'test2.fasta' 'test3.fasta' 1", numTest*10)
                                    #if gcups > GCUPS_max:
                                        if not flto:
                                            print(f"(j: {j}, i: {i}),   {cycles} :=>\t({GCUPS_max:.4f} -> {gcups:.4f}),\t({GCUPS_max_main:.4f} -> {gcups_main:.4f})")
                                        else:
                                            print(f"(j: {j}, i: {i}) :=>\t({GCUPS_max:.4f} -> {gcups:.4f}),\t({GCUPS_max_main:.4f} -> {gcups_main:.4f})")
                                        GCUPS_max = gcups
                                        GCUPS_max_main = gcups_main
                                        gcc_params_min = gcc_params
                                        selected_indices_min = selected_indices
                                        save_dictionary_to_file([gcc_params_min,selected_indices_min, cycles_pre],'Par_Val_temp')
                          
                    elif optTarget == 2: 
                        if flto:
                            print("flto should be 0")
                            break                       
                        instruction_count, total_instructions = count_instructions_in_directory('./')
                        if total_instructions < total_instructions_min:
                            print(i,'of',j, ':= ', total_instructions_min, '->',total_instructions)
                            total_instructions_min = total_instructions
                            gcc_params_min = gcc_params
                            selected_indices_min = selected_indices
                            save_dictionary_to_file([gcc_params_min,selected_indices_min, cycles_pre],'Par_Val_temp')

                    elif optTarget == 3:  
                        same_cnt += 1
                        if not flto:
                            cycles = get_asm_info('./')
                            instruction_count, total_instructions = count_instructions_in_directory('./')
                            cycles.append(total_instructions)
                        else:
                            preBinary, eq = are_files_equal(binaries, output_binary)   
                        if ((not are_lists_identical(cycles,cycles_pre)) and not flto) or (flto and not eq):
                            same_cnt = 0
                            if not flto:
                                cycles_pre.append(cycles)
                            else:
                                binaries.append(preBinary) 
                            size = get_size_info(output_binary)
                            if size < Size_min:
                                same_cnt = 0
                                print('******************', i,'of',j, ':= ', Size_min, '->',size, '******************')
                                Size_min = size
                                gcc_params_min = gcc_params
                                selected_indices_min = selected_indices
                                save_dictionary_to_file([gcc_params_min,selected_indices_min, cycles_pre],'Par_Val_temp')

                    elif optTarget == 4:
                        same_cnt += 1
                        if not flto:
                            cycles = get_asm_info('./')
                            instruction_count, total_instructions = count_instructions_in_directory('./')
                            cycles.append(total_instructions)
                        else:
                            preBinary, eq = are_files_equal(binaries, output_binary)   
                        if ((not are_lists_identical(cycles,cycles_pre)) and not flto) or (flto and not eq):
                            same_cnt = 0
                            if not flto:
                                cycles_pre.append(cycles)
                            else:
                                binaries.append(preBinary) 
                            size = get_size_info(output_binary)
                            if size < Size_min:    
                                gcups = get_gcups_from_command(f"./{output_binary} {args}", numTest)
                                if (GCUPS_max-gcups)/GCUPS_max>0.005:
                                    gcups_main = get_gcups_from_command(f"./{output_binary} {args}", numTest*10)
                                    if  gcups_main < GCUPS_max_main:
                                        #gcups = get_gcups_from_command(f"./{output_binary} {args}", numTest*10)
                                        #if gcups > GCUPS_max:
                                        if not flto:
                                            print(f"(j: {j}, i: {i}),   {cycles} :=>\t({Size_min} -> {size})\t({GCUPS_max:.4f} -> {gcups:.4f}),\t({GCUPS_max_main:.4f} -> {gcups_main:.4f})")
                                        else:
                                            print(f"(j: {j}, i: {i}) :=>\t({Size_min} -> {size})\t({GCUPS_max:.4f} -> {gcups:.4f}),\t({GCUPS_max_main:.4f} -> {gcups_main:.4f})")
                                        GCUPS_max = gcups
                                        GCUPS_max_main = gcups_main
                                        gcc_params_min = gcc_params
                                        selected_indices_min = selected_indices
                                        save_dictionary_to_file([gcc_params_min,selected_indices_min, cycles_pre],'Par_Val_temp')


                    else:
                        if flto:
                            print("flto should be 0")
                            break
                        cycles = get_asm_info('./')
                        if sum(cycles[:2]) < sum(cycles_min[:2]):
                            print(f"(j: {j}, i: {i}) :=>\t({cycles_min} -> {cycles})")
                            cycles_min = cycles
                            gcc_params_min = gcc_params
                            selected_indices_min = selected_indices
                            save_dictionary_to_file([gcc_params_min,selected_indices_min, cycles_pre],'Par_Val_temp')
        print("---------------------------------------------\n")
        print('With Tuning:')
        compile_with_gcc(gcc_params_min, selected_indices_min, optPass, -1, optTarget, output_binary=output_binary, flto=flto, compile_args=compile_args)    
        GCUPS_max = get_gcups_from_command(f"./{output_binary} {args}", numTest*10)
        GCUPS_max_main = get_gcups_from_command(f"./{output_binary} {args}", numTest*10)
        if not flto:
            cycles_min = get_asm_info('./')
            instruction_count, total_instructions_min = count_instructions_in_directory('./')
            cycles_min.append(total_instructions_min)
        try:
            Size_min   = get_size_info(output_binary)
        except:
            Size_min = 0
        print(f"Final GCUPS : {GCUPS_max:.4f}")
        print(f"Final GCUPS main: {GCUPS_max_main:.4f}")
        if not flto:
            print(f"Final total Instructions: {total_instructions_min}")
            print(f"Final cycles: {cycles_min}")
        print(f"Final binary size: {Size_min}")
        if not flto:
            print("Size of the solution space: ", len(cycles_pre))
        else:
            print("Size of the solution space: ", len(binaries))
        save_dictionary_to_file([gcc_params_min,selected_indices_min, cycles_pre],'Par_Val')
    except subprocess.CalledProcessError as e:
        print("Error running 'gcc --help=params':")
        print(e.output)