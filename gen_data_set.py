import argparse
import glob
import os
import shutil
import json

from helper.helpers import createDir


def create_scene_folder_structure(baseDir, videoName, chapterSceneFrames):
    for chapter, sceneFrames in chapterSceneFrames.items():
        inPath = baseDir
        outPath = os.path.join(
            baseDir, "test_dataset_filtered", videoName, chapter)

        for scene, frames in sceneFrames.items():
            out = os.path.join(outPath, scene)
            createDir(out)

            for frame in frames:
                inImage = os.path.join(
                    inPath, frame)

                split = frame.split("/")[-1].split(".")[0][3:]
                outImage = os.path.join(
                    out, "out{}.jpg".format(str(split)))
                shutil.copy(inImage, outImage)


def run(args):

    oriFrameRate = 24
    path = os.path.join(args.baseDir, "sbs_frames/image_meta/")
    videoList = glob.glob(path + "*/")

    trainSetTXTName = os.path.join(path,
                                   args.name +
                                   "_sampleFPS_{}".format(
                                       args.sampleFPS) + ".txt"
                                   )
    trainSetJsonName = os.path.join(path,
                                    args.name +
                                    "_sampleFPS_{}".format(
                                        args.sampleFPS) + ".json"
                                    )

    frameSampleFactor = int(round(oriFrameRate / args.sampleFPS))
    
    # dictionary containing all videos with all filtered
    # frames sorted with respect to their chapter and scene
    trainSetDict = {}   

    with open(trainSetTXTName, "w+") as logFile:
        # iterate over all the videos
        for video in videoList:
            videoNameSplit = video.split("/")
            videoName = videoNameSplit[-2]
            if videoName in args.blacklist:
                print(videoName + " on blacklist")
                continue
            print("processing " + videoName)
            print("")

            # open json file containing the grouping of each frame to their scene
            pathChapterSceneFramesRaw = os.path.join(
                video, "sceneFramesRaw.json")
            chapterSceneFramesFiltered = {}
            with open(pathChapterSceneFramesRaw, "r") as fp:
                chapterSceneFrames = json.load(fp)

            for chap, sequenceDict in chapterSceneFrames.items():
                temp = {}
                for sequence, frames in sequenceDict.items():
                    frames = frames[1:-1] # remove first and last frame to remove frames at scene cuts
                    numFrames = len(frames)

                    # ignore scenes that are to short (shorter then .5s)
                    if numFrames <= oriFrameRate / 2:
                        continue

                    filteredFrames = []
                    for i, frame in enumerate(frames):
                        if i % frameSampleFactor == 0:
                            filteredFrames.append(frame)

                    numFramesFiltered = len(filteredFrames)
                    short = False if numFramesFiltered >= 10 else True
                    if not short:
                        sectionLength = int(
                            numFramesFiltered * args.sceneCoverage / 3.0)
                        front = filteredFrames[0:sectionLength]
                        middle = filteredFrames[2*sectionLength:3*sectionLength]
                        back = filteredFrames[-sectionLength:]
                        temp[sequence] = front + middle + back

                        for f in temp[sequence]:
                            logFile.write(f + "\n")
                    else:
                        if numFramesFiltered <= 3:
                            temp[sequence] = filteredFrames
                        elif 4 <= numFramesFiltered <= 5:
                            temp[sequence] = [
                                filteredFrames[0], filteredFrames[-1]]
                        else:
                            temp[sequence] = filteredFrames[0:2] + \
                                filteredFrames[-2:]

                        for f in temp[sequence]:
                            logFile.write(f + "\n")

                chapterSceneFramesFiltered[chap] = temp

            trainSetDict[videoName] = chapterSceneFramesFiltered

            with open(trainSetJsonName, "w+") as fp:
                json.dump(trainSetDict, fp, indent=True)

            #create_scene_folder_structure(args.baseDir, videoName, chapterSceneFramesFiltered)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="create training/test/validation sets from video list"
    )

    parser.add_argument("--baseDir", type=str,
                        help="path to folder containing the expected folders (mkv_videos, sbs_videos, sbs_frames)", required=True)
    parser.add_argument(
        "--sampleFPS", type=int, help="fps to use to subsample from full fps of original stream",
        default=4
    )
    parser.add_argument("--sceneCoverage",
                        type=float,
                        help="percentage of the scene to cover. the frames will be choosen from the front, middle and back",
                        default=0.6)
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
