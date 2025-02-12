# %%

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from steering.gpu_graph import run
from steering.caa_test_open_ended import ALL_BEHAVIORS

import numpy as np

name = "0724_llama31"

commands = {}
dependencies = {}
port = 8000

# starts = list(np.round(np.arange(-0.2, 0.21, .04), 3))[7:]


for dataset in ["ab", "openr", "opencon", "caa", "abcon", "prompts"]:
    for behavior in ((ALL_BEHAVIORS + [None]) if dataset in ["ab", "openr"] else [None]):
        for layer in ["all", 15]:
            for logit in [False, True]:
                if logit and dataset not in ["ab", "abcon"]:
                    continue

                if logit and layer == 15:
                    continue

                cmd_suffix = f"--dataset {dataset} --model llama31"
                if behavior is not None:
                    cmd_suffix += f" --behavior {behavior}"
                if layer == "all":
                    cmd_suffix += " --residual"
                if logit:
                    cmd_suffix += " --logit"
                cmd = f"python steering/generate_vectors.py {cmd_suffix}"

                job_suffix = f"{dataset}_{behavior}_{layer}_{logit}"

                commands[f"gen_{job_suffix}"] = cmd
                dependencies[f"gen_{job_suffix}"] = []

                for leace in [None, "orth", "leace"]:
                    if logit and leace is not None:
                        continue
                    if layer == 15 and leace is not None:
                        continue

                    maxmult = {
                        "ab": 4,
                        "openr": 2,
                        "opencon": 1,
                        "caa": 1.5,
                        "abcon": 3,
                        "prompts": 1.5,
                    }[dataset]

                    if logit:
                        maxmult *= 4
                    if layer == 15:
                        maxmult *= 2.5

                    multstep = maxmult / 5

                    steer_suffix = f"{cmd_suffix} --layer {layer} --mults $(seq -{maxmult} {multstep} {maxmult})"
                    # NB: overwrite was originally unconditional
                    # if behavior is None:
                    #     steer_suffix += " --overwrite"
                    if leace is not None:
                        steer_suffix += f" --leace {leace}"
                    cmd = f"python steering/steer.py {steer_suffix}"
                    commands[f"steer_{job_suffix}_{leace}"] = cmd
                    dependencies[f"steer_{job_suffix}_{leace}"] = [f"gen_{job_suffix}"]

                    cmd = f"python steering/eval.py {steer_suffix} --port {port} --server"
                    commands[f"eval_{job_suffix}_{leace}"] = cmd
                    dependencies[f"eval_{job_suffix}_{leace}"] = [f"steer_{job_suffix}_{leace}"]
                    port += 1

print(f"Generated {len(commands)} commands")

# %%

for job in commands:
    commands[job] += f" > logs/{name}_{job}.log 2> logs/{name}_{job}.err"

if __name__ == "__main__":
    # usage: python run_whatever.py 1,2,3,4,5,6,7
    if len(sys.argv) == 1:
        # default to all GPUs
        gpus = list(range(8))
    else:
        gpus = [int(gpu) for gpu in sys.argv[1].split(",")]

    for job in commands:
        print(f"{job}: {commands[job]} <-- {dependencies[job]}")
    print()
    print(f"Running on GPUs: {gpus}")

    run(gpus, commands, dependencies)