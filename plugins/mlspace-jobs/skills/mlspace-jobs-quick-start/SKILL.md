---
name: mlspace-jobs-quick-start
description: Interactive, step-by-step first-time MLSpace Jobs setup — create a conda environment, install and configure the mls CLI, and submit + monitor your first job. Explicit-only: launch it deliberately with /mlspace-jobs-quick-start when setting up MLSpace from scratch. Once mls is configured, use the mlspace-jobs skill for day-to-day work, or mlspace-jobs-scaffold to generate experiments-as-code launchers.
disable-model-invocation: true
---

# MLSpace Jobs — Interactive Quick Start

This skill is an interactive walkthrough. Do NOT dump all steps at once. Walk the user through one step at a time, asking for input when needed (e.g. credentials, environment name). Only move to the next step after the current one succeeds.

IMPORTANT: Track progress with tasks. At the START of the walkthrough, use `TaskCreate` to create a task for each step (e.g. "Step 1: Create Conda Environment", "Step 2: Set Environment Variables", etc.). Use `TaskUpdate` to mark each step as `completed` when it finishes. This prevents losing track of progress. NEVER skip ahead to the summary/next-steps section until ALL numbered steps are marked completed.

IMPORTANT: Be proactive after user output. When the user shares command output or says they ran a command, immediately acknowledge the result and proceed to the next step with the specific command to run. The user should NEVER need to ask "what's next?" — the walkthrough must flow automatically. At the end of EVERY message, give the user the exact next command to run.

IMPORTANT: Do NOT run mutating commands yourself. Instead, tell the user what command to run and ask them to execute it via `! <command>`. This lets them see the output directly and interrupt long-running commands. However, you MAY run read-only commands yourself for gathering info. Here's the split:
- **OK to run yourself** (read-only): `mls configure region`, `mls job instance_types`, `mls job table`, `mls job status`, `mls job logs` (without -w), `which mls`, `df -h`, `cat`, `conda env list`
- **Must be user-run** (via `! ...`): `mls configure`, `mls job yaml`, `mls job submit`, `mls job kill`, `mls job logs -w`, `pip install`, `conda` create/activate/deactivate, `mlspace environments create`

IMPORTANT: All commands that depend on the conda environment MUST be run via `conda run -n <env_name> <command>` (e.g. `conda run -n my_env mls job submit -c run.yaml`). This ensures the correct environment is used without requiring activation. The `<env_name>` is the environment name from Step 1.

IMPORTANT: Be proactive — before walking the user through an installation step, CHECK if the tool/package is already installed by running a quick verification command yourself. For example, check `conda run -n <env_name> which mls` before suggesting mls install. Skip steps that are already satisfied and tell the user what you found. However, when skipping steps because the environment already exists, still verify Step 2 (HF_HOME) independently — an existing environment does not mean environment variables are configured.

## Step 1: Create a Conda Environment

Ask the user what they want to name their environment (suggest `jobs_demo` as default).

Then run:

```bash
mlspace environments create --env "<ENVIRONMENT_NAME>" -p 3.12 --cuda 12.6.0
```

After it completes, activate it:

```bash
conda activate "<ENVIRONMENT_NAME>"
```

## Step 2: Set Environment Variables

### HuggingFace cache

Before setting HF_HOME, check available disk space on mounted volumes to help the user choose the best location. Run:

```bash
df -h | grep -E '(/workspace-|/mnt/)' | grep -v '/mnt/s3' | sort -k4 -h -r
```

Never suggest `/mnt/s3` — it is not suitable for HF_HOME.

Show the user the results and suggest placing HF_HOME on the mount with the most free space (prefer `/workspace-*` and `/mnt/*` mounts). Ask the user to confirm or pick a different path. If no suitable mounts are found, skip setting HF_HOME entirely (leave it at its default). Then run:

```bash
conda env config vars set HF_HOME=<chosen-path>/.cache/huggingface
```

### Reactivate to apply vars

```bash
conda deactivate
conda activate "<ENVIRONMENT_NAME>"
```

## Step 3: Install and Configure `mls` CLI

