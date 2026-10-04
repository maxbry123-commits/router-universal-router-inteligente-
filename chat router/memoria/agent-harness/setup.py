from setuptools import find_packages, setup

setup(name='cli-anything-memoria', version='1.0.0', packages=find_packages(), install_requires=['click>=8.0'],
      entry_points={'console_scripts': ['cli-anything-memoria=cli_anything.memoria.memoria_cli:main']})
