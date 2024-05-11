#!/bin/bash -l

#$ -l h_rt=06:00:00 
#$ -N GCC_PARAM 
#$ -P caad
#$ -pe omp 8

module load gcc/11

module load llvm/16.0.6

module load python3

python3 train.py

