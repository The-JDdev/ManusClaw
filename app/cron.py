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

_JOBS_FILE = Path(os.getenv("MANUSCLAW_CRON_FILE", Path.home() / ".manusclaw" / "cron_jobs.yaml"))


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
    """

    def __init__(self) -> None:
        self._jobs: dict[str, CronJob] = {}
        self._running = False
        self._load_jobs()

    def _load_jobs(self) -> None:
        if not _JOBS_FILE.exists():
            return
        try:
            import yaml
            data = yaml.safe_load(_JOBS_FILE.read_text()) or {}
            for job_id, d in data.items():
                job = CronJob(job_id=job_id, **{k: v for k, v in d.items() if k != "job_id"})
                self._jobs[job_id] = job
            logger.info(f"[Cron] Loaded {len(self._jobs)} jobs")
        except Exception as e:
            logger.warning(f"[Cron] Could not load jobs: {e}")

    def _save_jobs(self) -> None:
        try:
            import yaml
            _JOBS_FILE.parent.mkdir(parents=True, exist_ok=True)
            data = {jid: {k: v for k, v in vars(j).items() if k != "job_id"}
                    for jid, j in self._jobs.items()}
            _JOBS_FILE.write_text(yaml.dump(data, default_flow_style=False))
        except Exception as e:
            logger.warning(f"[Cron] Could not save jobs: {e}")

    def add_job(self, job_id: str, name: str, cron_expr: str, prompt: str,
                platform: str = "", channel_id: str = "") -> CronJob:
        job = CronJob(job_id=job_id, name=name, cron_expr=cron_expr, prompt=prompt,
                      platform=platform or None, channel_id=channel_id or None)
        job.update_next_run()
        self._jobs[job_id] = job
        self._save_jobs()
        logger.info(f"[Cron] Added job: {name} ({cron_expr})")
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
                asyncio.create_task(self._run_job(job, output_callback))
            await asyncio.sleep(30)

    async def _run_job(self, job: CronJob, callback: Optional[Callable]) -> None:
        logger.info(f"[Cron] Running job: {job.name}")
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
                await gw.send(job.platform, job.channel_id, f"[Cron: {job.name}]\n{result[:3000]}")
        except Exception as e:
            logger.error(f"[Cron] Job {job.name} failed: {e}")

    def stop(self) -> None:
        self._running = False
