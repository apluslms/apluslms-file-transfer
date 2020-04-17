import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as f:
    requirements = f.read().splitlines()

setuptools.setup(
    name="apluslms_file_transfer",
    version="0.1",
    author="Qianqian Qin",
    author_email="qianqian.qin@outlook.com",
    description="A package for file transfer in apluslms",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/QianqianQ/apluslms-file-transfer",
    packages=setuptools.find_packages(include=['apluslms_file_transfer',
                                               'apluslms_file_transfer.*']),
    install_requires=requirements,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
)
