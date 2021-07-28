import os
bump = "patch"

# Read Pat
def bumps():
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
        newverstr = "0.0.0"
        print(f"Could not find version string in ./version.txt, setting to default: {newverstr}")

    try:
        print(f'v{verstr} ->  Bump: {bump}  -> v{newverstr}')
        for root, dirs, files in os.walk("."):
            for file in files:
                if 'version.txt' == file:
                    path = os.path.join(root, file)
                    with open(path, 'w') as versiontxt:
                        print(f'\tupdating {path}')
                        versiontxt.write(newverstr)
    except OSError as e:
        raise



bumps()