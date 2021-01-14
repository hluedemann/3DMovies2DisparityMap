#!/usr/bin/env python
"""
    Generate disparity and uncertainty maps for given list.
    Assumumption: (full-resolution; i.e. 1880x800) forward / backward flow is located
    in the folders flow_forward and flow_backward.
"""
import os
import argparse
import numpy as np
import cv2
from PIL import PngImagePlugin
from PIL import Image
import imageio
import glob
from tqdm import tqdm


def read_flow(filename):
    flow = np.load(filename)

    u = flow[:, :, 0]
    v = flow[:, :, 1]

    assert u.shape[0] == 800, f"hight of flow needs to be 800 but is {u.shape[0]}"
    assert u.shape[1] == 1880, f"width of flow needs to be 1880 but is {u.shape[1]}"

    return u, v


def read_sky_segmentation(filename):
    """Read the sky segmentation and convert it into a binary array indicating pixels belonging to the sky"""

    array = np.asarray(Image.open(filename))
    return np.where(array == 255, 1, 0)


def create_dir(path):
    try:
        os.makedirs(path, exist_ok=True)
    except:
        print(f"Failed to create dir: {path}")
    else:
        print(f"Created dir: {path}")


def get_file_name(path):
    return path.split("/")[-1].split(".")[0]


def create_log_header(l):
    l.write("## Log file for disparity filtering\n\n")
    l.write(
        f"# v_threshold: {args.v_threshold} - threshold vertical flow check\n")
    l.write(
        f"# max_v_fail: {args.max_v_fail} - max percentage of pixels that fail vertical flow check\n")
    l.write(
        f"# fbc_threshold: {args.fbc_threshold} - threshold for forward-backward check\n")
    l.write(
        f"# min_fbc_pass: {args.min_fbc_pass} - min percentage of pixels that pass forward-backward check\n")
    l.write(
        f"# range_threshold: {args.range_threshold} - threshold for horizontal flow range check\n\n")


