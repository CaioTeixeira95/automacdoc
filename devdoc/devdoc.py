import inspect
import importlib
import os
import sys
import platform
import glob


def rm_docstring_from_source(source):
    """
    Remote the docstring from the source code of a function or a class

    **Parameters**
    > **source:** `str` -- Source code of a function or a class

    **Returns**
    > `str` -- Source code of a class without docstring
    """
    source = source.split('"""')
    if len(source) > 1:
        del source[1]  # remove docstring
    source = ''.join(source)

    # to handle intendation inside functions and classes
    source = source.split('\n')
    numbers_of_indent = len(source[0]) - len(source[0].lstrip())
    for i in range(len(source)):
        source[i] = '\t' + source[i][numbers_of_indent:]
    source = '\n'.join(source)
    return source


def create_fun(name: str, obj, ignore_prefix_function: str):
    """
    Generate a dictionnary that contains the information about a function

    **Parameters**
    > **name:** `str` -- name of the function as returned by `inspect.getmembers`
    > **obj:** `object` -- object of the function as returned by `inspect.getmembers`
    > **ignore_prefix_function:** `str` -- *None* -- precise the prefix of function names to ignore

    **Returns**
    > `dict` -- with keys:
    >  - *name*, *obj* -- the function name and object as returned by `inspect.getmembers`
    >  - *module* -- name of the module
    >  - *path* -- path of the module file
    >  - *doc* -- docstring of the function
    >  - *source* -- source code of the function
    >  - *args* -- arguments of the function as a `inspect.signature` object
    """

    if (
        ignore_prefix_function is not None
        and name[:len(ignore_prefix_function)] == ignore_prefix_function
    ):
        return None

    fun = dict()
    fun['name'] = name
    fun['obj'] = obj
    fun['module'] = inspect.getmodule(obj).__name__
    fun['path'] = inspect.getmodule(obj).__file__
    fun['doc'] = inspect.getdoc(obj) or ''
    fun['source'] = rm_docstring_from_source(inspect.getsource(obj))
    fun['args'] = inspect.signature(obj)
    return fun


def create_class(name: str, obj, ignore_prefix_function: str):
    """
    Generate a dictionnary that contains the information about a class

    **Parameters**
    > **name:** `str` -- name of the class as returned by `inspect.getmembers`
    > **obj:** `object` -- object of the class as returned by `inspect.getmembers`
    > **ignore_prefix_function:** `str` -- *None* -- precise the prefix of function or method names to ignore

    **Returns**
    > `dict` -- with keys:
    >  - *name*, *obj* -- the class name and object as returned by `inspect.getmembers`
    >  - *module* -- name of the module
    >  - *path* -- path of the module file
    >  - *doc* -- docstring of the class
    >  - *source* -- source code of the class
    >  - *args* -- arguments of the class as a `inspect.signature` object
    >  - *functions* -- list of functions that are in the class (formatted as dict)
    >  - *methods* -- list of methods that are in the class (formatted as dict)
    """
    clas = dict()
    clas['name'] = name
    clas['obj'] = obj
    clas['module'] = inspect.getmodule(obj).__name__
    clas['path'] = inspect.getmodule(obj).__file__
    clas['doc'] = inspect.getdoc(obj) or ''
    clas['source'] = rm_docstring_from_source(inspect.getsource(obj))
    clas['args'] = inspect.signature(obj)
    clas['functions'] = [
        create_fun(n, o, ignore_prefix_function)
        for n, o in inspect.getmembers(obj, inspect.isfunction)
    ]
    clas['methods'] = [
        create_fun(n, o, ignore_prefix_function)
        for n, o in inspect.getmembers(obj, inspect.ismethod)
    ]
    return clas


class_name_md = (
    "## **{0}**`#!py3 class` {{ #{0} data-toc-label={0} }}\n\n".format
)  # name

method_name_md = (
    "### *{0}*.**{1}**`#!py3 {2}` {{ #{1} data-toc-label={1} }}\n\n".format
)  # class, name, args

