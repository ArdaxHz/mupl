from setuptools import setup, find_packages

setup(
    name="mupl",
    version="2.1.0",
    description="mupl: Bulk MangaDex Upload Tool",
    author="ArdaxHz",
    author_email="70710586+ArdaxHz@users.noreply.github.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "requests",
        "natsort",
        "packaging",
        "Pillow",
        "tqdm",
    ],
)
