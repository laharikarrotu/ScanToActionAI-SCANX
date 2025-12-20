"""
Task queue for background processing
Supports async task execution without blocking API responses
"""
from typing import Callable, Any, Optional, Dict
import asyncio
import uuid
from datetime import datetime
from enum import Enum
import json

class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskQueue:
    """
    In-memory task queue for background processing
    For production, replace with Redis Queue (RQ) or Celery
    """
    
    def __init__(self):
        self.tasks: Dict[str, dict] = {}
        self.queue: asyncio.Queue = asyncio.Queue()
        self.workers: list = []
        self.max_workers = 4
    
    async def enqueue(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> str:
        """
        Enqueue a task for background processing
        
        Returns:
            task_id: Unique identifier for the task
        """
        task_id = str(uuid.uuid4())
        
        task = {
            "id": task_id,
            "func": func,
            "args": args,
            "kwargs": kwargs,
            "status": TaskStatus.PENDING,
            "created_at": datetime.now(),
            "result": None,
            "error": None
        }
        
        self.tasks[task_id] = task
        await self.queue.put(task)
        
        return task_id
    
    async def get_task_status(self, task_id: str) -> Optional[dict]:
        """Get status of a task"""
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        return {
            "id": task["id"],
            "status": task["status"].value,
            "created_at": task["created_at"].isoformat(),
            "result": task["result"],
            "error": task["error"]
        }
    
    async def get_result(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """
        Wait for task to complete and return result
        
        Args:
            task_id: Task identifier
            timeout: Maximum time to wait in seconds
        
        Returns:
            Task result
        """
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        start_time = asyncio.get_event_loop().time()
        
        while task["status"] == TaskStatus.PENDING:
            if timeout:
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > timeout:
                    raise TimeoutError(f"Task {task_id} timed out")
            
            await asyncio.sleep(0.1)
            task = self.tasks.get(task_id)
        
        if task["status"] == TaskStatus.FAILED:
            raise Exception(task["error"])
        
        return task["result"]
    
    async def _worker(self):
        """Background worker that processes tasks"""
        while True:
            try:
                task = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                
                task["status"] = TaskStatus.PROCESSING
                
                try:
                    if asyncio.iscoroutinefunction(task["func"]):
                        result = await task["func"](*task["args"], **task["kwargs"])
                    else:
                        result = task["func"](*task["args"], **task["kwargs"])
                    
                    task["status"] = TaskStatus.COMPLETED
                    task["result"] = result
                except Exception as e:
                    task["status"] = TaskStatus.FAILED
                    task["error"] = str(e)
                
                self.queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Worker error: {e}")
    
    async def start_workers(self):
        """Start background workers"""
        for _ in range(self.max_workers):
            worker = asyncio.create_task(self._worker())
            self.workers.append(worker)
    
    async def stop_workers(self):
        """Stop all workers"""
        for worker in self.workers:
            worker.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()

# Global task queue instance
task_queue = TaskQueue()

