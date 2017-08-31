from setuptools import setup, find_packages

setup(
    name='website',
    version='0.0.0',
    description='Source code of my website',
    url='https://github.com/arugifa/website',
    author='Alexandre Figura',
    license='GNU General Public License v3',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
    packages=find_packages(),
    install_requires=[
        'flask>=0.12',
    ],
)
