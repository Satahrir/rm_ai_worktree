from rm_ref.core.algorithm import Algorithm
from rm_ref.core.config import TestcaseConfig
from rm_ref.core.errors import AlgorithmExecutionError, ConfigError
from rm_ref.core.lifecycle import prepare_run
from rm_ref.core.pipeline import execute_pipeline
from rm_ref.core.result import build_run_result


def _algorithm_name(algorithm):
    return algorithm.__class__.__name__


def run_config(cfg, algorithm):
    if not isinstance(cfg, TestcaseConfig):
        raise ConfigError(
            "cfg must be TestcaseConfig, got {0!r}".format(cfg)
        )
    if not isinstance(algorithm, Algorithm):
        raise ConfigError(
            "algorithm must be Algorithm, got {0!r}".format(algorithm)
        )

    rm_ctx = prepare_run(cfg)
    try:
        execute_pipeline(rm_ctx, algorithm)
    except AlgorithmExecutionError as exc:
        return build_run_result(
            rm_ctx,
            _algorithm_name(algorithm),
            exc.original_exception,
        )
    return build_run_result(rm_ctx, _algorithm_name(algorithm))
