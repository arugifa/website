from setuptools import find_packages, setup

setup(
    name='arugifa-website',
    version='0.1.0',
    description='Source code of my website',
    url='https://github.com/arugifa/website',
    author='Alexandre Figura',
    license='GNU General Public License v3',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
    ],
    packages=find_packages(),
    install_requires=[
        'aiofiles>=0.4',
        'beautifulsoup4>=4.7',
        'factory_boy>=2.9',
        'flask>=0.12',
        'flask-sqlalchemy>=2.3',
        'frozen-flask>=0.15',
        'lxml[cssselect]>=4.3',
        'invoke>=0.22',
        'sortedcontainers>=2.1.0',
    ],
)
