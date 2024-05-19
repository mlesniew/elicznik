from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(
    name='elicznik',
    version='2.2.0',
    description='Tauron eLicznik scrapper',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/mlesniew/elicznik',
    author='Michał Leśniewski',
    author_email='mlesniew@gmail.com',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3',
        'Topic :: Home Automation',
        'Topic :: Internet',
        'Topic :: Utilities',
    ],
    keywords='elicznik, tauron, scrapper',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    python_requires='>=3.6, <4',
    install_requires=['requests', 'tabulate'],
    entry_points={
        'console_scripts': [
            'elicznik=elicznik.__main__:main',
        ],
    },
)
