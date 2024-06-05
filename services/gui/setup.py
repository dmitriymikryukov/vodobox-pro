from setuptools import setup, find_packages

setup(
    name='vodobox-pro-ui',
    version='1.0.0',
    description='Applications for the UI part of "Vodobox" kiosks',
    author='Zaur',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    long_description_content_type="text/markdown",
    url='https://github.com/bl4ckfl4me-dev/vodobox',
    entry_points={
        'console_scripts': [
            'run_ui = ui.__main__',
        ],
    },
    python_requires=">=3.11.6",
)

