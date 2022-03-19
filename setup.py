"""
setup file. run 'python3 setup.py install' to install.
"""
from setuptools import setup  # type: ignore

import bibtexautocomplete

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name=bibtexautocomplete.__name__,
    version=bibtexautocomplete.__version__,
    author=bibtexautocomplete.__author__,
    author_email=bibtexautocomplete.__email__,
    url=bibtexautocomplete.__url__,
    description=bibtexautocomplete.__description__,
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=["bibtexautocomplete"],
    scripts=["scripts/btac"],
    install_requires=[
        "bibtexparser",
        "alive-progress @ git+https://github.com/dlesbre/alive-progress.git",
    ],
    extras_require={
        "dev": ["pre-commit", "pytest", "mypy", "black", "flake8", "isort"],
    },
    python_requires=">=3.6",
    license="MIT",
    platforms=["any"],
    keywords=["bibtex biblatex latex autocomplete btac"],
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        "Development Status :: 5 - Production/Stable",
        # Indicate who your project is intended for
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Environment :: Console",
        "Natural Language :: English",
        # Pick your license as you wish (should match "license" above)
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
        "Topic :: Text Processing :: Markup :: LaTeX",
        "Topic :: Utilities",
        "Topic :: Scientific/Engineering",
        "Typing :: Typed",
    ],
    data_files=[("", ["LICENSE"])],
)
