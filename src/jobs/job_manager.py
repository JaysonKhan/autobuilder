"""Job queue manager"""

import sqlite3
import threading
import time
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any
import json

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobManager:
    """Manages job queue and execution"""
    
    def __init__(self, config: dict):
        self.config = config
        self.db_type = config.get('database', {}).get('type', 'sqlite')
        self.db_path = config.get('database', {}).get('sqlite_path', '/opt/autobuilder/storage/jobs.db')
        self.connection_string = config.get('database', {}).get('connection_string', '')
        self.lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables"""
        if self.db_type == 'sqlite':
            # Ensure directory exists
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    command TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    logs_path TEXT,
                    report_path TEXT,
                    error_message TEXT,
                    metadata TEXT
                )
            """)
            conn.commit()
            conn.close()
        else:
            # MariaDB initialization would go here
            # For now, we'll use SQLite as default
            logger.warning("MariaDB support not fully implemented, using SQLite")
            self.db_type = 'sqlite'
            self._init_database()
    
    def _get_connection(self):
        """Get database connection"""
        if self.db_type == 'sqlite':
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        else:
            # MariaDB connection would go here
            raise NotImplementedError("MariaDB not implemented")
    
    def create_job(self, command: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a new job and return job ID"""
        import uuid
        job_id = str(uuid.uuid4())
        
        with self.lock:
            conn = self._get_connection()
            try:
                conn.execute("""
                    INSERT INTO jobs (id, command, status, metadata)
                    VALUES (?, ?, ?, ?)
                """, (job_id, command, JobStatus.PENDING.value, json.dumps(metadata or {})))
                conn.commit()
                logger.info(f"Created job {job_id}: {command}")
            finally:
                conn.close()
        
        return job_id
    
    def update_job(
        self,
        job_id: str,
        status: Optional[JobStatus] = None,
        logs_path: Optional[str] = None,
        report_path: Optional[str] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Update job status and information"""
        with self.lock:
            conn = self._get_connection()
            try:
                updates = []
                params = []
                
                if status:
                    updates.append("status = ?")
                    params.append(status.value)
                
                if logs_path:
                    updates.append("logs_path = ?")
                    params.append(logs_path)
                
                if report_path:
                    updates.append("report_path = ?")
                    params.append(report_path)
                
                if error_message:
                    updates.append("error_message = ?")
                    params.append(error_message)
                
                if metadata:
                    updates.append("metadata = ?")
                    params.append(json.dumps(metadata))
                
                if status == JobStatus.COMPLETED or status == JobStatus.FAILED:
                    updates.append("completed_at = ?")
                    params.append(datetime.now().isoformat())
                
                updates.append("updated_at = ?")
                params.append(datetime.now().isoformat())
                
                params.append(job_id)
                
                query = f"UPDATE jobs SET {', '.join(updates)} WHERE id = ?"
                conn.execute(query, params)
                conn.commit()
            finally:
                conn.close()
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job by ID"""
        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()
    
    def list_jobs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent jobs"""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job (best effort)"""
        job = self.get_job(job_id)
        if not job:
            return False
        
        if job['status'] in [JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.CANCELLED.value]:
            return False
        
        self.update_job(job_id, status=JobStatus.CANCELLED)
        logger.info(f"Cancelled job {job_id}")
        return True
    
    def cleanup_old_jobs(self, days: int = 30):
        """Cleanup old jobs"""
        conn = self._get_connection()
        try:
            cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
            cutoff_iso = datetime.fromtimestamp(cutoff).isoformat()
            conn.execute(
                "DELETE FROM jobs WHERE created_at < ?",
                (cutoff_iso,)
            )
            conn.commit()
            logger.info(f"Cleaned up jobs older than {days} days")
        finally:
            conn.close()
    
    def shutdown(self):
        """Shutdown job manager"""
        logger.info("Job manager shutting down")

