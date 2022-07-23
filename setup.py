import pathlib
import setuptools


def from_file(*names, encoding='utf8'):
    return pathlib.Path(
        pathlib.Path(__file__).parent, *names
    ).read_text(encoding=encoding)


version = {}
contents = pathlib.Path('src/pukpuk/version.py').read_text()
exec(contents, version)


setuptools.setup(
    name='pukpuk',
    version=version['__version__'],
    description='HTTP discovery toolkit',
    long_description=from_file('README.md'),
    long_description_content_type='text/markdown',
    license='MIT License',
    url='https://github.com/tasooshi/pukpuk/',
    author='tasooshi',
    author_email='tasooshi@pm.me',
    keywords=[
        'HTTP',
        'scanning',
        'discovery',
    ],
    python_requires='>=3.8',
    packages=setuptools.find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=(
        'netaddr==0.8.0',
        'pyOpenSSL==22.0.0',
        'dnspython==2.2.1',
        'requests==2.28.1',
        'Pillow==9.2.0',
    ),
    zip_safe=False,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    entry_points={
        'console_scripts': [
            'pukpuk = pukpuk.cli:main'
        ]
    },
)
