import json


def parse_manifest(filename, content) -> list:
    """
    Returns a list of (ecosystem, package_name) tuples.

    """

    if filename == 'package.json':
        data = json.loads(content)
        deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
        packages = [("npm", pkg) for pkg in deps.keys()]
        return packages

    elif filename.endswith(('.txt', '.in')):
        packages = []
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                pkg_name = line.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0].strip()
                if pkg_name:
                    packages.append(("PyPI", pkg_name))
        return packages

    return None
