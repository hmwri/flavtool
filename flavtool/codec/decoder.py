from typing import Callable, Final

import numpy as np
import zlib


def raw5_decoder(code: bytes) -> np.ndarray :
    return np.frombuffer(code, dtype=np.uint8)

def rmix_decoder(code: bytes) -> np.ndarray:
    return np.frombuffer(zlib.decompress(code), dtype=np.uint8)

decoder_func_type = Callable[[bytes], np.ndarray]

decoders : Final[dict[str, decoder_func_type]] = {
    "raw5" : raw5_decoder,
    "rmix" : rmix_decoder,
}

