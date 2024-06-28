from kfp.dsl import  component

@component(base_image="python:3.10.14")
def get_workerpool_spec_op(
    worker_pool_specs: list,
    args: dict = {},
    env: dict = {},
) -> list:

    for spec in worker_pool_specs:
        if "args" not in spec["container_spec"]:
            spec["container_spec"]["args"] = []
        for k, v in args.items():
            spec["container_spec"]["args"].append(f"--{k.replace('_', '-')}={v}")
        if env:
            if "env" not in spec["container_spec"]:
                spec["container_spec"]["env"] = []
            for k, v in env.items():
                spec["container_spec"]["env"].append(dict(name=k, value=v))

    return worker_pool_specs