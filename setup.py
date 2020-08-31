from setuptools import setup, find_packages


with open("requirements.txt") as f:
    install_requirements = f.read().splitlines()

with open('LICENSE') as f:
    license = f.read()

setup(
    name="ec2_cli",
    version="0.0.1",
    description="a tiny command set for ec2",
    author="tatsuya4559",
    license=license,
    packages=find_packages(),
    install_requires=install_requirements,
    entry_points={
        "console_scripts": [
            "ec2=ec2_cli.main:main",
        ]
    },
    classifiers=[
        'Programming Language :: Python :: 3.8',
    ]
)
