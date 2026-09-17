# Robot Storage

How storage on the JetBot is set up, and the rules for where files go.

## Rule: images only on the USB stick

All camera images and image datasets are saved on the USB stick, never on the SD card.
Code, notebooks, and model weights (`*.pth`) stay on the SD card.

## Layout

| What | Where (host) | Where (inside Jupyter) |
|------|--------------|------------------------|
| USB stick | `/home/jetbot/usb` | `/workspace/usb` |
| Images and datasets | `/home/jetbot/usb/images/<notebook folder>/` | `/workspace/usb/images/<notebook folder>/` |
| Backups | `/home/jetbot/usb/backup/<date>/` | `/workspace/usb/backup/<date>/` |
| Repository | `/home/jetbot/jetbot` | `/workspace/jetbot` |

The existing notebooks save to relative folders such as `dataset`. Those folders are **symlinks** into the stick, so the notebooks work unchanged:

| Notebook folder | Symlink target |
|-----------------|----------------|
| `notebooks/collision_avoidance/dataset` | `../../../usb/images/collision_avoidance/dataset` |
| `notebooks/collision_avoidance/dataset.zip` | `../../../usb/images/collision_avoidance/dataset.zip` |
| `notebooks/road_following/dataset_xy` | `../../../usb/images/road_following/dataset_xy` |
| `notebooks/teleoperation/snapshots` | `../../../usb/images/teleoperation/snapshots` |

The symlinks are relative, so they resolve both on the host (`/home/jetbot/...`) and inside the Jupyter container (`/workspace/...`). They are gitignored and exist only on the robot.

### Adding a new image folder

For a notebook in `notebooks/<folder>/` that saves images to `<name>`:

```bash
mkdir -p ~/usb/images/<folder>/<name>
cd ~/jetbot/notebooks/<folder> && ln -s ../../../usb/images/<folder>/<name> <name>
```

Or use an absolute path in code: `/workspace/usb/images/<folder>/<name>`.

### Known caveat

`zip -r dataset.zip dataset` replaces the `dataset.zip` symlink with a regular file on the SD card, because `zip` writes a temp file and renames it. Delete the zip after downloading it, or create it on the stick directly:
`zip -r -q ../../../usb/images/collision_avoidance/dataset.zip dataset`.

## USB stick

- SanDisk Ultra 32 GB, exFAT, label `Niklas32GB`, UUID `6A78-691B`. It was not formatted, so it can still be read on a Mac/PC.
- exFAT driver: `exfat-fuse` and `exfat-utils` (installed with apt).
- Mounted at boot through `/etc/fstab` (backup of the old file: `/etc/fstab.bak-2026-09-16`):

  ```
  UUID=6A78-691B  /home/jetbot/usb  exfat  defaults,nofail,uid=1000,gid=1000,umask=022,x-systemd.device-timeout=15s,x-systemd.before=docker.service  0  0
  ```

  - `nofail`, `x-systemd.device-timeout=15s`: the robot still boots without the stick.
  - `x-systemd.before=docker.service`: the stick is mounted **before** Docker starts. The Jupyter container only sees mounts that exist when it starts (propagation `rprivate`).
- The empty mount point is locked with `chattr +i /home/jetbot/usb`. If the stick is not mounted, nothing can be written there, so images can never land on the SD card by accident. Notebooks fail with an error instead.

### If the stick was not mounted (plugged in after boot)

```bash
sudo mount /home/jetbot/usb
sudo docker restart jetbot_jupyter   # Jupyter only sees the stick after a restart
```

### Removing the stick safely

Stop data-collection notebooks first, then:

```bash
sync && sudo umount /home/jetbot/usb
```

### Checks

```bash
findmnt /home/jetbot/usb                                     # stick mounted?
sudo docker exec jetbot_jupyter ls /workspace/usb/images     # visible in Jupyter?
df -h / /home/jetbot/usb                                     # free space
```

## SD card

- 64 GB card (59.5 GB). The JetBot image created only a 24.4 GB root partition (`mmcblk0p1`, the last partition), leaving ~35 GB unused.
- Grow the root partition to the whole card with NVIDIA's script (online, no data moved):

  ```bash
  sudo /usr/lib/nvidia/resizefs/nvresizefs.sh -c   # prints "true" if supported
  sudo /usr/lib/nvidia/resizefs/nvresizefs.sh -m   # max size in MB (60891)
  sudo /usr/lib/nvidia/resizefs/nvresizefs.sh      # grow partition + filesystem
  df -h /                                          # should show ~59G
  ```

- Done on 2026-09-16: root is now 59 GB (23 GB used, 34 GB free).

- Keep the 4 GB swapfile (`/swfile`); training needs it with 4 GB RAM.
- Docker images (~4.6 GB) are both in use by the running containers (`jetbot_jupyter`, `jetbot_display`). Do not prune them.

## Housekeeping

- Claude Code keeps every downloaded version (~220 MB each) in `~/.local/share/claude/versions/`. Delete all except the one `readlink -f $(which claude)` points to.

## Backup

Before the migration on 2026-09-16, the collision-avoidance dataset, `dataset.zip`, `best_model.pth`, and `best_model_resnet18.pth` were copied to `/home/jetbot/usb/backup/2026-09-16/collision_avoidance/` and checked with sha256.

The stick is the only copy of the images. Copy important datasets to a laptop regularly.
