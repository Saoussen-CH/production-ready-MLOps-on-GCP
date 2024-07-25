import components

get_training_args_dict_op = components.get_training_args_dict_op.python_func


class MockDataset:
    def __init__(self, path):
        self.path = path


def test_get_training_args_dict_op():
    # Test data
    train_data = MockDataset("train_data_path")
    valid_data = MockDataset("valid_data_path")
    test_data = MockDataset("test_data_path")
    hypertune = True

    # Call the function
    result = get_training_args_dict_op(train_data, valid_data, test_data, hypertune)

    # Assertions
    assert result == {
        "train_data": "train_data_path",
        "valid_data": "valid_data_path",
        "test_data": "test_data_path",
        "hypertune": True,
    }
