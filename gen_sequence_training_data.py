""" This script creates
"""

from __future__ import print_function
import numpy as np
import argparse
import glob
import os
import errno
import math
import cv2
from random import shuffle
from shutil import copyfile

from helper.helpers import silentremove, processShotFile

parser = argparse.ArgumentParser(
    description="create training/test/validation sets from video list"
)

parser.add_argument("--baseDir", type=str,
                    help="path to folder containing the expected folders (mkv_videos, sbs_videos, sbs_frames)", required=True)
parser.add_argument(
    "--fps", type=int, help="fps of the extracted sequences", default=2)
parser.add_argument(
    "--min_frames", type=int, help="minimum number of frames of sequences (depends on --fps)", default=30)
parser.add_argument(
    "--chapterTiming",
    type=str,
    help="start and end timing list for all chapters",
    default="timingChapters.txt",
)
parser.add_argument("--name", type=str, help="name of the generated dataset", default="training")
parser.add_argument("--blacklist", type=str, help="ignore video", default="-1")
parser.add_argument(
    "--whitelist",
    type=str,
    help="specifies list of selected videos, if not set all videos are selected",
    default="-1",
)


def processChapter_cutlist(
    video,
    chap,
    origFramerate,
    timing,
    outputFileSingle,
    cutList,
    fps,
    minFrames,
    saved_frames,
    saved_sequences
):
    videoName = video.split("/")[-2]

    imgPathRel = videoName + "/chapter" + str(chap) + "/"

    modFrameFactor = int(round(origFramerate / fps))

    minSequenceLength = minFrames * modFrameFactor

    added_frames = 0
    num_sequences_in_chap = 0
    added_sequences = 0

    logFilename = video + "log" + str(chap) + ".txt"
    with open(logFilename, "r") as fp:
        with open(outputFileSingle, "a") as ofp_single:
            prevIdx = -1
            # iterate over log list
            for cnt, line in enumerate(fp):

                idx = line.find("pts_time:")
                if idx == -1:
                    continue

                pts_time = float(line[idx + 9: idx + 9 + 7])
                idx2 = line.find("n:")
                frame_idx = int(line[idx2 + 2: idx2 + 2 + 5]) + 1
                # use floor here to be on the save side
                if pts_time <= timing[0] or pts_time > math.floor(timing[1]):
                    continue
                # ignore if at cut position
                if pts_time in cutList:
                    continue
                # sequence already processed
                if frame_idx < prevIdx:
                    continue

                largerElemCutList = [
                    x for x in cutList if x > pts_time and x < timing[1]
                ]
                largerElemCutList.append(timing[1])
                cutTimeNext = min(largerElemCutList)
                smallerElemCutList = [
                    x for x in cutList if x < pts_time and x > timing[0]
                ]
                smallerElemCutList.append(timing[0])

                seqLength = (cutTimeNext - pts_time) * origFramerate

                # for long sequences jump to some point later in the same sequence
                jump = int(seqLength)
                prevIdx = frame_idx + int(jump)

                # ignore if sequence to short
                if seqLength < minSequenceLength:
                    num_sequences_in_chap += 1
                    continue

                imgFilename = {}

                for ri in range(0, int(seqLength)):
                    frame_str = "out" + str(frame_idx + ri + 1).zfill(8)
                    frame_out_name = "out" + str(saved_frames + added_frames).zfill(8)
                    sequence_name = "seq" + str(saved_sequences + added_sequences).zfill(8)

                    if ri % modFrameFactor != 0:
                        continue

                    ofp_single.write(videoName + "," + str(chap) + "," + imgPathRel + frame_str + "," + sequence_name + "," + frame_out_name + "\n")

                    added_frames += 1

                added_sequences += 1
                num_sequences_in_chap += 1

    return added_frames, added_sequences


def run(args):

    path = os.path.join(args.baseDir, "sbs_frames/image_meta/")
    videoList = glob.glob(path + "*/")
    origFramerate = 24

    trainingSingleFile = os.path.join(path, args.name + f"_{args.fps}fps" + ".csv")

    silentremove(trainingSingleFile)

    saved_frames = 0
    saved_sequences = 0

    for video in videoList:

        videoName = video.split("/")[-2]

        if videoName in args.blacklist:
            print(videoName + " on blacklist")
            continue
        if args.whitelist != "-1" and videoName not in args.whitelist:
            print(videoName + " not on whitelist")
            continue

        print("Processing video: " + videoName)
        print("")

        cutList = processShotFile(video, "shots.txt")
        timingList = []
        with open(video + args.chapterTiming, "r") as fp:
            timingListTmp = fp.read().splitlines()
            for timingLine in timingListTmp:
                timingList.append([float(x) for x in timingLine.split(",")])

        chapterList = glob.glob(video + "log*.txt")
        numChapters = len(chapterList)
        validChapters = range(2, numChapters)
        trainingSet = validChapters

        for chap in trainingSet:
            num_added_frames, num_added_sequences = processChapter_cutlist(
                video,
                chap,
                origFramerate,
                timingList[chap - 1],
                trainingSingleFile,
                cutList,
                args.fps,
                args.min_frames,
                saved_frames,
                saved_sequences
            )

            saved_frames += num_added_frames
            saved_sequences += num_added_sequences


if __name__ == '__main__':

    args = parser.parse_args()

    run(args)
