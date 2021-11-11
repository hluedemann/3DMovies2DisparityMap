from __future__ import print_function
import shutil
import numpy as np
import argparse
import glob
import os
import math
import cv2
from random import shuffle
from shutil import copyfile
import json

from helper.helpers import processShotFile, createDir, truncate


def get_chapter_scene_times(sceneCutList, chapterTimingList, validChapters):
    chapterSceneTimes = {}
    for chap in validChapters:
        chapBegin = chapterTimingList[chap-1][0]
        chapEnd = chapterTimingList[chap-1][1]
        sceneCuts = []
        for cut in sceneCutList:
            # get all the scenes belonging to the chapter
            if cut >= chapBegin and cut < chapEnd:
                sceneCuts.append(cut)

        sceneNumber = 1
        chapterSceneTimes["chapter{}".format(chap)] = []
        i = 0
        while i < len(sceneCuts)-1:
            sceneBegin = sceneCuts[i]
            sceneEnd = sceneCuts[i+1]

            if i != len(sceneCuts)-2:
                nextScene = sceneCuts[i+2]
            else:
                nextScene = sceneEnd

            isShortScene = nextScene - sceneEnd < 0.5 or sceneEnd - sceneBegin < 0.5
            if isShortScene:
                sceneEnd = nextScene

            chapterSceneTimes["chapter{}".format(
                chap)].append([sceneBegin, sceneEnd])

            sceneNumber += 1
            if isShortScene:
                i += 2
            else:
                i += 1

    return chapterSceneTimes


def get_chapter_scene_frames(video, validChapters, chapterSceneTimes):
    chapterSceneFrames = {}

    for chap in validChapters:
        sceneFrames = {}

        videoNameSplit = video.split("/")
        videoName = videoNameSplit[-2]

        imgPathRel = videoName + "/chapter" + str(chap) + "/"
        scenes = chapterSceneTimes["chapter{}".format(chap)]

        logFilename = video + "log" + str(chap) + ".txt"
        with open(logFilename, "r") as fp:
            currentScene = 0
            currentSceneFrames = []

            for line in fp:
                idx = line.find("pts_time:")
                if idx == -1:
                    continue

                pts_time = float(line[idx + 9: idx + 9 + 7])
                idx2 = line.find("n:")
                frame_idx = int(line[idx2 + 2: idx2 + 2 + 5]) + 1

                imagePath = os.path.join("sbs_frames/image_left",
                                         imgPathRel,
                                         "out{}.jpg".format(str(frame_idx).zfill(8)))

                # Check if frame time is inside current scene. Use truncate to account
                # for different precision
                if truncate(scenes[currentScene][0], 2) <= pts_time < truncate(scenes[currentScene][1], 2):
                    currentSceneFrames.append(imagePath)
                else:
                    sceneFrames["scene{}".format(currentScene)] = currentSceneFrames
                    currentSceneFrames = []
                    currentSceneFrames.append(imagePath)
                    currentScene += 1
                    if currentScene == len(scenes):
                        break
                    
        chapterSceneFrames["chapter{}".format(chap)] = sceneFrames

    return chapterSceneFrames


def create_scene_folder_structure(videoName, chapterSceneFrames):
    for chapter, sceneFrames in chapterSceneFrames.items():
        inPath = os.path.join(
            args.baseDir, "sbs_frames/image_left/", videoName, chapter)
        outPath = os.path.join(
            args.baseDir, "test_dataset", videoName, chapter)

        for scene, frames in sceneFrames.items():
            out = os.path.join(outPath, scene)
            createDir(out)

            for frame in frames:
                inImage = os.path.join(
                    inPath, "out{}.jpg".format(str(frame).zfill(8)))
                outImage = os.path.join(
                    out, "out{}.jpg".format(str(frame).zfill(8)))
                shutil.copy(inImage, outImage)


def run(args):
    path = os.path.join(args.baseDir, "sbs_frames/image_meta/")
    videoList = glob.glob(path + "*/")

    for video in videoList:
        videoNameSplit = video.split("/")
        videoName = videoNameSplit[-2]
        if videoName in args.blacklist:
            print(videoName + " on blacklist")
            continue
        if args.whitelist != "-1" and videoName not in args.whitelist:
            print(videoName + " not on whitelist")
            continue
        print("processing " + videoName)
        print("")

        chapterTimingList = []
        with open(video + args.chapterTiming, "r") as fp:
            timingListTmp = fp.read().splitlines()
            for timingLine in timingListTmp:
                chapterTimingList.append(
                    [truncate(float(x), 2) for x in timingLine.split(",")])

        chapterList = glob.glob(video + "log*.txt")
        numChapters = len(chapterList)
        validChapters = range(2, numChapters-1)

        # extract the individual scenes
        sceneCutList = processShotFile(video, "shots.txt")

        # get the individual scenes of belonging to each chapter
        chapterScenesTimes = get_chapter_scene_times(sceneCutList,
                                                     chapterTimingList,
                                                     validChapters)
        # get the frames belonging the each scene
        chapterSceneFrames = get_chapter_scene_frames(video,
                                                      validChapters,
                                                      chapterScenesTimes)

        outFile = os.path.join(args.baseDir,
                               "sbs_frames/image_meta/",
                               videoName, "sceneFramesRaw.json")

        with open(outFile, "w+") as fp:
            json.dump(chapterSceneFrames, fp, indent=True)

        #create_scene_folder_structure(videoName, chapterSceneFrames)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="create training/test/validation sets from video list"
    )

    parser.add_argument("--baseDir", type=str,
                        help="path to folder containing the expected folders (mkv_videos, sbs_videos, sbs_frames)", required=True)
    parser.add_argument(
        "--chapterTiming",
        type=str,
        help="start and end timing list for all chapters",
        default="timingChapters.txt",
    )
    parser.add_argument("--name", type=str,
                        help="run name", default="training")
    parser.add_argument("--blacklist", type=str,
                        help="ignore video", default="-1")
    parser.add_argument(
        "--whitelist",
        type=str,
        help="specifies list of selected videos, if not set all videos are selected",
        default="-1",
    )

    args = parser.parse_args()

    run(args)
