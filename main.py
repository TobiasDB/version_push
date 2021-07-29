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

    parser.add_argument(
        "-np", "--no-push",
        help="If flag is passed the WILL BE versioned and committed but WILL NOT push (if no other flags are passed) ", 
        action='store_false'
    )

    parser.add_argument(
        "-nb", "--no-bump",
        help="If flag is passed changes WILL BE committed and pushed but WILL NOT versioned (if no other flags are passed) ", 
        action='store_false'
    )

    cmd_args = vars(parser.parse_args())

    return cmd_args


def update_version_txt(bump):
    """ 
    Attempt to bump the verion in the version.txt file

    params:
        bump - 'major', 'minor' or 'patch' 
    """
    updated_files = []

    try:
        with open('./version.txt', 'r') as versiontxt:
            verstr = versiontxt.readline()

        ver = verstr.split('.')
        ver[0] = int(ver[0]) + bump['major']
        ver[1] = int(ver[1]) + bump['minor']
        ver[2] = int(ver[2]) + bump['patch']
        newverstr = str(ver[0]) + '.' + str(ver[1]) + '.' + str(ver[2])
    except (IndexError, ValueError, OSError):
        print("Could not find version string in ./version.txt")
        raise
    
    # Output any change in version
    print(f'v{verstr} ->  Bump: {bump}  -> v{newverstr}')

    # Check if the version has changed to see if the files need to be updated
    if newverstr == verstr:
        return updated_files

    try:
        for root, dirs, files in os.walk("."):
            for file in files:
                if 'version.txt' == file:
                    # Get and save path to version.txt
                    path = os.path.join(root, file)
                    updated_files.append(path)

                    # Write new version to txt
                    with open(path, 'w') as versiontxt:
                        versiontxt.write(newverstr)
                        print(f' - updating {path}')
    except OSError as e:
        raise

    return updated_files


def get_bumps_from_messages(messages):
    """ 
    Return the bump type from the passed in commit 
    message based on convensional commits

    params:
        message - Commmit message to be parsed
    """
    tags = {
        'major': ['breaking change', '!'],
        'minor': ['feat'],
        'patch': ['fix'],
    }
    bump = {'major': 0, 'minor':0, 'patch':0}
    for message in messages:
        for bump_type, keywords in tags.items():
            message_done = False
            for keyword in keywords:
                if keyword + ":" in message:
                    bump[bump_type] += 1
                    message_done = True
                    break
            if message_done:
                break
    return bump


def ci():
    """ TODO: Any CI specific steps """
    pass


def main():
    # Get the commit messages

    # Get the name of the local branch
    local_branch = git('name-rev', '--name-only', 'HEAD').strip().replace('\n', '')

    # Get the name of the git head
    git_head = git('symbolic-ref', '-q', 'HEAD').strip().replace('\n', '')

    # Get the name of the remote branch
    remote_branch= git('for-each-ref', '--format=%(upstream:short)', git_head).strip().replace('\n', '')

    # Get the commits not yet pushed up to the remote
    commits = git('log', f'{remote_branch}..{local_branch}')

    # Extract only the commit messages from the commits
    commit_messages = [item.strip().lower() for i, item in enumerate(commits.split('\n\n')) if i % 2 ==1]

    # Get them to get them in the correct chronological order
    commit_messages.reverse() 

    print(f'Found {len(commit_messages)} on local branch ({local_branch}) not pushed to remote ({remote_branch})')
    [print(" - " + message) for message in commit_messages]

    # Until CI is implemented cmdline is always true
    cmdline = True
    bump = {'major': 0, 'minor':0, 'patch':0}
    push = True
    shouldBump = True
    # Get the bump version
    if cmdline:
        args = commandline()
        push = args['no_push']
        shouldBump = args['no_bump']
        if args['bump']:
            bump[args['bump']] = 1
        else:
            bump = get_bumps_from_messages(commit_messages)
    else:
        bump = get_bumps_from_messages(commit_messages)

    # Update the version.txt
    updated_files = []
    if shouldBump:
        updated_files = update_version_txt(bump)

    # Recommit and push up the changes
    try:
        for file in updated_files:
            git('add', file)
        if (len(updated_files)):
            last_message = commit_messages[len(commit_messages)-1]
            if 'version bump' in last_message:
                git('commit', '-m', last_message)
            else:
                git('commit', '-m', last_message + ' - (version bump)')
        if push:
            git('push')
    except subprocess.CalledProcessError as e:
        print(f'Could not push code up to repository:\n{str(e)}')
        return 1

    return 0

    
if __name__ == "__main__":
    sys.exit(main())
