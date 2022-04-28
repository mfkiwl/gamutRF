#!/usr/bin/python3

import re
import os
from pathlib import Path
import numpy as np


# Use max recv_frame_size for USB - because we don't mind latency,
# we are optimizing for lower CPU.
# https://files.ettus.com/manual/page_transport.html
# https://github.com/EttusResearch/uhd/blob/master/host/lib/usrp/b200/b200_impl.hpp
# Should result in no overflows:
# UHD_IMAGES_DIR=/usr/share/uhd/images ./examples/rx_samples_to_file --args num_recv_frames=128,recv_frame_size=16360 --file test.gz --nsamps 200000000 --rate 20000000 --freq 101e6 --spb 20000000
ETTUS_ARGS = 'num_recv_frames=128,recv_frame_size=16360'
ETTUS_ANT = 'TX/RX'
SAMPLE_FILENAME_RE = re.compile(r'^.+_([0-9]+)Hz_([0-9]+)sps\.(s\d+|raw).*$')
SAMPLE_DTYPES = {
    's8':  ('<i1', 'signed-integer'),
    's16': ('<i2', 'signed-integer'),
    's32': ('<i4', 'signed-integer'),
    'u8':  ('<u1', 'unsigned-integer'),
    'u16': ('<u2', 'unsigned-integer'),
    'u32': ('<u4', 'unsigned-integer'),
    'raw': ('<f4', 'float'),
}


def replace_ext(filename, ext, all_ext=False):
    basename = os.path.basename(filename)
    if all_ext:
        dot = basename.index('.')
    else:
        dot = basename.rindex('.')
    new_basename = basename[:(dot + 1)] + ext
    return filename.replace(basename, new_basename)


def parse_filename(filename):
    # TODO: parse from sigmf.
    match = SAMPLE_FILENAME_RE.match(filename)
    try:
        freq_center = int(match.group(1))
        sample_rate = int(match.group(2))
        sample_type = match.group(3)
    except AttributeError:
        freq_center = None
        sample_rate = None
        sample_type = None
    # FFT is always float not matter the original sample type.
    if os.path.basename(filename).startswith('fft_'):
        sample_type = 'raw'
    sample_dtype, sample_type = SAMPLE_DTYPES.get(sample_type, (None, None))
    sample_bits = None
    sample_len = None
    if sample_dtype:
        sample_dtype = np.dtype([('i', sample_dtype), ('q', sample_dtype)])
        sample_bits = sample_dtype[0].itemsize * 8
        sample_len = sample_dtype[0].itemsize * 2
    return (freq_center, sample_rate, sample_dtype, sample_len, sample_type, sample_bits)


def get_nondot_files(filedir, glob='*.s*.*'):
    return [str(path) for path in Path(filedir).rglob(glob)
            if not os.path.basename(path).startswith('.')]
