import os
import argparse
from subprocess import call, Popen
import webbrowser
from devdoc import write_doc


parser = argparse.ArgumentParser(description='DevDoc make it easier to build documentations.')

parser.add_argument(
    '--folder',
    help='The folder that contains the source code you want to document',
    type=str,
    required=True
)
parser.add_argument(
    '--name',
    help='The name of main folder that will contain the documentation',
    type=str,
    required=True
)
parser.add_argument(
    '--django',
    help='Is a Django project?',
    choices=['True', 'False'],
    default='True'
)
parser.add_argument(
    '--django-project-name',
    help='The Django project name',
    type=str
)
parser.add_argument(
    '--server',
    help='IP address and port to serve documentation locally (default: localhost:8000)',
    type=str,
    default='localhost:8000',
)


def main():
    args = parser.parse_args()
    args.django = args.django == 'True'

    try:
        write_doc(args.folder, args.name, args.django, args.django_project_name)
    except Exception as error:
        print("[-] Error ", str(error))
        return

    os.chdir(args.name)
    call(['mkdocs', 'build', '--clean'])
    Popen(['mkdocs', 'serve', '-a', args.server])

    webbrowser.open(f'http://{args.server}/')


if __name__ == "__main__":
    main()
