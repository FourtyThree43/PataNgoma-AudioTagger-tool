import toml

def get_app_info(file_path):
    # Load the toml file
    data = toml.load(file_path)

    # Get the application name and version
    app_name = data.get('project', {}).get('name')
    app_version = data.get('project', {}).get('version')

    return app_name, app_version

# Usage
file_path = 'pyproject.toml'  # replace with your file path
name, version = get_app_info(file_path)
print(f'Application Name: {name}, Version: {version}')

