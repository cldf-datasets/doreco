from setuptools import setup


setup(
    name='cldfbench_doreco',
    py_modules=['cldfbench_doreco'],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'cldfbench.dataset': [
            'doreco=cldfbench_doreco:Dataset',
        ],
        'cldfbench.commands': [
            'doreco=dorecocommands',
        ]
    },
    install_requires=[
        'cldfbench',
    ],
    extras_require={
        'test': [
            'pytest-cldf',
        ],
    },
)
