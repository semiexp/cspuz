import warnings
import subprocess
import signal


try:
    import psutil
    _PSUTIL_AVAILABLE = True
except ImportError:
    _PSUTIL_AVAILABLE = False


def run_subprocess(args, input, timeout=None):
    if timeout and not _PSUTIL_AVAILABLE:
        warnings.warn('psutil not found; timeout is ignored')
    if timeout and _PSUTIL_AVAILABLE:
        proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        try:
            out, _ = proc.communicate(input.encode('ascii'), timeout=timeout)
            out = out.decode('utf-8')
        except subprocess.TimeoutExpired:
            parent = psutil.Process(proc.pid)
            children = parent.children(recursive=True)
            children.append(parent)
            for p in children:
                p.send_signal(signal.SIGTERM)
            raise
        return out
    else:
        res = subprocess.run(args, input=input.encode('ascii'), stdout=subprocess.PIPE)
        out = res.stdout.decode('utf-8')
        return out
