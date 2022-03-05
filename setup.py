"""
setup file. run 'python3 setup.py install' to install.
"""
from setuptools import setup  # type: ignore

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="bibtexautocomplete",
    version="0.2",
    author="Dorian Lesbre",
    url="https://github.com/dlesbre/bibtex-autocomplete",
    description="Python package to autocomplete bibtex bibliographies ",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=["bibtexautocomplete"],
    scripts=["scripts/bibtexautocomplete"],
    install_requires=[
        "bibtexparser",
        "git+https://github.com/dlesbre/alive-progress.git",
    ],
    extras_require={
        "dev": ["pre-commit", "pytest", "mypy", "black", "flake8", "isort"],
    },
    python_requires=">=3.9",
    license="MIT",
    platforms=["any"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Utilities",
    ],
)
