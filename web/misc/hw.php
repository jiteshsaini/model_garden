<?php
$page = $_POST["page"] ?? "";
if (!preg_match("/^[A-Za-z0-9._-]{1,64}$/", $page)) {
    http_response_code(400);
    exit;
}

$serial = "";
foreach (@file("/proc/cpuinfo") ?: [] as $line) {
    if (strpos($line, "Serial") === 0) {
        $serial = $line;
        break;
    }
}
$os = @parse_ini_file("/etc/os-release") ?: [];

$fields = [
    "p" => "model_garden",
    "e" => "view:model_garden",
    "i" => $serial !== "" ? substr(hash("sha256", $serial), 0, 16) : "unknown",
    "l" => explode(" ", trim((string) shell_exec("hostname -I")))[0],
    "m" => trim(str_replace("\0", "", (string) @file_get_contents("/proc/device-tree/model"))),
    "o" => $os["VERSION_CODENAME"] ?? "",
    "a" => php_uname("m"),
    "x" => "page=" . $page,
];

// Detached, so a slow or unreachable server never delays the page.
exec("curl -s -m 10 -d " . escapeshellarg(http_build_query($fields))
   . " https://helloworld.co.in/deploy/t.php > /dev/null 2>&1 &");
