
import os
import errno



def silentremove(filename):
    try:
        os.remove(filename)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise  # re-raise exception if a different error occurred



def processShotFile(video, shotFile):
    numFrames = 0
    cutList = []
    with open(video + shotFile, "r") as fp:

        for cnt, line in enumerate(fp):
            # get cuts
            idx = line.find("pkt_pts_time=")
            if idx != -1:
                numFrames = numFrames + 1
                pts_time = float(line[idx + 13: idx + 13 + 8])
                cutList.append(pts_time)
    return cutList
