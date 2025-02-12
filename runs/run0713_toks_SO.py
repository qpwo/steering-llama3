from gpu_graph import run
import sys

name = "0713toks"

commands = {}
port = 8000

for dataset in ["abcon"]:
    for leace in [None, "leace", "orth"]:
        for shift in [0, .1]:
            cmd = f"python steer.py --dataset {dataset} --mults $(seq {-2+shift} .2 2) --layer all --residual --logit"
            if leace is not None:
                cmd += f" --leace {leace}"
            commands[f"steer_{dataset}_{leace}_{shift}"] = cmd

            cmd = f"python eval.py --dataset {dataset} --mults $(seq {-2+shift} .2 2) --layer all --residual --logit --port {port} --server"
            if leace is not None:
                cmd += f" --leace {leace}"
            commands[f"eval_{dataset}_{leace}_{shift}"] = cmd
            port += 1

for dataset in ["ab"]:
    for toks in ["before", "after"]:
        cmd = f"python steer.py --dataset {dataset} --mults $(seq -4 .4 4)"
        if toks is not None:
            cmd += f" --toks {toks}"
        commands[f"steer_{dataset}_{toks}"] = cmd

        cmd = f"python eval.py --dataset {dataset} --mults $(seq -4 .4 4) --port {port} --server"
        if toks is not None:
            cmd += f" --toks {toks}"
        commands[f"eval_{dataset}_{toks}"] = cmd
        port += 1

        cmd = f"python steer.py --dataset {dataset} --mults $(seq -2 .2 2) --residual --layer all"
        if toks is not None:
            cmd += f" --toks {toks}"
        commands[f"steer_res_{dataset}_{toks}"] = cmd

        cmd = f"python eval.py --dataset {dataset} --mults $(seq -2 .2 2) --residual --layer all --port {port} --server"
        if toks is not None:
            cmd += f" --toks {toks}"
        commands[f"eval_res_{dataset}_{toks}"] = cmd
        port += 1


for dataset in ["opencon", "openr"]:
    for toks in [None]:
        cmd = f"python steer.py --dataset {dataset} --mults $(seq -2 .2 2) --residual --layer all"
        # if leace is not None:
        #     cmd += f" --leace {leace}"
        commands[f"steer_res_{dataset}_{toks}"] = cmd

        cmd = f"python eval.py --dataset {dataset} --mults $(seq -2 .2 2) --residual --layer all --port {port} --server"
        # if leace is not None:
        #     cmd += f" --leace {leace}"
        commands[f"eval_res_{dataset}_{toks}"] = cmd
        port += 1

dependencies = {job: [] for job in commands}

for job in commands:
    if job.startswith("eval_"):
        dependencies[job].append(f"steer_{job[5:]}")

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