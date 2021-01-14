import os
import argparse
from tqdm import tqdm
import shutil

parser = argparse.ArgumentParser(
    description="rename and copy all the images from one data set list to one folder"
)
parser.add_argument("--baseDir", type=str, required=True,
                    help="path to folder containing expected folders (mkv_videos, sbs_videos, sbs_frames)")
parser.add_argument("--name", type=str, required=True,
                    help="name of the txt file containing the names of the images belonging to the data set")
parser.add_argument("--outDir", type=str, required=True,
                    help="name of the output folder")


args = parser.parse_args()


def createDir(path):
    try:
        os.makedirs(path, exist_ok=True)
    except OSError:
        print(f"Failed to create dir: {path}")
    else:
        print(f"Created dir: {path}")


def main():

    # Create required folders
    createDir(os.path.join(args.outDir, "image_left"))
    createDir(os.path.join(args.outDir, "image_right"))
    createDir(os.path.join(args.outDir, "meta"))

    dataFile = os.path.join(args.baseDir, "sbs_frames",
                            "image_meta", args.name + ".txt")
    logFile = os.path.join(args.outDir, "meta", "image_mapping_log.txt")

    # Just count the number of lines in order to see how many images need to copied
    counter = 0
    with open(dataFile, "r") as f:

        for _ in f:
            counter += 1
    print(f"Copying dataset of size: {counter}")

    with open(dataFile, "r") as f, open(logFile, "w+") as l:

        for i, line in tqdm(enumerate(f)):
            line = line.rstrip()
            if not line:
                continue

            inPathLeft = os.path.join(
                args.baseDir, "sbs_frames", "image_left", line + ".jpg")
            inPathRight = os.path.join(
                args.baseDir, "sbs_frames", "image_right", line + ".jpg")
            outName = "out" + str(i).zfill(8)
            outPathLeft = os.path.join(
                args.outDir, "image_left", outName + ".jpg")
            outPathRight = os.path.join(
                args.outDir, "image_right", outName + ".jpg")

            shutil.copy(inPathLeft, outPathLeft)
            shutil.copy(inPathRight, outPathRight)

            # wirte to log file the mapping of the old image name to the new name
            l.write(line + " " + outName + "\n")


main()
