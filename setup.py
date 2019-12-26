# coding=utf-8
from trcdash import __version__
from setuptools import setup, find_packages

setup(
    name='trcdash',
    version=__version__,
    description='Terracoin system information web dashboard',
    long_description='trcdash is a system information web dashboard for Terracoin based on psdash',
    classifiers=[
        'Topic :: System :: Monitoring',
        'Topic :: System :: Logging',
        'Topic :: System :: Networking :: Monitoring',
        'Development Status :: 4 - Beta',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'License :: Public Domain',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators'
    ],
    keywords='linux web dashboard terracoin',
    author='Justin F. Hallett',
    author_email='thesin@terracoin.io',
    url='https://github.com/thesin-/trcdash',
    license='CC0',
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Flask==0.10.1',
        'psutil==2.1.3',
        'glob2==0.4.1',
        'gevent==1.0.2',
        'zerorpc==0.4.4',
        'netifaces==0.10.4',
        'argparse'
    ],
    test_suite='tests',
    tests_require=['unittest2'],
    entry_points={
        'console_scripts': [
            'trcdash = trcdash.run:main'
        ]
    }
)
