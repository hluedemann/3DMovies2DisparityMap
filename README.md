# 3D Movies to Disparity Maps

This repository provides scripts that allow to extract stereo data from 3D movies and convert them into disparity/depth maps.

The scripts are based on the code provided in the repository [https://github.com/lasinger/3DVideos2Stereo](https://github.com/lasinger/3DVideos2Stereo). This repo implements the extraction of stereo data as described in the [paper](https://arxiv.org/abs/1907.01341):

>Towards Robust Monocular Depth Estimation: Mixing Datasets for Zero-shot Cross-dataset Transfer  
René Ranftl, Katrin Lasinger, David Hafner, Konrad Schindler, Vladlen Koltun

To check out the code of the paper go to: [https://github.com/intel-isl/MiDaS](https://github.com/intel-isl/MiDaS)

## Overview

The extraction of disparity maps form 3D movies will be done in multiple steps. For every of these steps there are one or more scripts available. The following steps will be explained below

[1. Extract 3D movies from blu ray](#Extract-3D-Movies-from-blu-ray)   
[2. Convert to SBS format](#Convert-to-SBS-format)  
[3. Extract left and right frames](#Extract-left-and-right-frames)   
[4. Data Set Creation](#Data-Set-Creation)  
[5. Compute Sky Segmentation](#Compute-sky-segmentation)  
[6. Compute Optical Flow](#Compute-Optical-Flow)  
[7. Disparity and Unvertainty Computation](#Disparity-and-Uncertainty-Computation)    

## Assumed Folder Structure
All the provided scripts assume the folder structure to be as follows: 

```
${base_dir}
|
|---mvc_videos
|   |
|   |-- all videos in the MVC format
|
|---sbs_frames
|   |
|   |-- all the extracted frames
|
|---sbs_videos
|   |
|   |-- all the videos in SBS format
```
If a different folder structure is desired the paths in the scripts need to adjusted accordingly.

## Extract 3D Movies from blu ray

There are multiple formats to store 3D movies. Here it is assumed that the videos are given in the MVC format with a resolution 1080p, stored as MKVs.  

In order to extract the videos from the blu ray meeting these requirements [makemkv](https://www.makemkv.com/) can be used.  

On an arch based system this can be installed with:
```
sudo pacman -Syu makemkv
```
When using `makemkv` it is important to include the stream containing the 3D data which is not included by default (check the video stream `Mpeg4 MVC`).  

Note:
* Run makemkv with sudo
* If the optical drive is not found try `sudo modprobe sg`
* If the movie is already in SBS format this and the next step are not required

## Convert to SBS format
The next step is to convert the videos to the SBS (side by side) format. The resulting resolution should then be 3840x1080px (2x 1920x1080).  

For this the script `convertToSBS.sh` is provided

Requirements:  
[ffmpeg](https://www.ffmpeg.org/):  
* Install with: ``` sudo pacman -Syu ffmpeg```  

[mkvtoolnix](https://mkvtoolnix.download/):  
* Install with: ```sudo pacman -Syu mkvtoolnix-cli```  

[FRIMDecode](https://forum.doom9.org/showthread.php?t=169651):
* This only works on Windows but can be run on linux using [wine](https://www.winehq.org/).
* Install wine with: ```sudo pacman -S wine winetricks wine-mono wine_gecko```


Now run the script as follows:

```
./convertToSBS /path/to/base_dir nameOfMVCVideo /path/to/FRIMDecode32
```
The resulting SBS video will be saved in th folder `${base_dir}/sbs_videos/${video_name}_SBS/${video_name}_SBS.mkv`  
The script will also save chapter information to the same location. This is required for later steps. 

Note:  
The mvc video needs to located in the folder `mvc_videos` located in the base dir (see [folder structure](#Assumed-Folder-Structure)). The name of the video needs to be given without the `.mkv` extension.

## Extract left and right frames

The next step is to extract the left and right frames from the SBS video.  

For this the script `run_extractFrames.sh` can be used.

```
./run_stractFrames.sh /path/to/base_dir nameOfSBSVideo
```

This script will create the following folders inside sbs_frames: `image_left`, `image_right`, `image_meta`, `image_raw`  

In order to remove black bars at the sides of the frames the extracted frames are centrally cropped to the resolution 1880x800.

Note:  
Ths SBS video needs to be located in the folder sbs_videos inside the base dir (or the paths inside the script need to be adjusted).

## Data Set Creation

The next step is to create a data set from all the extracted frames. This is done in order to remove undesired frames (frames from first and last chapter, frames at cuts). Also multiple frames are part of the same scene and are therefore highly correlated. Hence the complete set of frames is subsampled.  

This process is explained in the [paper](https://arxiv.org/abs/1907.01341).

To generate the training data set as discribed in this paper run.

```python
python genTraining_recurr.py --base_dir /path/to/base_dir --numRecurrent 24 --fpsRecurrent 24 --fpsSingle 4 --name training_set --blacklist testVid1,testVid2,valVid1,valVid2
```

For the validation set run:
```python
python genTraining_recurr.py --baseDir /path/to/base_dir --numRecurrent 24 --fpsRecurrent 24 --fpsSingle 1 --name validation_set --whitelist valVid1,valVid2
```

This will create a file inside `${base_dir}/sbs_frames/image_meta` containing the paths to all the images in the created training/validation set.  

In order to copy all these files to a separate folder (required for the subsequent steps) the script `helper/createDataSet.py` can be used:  

```python
python helper/createDataSet.py --baseDir /path/to/bas_dir --name nameDataSetListFile --outDir /path/to/out_dir
```
In process the log file `image_mapping_log.txt` will be created in the folder `meta/` specifying the mapping of each frame to it's new name.

Note:  
The option `--name` requires only the name of the `.txt` file containing the paths to the images. The script will automatcally look inside the folder `sbs_frames/image_meta/nameDataSetListFile` for the name.

## Compute Sky Segmentation  
In order to set the depth of the sky manually a sky segmentation of the images is required.  

In this repo a fork of Mapillary's Inplace ABN (https://github.com/mapillary/inplace_abn) algorithm is included. This repo provides scripts to compute the sky segmentation as rquired for the next steps.  

First download the [pretrained model](https://drive.google.com/file/d/1SJJx5-LFG3J3M99TrPMU-z6ZmgWynxo-/view).

Then run:
```
python skySegmentation/inplace_abn/scripts/test_vistas.py /path/to/model /path/to/in_dir /path/to/out_dir
```  

The script will compute the sky segmentation for all the images inside `in_dir`. With the folder structure form above the input and output needs to be set as follows:  
* in_dir:  `/path/to/data_set/image_left`
* out_dir: `/path/to/data_set/sky_segmentation`

Note:  
The sript will automatically run the segmentation on all available GPUs. To restric the number of GPUs run:
```
export CUDA_VISIBLE_DEVICES=1,2
```
or 
```
CUDA_VISIBLE_DEVICES=1,2 python skySegmentation/inplace_abn/scripts/test_vistas.py /path/to/model /path/to/in_dir /path/to/out_dir
```

This will run the code only on the GPUs with the id's 1 and 2.
## Compute Optical Flow


The next step is to compute the forward and backward optical flow between the left and right frames.  

For this a fork of the [repe](https://github.com/princeton-vl/RAFT) is included as a submodule. The code implements the new optical flow algorithm presented in the  [RAFT: Recurrent All Pairs Field Transforms for Optical Flow](https://arxiv.org/pdf/2003.12039.pdf) paper.  

First download pretrained models with:
```
python opticalFlow/RAFT/download_models.sh
```

Then run the optical flow computation with:
```
python opticalFlow/RAFT/getForwardBackwardFlow.py --mdoel /path/to/model --path /path/to/data_set 
```

This will create the folders `flow_forward` and `flow_backward` inside the folder of the date set.  

Note:  
* The pretrained model will be downloaded into `opticalFlow/RAFT/models/raft-things.pth`
* The data set folder specified needs to contain the folders `image_left` and `image_right` as created with the script `helper/createDataSet.py`.


## Disparity and Uncertainty Computation

The last step is to compute the disparity and uncertainty maps using the forward, backward flow and the sky segmentation.  

For this run:

```python
python get_disp_and_uncertainty.py /path/to/data_set
```

This script generates disparity and corresponding uncertainty maps and outputs them into the folders `disparity/` and `uncertainty/`.
These maps are saved with half the resolution (940x400).  

When explicit filtering of the disparity maps is desired use the option `--filter` (see the script for parameters that can be specified for the filtering).  
If filtering is activated the log file `disp_filter_log.txt` is created in the `meta/` folder storing information about frames that were rejected due to filtering. 

## Data Reading

The generated disparity and uncertainty maps can be read as follows.

### Read Disparity

```python
disp = imageio.imread("disp.png")

offset = float(disp.meta["offset"])
scale = float(disp.meta["scale"])

disp = (offset + scale * disp).astype(np.float32)
```

### Read Uncertainty

```python
uncertainty = imageio.imread("uncertainty.png")
uncertainty = 0.1 * uncertainty
```

## Citation

As mentioned above this code is based on a repository which was created in conjunction with a paper. Please cite this paper if you use this code in research.
```
@article{Ranftl2019,
	author    = {Ren\'{e} Ranftl and Katrin Lasinger and David Hafner and Konrad Schindler and Vladlen Koltun},
	title     = {Towards Robust Monocular Depth Estimation: Mixing Datasets for Zero-shot Cross-dataset Transfer},
	journal   = {arXiv:1907.01341},
	year      = {2019},
}
```
## License 

MIT License 
