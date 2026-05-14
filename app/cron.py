from __future__ import annotations
"""CronScheduler — persists cron jobs as YAML, delivers output to messaging platforms."""
import asyncio
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Callable

from app.logger import logger

try:
    from croniter import croniter
    _HAS_CRONITER = True
except ImportError:
    _HAS_CRONITER = False

try:
    import yaml as _yaml
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False

_DEFAULT_CRON_FILE = str(Path.home() / ".manusclaw" / "cron_jobs.yaml")
_JOBS_FILE = Path(os.getenv("MANUSCLAW_CRON_FILE", _DEFAULT_CRON_FILE))


@dataclass
class CronJob:
    job_id: str
    name: str
    cron_expr: str
    prompt: str
    platform: Optional[str] = None
    channel_id: Optional[str] = None
    enabled: bool = True
    last_run: float = 0.0
    next_run: float = 0.0
    run_count: int = 0

    def update_next_run(self) -> None:
        if not _HAS_CRONITER:
            self.next_run = time.time() + 3600
            return
        try:
            self.next_run = croniter(self.cron_expr, time.time()).get_next(float)
        except Exception:
            self.next_run = time.time() + 3600

    @property
    def is_due(self) -> bool:
        return self.enabled and time.time() >= self.next_run


class CronScheduler:
    """
    Simple cron scheduler that runs agent prompts on a schedule.
    Jobs are persisted to YAML and survive restarts.
    Requires: pip install croniter pyyaml
    """

    def __init__(self) -> None:
        self._jobs: dict[str, CronJob] = {}
        self._running = False
        self._tasks: set[asyncio.Task] = set()
        self._load_jobs()

    def _load_jobs(self) -> None:
        if not _JOBS_FILE.exists():
            return
        if not _HAS_YAML:
            logger.warning("[Cron] PyYAML not installed — cannot load persisted jobs. pip install pyyaml")
            return
        try:
            data = _yaml.safe_load(_JOBS_FILE.read_text()) or {}
            for job_id, d in data.items():
                kwargs = {k: v for k, v in d.items() if k != "job_id"}
                job = CronJob(job_id=job_id, **kwargs)
                self._jobs[job_id] = job
            logger.info(f"[Cron] Loaded {len(self._jobs)} jobs")
        except Exception as e:
            logger.warning(f"[Cron] Could not load jobs: {e}")

    def _save_jobs(self) -> None:
        if not _HAS_YAML:
            logger.warning("[Cron] PyYAML not installed — job persistence disabled.")
            return
        try:
            _JOBS_FILE.parent.mkdir(parents=True, exist_ok=True)
            data = {
                jid: {k: v for k, v in vars(j).items() if k != "job_id"}
                for jid, j in self._jobs.items()
            }
            _JOBS_FILE.write_text(_yaml.dump(data, default_flow_style=False))
        except Exception as e:
            logger.warning(f"[Cron] Could not save jobs: {e}")

    def add_job(self, job_id: str, name: str, cron_expr: str, prompt: str,
                platform: str = "", channel_id: str = "") -> CronJob:
        job = CronJob(
            job_id=job_id, name=name, cron_expr=cron_expr, prompt=prompt,
            platform=platform or None, channel_id=channel_id or None,
        )
        job.update_next_run()
        self._jobs[job_id] = job
        self._save_jobs()
        logger.info(f"[Cron] Added job: {name!r} ({cron_expr})")
        return job

    def remove_job(self, job_id: str) -> bool:
        if job_id in self._jobs:
            del self._jobs[job_id]
            self._save_jobs()
            return True
        return False

    def list_jobs(self) -> list[CronJob]:
        return list(self._jobs.values())

    def trigger_job(self, job_id: str) -> Optional[CronJob]:
        """Force a job to run on the next scheduler tick."""
        job = self._jobs.get(job_id)
        if job:
            job.next_run = time.time()
        return job

    async def run_forever(self, output_callback: Optional[Callable] = None) -> None:
        self._running = True
        logger.info("[Cron] Scheduler started")
        while self._running:
            due = [j for j in self._jobs.values() if j.is_due]
            for job in due:
                # FIX: store task reference to prevent GC mid-execution
                task = asyncio.create_task(self._run_job(job, output_callback))
                self._tasks.add(task)
                task.add_done_callback(self._tasks.discard)
            await asyncio.sleep(30)

    async def _run_job(self, job: CronJob, callback: Optional[Callable]) -> None:
        logger.info(f"[Cron] Running job: {job.name!r}")
        job.last_run = time.time()
        job.run_count += 1
        job.update_next_run()
        self._save_jobs()
        try:
            from app.agent.manus import Manus
            agent = Manus()
            result = await agent.run(job.prompt)
            if callback:
                await callback(job, result)
            elif job.platform and job.channel_id:
                from app.messaging.gateway import MessagingGateway
                gw = MessagingGateway()
                await gw.send(job.platform, job.channel_id,
                              f"[Cron: {job.name}]\n{result[:3000]}")
        except Exception as e:
            logger.error(f"[Cron] Job {job.name!r} failed: {e}")

    def stop(self) -> None:
        self._running = False
        logger.info("[Cron] Scheduler stopped")


