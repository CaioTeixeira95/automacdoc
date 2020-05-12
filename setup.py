import setuptools

with open('README.md', 'r') as file:
    long_description = file.read()

setuptools.setup(
     name='DevDoc',
     version='0.3',
     entry_points={'console_scripts': ['devdoc = devdoc.main:main']},
     author='Caio Teixeira and Samuel Almeida',
     author_email='caio.xd63@hotmail.com',
     description='Automatic generation of documentation for Django or python projects.',
     long_description=long_description,
     long_description_content_type='text/markdown',
     packages=setuptools.find_packages(),
     install_requires=['mkdocs', 'mkdocs-material', 'pymdown-extensions'],
     classifiers=[
         'Programming Language :: Python :: 3',
         'License :: OSI Approved :: MIT License',
         'Operating System :: OS Independent',
     ],
 )
