"""Job executor with async task running"""

import asyncio
import logging
import threading
from pathlib import Path
from typing import Callable, Dict, Any, Optional

from src.jobs.job_manager import JobManager, JobStatus
from src.utils.redact import get_redactor

logger = logging.getLogger(__name__)


class JobExecutor:
    """Executes jobs asynchronously"""
    
    def __init__(self, job_manager: JobManager, config: dict):
        self.job_manager = job_manager
        self.config = config
        self.running_jobs: Dict[str, threading.Thread] = {}
        self.redactor = get_redactor(config)
    
    async def execute_job(
        self,
        job_id: str,
        task_func: Callable,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute a job task"""
        # Update status to running
        self.job_manager.update_job(job_id, status=JobStatus.RUNNING)
        
        # Create workspace directory
        workspace_dir = Path(self.config['paths']['workspaces_dir']) / job_id
        workspace_dir.mkdir(parents=True, exist_ok=True)
        
        logs_path = workspace_dir / "logs.txt"
        report_path = workspace_dir / "report.md"
        
        try:
            # Run task in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._run_task_sync,
                task_func,
                job_id,
                str(workspace_dir),
                str(logs_path),
                str(report_path),
                *args,
                **kwargs
            )
            
            # Update job with results
            self.job_manager.update_job(
                job_id,
                status=JobStatus.COMPLETED,
                logs_path=str(logs_path),
                report_path=str(report_path) if report_path.exists() else None,
            )
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Job {job_id} failed: {error_msg}")
            
            # Redact sensitive info from error
            error_msg_redacted = self.redactor.redact(error_msg)
            
            self.job_manager.update_job(
                job_id,
                status=JobStatus.FAILED,
                error_message=error_msg_redacted,
                logs_path=str(logs_path) if logs_path.exists() else None,
            )
            
            raise
    
    def _run_task_sync(
        self,
        task_func: Callable,
        job_id: str,
        workspace_dir: str,
        logs_path: str,
        report_path: str,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """Run task synchronously (in thread)"""
        import sys
        from io import StringIO
        
        # Capture stdout/stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        log_buffer = StringIO()
        
        try:
            sys.stdout = log_buffer
            sys.stderr = log_buffer
            
            # Call task function
            result = task_func(
                job_id=job_id,
                workspace_dir=workspace_dir,
                logs_path=logs_path,
                report_path=report_path,
                *args,
                **kwargs
            )
            
            return result or {}
            
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            
            # Write logs (redacted)
            log_content = log_buffer.getvalue()
            redacted_logs = self.redactor.redact(log_content)
            
            with open(logs_path, 'w', encoding='utf-8') as f:
                f.write(redacted_logs)
    
    def cleanup_workspace(self, job_id: str):
        """Cleanup workspace after job completion"""
        workspace_dir = Path(self.config['paths']['workspaces_dir']) / job_id
        if workspace_dir.exists():
            import shutil
            try:
                shutil.rmtree(workspace_dir)
                logger.info(f"Cleaned up workspace for job {job_id}")
            except Exception as e:
                logger.warning(f"Failed to cleanup workspace {job_id}: {e}")

