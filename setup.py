from setuptools import setup

setup(
    name='scraper',
    version='0.1.0',
    description='A Python template repo to save you some yak-shaving.',
    long_description='',
    author='Jason White',
    author_email='jason.white@shopify.com',
    url='https://github.com/JasonMWhite/scraper',
    packages=['scraper', 'pylint_custom'],
    include_package_data=True,
    install_requires=[
    ],
    license="MIT",
    zip_safe=False,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
    ],
    test_suite='tests',
    entry_points='''
        [console_scripts]
        gitlawca=scraper.cli:main
    ''',
)