function_name_md = (
    "### **{0}**`#!py3 {1}` {{ #{0} data-toc-label={0} }}\n\n".format
)  # name, args

doc_md = "{}\n".format  # doc

source_md = (
    '\n\n??? info "Source Code" \n\t```py3 linenums="1 1 2" \n{}\n\t```\n'.format
)  # source


def write_function(md_file, fun):
    """
    Add the documentation of a function to a markdown file

    **Parameters**
    > **md_file:** `file` -- file object of the markdown file
    > **fun:** `dict` -- function information organized as a dict (see `create_fun`)
    """
    if fun is None:
        return

    md_file.writelines(function_name_md(fun['name'], fun['args']))
    md_file.writelines(doc_md(fun['doc']))
    md_file.writelines(source_md(fun['source']))


def write_method(md_file, method, clas):
    """
    Add the documentation of a method to a markdown file

    **Parameters**
    > **md_file:** `file` -- file object of the markdown file
    > **method:** `dict` -- method information organized as a dict (see `create_fun`)
    > **class:** `dict` -- class information organized as a dict (see `create_fun`)

    """
    if method is None:
        return

    md_file.writelines(method_name_md(clas['name'], method['name'], method['args']))
    md_file.writelines(doc_md(method['doc']))
    md_file.writelines(source_md(method['source']))


def write_class(md_file, clas):
    """
    Add the documentation of a class to a markdown file

    **Parameters**
    > **md_file:** `file` -- file object of the markdown file
    > **clas:** `dict` -- class information organized as a dict (see `create_clas`)

    """
    md_file.writelines(class_name_md(clas['name']))
    md_file.writelines(doc_md(clas['doc']))
    # list of methods
    if len(clas['methods']):
        md_file.writelines("\n**class methods:** \n\n")
        for method in clas['methods']:
            md_file.writelines(" - [`{0}`](#{0})\n".format(method['name']))

            # list of functions
    if len(clas['functions']) > 0:
        md_file.writelines("\n**class functions & static methods:** \n\n")
        for func in clas['functions']:
            md_file.writelines(" - [`{0}`](#{0})\n".format(func['name']))

    md_file.writelines("\n")

    for method in clas['methods']:
        write_method(md_file, method, clas)

    for func in clas['functions']:
        write_method(md_file, func, clas)  # use write_method to get the clas prefix


def write_module(
    path_to_home: str,
    module_import: str,
    path_to_md: str,
    is_django_project: bool,
    django_project_name: str,
    ignore_prefix_function: str = None,
):
    """
    Generate a Markdown file based on the content of a Python module

    **Parameters**
    > **path_to_home:** `str` -- path to the root of the project (2 steps before the `__init__.py`)
    > **module_import:** `str` -- module name (ex: `my_package.my_module`)
    > **path_to_md:** `str` -- path to the output markdown file
    > **is_django_project:** `bool` -- says if the project is a django project
    > **django_project_name** `str` -- Django project name (django-admin startproject project_name)
    > **ignore_prefix_function:** `str` -- *None* -- precise the prefix of function or method names to ignore

    """
    package_path = os.path.abspath(path_to_home)
    sys.path.insert(0, package_path)

    if is_django_project:
        try:
            import django
        except ModuleNotFoundError:
            raise ModuleNotFoundError((
                'Seems that is not a Django project. '
                'You can use "--django False" flag or '
                'be sure that you have Django installed in your environment.'
            ))
        if django_project_name is None:
            raise Exception((
                'Django project name has not been specified. '
                'Please use "--django-project-name myproject" flag to specify.'
            ))
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'{django_project_name}.settings')
        django.setup()

    try:
        module = importlib.import_module(
            module_import, package=module_import.split('.')[0]
        )
    except ModuleNotFoundError as error:
        raise ModuleNotFoundError(str(error) + ' in ' + module_import)

    clas = [
        create_class(n, o, ignore_prefix_function)
        for n, o in inspect.getmembers(module, inspect.isclass)
    ]
    funs = [
        create_fun(n, o, ignore_prefix_function)
        for n, o in inspect.getmembers(module, inspect.isfunction)
    ]

    if not os.path.isdir(os.path.dirname(path_to_md)):
        os.makedirs(os.path.dirname(path_to_md))
    md_file = open(path_to_md, "w")

    for c in clas:
        write_class(md_file, c)
        md_file.writelines("""\n______\n\n""")

    for f in funs:
        write_function(md_file, f)
        md_file.writelines("""\n______\n\n""")

    md_file.close()


