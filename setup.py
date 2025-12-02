"""Setup configuration for GitGotchi."""
from pathlib import Path

from setuptools import find_packages, setup

# Read README for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="gitgotchi",
    version="0.1.1",
    author="GitGotchi Team",
    author_email="gitgotchi@example.com",
    description="A Stardew Valley-inspired terminal companion that lives in your git repository",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/gitgotchi",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/gitgotchi/issues",
        "Source": "https://github.com/yourusername/gitgotchi",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Version Control :: Git",
        "Topic :: Games/Entertainment :: Simulation",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
        "Environment :: Console",
    ],
    python_requires=">=3.10",
    install_requires=[
        "rich>=13.7.0",
        "gitpython>=3.1.40",
        "anthropic>=0.34.0",
        "sqlalchemy>=2.0.36",
        "typer>=0.9.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "gitgotchi=src.cli:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "src": ["assets/sprites/*.txt"],
    },
)
