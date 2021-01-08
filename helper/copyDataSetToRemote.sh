#!/bin/bash

dataSetName=$1
outDir=$2

baseDir="/home/hauke/Master/MasterThesis/data/3dmovies/"
# baseDir="/run/media/hauke/Elements1/"
inDir="${baseDir}${dataSetName}"
outDir="compgpu1:/export/scratch/hluedema/3dmovies/${outDir}"


rsync -a -P ${inDir} ${outDir} 