### Install

First, proactively check if `mls` is already installed:
```bash
conda run -n <env_name> which mls
```
If found, also check if it's configured:
```bash
conda run -n <env_name> mls configure region
```
If both succeed, skip to Step 4b and tell the user mls is already installed and configured (mention the region).

If not installed, ask the user to run:
```bash
! conda run -n <env_name> pip install --force git+https://gitverse.ru/mrsndmn/mls@master
```

### Configure

Tell the user you're about to run `mls configure`, which will ask for 4 credentials interactively. Walk them through where to find each one BEFORE running the command:

1. **Key ID** and **Key Secret**:
   > Go to https://console.cloud.ru/profile/apiKeys
   > If you don't have an API key yet, create one. Copy the Key ID and Key Secret.

2. **x-workspace-id** and **x_api_key**:
   > Go to https://console.cloud.ru/spa/mlspace/profile/review
   > Find your workspace, click the three-dot menu (⋮), then "Developer Settings" (Параметры разработчика).
   > Copy the workspace ID and API key from there.

3. **Region**: the user will need to enter their region when prompted. After configuration, verify the configured region by running:
   ```bash
   mls configure region
   ```
   This command prints the currently configured region (e.g. `SR004`, `SR008`).

4. **Everything else**: just press Enter to accept defaults.

Once the user confirms they have the credentials ready, ask them to run:

```bash
! conda run -n <env_name> mls configure
```

This is interactive — the user will need to paste values into the prompts.

After configuration, verify the region:
```bash
conda run -n <env_name> mls configure region
```

## Step 4: Job Description Tags

Before creating the job config, ask the user for two things:

1. **Username** (required) — their short name for the job description `#username` tag (e.g. `ivanov`, `j.smith`). This is used to identify who launched the job.
2. **Telegram nick** (required) — their Telegram `@handle` for job notification mentions (e.g. `@ivanov`). Job status notifications are sent to a Telegram chat. If the user is not yet in the notifications chat, tell them to ask their teamlead to add them.

These will be used in the job description field, e.g.:
```
description: "my_experiment #<username> @<telegram_nick>"
```
(You can append any project/team tags your group uses after these, e.g. `#myteam`.)

## Step 5: Create a Job Config

Before generating the config, explore the current environment so you can set the right instance type:

1. Check the configured region:
   ```bash
   conda run -n <env_name> mls configure region
   ```
   This prints the region code (e.g. `SR004`, `SR008`). Tell the user which region they're configured for.

2. List available instance types and their availability:
   ```bash
   conda run -n <env_name> mls job instance_types
   ```
   This prints a table of all instance types in the current region with columns: type name, available count, and description (GPU model, GPU count, CPU cores, RAM). Show the table to the user and explain what the columns mean. Highlight which instance types actually have availability (count > 0).

3. Generate a starter YAML config — ask the user to run this themselves since it writes a file:
   ```bash
   ! conda run -n <env_name> mls job yaml binary > run.yaml
   ```

After the user generates it, read `run.yaml` and update:
- The `instance_type` field to use an available instance type from step 2 (prefer the smallest available GPU instance unless the user needs more).
- The `description` field to include the user's `#username` tag and `@telegram_nick` from Step 4 (e.g. `"my_experiment #j.smith @j_smith"`).

Show the final config to the user. Explain the key fields (image, resources, command) and ask if they want to modify anything — for example, the script to run, GPU count, or shared memory settings.

## Step 6: Submit the Job

```bash
conda run -n <env_name> mls job submit -c run.yaml
```

Tell the user: the first run may take several minutes if the Docker image isn't cached yet. Subsequent runs will be faster.

After submission, capture the job ID from the output — you'll need it for logs and status checks.

## Step 7: Monitor the Job

List recent jobs to check status:

```bash
conda run -n <env_name> mls job table --limit 10
```

Show the output and explain the status column. Also tell the user they can monitor via the web UI:

> You can also watch your job at https://console.cloud.ru/spa/mlspace/env-jobs/jobs
> The web UI shows logs, lets you restart jobs, and has GPU/CPU/memory metrics.

