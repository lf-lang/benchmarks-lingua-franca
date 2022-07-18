#!/usr/bin/env python3

import csv
import os
import signal
import time
import hydra
import logging
import multiprocessing
import numpy as np
import omegaconf
import subprocess
from queue import Empty, Queue
from threading import Thread


log = logging.getLogger("run_benchmark")


@hydra.main(config_path="conf", config_name="default")
def main(cfg):
    # some aliases for convenience
    benchmark = cfg["benchmark"]
    target = cfg["target"]
    benchmark_name = benchmark["name"]
    target_name = target["name"]
    continue_on_error = cfg["continue_on_error"]
    test_mode = cfg["test_mode"]

    # initialize the thread number if not specified
    if cfg["threads"] is None:
        cfg["threads"] = multiprocessing.cpu_count()

    # a function for resolving 'args:' in the configuration. We need the
    # closure here in order to have access to 'cfg'
    def resolve_args(config_key):
        # lookup the specified arguments in the configuration tree
        cfg_args = cfg
        for key in config_key.split("."):
            cfg_args = cfg_args[key]

        res = []
        if cfg_args is None:
            return res

        params = benchmark["params"]
        for k, v in cfg_args.items():
            value = str(params[k])
            for i in v:
                res.append(i.replace("<value>", value))

        return res

    # register the resolver for 'args:'
    omegaconf.OmegaConf.register_new_resolver("args", resolve_args, replace=True)

    log.info(f"Running {benchmark_name} using the {target_name} target.")



    # perform some sanity checks
    if "validation_alias" in target:
        target_validation_name = target["validation_alias"]
    else:
        target_validation_name = target_name

    if target_validation_name not in benchmark["targets"]:
        log.warning(f"target {target_name} is not supported by the benchmark {benchmark_name}")
        return

    if not check_benchmark_target_config(benchmark, target_validation_name):
        if continue_on_error:
            return
        else:
            raise RuntimeError("Aborting because an error occurred")

    # prepare the benchmark
    for step in ["prepare", "copy", "gen", "compile"]:
        if target[step] is not None:
            _, code = execute_command(target[step])
            if not check_return_code(code, continue_on_error):
                return

    # run the benchmark
    if target["run"] is not None:
        cmd = omegaconf.OmegaConf.to_object(target["run"])
        if test_mode:
            # run the command with a timeout of 1 second. We only want to test
            # if the command executes correctly, not if the full benchmark runs
            # correctly as this would take too long
            _, code = execute_command(["timeout", "1"] + cmd, 2)
            # timeout returns 124 if the command executed correctly but the
            # timeout was exceeded
            if code != 0 and code != 124:
                raise RuntimeError(
                    f"Command returned with non-zero exit code ({code})"
                )
        else:
            output, code = execute_command(cmd, cfg["timeout"], cfg["passwordless_sudo"] if "passwordless_sudo" in cfg else False)
            if code == 124:
                log.error(f"The command \"{' '.join([str(word) for word in cmd])}\" timed out.")
            check_return_code(code, continue_on_error)
            times = hydra.utils.call(target["parser"], output)
            times += [np.infty] * (cfg["iterations"] - len(times))
            write_results(times, cfg)
    else:
        raise ValueError(f"No run command provided for target {target_name}")


def check_return_code(code, continue_on_error):
    if code != 0:
        if continue_on_error:
            log.error(
                f"Command returned with non-zero exit code ({code})"
            )
        else:
            raise RuntimeError(
                f"Command returned with non-zero exit code ({code})"
            )
    return code == 0

def check_benchmark_target_config(benchmark, target_name):
    benchmark_name = benchmark["name"]
    # keep a list of all benchmark parameters
    bench_params = list(benchmark["params"].keys())

    # collect all parameters used in target command arguments
    used_params = set()
    target_cfg = benchmark["targets"][target_name]
    for arg_type in ["gen_args", "compile_args", "run_args"]:
        if arg_type in target_cfg and target_cfg[arg_type] is not None:
            for param in target_cfg[arg_type].keys():
                if param not in bench_params:
                    log.error(f"{param} is not a parameter of the benchmark!")
                    return False
                used_params.add(param)

    for param in bench_params:
        if param not in used_params:
            log.warning(f"The benchmark parameter {param} is not used in any command")

    return True


def command_to_list(command):
    # the command can be a list of lists due to the way we use an omegaconf
    # resolver to determine the arguments. We need to flatten the command list
    # first. We also need to touch each element individually to make sure that
    # the resolvers are called.
    cmd = []
    for i in command:
        if isinstance(i, list) or isinstance(i, omegaconf.listconfig.ListConfig):
            cmd.extend(i)
        else:
            cmd.append(str(i))
    return cmd


def enqueue_output(out, queue):
    while True:
        line = out.readline()
        queue.put(line)
        if not line:
            break
    out.close()


def execute_command(command, timeout=None, passwordless_sudo=False):
    cmd = command_to_list(command)
    cmd_str = " ".join(cmd)
    log.info(f"run command: {cmd_str}")
    # run the command while printing and collecting its output
    output = []
    with subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, text=True
    ) as process:
        q = Queue()
        t = Thread(target=enqueue_output, args=(process.stdout, q))
        t.daemon = True
        t.start()
        cmd_log = logging.getLogger(command[0])
        try:
            line = q.get(timeout=timeout)
            while line:
                line = q.get(timeout=timeout)
                output.append(line)
                cmd_log.info(line.rstrip())
            code = process.wait(timeout=timeout)
        except (Empty, subprocess.TimeoutExpired):
            cmd_log.error(f"{cmd_str} timed out.")
            completed_stacktrace = None
            cmd_log.info("We may need to ask you for sudo access in order to get a stacktrace.")
            completed_stacktrace = subprocess.run(
                ["sudo", "eu-stack", "-p", str(process.pid)],
                capture_output=True
            )
            process.kill()
            if completed_stacktrace.returncode != 0:
                cmd_log.error("Failed to debug the timed-out process.")
            for line in (
                completed_stacktrace.stdout.decode().splitlines()
                + completed_stacktrace.stderr.decode().splitlines()
            ):
                cmd_log.error(line)
            return (output, 124)

    return output, code


def write_results(times, cfg):
    row = {
        "benchmark": cfg["benchmark"]["name"],
        "target": cfg["target"]["name"],
        "total_iterations": cfg["iterations"],
        "threads": cfg["threads"],
        "iteration": None,
        "time_ms": None,
    }
    # also add all parameters and their values
    row.update(cfg["benchmark"]["params"])
    if "params" in cfg["target"]:
        row.update(cfg["target"]["params"])

    with open("results.csv", "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=row.keys())
        writer.writeheader()
        i = 0
        for t in times:
            row["iteration"] = i
            row["time_ms"] = t
            writer.writerow(row)
            i += 1


if __name__ == "__main__":
    main()
