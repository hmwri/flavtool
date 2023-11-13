

from typing import Literal

from TsMovieComposer.analyzer.components import *
from TsMovieComposer.analyzer.media_data import MediaData
from TsMovieComposer.parser.boxs.container import ContainerBox
from TsMovieComposer.parser.boxs.leaf import *
from TsMovieComposer.logger import logger


media_types = Literal["tast", "soun", "vide", "scnt"]


class FlavMP4:
    """
    Composer
        VideoとSoundがすでにあるmp4ファイルについて、味トラックと香りトラックを付け加える
    """

    def __init__(self, parsed_box: ContainerBox):
        """
        パースされたMp4の情報をもとに、トラック情報、サンプルデータ情報を構築
        Parameters
        ----------
        parsed_box : ContainerBox
            パースされたMP4データ
        """
        self.tracks: dict[media_types, TrackComponent | None] = {
            "tast": None,
            "soun": None,
            "vide": None,
            "scnt": None,
        }

        self.media_datas: dict[media_types, MediaData | None] = {
            "tast": None,
            "soun": None,
            "vide": None,
            "scnt": None,
        }

        self.parsed: ContainerBox = parsed_box

        mdat = self.parsed["mdat"]
        if not isinstance(mdat, MdatBox):
            raise Exception("mdat parse error")
        self.mdat: MdatBox = mdat

        mov_header = self.parsed["moov"]["mvhd"]
        if not isinstance(mov_header, MvhdBox):
            raise Exception("mov header parse error")
        self.mov_header = mov_header

        for box in self.parsed["moov"].children:
            if box.box_type == "trak":
                handler_box = box["mdia"]["hdlr"]
                if not isinstance(handler_box, HdlrBox):
                    logger.error("handler box parse error, this track will be ignored. ")
                    continue
                subtype: str = handler_box.component_subtype
                if subtype not in subtype:
                    logger.warning(f"{subtype} is not supported media type, so it will be ignored.")
                    continue

                subtype: media_types
                self.tracks[subtype] = TrackComponent(box)
                self.media_datas[subtype] = MediaData.from_mdat_box(
                    self.mdat,
                    self.sample_tables[subtype],
                    subtype,
                    streaming=not self.mdat.read_bytes
                )

    @property
    def sample_tables(self) -> dict[media_types, SampleTableComponent | None]:
        sample_tables: dict[media_types, SampleTableComponent | None] = {}
        for k, v in self.tracks.items():
            if v is None:
                sample_tables[k] = None
                continue
            sample_tables[k] = v.media.media_info.sample_table
        return sample_tables
