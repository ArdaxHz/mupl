from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


setup(
    name="muplr",
    version="2.1.1",
    description="mupl: Bulk MangaDex Upload Tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="ArdaxHz",
    author_email="70710586+ArdaxHz@users.noreply.github.com",
    url="https://github.com/ArdaxHz/mupl",
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
