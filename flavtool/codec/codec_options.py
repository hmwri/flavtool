
class MixInfo:
    def __init__(self, name, concentration : float, max_amount : float):
        self.name :str = name
        self.concentration : float = concentration
        self.max_amount : float = max_amount

    def __str__(self):
        return f"name : {self.name}, concentration : {self.concentration}, max_amount : {self.max_amount}"

# 塩化ナトリウム:NaCl
# クエン酸:CitA
# リンゴ酸:Mali
# プロピオン乳酸:PPLA
# 酢酸:AceA
# フルクトース:Fruc
# スクロース:Sucr
# 炭酸カリウム:Pota
# キニーネ:Quin
# アルギニン:Argi
# テオブロミン:Theo
# グルタミン酸ナトリウム:Glut
# カプサイシン:Caps
# タンニン酸:Tann
# 炭酸水素ナトリウム:SodB

class CodecOption:
    def __init__(self, corresponding_codec):
        self.corresponding_codec = corresponding_codec
        pass


class MixCodecOption(CodecOption):
    def __init__(self, infos:list[MixInfo]):
        super().__init__(corresponding_codec="rmix")
        self.infos : list[MixInfo] = infos

    @staticmethod
    def default():
        return MixCodecOption(
            [
                MixInfo(name="NaCl", concentration=17, max_amount=100),
                MixInfo(name="CitA", concentration=17, max_amount=100),
                MixInfo(name="Fruc", concentration=30, max_amount=100),
                MixInfo(name="Pota", concentration=20, max_amount=100),
                MixInfo(name="Glut", concentration=9, max_amount=100),
            ]
        )

    def __str__(self):
        result = "codec_option\n"
        for i in self.infos:
            result += f"\t{i}\n"
        return result



