---
name: mlspace-jobs
description: Common mls CLI commands for managing MLSpace Jobs.
---

# MLSpace Jobs — Command Reference

This skill is for users who already have `mls` installed and configured. It provides direct guidance on common job operations without walking through initial setup.

## Common Commands

### Monitor Jobs

```bash
# List recent jobs
mls job table --limit 10

# Check specific job status
mls job status <job-id>
```

Web UI is also available at: https://console.cloud.ru/spa/mlspace/env-jobs/jobs

### View Logs

```bash
# Save logs to a tmp file first (output can be very large and consume many tokens)
mls job logs <job-id> > /tmp/job_logs_<job-id>.txt

# Then read only the relevant portion (e.g. tail for recent output)
tail -100 /tmp/job_logs_<job-id>.txt

# Stream logs in real-time (must be user-run, blocks until Ctrl+C)
mls job logs -w <job-id>
```

### Wait for a Job to Finish

```bash
# Block until the job completes (exit 0 on success, 1 on failure)
mls job wait <job-id>

# Custom poll interval (in seconds, default varies)
mls job wait <job-id> -i 30
```

### Kill a Job

```bash
mls job kill <job-id>
```

## Multi-GPU Training with Accelerate

When using `accelerate` for multi-GPU training, the job config must have:
```yaml
processes_per_worker: 1
n_workers: 1
```

This is because `accelerate` handles multi-process spawning internally. If MLSpace also spawns multiple processes, they will conflict. Let `accelerate launch` manage the GPU distribution.

Also use `shm_size_class: large` with the `binary_exp` template — multi-GPU training with DataLoader workers requires substantial shared memory.

## Troubleshooting

### Segfault

The most common cause is a mismatch between CUDA/Python versions in the conda environment and the base Docker image used by the job. Ask the user to check:
- The `image` field in their job YAML
- Their PyTorch install command (which CUDA index URL they used)
- Whether they're using `--cuda 12.6.0` in environment creation but a different CUDA in the image

### "No space left on device" from DataLoader

This is a shared memory (`/dev/shm`) issue, not actual disk space. Fix:
1. Use the `binary_exp` template: `mls job yaml binary_exp > run.yaml`
2. Add `shm_size_class: large` to the YAML

### Unknown Errors

Suggest SSH-ing into the running job for interactive debugging:
> Follow the official guide: https://cloud.ru/docs/aicloud/mlspace/concepts/guides/guides__cli/environments__cli-ssh-connect
