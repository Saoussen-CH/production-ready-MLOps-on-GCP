import components

get_workerpool_spec_op = components.get_workerpool_spec_op.python_func


def test_get_workerpool_spec_op():
    # Test data
    worker_pool_specs = [
        {"container_spec": {}},
        {"container_spec": {"args": ["existing_arg"]}},
        {
            "container_spec": {
                "env": [{"name": "existing_env", "value": "existing_val"}]
            }
        },
    ]
    args = {"arg1": "val1", "arg2": "val2"}
    hyperparams = {"hyperparam1": "val1", "hyperparam2": "val2"}
    env = {"env1": "val1", "env2": "val2"}

    # Call the function
    result = get_workerpool_spec_op(worker_pool_specs, args, hyperparams, env)

    # Assertions
    for spec in result:
        container_spec = spec["container_spec"]
        assert "args" in container_spec
        assert all(
            f"--{k.replace('_', '-')}={v}" in container_spec["args"]
            for k, v in args.items()
        )
        assert all(
            f"--{k.replace('_', '-')}={v}" in container_spec["args"]
            for k, v in hyperparams.items()
        )
        if "env" in container_spec:
            assert all(
                dict(name=k, value=v) in container_spec["env"] for k, v in env.items()
            )
