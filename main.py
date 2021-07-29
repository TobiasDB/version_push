"""
TODO:
    - Make CI Compatible 
    - Add Option to tag repository
"""
import os
import sys
import subprocess
import argparse


def git(*args):
    """ 
    Spawn a subprocess that runs a git command
    """
    return subprocess.check_output(["git"] + list(args)).decode("utf-8")


def commandline():
    """ 
    Parse Commandline arguements returning them in a dict 
    """
    parser = argparse.ArgumentParser(        
        description="Automaticlly bumps the version.txt and push local commits to remote repository",
        # Allow multiline args help description
        formatter_class=argparse.RawTextHelpFormatter,)

    parser.add_argument(
        "-b", "--bump",
        type=lambda s: str(s).lower(),
        choices=('major', 'minor', 'patch'),
        help="Bump the current version by either: Major.Minor.Patch",
    )

    cmd_args = vars(parser.parse_args())

    return cmd_args


def update_version_txt(bump='patch'):
    """ 
    Attempt to bump the verion in the version.txt file

    params:
        bump - 'major', 'minor' or 'patch' 
    """
    try:
        with open('./version.txt', 'r') as versiontxt:
            verstr = versiontxt.readline()

        ver = verstr.split('.')
        if bump == 'major':
            ver[0] = int(ver[0]) + 1
        elif bump == 'minor':
            ver[1] = int(ver[1]) + 1
        elif bump == 'patch':
            ver[2] = int(ver[2]) + 1
        newverstr = str(ver[0]) + '.' + str(ver[1]) + '.' + str(ver[2])

    except (IndexError, ValueError, OSError):
        print("Could not find version string in ./version.txt")
        raise
    
    updatedfiles = []

    try:
        print(f'v{verstr} ->  Bump: {bump}  -> v{newverstr}')
        for root, dirs, files in os.walk("."):
            for file in files:
                if 'version.txt' == file:
                    # Get and save path to version.txt
                    path = os.path.join(root, file)
                    updatedfiles.append(path)

                    # Write new version to txt
                    with open(path, 'w') as versiontxt:
                        versiontxt.write(newverstr)
                        print(f' - updating {path}')
    except OSError as e:
        raise

    return updatedfiles


def get_bump_from_message(message, default_bump='none'):
    """ 
    Return the bump type from the passed in commit 
    message based on convensional commits

    params:
        message - Commmit message to be parsed
    """
    tags = {
        'patch': ['fix'],
        'minor': ['feat'],
        'major': ['breaking change', '!']
    }

    for bump, keywords in tags.items():
        for keyword in keywords:
            if keyword + ":" in message:
                return bump

    return default_bump

def ci():
    """ TODO: Any CI specific steps """
    pass


def main():
    # Fetch the latest commit message
    #   Under CLI this is only used to maintain the latest commit message
    #   Under CI this is used to decide the bump type (MAJOR.MINOR.PATCH) based on convensional commits
    local_branch = git('name-rev', '--name-only', 'HEAD')
    remote_branch= git('for-each-ref' '--format="%(upstream:short)"', '"$(git symbolic-ref -q HEAD)"')
    commit_messages = git('log' '{remote_branch}..{local_branch}')


    commitmessage = git('show', '-s', '--format=%s').strip().lower()

    # Until CI is implemented cmdline is always true
    cmdline = True

    # Get the bump version
    if cmdline:
        args = commandline()
        if args['bump']:
            bump = args['bump']
        else:
            bump = get_bump_from_message(commitmessage)
    else:
        bump = get_bump_from_message(commitmessage)

    # Update the version.txt
    updatedfiles = update_version_txt(bump)

    # Recommit and push up the changes
    try:
        for file in updatedfiles:
            git('add', file)
        if 'AutoSemVerBump' in commitmessage:
            git('commit', '-m', commitmessage)
        else:
            git('commit', '-m', commitmessage + ' - (AutoSemVerBump)')
        git('push')
    except subprocess.CalledProcessError as e:
        print(f'Could not push code up to repository:\n{str(e)}')
        return 1

    return 0

    
if __name__ == "__main__":
    sys.exit(main())