If the job is still running, offer to re-check status after a short wait.

To check the status of a specific job:

```bash
conda run -n <env_name> mls job status <job-id>
```

This shows detailed status info for a single job. Ask the user to run it via `! conda run -n <env_name> mls job status <job-id>`.

IMPORTANT: Do NOT run `mls job logs` at this step. Only use `mls job table` and `mls job status` to monitor the first job. Logs will be viewed after the job is killed.

## Step 8: Kill the Running Job

Once the user has seen the job status, kill the running job:

```bash
conda run -n <env_name> mls job kill <job-id>
```

This stops the job immediately. Useful for test jobs, runaway training, or jobs that have served their purpose.

## Step 9: View Logs of the Killed Job

After the job has been killed, show the user how to view its logs:

```bash
conda run -n <env_name> mls job logs <job-id>
```

This retrieves a snapshot of the logs from the (now stopped) job. Show the logs to the user and help interpret any output or errors.

Also mention the `-w` flag for future use with running jobs:

> For running jobs, you can use `mls job logs -w <job-id>` to poll until the job starts and then stream logs in real-time. Hit Ctrl+C when you've seen enough. Since this streams indefinitely, run it yourself via `! conda run -n <env_name> mls job logs -w <job-id>`.

## Step 10: Quick Test Job

Now that the user knows how to submit, monitor, kill, and view logs, suggest they run a quick test to see a successfully completed job. Ask them to update the `script` field in `run.yaml` to something that finishes instantly, e.g.:

```yaml
script: 'python -c "print(\"Hello from MLSpace!\")"'
```

Then submit it and wait for completion. Once done, ask them to check how a completed job looks:

```bash
conda run -n <env_name> mls job logs -w <job-id>
conda run -n <env_name> mls job status <job-id>
conda run -n <env_name> mls job table --limit 3
```

This confirms the full lifecycle works: submit → running → completed, and shows the job output in logs.

## Step 11: Troubleshooting

If the user hits issues at any point, diagnose based on these common problems:

### Segfault
The most common cause is a mismatch between CUDA/Python versions and the base Docker image. Ask the user to verify their versions match.

### Multi-GPU Training Not Working
When using `accelerate`, the job config must have:
```
processes_per_worker: 1
n_workers: 1
```
Check their config and fix if needed.

### Shared Memory Errors (e.g. "No space left on device" from DataLoader)
The fix is to use the `binary_exp` template and add `shm_size_class: large` to the job YAML. Offer to regenerate the config:
```bash
conda run -n <env_name> mls job yaml binary_exp > run.yaml
```
Then add `shm_size_class: large` to the YAML.

### Unknown / Undiagnosable Errors
Suggest SSH-ing into the running job for interactive debugging:
> Follow the official guide: https://cloud.ru/docs/aicloud/mlspace/concepts/guides/guides__cli/environments__cli-ssh-connect

## Common `mls` Commands Reference

All commands below assume `conda run -n <env_name>` prefix (e.g. `conda run -n my_env mls job table --limit 10`).

| Command | Description |
|---------|-------------|
| `mls configure` | Set up credentials and region |
| `mls configure region` | Show the currently configured region |
| `mls job instance_types` | List available instance types and their availability |
| `mls job yaml binary > run.yaml` | Generate a starter job config |
| `mls job submit -c run.yaml` | Submit a job |
| `mls job table --limit N` | List recent jobs |
| `mls job status <job-id>` | Check status of a specific job |
| `mls job logs <job-id>` | View job logs (snapshot) |
| `mls job logs -w <job-id>` | Wait for job to run, then stream logs |
| `mls job kill <job-id>` | Stop a running job |

## Next Steps

After completing the quick start, show the user these useful commands for setting up their real workload:

### Install PyTorch (if needed for training jobs)
```bash
conda run -n <env_name> pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
```

### Install project dependencies
```bash
conda run -n <env_name> pip install -e .
```

### SSH into a running job for debugging
Follow the official guide: https://cloud.ru/docs/aicloud/mlspace/concepts/guides/guides__cli/environments__cli-ssh-connect
