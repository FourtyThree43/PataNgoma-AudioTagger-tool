import yaml


def load_config():
    """
    Load the configuration data for the APIs from a YAML file.

    :return: A dictionary containing the configuration data.
    """
    config_file = "config.yaml"

    with open(config_file, "r") as f:
        config_data = yaml.safe_load(f)

    return config_data


if __name__ == '__main__':
    # Load the configuration data
    config = load_config()

    # Create instances of the MusicBrainAPI and SpotifyAPI classes using the configuration
    mb_api = MusicBrainAPI(app_name=config["MusicBrainAPI"]["app_name"],
                           app_version=config["MusicBrainAPI"]["app_version"],
                           app_contact=config["MusicBrainAPI"]["app_contact"])
    sp_api = SpotifyAPI(client_id=config["SpotifyAPI"]["client_id"],
                        client_secret=config["SpotifyAPI"]["client_secret"])
