import subprocess
import os
import time
import threading
import glob

BASE_DIR = r"C:\Users\aushr\Music\vik"
compiler_script = "Compiler.py"
modem_script = "modem_reboot.py"

process_status = {
    "running": False,
    "logs": [],
    "current": "idle",
    "progress": "0/0"
}

processes = {}
compiler_process = None
modem_process = None

def log(msg):
    process_status["logs"].append(msg)
    if len(process_status["logs"]) > 200:
        process_status["logs"].pop(0)

def detect_scripts():
    files = glob.glob(os.path.join(BASE_DIR, "*.py"))
    return [
        os.path.basename(f)
        for f in files
        if os.path.basename(f) not in [compiler_script, modem_script]
    ]

def run_scraper(target_script=None):
    global compiler_process, modem_process
    
    process_status["logs"] = []
    process_status["running"] = True
    
    scripts = detect_scripts()
    if target_script:
        scripts = [s for s in scripts if s == target_script]
        if not scripts:
            log(f"Script {target_script} not found")
            process_status["running"] = False
            process_status["current"] = "idle"
            return
    
    total = len(scripts)
    processes.clear()  # Clear previous processes
    
    # Staggered parallel launch: 4s gap between starts
    for i, script in enumerate(scripts):
        if not process_status["running"]:
            break
        
        process_status["current"] = f"Launching {script}"
        log(f"Starting {script} (staggered)")
        
        p = subprocess.Popen(["python", os.path.join(BASE_DIR, script)])
        processes[script] = p
        
        # 4-second gap before launching next script (except last)
        if i < total - 1:
            time.sleep(4)
    
    # Wait for ALL processes to complete (they run in parallel)
    process_status["progress"] = "waiting..."
    process_status["current"] = f"All {total} running in parallel"
    log(f"All {total} scripts launched with 4s stagger, waiting for completion")
    
    completed = 0
    while processes and process_status["running"]:
        for script in list(processes.keys()):
            if processes[script].poll() is not None:
                log(f"Completed {script}")
                del processes[script]
                completed += 1
                process_status["progress"] = f"{completed}/{total}"
        time.sleep(1)  # Poll every second
    
    if not process_status["running"]:
        process_status["current"] = "idle"
        return
    
    # Run compiler and modem only if batch completed successfully
    if not target_script:
        log("Launching Compiler...")
        compiler_process = subprocess.Popen(
            ["python", os.path.join(BASE_DIR, compiler_script)]
        )
        compiler_process.wait()
        
        log("Rebooting modem...")
        modem_process = subprocess.Popen(
            ["python", os.path.join(BASE_DIR, modem_script)]
        )
        modem_process.wait()
    
    log("Batch completed")
    process_status["running"] = False
    process_status["current"] = "idle"

def start_all_scripts(target_script=None):
    if process_status["running"]:
        return {"status": "already running"}
    
    threading.Thread(target=run_scraper, args=(target_script,), daemon=True).start()
    return {"status": "started"}

def stop_all_scripts():
    process_status["running"] = False
    
    for p in processes.values():
        if p.poll() is None:
            p.terminate()
    
    if compiler_process and compiler_process.poll() is None:
        compiler_process.terminate()
    if modem_process and modem_process.poll() is None:
        modem_process.terminate()
    
    log("All processes stopped")
    return {"status": "stopped"}

def get_process_status():
    return process_status

# NEW FUNCTIONS
def run_compiler():
    global compiler_process
    if process_status["running"]:
        return {"status": "batch_running", "message": "Wait for batch to finish"}
    
    log("Manual Compiler run requested")
    compiler_process = subprocess.Popen(
        ["python", os.path.join(BASE_DIR, compiler_script)]
    )
    compiler_process.wait()
    log("Compiler completed")
    return {"status": "compiler_done"}

def run_modem():
    global modem_process
    if process_status["running"]:
        return {"status": "batch_running", "message": "Wait for batch to finish"}
    
    log("Manual Modem reboot requested")
    modem_process = subprocess.Popen(
        ["python", os.path.join(BASE_DIR, modem_script)]
    )
    modem_process.wait()
    log("Modem reboot completed")
    return {"status": "modem_done"}