def main() -> None:
    """
    Entry point for manusclaw-cron command.

    Usage:
      manusclaw-cron --run                          # Start scheduler loop
      manusclaw-cron --list                         # List all jobs
      manusclaw-cron --add ID NAME EXPR PROMPT      # Add a new job
      manusclaw-cron --remove JOB_ID                # Remove a job
      manusclaw-cron --trigger JOB_ID               # Force-trigger a job now
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="ManusClaw Cron Scheduler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  manusclaw-cron --run
  manusclaw-cron --list
  manusclaw-cron --add daily-report "Daily Report" "0 9 * * *" "Summarise today's news"
  manusclaw-cron --remove daily-report
  manusclaw-cron --trigger daily-report
        """,
    )
    parser.add_argument("--run",     action="store_true", help="Start the scheduler loop")
    parser.add_argument("--list",    action="store_true", help="List all scheduled jobs")
    parser.add_argument("--add",     nargs=4, metavar=("ID", "NAME", "EXPR", "PROMPT"),
                        help="Add a new job")
    parser.add_argument("--remove",  metavar="JOB_ID", help="Remove a job by ID")
    parser.add_argument("--trigger", metavar="JOB_ID", help="Force-trigger a job immediately")

    args = parser.parse_args()

    scheduler = CronScheduler()

    if args.list:
        jobs = scheduler.list_jobs()
        if not jobs:
            print("No scheduled jobs.")
            return
        print(f"{'ID':<20} {'NAME':<24} {'CRON':<16} {'RUNS':>5}  {'ENABLED'}")
        print("-" * 72)
        for j in jobs:
            status = "yes" if j.enabled else "no"
            print(f"{j.job_id:<20} {j.name:<24} {j.cron_expr:<16} {j.run_count:>5}  {status}")
        return

    if args.add:
        job_id, name, expr, prompt = args.add
        job = scheduler.add_job(job_id, name, expr, prompt)
        print(f"Added job '{job_id}'. Next run at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(job.next_run))}")
        return

    if args.remove:
        removed = scheduler.remove_job(args.remove)
        print(f"Removed job '{args.remove}'." if removed else f"Job '{args.remove}' not found.")
        return

    if args.trigger:
        job = scheduler.trigger_job(args.trigger)
        print(f"Job '{args.trigger}' scheduled to run on next tick." if job else f"Job '{args.trigger}' not found.")

    # Default: run the scheduler (also triggered by --run)
    try:
        asyncio.run(scheduler.run_forever())
    except KeyboardInterrupt:
        scheduler.stop()
        print("\n[Cron] Stopped.")
        sys.exit(0)
