"""
손처럼 클릭 - 설치 스크립트
"""
from setuptools import setup, find_packages
from pathlib import Path

# version.py에서 버전 정보 읽기
version_file = Path(__file__).parent / "autoclicker" / "version.py"
exec(open(version_file, encoding="utf-8").read())

# README 파일 읽기 (있는 경우)
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    long_description = readme_file.read_text(encoding="utf-8")

# requirements.txt 읽기
requirements_file = Path(__file__).parent / "requirements.txt"
install_requires = []
if requirements_file.exists():
    install_requires = [
        line.strip()
        for line in requirements_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

setup(
    name="autoclicker",
    version=__version__,
    author="JaeUk",
    description="자동 클릭 유틸리티 애플리케이션",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jaeuk9060/dding_mecro",  # 실제 GitHub URL로 변경 필요
    packages=find_packages(),
    package_data={
        "autoclicker": [
            "config.json",
            "assets/*.ico",
            "assets/*.png",
        ],
    },
    include_package_data=True,
    install_requires=install_requires,
    python_requires=">=3.8",
    entry_points={
        "gui_scripts": [
            "autoclicker=autoclicker.__main__:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: Microsoft :: Windows",
    ],
)

