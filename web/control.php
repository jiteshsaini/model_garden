<?php
// Starts and stops model_garden.py for the web page. It runs as the web
// server's user, which reaches the camera and the Coral through the video and
// plugdev groups.
header('Content-Type: application/json');

const PORT = 2205;
$app = dirname(__DIR__);
$logs = "$app/logs";
$pid_file = "$logs/model_garden.pid";
$log_file = "$logs/model_garden.log";

function stream_up() {
    $s = @fsockopen('127.0.0.1', PORT, $errno, $errstr, 0.5);
    if (!$s) {
        return false;
    }
    fclose($s);
    return true;
}

// A PID file can outlive its process and the number can be reused, so it is
// only trusted while that process is still model_garden.py.
function started_here($pid_file) {
    $pid = (int) @file_get_contents($pid_file);
    $cmdline = $pid > 0 ? @file_get_contents("/proc/$pid/cmdline") : false;
    return ($cmdline !== false && strpos($cmdline, 'model_garden.py') !== false) ? $pid : 0;
}

function status($pid_file, $log_file) {
    $pid = started_here($pid_file);
    $s = ['running' => false, 'owned' => $pid > 0, 'starting' => false];
    if (stream_up()) {
        $s['running'] = true;
        $s['message'] = $pid ? 'Running'
            : 'Running, but not started from this page - stop it where it was started';
    } elseif ($pid) {
        $s['starting'] = true;
        $s['message'] = 'Starting...';
    } elseif (file_exists($pid_file)) {
        $lines = array_values(array_filter(array_map('trim', @file($log_file) ?: [])));
        $s['message'] = 'Model Garden is not running. Press Start.'
            . ($lines ? ' (last log line: ' . end($lines) . ')' : '');
    } else {
        $s['message'] = 'Model Garden is not running. Press Start.';
    }
    return $s;
}

$action = $_POST['action'] ?? 'status';

if ($action === 'start') {
    $s = status($pid_file, $log_file);
    if ($s['running'] || $s['starting']) {
        echo json_encode($s);
        exit;
    }
    if (!is_dir($logs) && !@mkdir($logs, 02775)) {
        echo json_encode($s + ['message' => "The web server cannot create $logs - check that folder's owner"]);
        exit;
    }
    // Backgrounded with its output redirected, so PHP returns at once instead
    // of waiting on the child. env and nohup both exec, so $! is python's PID.
    $pid = (int) shell_exec('cd ' . escapeshellarg($app) . ' || exit 1; '
        . 'env PYTHONDONTWRITEBYTECODE=1 nohup python3 -u model_garden.py > '
        . escapeshellarg($log_file) . ' 2>&1 < /dev/null & echo $!');
    file_put_contents($pid_file, $pid);
}

if ($action === 'stop') {
    $pid = started_here($pid_file);
    if ($pid) {
        exec("kill $pid");
        for ($i = 0; $i < 30 && file_exists("/proc/$pid"); $i++) {
            usleep(100000);
        }
        if (file_exists("/proc/$pid")) {
            exec("kill -9 $pid");
        }
        @unlink($pid_file);
    }
}

echo json_encode(status($pid_file, $log_file));
