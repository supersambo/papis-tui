# -*- coding: utf-8 -*-
from setuptools import setup
from papistui import __version__


setup(
    name="papistui",
    version=__version__,
    author="Stephan Schlögl",
    author_email="stephan@schloegl.net",
    license="GPLv3",
    url="https://github.com/supersambo/papistui",
    install_requires=[
        "papis>=0.11",
        "clipboard",
        "pybtex",
        "neovim-remote",
    ],
    classifiers=[
        "Environment :: Console",
        "Environment :: Console :: Curses",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: MacOS",
        "Operating System :: POSIX",
        "Operating System :: Unix",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Utilities",
    ],
    description="terminal user interface for papis",
    long_description="terminal user interface for papis",
    extras_require=dict(
        develop=[
            "sphinx",
            "sphinx-click",
            "sphinx_rtd_theme",
            "pytest",
            "pytest-cov",
        ]
    ),
    keywords=[
        "papis", "tui", "bibtex",
        "management", "cli", "biliography"
    ],
    packages=[
        "papistui",
        "papistui.components",
        "papistui.features",
        "papistui.helpers",
    ],
    entry_points={
        "console_scripts": [
            "papis-tui=papistui.main:run",
        ],
        "papis.picker": [
            "papis-tui=papistui.main:Picker",
        ],
        "papis.command": [
            "tui=papistui.main:run",
        ]
    },
    platforms=["linux", "osx"],
)
