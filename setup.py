from setuptools import setup


setup(
    name='scrapy-cdr',
    version='0.2.0',
    packages=['scrapy_cdr'],
    install_requires=[
        'scrapy',
        'json_lines',
    ],
    entry_points={
        'console_scripts': [
            'cdr-v2-to-v3=scrapy_cdr.v2_to_v3:main',
            ],
    },
    license='MIT license',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)
