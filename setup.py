import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

# with open('requirements.txt') as f:
#     requirements = f.read().splitlines()

setuptools.setup(
    name="aplus-file-management",
    version="0.0.1",
    author="Qianqian Qin",
    author_email="qianqian.qin@outlook.com",
    description="A package for file management in apluslms",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    packages=setuptools.find_packages(),
    # packages=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
    # extras_require={
    #     'dev': ['check-manifest'],
    #     'test': [
    #         'mock',
    #         'PyHamcrest',
    #         'pytest',
    #         'pytest-cov'
    #     ]
    # },
)
