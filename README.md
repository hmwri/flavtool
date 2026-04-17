# flavtool

## 日本語

`flavtool` は、味覚情報を記録できる FlavMP4 を解析・編集・再構成するための低レベル Python ツールキットです。MP4 の box 構造を読み、トラック情報を整理し、味データを encode/decode し、必要に応じて MP4 を再合成します。

TasteColorizer のように、既存の映像メディアへ推定された味データを付与する用途の基盤になります。

参考: https://www.honma.site/ja/works/TasteColorizer/

### インストール

```bash
pip install flavtool
```

ローカルで開発する場合:

```bash
pip install -e .
```

### 主なモジュール

- `parser`: MP4 box 構造の解析
- `analyzer`: 解析結果からトラックやメディア情報を整理
- `codec`: 味データの encode/decode
- `composer`: 解析・編集した情報から MP4 を再構成

### MP4 を解析する

```python
from flavtool.parser import Parser

parser = Parser("path/to/file.mp4")
box = parser.parse(read_mdat_bytes=False)
box.print()
```

`read_mdat_bytes=False` にすると、メディア本体をメモリに読み込まずに構造を確認できます。

### トラックを解析する

```python
from flavtool.analyzer import analyze
from flavtool.parser import Parser

parser = Parser("path/to/file.mp4")
box = parser.parse(read_mdat_bytes=False)
flav_mp4 = analyze(box)

taste_track = flav_mp4.tracks["tast"]
```

### 味データを encode/decode する

```python
import numpy as np
from flavtool.codec import get_decoder, get_encoder

taste = np.array([1, 2, 3, 4, 5], dtype=np.uint8)

encoder = get_encoder("raw5")
encoded = encoder(taste)

decoder = get_decoder("raw5")
decoded = decoder(encoded)
```

### 構成

- `flavtool/parser/`: MP4 parser
- `flavtool/analyzer/`: track/media analyzer
- `flavtool/codec/`: taste codec
- `flavtool/composer/`: MP4 composer
- `main.py`, `vit_test.py`: ローカル実験用コード
- `*.mp4`: サンプルまたは生成されたメディアファイル

## English

`flavtool` is a low-level Python toolkit for parsing, analyzing, editing, encoding, and composing FlavMP4 files.

It is the lower layer used when applications need direct access to MP4 structures, taste tracks, codecs, and composition.

Reference: https://www.honma.site/ja/works/TasteColorizer/

### Install

```bash
pip install flavtool
```

For local development:

```bash
pip install -e .
```

### Modules

- `parser`: parse MP4 box structures
- `analyzer`: organize parsed boxes into tracks and media information
- `codec`: encode/decode taste data
- `composer`: rebuild MP4 data

### Parse an MP4

```python
from flavtool.parser import Parser

parser = Parser("path/to/file.mp4")
box = parser.parse(read_mdat_bytes=False)
box.print()
```

### Analyze Tracks

```python
from flavtool.analyzer import analyze
from flavtool.parser import Parser

parser = Parser("path/to/file.mp4")
box = parser.parse(read_mdat_bytes=False)
flav_mp4 = analyze(box)

taste_track = flav_mp4.tracks["tast"]
```

### Encode and Decode Taste Data

```python
import numpy as np
from flavtool.codec import get_decoder, get_encoder

taste = np.array([1, 2, 3, 4, 5], dtype=np.uint8)

encoder = get_encoder("raw5")
encoded = encoder(taste)

decoder = get_decoder("raw5")
decoded = decoder(encoded)
```
