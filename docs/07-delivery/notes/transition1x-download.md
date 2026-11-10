---
status: reviewed
confidence: high
last_verified: 2026-11-10
depends_on: [../14-g4-plan.md]
---

# Transition1x download instructions

## Bottom line

- One file, `Transition1x.h5`, 6,623,929,000 bytes (6.62 GB), MD5 `faab0413cf6b042b6d50e6272dea9a8c`, MIT-licensed.
- Download from `https://ndownloader.figshare.com/files/36035789` with `wget -c` (resumable).
- Put it on ext4 (`~/npa-work/data/`), not on `/mnt/d` if you can avoid it.
- Verify the byte count and MD5 before using it. A truncated HDF5 may still open.
- After download, slice a smaller file with `code/g4_slice.py` for CPU iteration.

> **In plain words.** You are downloading a single 6.6 GB HDF5 file that holds 10,073
> reactions and 9.6 million molecular configurations at the ωB97x/6-31G(d) level. The
> file is the whole dataset; there is nothing to unzip. The download is the only
> manual step — everything else (loading, training, slicing) is code.

## Before you start

Check free space:

```bash
df -h ~/npa-work
```

Keep at least 20 GB free: 6.62 GB for the download, plus room for a small slice and
the runs. Check that `wget` exists (`command -v wget`); if not, use `curl`.

## Download

```bash
mkdir -p ~/npa-work/data
cd ~/npa-work/data
wget -c -O Transition1x.h5 "https://ndownloader.figshare.com/files/36035789"
```

`-c` resumes a partial file. If the download stops, run the exact same command
again; it continues from where it left off. If `wget` is unavailable:

```bash
curl -L -C - -o Transition1x.h5 "https://ndownloader.figshare.com/files/36035789"
```

For a long download, run it in the background and watch the log:

```bash
nohup wget -c -O Transition1x.h5 \
  "https://ndownloader.figshare.com/files/36035789" > download.log 2>&1 &
tail -f download.log
```

`Ctrl-C` only stops the watcher; the download keeps running. To stop the download,
`pkill -f 'wget -c -O Transition1x.h5'`.

## Verify

```bash
cd ~/npa-work/data
stat -c '%s %n' Transition1x.h5
# 6623929000 Transition1x.h5
md5sum Transition1x.h5
# faab0413cf6b042b6d50e6272dea9a8c  Transition1x.h5
```

`md5sum` on 6.6 GB takes a few minutes. Do not skip it; a truncated HDF5 may still
open.

Open the file with h5py (use the repo venv):

```bash
cd /mnt/d/dev/ai/experiments/npa
.venv/bin/python - <<'PY'
import h5py
p = "/home/<user>/npa-work/data/Transition1x.h5"
with h5py.File(p, "r") as f:
    print("top-level:", list(f.keys()))
    print("formulas:", len(f["data"]))
    print("test formulas:", list(f["test"].keys()))
PY
```

Expected: top-level `['data', 'train', 'val', 'test']`; `data` has 170 formula
groups; `test` has the 8 held-out formulas.

## After the download

Slice a smaller file for CPU iteration:

```bash
cd /mnt/d/dev/ai/experiments/npa
.venv/bin/python code/g4_slice.py \
  --input ~/npa-work/data/Transition1x.h5 \
  --output ~/npa-work/data/Transition1x_small.h5
```

## Do not

- Do not download the file inside an agent or commit it to the repo.
- Do not put it in `data/` on `/mnt/d` unless you have checked the free space and
  the drvfs speed; the ext4 path is better.
- Do not trust a partial file; verify the MD5 and the byte count.

## Sources

1. Figshare API, article 19614657 v4, `https://api.figshare.com/v2/articles/19614657`,
   retrieved 2026-11-10.
2. T1x `download_t1x.py`, `https://gitlab.com/matschreiner/T1x/-/raw/main/download_t1x.py`,
   retrieved 2026-11-10.
3. T1x `transition1x/dataloader.py`, `https://gitlab.com/matschreiner/T1x/-/raw/main/transition1x/dataloader.py`,
   retrieved 2026-11-10.
4. T1x `scripts/combine_dbs.py`, `https://gitlab.com/matschreiner/T1x/-/raw/main/scripts/combine_dbs.py`,
   retrieved 2026-11-10.
