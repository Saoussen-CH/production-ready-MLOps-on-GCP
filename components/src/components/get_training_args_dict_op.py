from kfp.dsl import Input, component, Dataset


@component(base_image="python:3.10.14")
def get_training_args_dict_op(
    train_data: Input[Dataset],
    valid_data: Input[Dataset],
    test_data: Input[Dataset],
    hypertune: bool,
) -> dict:
    return dict(
        train_data=train_data.path,
        valid_data=valid_data.path,
        test_data=test_data.path,
        hypertune=hypertune,
    )
