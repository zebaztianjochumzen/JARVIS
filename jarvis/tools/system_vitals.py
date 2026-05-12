"""System vitals tool — lets Claude verbally report CPU, RAM, disk, and network stats."""


def get_system_vitals() -> str:
    try:
        import psutil
    except ImportError:
        return "psutil is not installed. Run: pip install psutil"

    try:
        cpu  = psutil.cpu_percent(interval=0.4)
        mem  = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        net  = psutil.net_io_counters()

        return (
            f"CPU: {cpu:.1f}% | "
            f"RAM: {mem.used / 1e9:.1f} GB / {mem.total / 1e9:.1f} GB ({mem.percent:.0f}%) | "
            f"Disk: {disk.used / 1e9:.0f} GB used, {disk.free / 1e9:.0f} GB free ({disk.percent:.0f}%) | "
            f"Network: ↑ {net.bytes_sent / 1e6:.0f} MB  ↓ {net.bytes_recv / 1e6:.0f} MB (cumulative since boot)"
        )
    except Exception as exc:
        return f"Could not read vitals: {exc}"
