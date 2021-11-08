import argparse
import os
import numpy as np
import pandas as pd
import shutil
from tqdm import tqdm

from helpers import createDir


def get_num_sequences(sequences):
    return int(sequences[-1][3:11])


def process_sequence(args, seq, sequences, image_names):

    seq_str = "seq" + str(seq).zfill(8)
    idx = np.where(sequences == seq_str)[0]

    # Create required folders
    image_out_folder = os.path.join(args.baseDir, "sequence_data", "images", "seq" + str(seq).zfill(4))
    depth_out_folder = os.path.join(args.baseDir, "sequence_data", "depth", "seq" + str(seq).zfill(4))
    createDir(image_out_folder, verbose=False)
    createDir(depth_out_folder, verbose=False)

    for i in idx:

        image_name = image_names[i]

        image_path_src = os.path.join(args.baseDir, "image_left", image_name + ".jpg")
        depth_path_src = os.path.join(args.baseDir, "disparity", image_name + ".png")

        image_path_dst = os.path.join(args.baseDir, "sequence_data", "images", "seq" + str(seq).zfill(4))
        depth_path_dst = os.path.join(args.baseDir, "sequence_data", "depth", "seq" + str(seq).zfill(4))

        try:
            shutil.copy(image_path_src, image_path_dst)
        except OSError as e:
            print(e)
            exit(-1)
        """
        try:
            shutil.copy(depth_path_src, depth_path_dst)
        except OSError as e:
            print(e)
            exit(-1)
        """


def run(args):

    data_file = os.path.join(args.baseDir, "meta", args.name + ".csv")

    try:
        data = pd.read_csv(data_file, delimiter=",", header=None)
    except OSError as e:
        print("e")
        print("Data set File does not exist. Aborting ...")
        return -1

    image_names = data.iloc[:, 4].values
    sequences = data.iloc[:, 3].values

    num_seq = get_num_sequences(sequences)

    createDir(os.path.join(args.baseDir, "sequence_data", "images"))
    createDir(os.path.join(args.baseDir, "sequence_data", "depth"))

    for seq in tqdm(range(num_seq + 1)):
        process_sequence(args, seq, sequences, image_names)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="move the data of the sequence data set into the required folder structure")

    parser.add_argument("--baseDir", type=str,
                        help="path to folder containing the expected folders (image_left, image_right, meta, disparity)",
                        required=True)
    parser.add_argument("--name", type=str, help="name of the generated dataset (csv file located in meta)", default="training")

    args = parser.parse_args()

    run(args)
