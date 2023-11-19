from TsMovieComposer.parser.boxs.container import ContainerBox
from TsMovieComposer.parser.boxs.leaf import *


class EmptyMp4Creator:
    """
    TrackBox を作るクラス
    """
    @staticmethod
    def create(major_brand:str,
               compatible_brands:list[str],
               time_scale:int,
               duration:int
               ):

        now = (datetime.now() - datetime(1904, 1, 1)).total_seconds()
        track_box = ContainerBox(
            box_type="root",
            children=[
                FtypBox(
                    box_type="ftyp",
                    major_brand=major_brand,
                    compatible_brands=compatible_brands,
                ),
                ContainerBox(
                    box_type="moov",
                    children=[
                        MvhdBox(
                            box_type="mvhd",
                            creation_time=int(now),
                            modification_time=int(now),
                            time_scale=time_scale,
                            duration=duration,
                        )
                    ]
                ),
                MdatBox(
                    box_type="mdat",
                    is_extended=True,
                    begin_point=None,
                    read_bytes=True,


                )

            ]
        )
        track_box.print()
        return track_box