def get_toc_lines_from_file_path(mdfile_name):
    lines = ''
    for i, layer in enumerate(mdfile_name.split('/')):
        if i + 1 != len(mdfile_name.split('/')):
            lines += "        " * (i + 1) + "- " + layer + ":\n"
        else:
            lines += "        " * (i + 1) + "- " + mdfile_name + "\n"
    return lines


def write_mkdocs_yaml(path_to_yaml: str, project_name: str, toc: str):
    """
    Generate the YAML file that contains the website configs

    **Parameters**
    > **path_to_yaml:** `str` -- path to the output YAML file
    > **project_name:** `str` -- name of the project
    > **toc:** `str` -- the toc and the all hierarchy of the website
    """
    with open(path_to_yaml, 'w') as yaml_file:
        content = """site_name: {}
theme:
  name: 'material'
nav:
    - Home: index.md
    - Reference:
{}
markdown_extensions:
    - toc:
        toc_depth: 3
        permalink: True
    - extra
    - smarty
    - codehilite
    - admonition
    - pymdownx.details
    - pymdownx.superfences
    - pymdownx.emoji
    - pymdownx.inlinehilite
    - pymdownx.magiclink
        """.format(project_name, toc)
        yaml_file.writelines(content)


def write_indexmd(path_to_indexmd: str, project_name: str):
    """
    Generate the YAML file that contains the website configs

    **Parameters**
    > **path_to_indexmd:** `str` -- path to the output YAML file
    > **project_name:** `str` -- name of the project
    """
    with open(path_to_indexmd, 'w') as indexmd_file:
        content = """# Welcome to {0}
This website contains the documentation for the wonderful project {0}
        """.format(project_name)
        indexmd_file.writelines(content)


def write_doc(
    folder: str,
    name: str,
    is_django_project: bool,
    django_project_name: str = None
):
    # setting the paths variable
    project_name = name.split('/')[-1]
    code_path = os.path.abspath(folder)
    doc_path = os.path.join(os.path.abspath(name), 'docs')
    root_path = os.path.dirname(code_path)

    # Since windows and Linux platforms utilizes different slash in their file structure
    system_slash_style = {
        'Windows': '\\',
        'Linux': '/'
    }

    # load the architecture of the module
    ign_pref_file = '__'
    file_list = glob.glob(code_path + '/**', recursive=True)

    valid_files = [
        file
        for file in file_list
        if f'/{ign_pref_file}' not in file
           and os.path.isfile(file)
           and file[-3:] == '.py'
           and '__init__' not in file
    ]

    # write every markdown files based on the architecture
    table_of_contents = ''
    for mod in valid_files:
        module_name = mod[len(root_path) + 1: -3].replace(system_slash_style.get(platform.system(), '/'), '.')
        mdfile_path = os.path.join(doc_path, mod[len(code_path) + 1:-3] + '.md')
        mdfile_name = mdfile_path[len(doc_path) + 1:]
        try:
            write_module(root_path, module_name, mdfile_path, is_django_project, django_project_name)
            table_of_contents += get_toc_lines_from_file_path(mdfile_name)
        except Exception as error:
            print('[-]Warning ', error)

    if len(table_of_contents) == 0:
        raise ValueError('All the files seems invalid')

    # removed the condition because it would'nt update the yml file in case
    # of any update in the source code
    yml_path = os.path.join(name, 'mkdocs.yml')
    write_mkdocs_yaml(yml_path, project_name, table_of_contents)

    index_path = os.path.join(doc_path, 'index.md')
    write_indexmd(index_path, project_name)
