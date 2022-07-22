# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import pathlib

__version__ = "1.0.0"

here = pathlib.Path(__file__).parent.resolve()

setup(
    name="supplypipe",
    version=__version__,
    description="Stock price extractor and signal generator",
    url="https://github.com/danielboloc/Supplypipe",
    author="Daniel Boloc",
    author_email="danielboloc@gmail.com",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers, Investors",
        "Topic :: Software Development :: Investment",
        "Programming Language :: Python :: 3.9",
        "License :: MIT License",
    ],
    keywords="stocks, investment, exponential moving average",
    package_dir={"": "supplypipe"},
    packages=find_packages(where="supplypipe"),
    python_requires=">=3.9, <4",
)