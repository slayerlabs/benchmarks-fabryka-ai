"""Sample GPU utilisation/memory (nvidia-smi) and CPU utilisation (/proc/stat) every 2 s until killed.

python benchmarks/blimp/sample_gpu.py <out.csv>      # lines: unix_time,gpu_util_%,gpu_mem_MiB,cpu_util_%
python benchmarks/blimp/sample_gpu.py --podsumuj <out.csv>   # JSON: mean GPU util, max GPU memory, mean CPU util
"""
import json
import subprocess
import sys
import time


def cpu_czasy():
    with open("/proc/stat") as f:
        v = [int(x) for x in f.readline().split()[1:]]
    return sum(v), v[3] + v[4]  # total, idle + iowait


def podsumuj(wiersze):
    """[(t, gpu_util, gpu_mem, cpu_util)] -> summary; empty input -> None values."""
    if not wiersze:
        return {"gpu_util_sr": None, "gpu_mem_max_MiB": None, "cpu_util_sr": None, "probek": 0}
    n = len(wiersze)
    return {"gpu_util_sr": round(sum(w[1] for w in wiersze) / n, 1), "gpu_mem_max_MiB": max(w[2] for w in wiersze),
            "cpu_util_sr": round(sum(w[3] for w in wiersze) / n, 1), "probek": n}


def main():
    if sys.argv[1] == "--podsumuj":
        w = [tuple(float(x) for x in l.split(",")) for l in open(sys.argv[2]) if l.strip()]
        print(json.dumps(podsumuj(w)))
        return
    out = open(sys.argv[1], "a", buffering=1)
    t0, i0 = cpu_czasy()
    while True:
        time.sleep(2)
        t1, i1 = cpu_czasy()
        cpu = 100.0 * (1 - (i1 - i0) / max(t1 - t0, 1))
        t0, i0 = t1, i1
        g = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used", "--format=csv,noheader,nounits"],
                           capture_output=True, text=True).stdout.split("\n")[0].split(",")
        out.write(f"{time.time():.0f},{float(g[0])},{float(g[1])},{cpu:.1f}\n")


if __name__ == "__main__":
    main()
