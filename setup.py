"""
setup file. run 'python3 setup.py install' to install.
"""
from setuptools import setup  # type: ignore

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="bibtexautocomplete",
    version="0.1.0",
    author="Dorian Lesbre",
    url="https://github.com/dlesbre/bibtex-autocomplete",
    description="Python package to autocomplete bibtex bibliographies ",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=["bibtexautocomplete"],
    # scripts = [""],
    install_requires=["bibtexparser", "python-Levenshtein"],
    extras_require={
        "dev": ["pytest", "mypy"],
    },
    python_requires=">=3.6",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Utilities",
    ],
)
