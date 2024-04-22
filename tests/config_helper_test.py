from app.helpers.config_helper import save_config, load_config


def test_save_config_saves_given_config_to_file(mocker):
    mock_file = mocker.mock_open()
    config = {"key": "value"}

    mocker.patch("builtins.open", mock_file)
    save_config("config.json", config)

    assert mock_file().write.call_count > 0
    written_content = "".join(call[0][0] for call in mock_file().write.call_args_list)
    assert written_content == '{"key": "value"}'


def test_load_config_returns_config_from_file(mocker):
    mock_file = mocker.mock_open(read_data='{"key": "value"}')

    mocker.patch("builtins.open", mock_file)
    config = load_config("config.json")

    assert config == {"key": "value"}


def test_load_config_returns_empty_dict_when_file_not_found(mocker):
    mock_file = mocker.mock_open()
    mock_file.side_effect = FileNotFoundError()

    mocker.patch("builtins.open", mock_file)
    config = load_config("config.json")

    assert config == {}


def test_load_config_returns_empty_dict_when_json_invalid(mocker):
    mock_file = mocker.mock_open(read_data="invalid json")

    mocker.patch("builtins.open", mock_file)
    config = load_config("config.json")

    assert config == {}
