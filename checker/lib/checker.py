from typing import List, Optional
import concurrent.futures
from threading import Lock
import sys
import time
from datetime import datetime

from lib.github_checker import GitHubReleaseChecker
from lib.openwrt_checker import OpenWrtChecker
from lib.openeuler_lpi4a_checker import OpenEulerLpi4aChecker
from lib.revyos_checker import RevyOSChecker
from lib.db_models import *

class ProgressTracker:
    def __init__(self, total_tasks):
        self.total_tasks = total_tasks
        self.completed_tasks = 0
        self.lock = Lock()
        self.start_time = time.time()
        self.current_task = ""
        
    def update(self, task_name):
        with self.lock:
            self.completed_tasks += 1
            self.current_task = task_name
            self._display_progress()
    
    def _display_progress(self):
        elapsed_time = time.time() - self.start_time
        percent = (self.completed_tasks / self.total_tasks) * 100
        
        # Calculate estimated time remaining
        if self.completed_tasks > 0:
            time_per_task = elapsed_time / self.completed_tasks
            remaining_tasks = self.total_tasks - self.completed_tasks
            eta = time_per_task * remaining_tasks
            eta_str = f"ETA: {eta:.1f}s"
        else:
            eta_str = "ETA: calculating..."
        
        # Create progress bar
        bar_length = 30
        filled_length = int(bar_length * self.completed_tasks // self.total_tasks)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        # Current timestamp
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        
        # Print progress
        sys.stdout.write(f"\r[{timestamp}] Progress: [{bar}] {percent:.1f}% ({self.completed_tasks}/{self.total_tasks}) | {eta_str} | Current: {self.current_task}")
        sys.stdout.flush()
        
        if self.completed_tasks == self.total_tasks:
            print(f"\nAll tasks completed in {elapsed_time:.2f} seconds")

def check_item(data: CheckInfoElement, progress_tracker=None) -> CheckResultElement:
    """Process a single check item."""
    try:
        if data.check_type == CheckType.GITHUB:
            checker = GitHubReleaseChecker()
        elif data.check_type == CheckType.OPENWRT:
            checker = OpenWrtChecker()
        elif data.check_type == CheckType.OPENEULER_LPI4A:
            checker = OpenEulerLpi4aChecker()
        elif data.check_type == CheckType.REVYOS:
            checker = RevyOSChecker()
        else:
            # Handle unknown check types
            progress_tracker.update(f"{data.check_type.name}: {data.check_path}")
            return None
        
        result = checker.check(data)
        
        # Update progress if tracker is provided
        if progress_tracker:
            progress_tracker.update(f"{data.check_type.name}: {data.check_path}")
            
        return result
    except Exception as exc:
        if progress_tracker:
            progress_tracker.update(f"ERROR: {data.check_path}")
        raise exc

def check_all(datas: List[CheckInfoElement], max_workers: int = None, show_progress: bool = True) -> List[CheckResultElement]:
    """
    Process all check items in parallel using multiple threads.
    
    Args:
        datas: List of CheckInfoElement objects to process
        max_workers: Maximum number of worker threads to use (defaults to None, 
                    which lets ThreadPoolExecutor choose based on the system)
        show_progress: Whether to show progress information
    
    Returns:
        List of CheckResultElement results
    """
    results = []
    total_items = len(datas)
    
    # Initialize progress tracker
    progress_tracker = ProgressTracker(total_items) if show_progress else None
    
    print(f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] Starting checks with {max_workers or 'auto'} workers")
    
    # Create a thread pool
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks to the executor and store the Future objects
        future_to_data = {executor.submit(check_item, data, progress_tracker): data for data in datas}
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_data):
            data = future_to_data[future]
            try:
                result = future.result()
                if result is not None:
                    results.append(result)
            except Exception as exc:
                print(f"\nItem {data.check_path} generated an exception: {exc}")
                # You might want to handle exceptions differently based on requirements
    
    return results