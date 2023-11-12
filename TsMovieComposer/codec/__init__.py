from typing import Literal
from .decoder import decoders, decoder_func_type
from .encoder import encoders, encoder_func_type
supported_codec_type = Literal["raw5"]
supported_codecs = ["raw5"]

def get_decoder(codec : supported_codec_type) -> decoder_func_type :
    if codec not in supported_codecs:
        raise Exception(f"This codec : {codec} is not supported")
    return decoders[codec]

def get_encoder(codec : supported_codec_type) -> encoder_func_type :
    if codec not in supported_codecs:
        raise Exception(f"This codec : {codec} is not supported")
    return encoders[codec]


