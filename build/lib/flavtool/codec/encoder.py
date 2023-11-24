from typing import Callable, Final

import numpy as np


def raw5_encoder(data: np.ndarray) -> bytes:
    if data.dtype != np.uint8:
        raise Exception("Encode Error. Only ndarray dtype=np.uint8 is supported")
    if not (data.shape[0] == 5 and len(data) == 5):
        raise Exception("Encode Error. Only ndarray (5,1) is supported")
    return data.tobytes()


encoder_func_type = Callable[[np.ndarray], bytes]

encoders: Final[dict[str, encoder_func_type]] = {
    "raw5": raw5_encoder
}
