from Tlog import TLog
import psutil
import time
import re

WORKSHOP_ID = "431960"

def get_active_ids_old():
    """
    获取当前所有活跃的壁纸id
    """
    active_ids = set()
    target_procs = ['wallpaper32.exe']
    
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'].lower() in target_procs:
                for f in proc.open_files():
                    match = re.search(rf'{WORKSHOP_ID}\\(\d+)\\', f.path, re.IGNORECASE)
                    if match:
                        active_ids.add(match.group(1))
        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
            continue
    return active_ids

_last_ids = set()
_last_check_time = 0

MICRO_SLEEP = 0
def get_active_ids():
    """
    获取当前所有活跃的壁纸id
    """
    global _last_ids, _last_check_time
    current_time = time.time()
    
    if current_time - _last_check_time < 1.0:
        return _last_ids.copy()
    
    active_ids = set()
    target_proc_name = 'wallpaper32.exe'
    
    try:
        wallpaper_pids = []
        proc_count = 0
        for proc in psutil.process_iter(['pid', 'name']):
            proc_count += 1
            if proc_count % 5 == 0:
                time.sleep(MICRO_SLEEP)
                
            try:
                if proc.info['name'] and proc.info['name'].lower() == target_proc_name:
                    wallpaper_pids.append(proc.info['pid'])
                    break
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                continue
        
        pattern = re.compile(rf'{WORKSHOP_ID}\\(\d+)\\', re.IGNORECASE)
        
        for pid in wallpaper_pids:
            try:
                proc = psutil.Process(pid)
                files = []
                try:
                    files = proc.open_files()
                except Exception:
                    pass
                
                file_count = 0
                for f in files:
                    file_count += 1
                    if file_count % 2 == 0:
                        time.sleep(MICRO_SLEEP)
                        
                    match = pattern.search(f.path)
                    if match:
                        active_ids.add(match.group(1))
                
                del proc
                
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                continue
        
        # 更新缓存
        _last_ids = active_ids
        _last_check_time = current_time
        
    except Exception as e:
        log.error(f"获取壁纸ID失败: {e}")
        return _last_ids.copy()
    
    return active_ids

if __name__ == '__main__':
    log = TLog("获取当前活跃壁纸")
    import psutil
    import time
    
    current_process = psutil.Process()
    
    current_process.cpu_percent(None)
    
    for i in range(100):
        start_time = time.perf_counter()
        tempval = get_active_ids()
        cpu_usage = current_process.cpu_percent(None)
        
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        
        log.val(tempval)
        log.debug(f"第{i+1:02d}次执行 - CPU占用: {cpu_usage:>5.2f}%, 执行时间: {execution_time:.4f}秒")
        
        time.sleep(0.5)
        
        current_process.cpu_percent(None)