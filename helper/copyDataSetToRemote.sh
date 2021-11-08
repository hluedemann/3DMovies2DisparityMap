#!/bin/bash

dataSetName=$1

baseDir="/home/hauke/Master/MasterThesis/data/3dmovies/"
# baseDir="/run/media/hauke/Elements1/"
inDir="${baseDir}${dataSetName}"
out="compgpu2:/export/scratch/hluedema/3dmovies/"


rsync -r -t -h --info=progress2 ${inDir} ${out}
