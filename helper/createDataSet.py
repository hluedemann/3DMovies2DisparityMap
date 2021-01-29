import os
import argparse
from tqdm import tqdm
import shutil
import pandas as pd

from helpers import createDir


def copy_images(args, rel_path, out_name):

    inPathLeft = os.path.join(
        args.baseDir, "sbs_frames", "image_left", rel_path + ".jpg")
    inPathRight = os.path.join(
        args.baseDir, "sbs_frames", "image_right", rel_path + ".jpg")
    outPathLeft = os.path.join(
        args.outDir, "image_left", out_name + ".jpg")
    outPathRight = os.path.join(
        args.outDir, "image_right", out_name + ".jpg")

    try:
        shutil.copy(inPathLeft, outPathLeft)
    except OSError as e:
        return e

    try:
        shutil.copy(inPathRight, outPathRight)
    except OSError as e:
        return e

    return None


def create_sequence_data_set(args):

    dataFile = os.path.join(args.baseDir, "sbs_frames", "image_meta", args.name + ".csv")

    data = pd.read_csv(dataFile, delimiter=",", header=None)

    paths = data.iloc[:, 2].values
    out_names = data.iloc[:, 4].values

    print(f"Copying dataset of size: {paths.shape[0]}")

    files_with_error = []

    for path, out_name in tqdm(zip(paths, out_names), total=paths.shape[0]):

        error = copy_images(args, path, out_name)

        if error is not None:
            print("")
            print(error)
            print(f"The file {path} does not exist. Skipping ...")
            files_with_error.append(path)

    print("Done copying files!")
    print("The following files were not found ...")
    print("")
    for file in files_with_error:
        print(file)

    print("")
    print(f"Remove these files from {dataFile}")

    shutil.copy(dataFile, os.path.join(args.outDir, "meta", args.name + ".csv"))


def create_paper_data_set(args):

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

        for i, line in tqdm(enumerate(f), total=(counter)):
            line = line.rstrip()
            if not line:
                continue

            outName = "out" + str(i).zfill(8)

            copy_images(args, line, outName)

            # wirte to log file the mapping of the old image name to the new name
            l.write(line + " " + outName + "\n")


def run(args):

    # Create required folders
    createDir(os.path.join(args.outDir, "image_left"))
    createDir(os.path.join(args.outDir, "image_right"))
    createDir(os.path.join(args.outDir, "meta"))

    if args.sequence:
        create_sequence_data_set(args)
    else:
        create_paper_data_set(args)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="rename and copy all the images from one data set list to one folder")
    parser.add_argument("--baseDir", type=str, required=True,
                        help="path to folder containing expected folders (mkv_videos, sbs_videos, sbs_frames)")
    parser.add_argument("--name", type=str, required=True,
                        help="name of the txt file containing the names of the images belonging to the data set")
    parser.add_argument("--outDir", type=str, required=True,
                        help="name of the output folder")
    parser.add_argument("--sequence", type=bool, default=False,
                        help="true if the data set is a sequence data set (see README)")

    args = parser.parse_args()

    run(args)
