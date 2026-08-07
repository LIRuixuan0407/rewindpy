# Report-generation performance

`benchmarks/report_benchmark.py` measures the Python-side cost of normalizing report data, computing the integrity digest, serializing JSON, and writing the self-contained HTML file.

Run the default benchmark:

```bash
python benchmarks/report_benchmark.py --events 5000 --files 4 --iterations 3
```

Machine-readable output:

```bash
python benchmarks/report_benchmark.py --events 5000 --json
```

CI uses deliberately generous limits:

```bash
python benchmarks/report_benchmark.py \
  --events 5000 \
  --files 4 \
  --iterations 2 \
  --max-seconds 12 \
  --max-html-mb 20
```

These limits are regression guards, not speed claims. Benchmark results depend on Python version, CPU, filesystem, captured values, source size, and event complexity. Use the same command and environment when comparing revisions.
