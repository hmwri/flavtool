from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='flavtool',
    version='0.1',
    author="Taiyu Honma",
    author_email="ev220526@meiji.ac.jp",
    description="味覚情報を埋め込み可能なファイル形式:FlavMP4の解析、編集を可能にするツールキット",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hmwri/flavtool",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)




