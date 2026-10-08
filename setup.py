"""
Setup script for LuckyClick
"""

from setuptools import setup, find_packages

setup(
    name='luckyclick',
    version='1.1.2',
    description='LuckyClick - Auto Clicker for Linux',
    long_description='A feature-rich auto clicker for Linux with virtual mouse support, '
                     'point recording, and system tray integration.',
    author='LuckyClick Team',
    url='https://github.com/luckyclick',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'PyQt5>=5.15.0',
        'pynput>=1.7.0',
        'python-xlib>=0.33',
    ],
    entry_points={
        'console_scripts': [
            'luckyclick=luckyclick.main:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Topic :: Utilities',
    ],
    python_requires='>=3.6',
)