def get_disp_and_uncertainty(
    path,
    use_filtering,
    v_threshold,
    max_v_fail,
    fbc_threshold,
    min_fbc_pass,
    range_threshold,
):

    out_path_disp = os.path.join(path, "disparity")
    out_path_uncer = os.path.join(path, "uncertainty")
    create_dir(out_path_disp)
    create_dir(out_path_uncer)

    path_flow_f = sorted(
        glob.glob(os.path.join(path, "flow_forward", "*.npy")))
    path_flow_b = sorted(
        glob.glob(os.path.join(path, "flow_backward", "*.npy")))
    path_sky_seg = sorted(
        glob.glob(os.path.join(path, "sky_segmentation", "*.png")))

    assert len(path_flow_f) == len(
        path_flow_b), "number of forward and backward flows not the same"
    assert len(path_flow_f) == len(
        path_sky_seg), "number of flow and sky segmentation not the same"

    # Logfile to store which images are ignored and why
    if use_filtering:
        if not os.path.exists(os.path.join(path, "meta")):
            os.makedirs(os.path.join(path, "meta"))
        log_file = os.path.join(path, "meta", "disp_filter_log.txt")
        l = open(log_file, "w")
        create_log_header(l)
        num_filterd = 0

    for file_forward, file_backward, file_sky in tqdm(zip(path_flow_f, path_flow_b, path_sky_seg), total=len(path_flow_f)):

        file_name_f = get_file_name(file_forward)
        file_name_b = get_file_name(file_backward)
        file_name_s = get_file_name(file_sky)

        # Check if all the data belongs to the same original image
        assert file_name_f[0:11] == file_name_b[0:11] == file_name_s[0:11], f"file names for forwad and backward flow and\
            sky segmentation should be the same - {file_name_f[0:11]} | {file_name_b[0:11]} | {file_name_s[0:11]}"

        out_file_name = file_name_f[0:11]

        # read flow
        u_fw, v_fw = read_flow(file_forward)
        u_bw, v_bw = read_flow(file_backward)
        sky_seg_idx = read_sky_segmentation(file_sky)

        if use_filtering:
            check_v_fw = abs(v_fw) > v_threshold
            v_fail_fw = 1.0 * np.count_nonzero(check_v_fw) / v_fw.size

            if v_fail_fw >= max_v_fail:
                l.write(out_file_name + " v_fail_fw to large\n")
                num_filterd += 1
                continue

            check_v_bw = abs(v_bw) > v_threshold
            v_fail_bw = 1.0 * np.count_nonzero(check_v_bw) / v_bw.size

            if v_fail_bw >= max_v_fail:
                l.write(out_file_name + " v_fail_fw too large\n")
                num_filterd += 1
                continue

            range_fw = u_fw.max() - u_fw.min()

            if range_fw <= range_threshold:
                l.write(out_file_name + " range_u_fw too small\n")
                num_filterd += 1
                continue

            range_bw = u_bw.max() - u_bw.min()

            if range_bw <= range_threshold:
                l.write(out_file_name + " range_threshold too small\n")
                num_filterd += 1
                continue

        # compute uncertainty and disparity
        ind_y, ind_x = np.indices(u_fw.shape, dtype=np.float32)
        y_map = ind_y
        x_map = ind_x + u_fw

        flow_flipped_and_warped = cv2.remap(
            -u_bw,
            x_map,
            y_map,
            interpolation=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REPLICATE,
        )

        uncertainty = abs(u_fw - flow_flipped_and_warped)

        if use_filtering:
            valid = uncertainty < fbc_threshold
            fbc_pass = 1.0 * np.count_nonzero(valid) / uncertainty.size

            if fbc_pass <= min_fbc_pass:
                l.write(out_file_name + " fbc_pass too small\n")
                num_filterd += 1
                continue

        disp = -u_fw

        # use sky segmentation to set disparity of sky to minimum disp in image
        disp[sky_seg_idx] = np.min(disp)

        # downsample disparity and uncertainty
        downscaling = 0.5

        disp = cv2.resize(
            disp, None, fx=downscaling, fy=downscaling, interpolation=cv2.INTER_LINEAR
        )

        disp = disp * downscaling

        uncertainty = cv2.resize(
            uncertainty,
            None,
            fx=downscaling,
            fy=downscaling,
            interpolation=cv2.INTER_LINEAR,
        )

        uncertainty = uncertainty * downscaling

        # quantize disparity and uncertainty
        disp_max = disp.max()
        disp_min = disp.min()

        if disp_max - disp_min > 0:
            disp = np.round((disp - disp_min) / (disp_max - disp_min) * 65535).astype(
                np.uint16
            )

            scale = 1.0 * (disp_max - disp_min) / 65535
            offset = disp_min
        else:
            disp = (0 * disp).astype(np.uint16)

            offset = disp_min
            scale = 1.0

        meta = PngImagePlugin.PngInfo()
        meta.add_text("offset", str(offset))
        meta.add_text("scale", str(scale))

        uncertainty = (10 * uncertainty).round()
        uncertainty[uncertainty > 255] = 255

        # save disparity and uncertainty

        disp_out_path = os.path.join(
            out_path_disp, out_file_name + "_disp.png")
        imageio.imwrite(disp_out_path, disp, pnginfo=meta, prefer_uint8=False)

        uncer_out_path = os.path.join(
            out_path_uncer, out_file_name + "_uncer.png")
        imageio.imwrite(uncer_out_path, uncertainty.astype(np.uint8))

    # Log percentage of filterd images
    if use_filtering:
        l.write(
            f"\nPercentage of filtered images: {num_filterd/len(path_flow_f)}\n")
        l.close()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Generate disparity and uncertainty maps for given list. Assumumption: \
                                                  (full-resolution; i.e. 1880x800) forward / backward flow is located in \
                                                  the folders flow_forward and flow_backward.")
    parser.add_argument(
        "path", type=str, help="path to folder of dataset - needs to contain flow_forward / flow_backward / sky_segmentation")
    parser.add_argument(
        "-f", "--filter", action="store_true", help="Apply filtering based on flow?")
    parser.add_argument(
        "--v_threshold", type=float, default=2, help="threshold vertical flow check")
    parser.add_argument(
        "--max_v_fail",
        type=float,
        default=0.1,
        help="max percentage of pixels that fail vertical flow check",)
    parser.add_argument(
        "--fbc_threshold",
        type=float,
        default=2,
        help="threshold for forward-backward check")
    parser.add_argument(
        "--min_fbc_pass",
        type=float,
        default=0.7,
        help="min percentage of pixels that pass forward-backward check")
    parser.add_argument(
        "--range_threshold",
        type=float,
        default=10,
        help="threshold for horizontal flow range check")
    args = parser.parse_args()

    get_disp_and_uncertainty(
        args.path,
        args.filter,
        args.v_threshold,
        args.max_v_fail,
        args.fbc_threshold,
        args.min_fbc_pass,
        args.range_threshold,
    )
