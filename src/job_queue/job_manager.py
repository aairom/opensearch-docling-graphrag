"""
Job queue manager for background document processing.
Uses SQLite for job persistence and threading for background execution.
"""
import sqlite3
import threading
import time
import uuid
from enum import Enum
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from pathlib import Path
from loguru import logger
import json


class JobStatus(Enum):
    """Job status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobManager:
    """
    Manages background job queue with SQLite persistence.
    Runs a background worker thread to process jobs.
    """
    
    def __init__(self, db_path: str = "jobs.db", max_workers: int = 2):
        """
        Initialize job manager.
        
        Args:
            db_path: Path to SQLite database
            max_workers: Maximum number of concurrent workers
        """
        self.db_path = db_path
        self.max_workers = max_workers
        self.workers: List[threading.Thread] = []
        self.running = False
        self.lock = threading.Lock()
        self.job_handlers: Dict[str, Callable] = {}
        
        # Initialize database
        self._init_database()
        
        logger.info(f"Job manager initialized with {max_workers} workers")
    
    def _init_database(self):
        """Initialize SQLite database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                job_type TEXT NOT NULL,
                status TEXT NOT NULL,
                priority INTEGER DEFAULT 0,
                payload TEXT,
                result TEXT,
                error TEXT,
                created_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                progress INTEGER DEFAULT 0,
                total_steps INTEGER DEFAULT 100
            )
        """)
        
        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_status_priority 
            ON jobs(status, priority DESC, created_at ASC)
        """)
        
        conn.commit()
        conn.close()
        
        logger.info("Job database initialized")
    
    def register_handler(self, job_type: str, handler: Callable):
        """
        Register a job handler function.
        
        Args:
            job_type: Type of job (e.g., 'process_document')
            handler: Function to handle the job
        """
        self.job_handlers[job_type] = handler
        logger.info(f"Registered handler for job type: {job_type}")
    
    def submit_job(
        self,
        job_type: str,
        payload: Dict[str, Any],
        priority: int = 0
    ) -> str:
        """
        Submit a new job to the queue.
        
        Args:
            job_type: Type of job
            payload: Job data
            priority: Job priority (higher = processed first)
            
        Returns:
            Job ID
        """
        job_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO jobs (
                job_id, job_type, status, priority, payload, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            job_id,
            job_type,
            JobStatus.PENDING.value,
            priority,
            json.dumps(payload),
            datetime.utcnow().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Job submitted: {job_id} (type: {job_type}, priority: {priority})")
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job details.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job details or None
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_all_jobs(
        self,
        status: Optional[JobStatus] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all jobs, optionally filtered by status.
        
        Args:
            status: Filter by status
            limit: Maximum number of jobs to return
            
        Returns:
            List of job details
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if status:
            cursor.execute("""
                SELECT * FROM jobs 
                WHERE status = ? 
                ORDER BY priority DESC, created_at DESC 
                LIMIT ?
            """, (status.value, limit))
        else:
            cursor.execute("""
                SELECT * FROM jobs 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        progress: Optional[int] = None,
        error: Optional[str] = None
    ):
        """
        Update job status.
        
        Args:
            job_id: Job ID
            status: New status
            progress: Progress percentage (0-100)
            error: Error message if failed
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updates = ["status = ?"]
        params = [status.value]
        
        if status == JobStatus.PROCESSING:
            updates.append("started_at = ?")
            params.append(datetime.utcnow().isoformat())
        elif status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            updates.append("completed_at = ?")
            params.append(datetime.utcnow().isoformat())
        
        if progress is not None:
            updates.append("progress = ?")
            params.append(progress)
        
        if error:
            updates.append("error = ?")
            params.append(error)
        
        params.append(job_id)
        
        cursor.execute(f"""
            UPDATE jobs 
            SET {', '.join(updates)}
            WHERE job_id = ?
        """, params)
        
        conn.commit()
        conn.close()
    
    def update_job_result(self, job_id: str, result: Dict[str, Any]):
        """
        Update job result.
        
        Args:
            job_id: Job ID
            result: Job result data
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE jobs 
            SET result = ?
            WHERE job_id = ?
        """, (json.dumps(result), job_id))
        
        conn.commit()
        conn.close()
    
    def _get_next_job(self) -> Optional[Dict[str, Any]]:
        """Get next pending job from queue."""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get highest priority pending job
            cursor.execute("""
                SELECT * FROM jobs 
                WHERE status = ? 
                ORDER BY priority DESC, created_at ASC 
                LIMIT 1
            """, (JobStatus.PENDING.value,))
            
            row = cursor.fetchone()
            
            if row:
                job = dict(row)
                # Mark as processing
                cursor.execute("""
                    UPDATE jobs 
                    SET status = ?, started_at = ?
                    WHERE job_id = ?
                """, (
                    JobStatus.PROCESSING.value,
                    datetime.utcnow().isoformat(),
                    job['job_id']
                ))
                conn.commit()
            else:
                job = None
            
            conn.close()
            return job
    
    def _process_job(self, job: Dict[str, Any]):
        """
        Process a single job.
        
        Args:
            job: Job details
        """
        job_id = job['job_id']
        job_type = job['job_type']
        
        try:
            logger.info(f"Processing job: {job_id} (type: {job_type})")
            
            # Get handler
            handler = self.job_handlers.get(job_type)
            if not handler:
                raise ValueError(f"No handler registered for job type: {job_type}")
            
            # Parse payload
            payload = json.loads(job['payload'])
            
            # Execute handler
            result = handler(job_id, payload, self)
            
            # Update result
            self.update_job_result(job_id, result or {})
            self.update_job_status(job_id, JobStatus.COMPLETED, progress=100)
            
            logger.success(f"Job completed: {job_id}")
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Job failed: {job_id} - {error_msg}")
            self.update_job_status(job_id, JobStatus.FAILED, error=error_msg)
    
    def _worker_loop(self):
        """Worker thread main loop."""
        logger.info("Worker thread started")
        
        while self.running:
            try:
                # Get next job
                job = self._get_next_job()
                
                if job:
                    self._process_job(job)
                else:
                    # No jobs, sleep briefly
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Worker error: {str(e)}")
                time.sleep(5)
        
        logger.info("Worker thread stopped")
    
    def start(self):
        """Start background workers."""
        if self.running:
            logger.warning("Job manager already running")
            return
        
        self.running = True
        
        # Start worker threads
        for i in range(self.max_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                name=f"JobWorker-{i}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
        
        logger.info(f"Started {self.max_workers} worker threads")
    
    def stop(self):
        """Stop background workers."""
        if not self.running:
            return
        
        logger.info("Stopping job manager...")
        self.running = False
        
        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=5)
        
        self.workers.clear()
        logger.info("Job manager stopped")
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get job queue statistics.
        
        Returns:
            Statistics dictionary
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        for status in JobStatus:
            cursor.execute(
                "SELECT COUNT(*) FROM jobs WHERE status = ?",
                (status.value,)
            )
            stats[status.value] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM jobs")
        stats['total'] = cursor.fetchone()[0]
        
        conn.close()
        return stats


# Made with Bob