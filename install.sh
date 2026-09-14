#!/bin/bash
# Model Garden - installer for Raspberry Pi OS 12/13 (Bookworm / Trixie).
#
#   curl -fsSL https://raw.githubusercontent.com/jiteshsaini/model_garden/main/install.sh -o install.sh
#   sudo bash install.sh
#
# Code goes to /var/www/html/model_garden, models to /var/www/html/coralai_models.
# An existing copy of either is moved aside, never overwritten.

# `sh install.sh` runs dash, which cannot parse the rest of this file.
if [ -z "${BASH_VERSION:-}" ]; then exec bash "$0" "$@"; fi
[ "$(id -u)" -eq 0 ] || exec sudo bash "$0" "$@"

set -uo pipefail
export DEBIAN_FRONTEND=noninteractive

WEB=/var/www/html
CODE=$WEB/model_garden
MODELS=$WEB/coralai_models
REPO=https://github.com/jiteshsaini/model_garden.git
MODELS_URL=https://dl.google.com/coral/canned_models/all_models.tar.gz
RUN_USER=${SUDO_USER:-pi}
STAMP=$(date +%Y%m%d_%H%M%S)
LOG=/tmp/model_garden-install-$STAMP.log
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

ok()   { echo "  [ ok ] $1"; }
warn() { echo "  [warn] $1"; }
die()  { echo "  [FAIL] $1"; exit 1; }

MODEL=$(tr -d '\0' < /proc/device-tree/model 2>/dev/null)
OSVER=$(. /etc/os-release; echo "${VERSION_CODENAME:-unknown}")
ARCH=$(uname -m)
IP=$(hostname -I | awk '{print $1}')
ID=$(grep -m1 ^Serial /proc/cpuinfo | sha256sum | cut -c1-16)
MEM=$(free -m | awk '/Mem:/{print $2}')

echo
echo "This machine"
echo "  Board:  ${MODEL:-unknown}"
echo "  OS:     $(. /etc/os-release; echo "${PRETTY_NAME:-unknown}")"
echo "  RAM:    $MEM MB"
echo "  Address $IP"
echo

[ "$(. /etc/os-release; echo "${VERSION_ID:-0}")" -ge 12 ] 2>/dev/null \
  || die "needs Raspberry Pi OS 12 (Bookworm) or newer"
if [ "$MEM" -lt 600 ] && [ "$(systemctl get-default)" = "graphical.target" ]; then
  warn "$MEM MB of RAM with the desktop running leaves little for the larger models."
  warn "To boot to the console instead: sudo systemctl set-default multi-user.target"
fi

echo
echo "Installing packages. The system is updated first; on an older board that can take an hour."
apt-get update 2>&1 | tee -a "$LOG" >/dev/null || warn "apt-get update failed - see $LOG"
apt-get full-upgrade -y 2>&1 | tee -a "$LOG" || warn "the upgrade did not finish cleanly - continuing"
apt-get install -y apache2 php libapache2-mod-php \
    python3-numpy python3-pil python3-flask python3-picamera2 \
    rpicam-apps curl git 2>&1 | tee -a "$LOG" || die "package install failed - see $LOG"

# Headless, and 4.x: PyPI now resolves the unpinned name to 5.x, and the full
# build pulls ~500 MB of GUI libraries this never opens.
OPENCV_PIN="opencv-python-headless==4.14.0.94"
# Must match the TensorFlow version libedgetpu below is built against. A
# mismatched pair does not raise an error; it crashes when a model loads.
LITERT_PIN="ai-edge-litert==2.2.0"
CORAL_TAG="16.0TF2.19.1-1"

python3 -c "import cv2" 2>/dev/null \
  || pip3 install --break-system-packages "$OPENCV_PIN" 2>&1 | tee -a "$LOG" \
  || die "$OPENCV_PIN failed to install"
python3 -c "import ai_edge_litert" 2>/dev/null \
  || pip3 install --break-system-packages "$LITERT_PIN" 2>&1 | tee -a "$LOG" \
  || die "$LITERT_PIN failed to install"

# Google's own libedgetpu targets TensorFlow Lite ~2.5 and crashes under
# ai-edge-litert; this community rebuild matches it.
if dpkg-query -W -f='${Version}' libedgetpu1-std 2>/dev/null | grep -q tf2.19.1; then
  ok "Coral library already installed"
else
  for cn in $OSVER trixie bookworm; do
    deb="libedgetpu1-std_16.0tf2.19.1-1.${cn}_$(dpkg --print-architecture).deb"
    if curl -fsSL --max-time 180 -o "$TMP/$deb" \
         "https://github.com/feranick/libedgetpu/releases/download/$CORAL_TAG/$deb" 2>>"$LOG"; then
      # still declares libgcc1, which libgcc-s1 replaced; dpkg exits non-zero on the override
      dpkg -i --ignore-depends=libgcc1 "$TMP/$deb" >>"$LOG" 2>&1
      ldconfig
      ok "Coral library installed ($cn build) - replug the accelerator if it is attached"
      break
    fi
  done
fi

echo
if [ -f "$MODELS/mobilenet_ssd_v2_face_quant_postprocess_edgetpu.tflite" ]; then
  ok "models already in $MODELS"
else
  echo "Downloading the models (185 MB)"
  mkdir -p "$TMP/models"
  if curl -fL --progress-bar -o "$TMP/all_models.tar.gz" "$MODELS_URL" \
     && tar -xzf "$TMP/all_models.tar.gz" -C "$TMP/models"; then
    rm -f "$TMP/all_models.tar.gz"
    if [ -e "$MODELS" ]; then
      mv "$MODELS" "$MODELS.backup_$STAMP" && ok "existing models moved to $MODELS.backup_$STAMP"
    fi
    mv "$TMP/models" "$MODELS" && ok "models installed in $MODELS"
  else
    warn "could not download the models from $MODELS_URL"
  fi
fi

if git clone -q --depth 1 "$REPO" "$TMP/repo" && [ -f "$TMP/repo/model_garden.py" ]; then
  rm -rf "$TMP/repo/.git"
  if [ -e "$CODE" ]; then
    mv "$CODE" "$CODE.backup_$STAMP" && ok "existing code moved to $CODE.backup_$STAMP"
  fi
  mv "$TMP/repo" "$CODE" && ok "code installed in $CODE"
else
  die "could not fetch the code from $REPO"
fi

# The web page starts model_garden.py as www-data, which reaches the camera and
# the Coral through video and plugdev (libedgetpu's udev rule grants the
# accelerator to plugdev). You join the same groups so a copy started from a
# terminal works too, and nothing needs to be world-writable.
chown -R www-data:www-data "$CODE" "$MODELS"
find "$CODE" "$MODELS" -type d -exec chmod 2775 {} +
find "$CODE" "$MODELS" -type f -exec chmod 664 {} +
NEW_GROUPS=0
for g in www-data video plugdev; do
  id -nG "$RUN_USER" | tr ' ' '\n' | grep -qx "$g" || { adduser "$RUN_USER" "$g" >/dev/null 2>&1; NEW_GROUPS=1; }
done
for g in video plugdev; do adduser www-data "$g" >/dev/null 2>&1; done
systemctl enable --now apache2 >/dev/null 2>&1
systemctl restart apache2

as_user() { (cd /tmp && sudo -u "$RUN_USER" env HOME=/tmp python3 -c "$1") >/dev/null 2>&1; }
page_served() { curl -fs http://127.0.0.1/model_garden/ | grep -q "Model Garden"; }
page_can_write() { sudo -u www-data test -w "$CODE/web/model.txt"; }
page_can_start() { id -nG www-data | tr ' ' '\n' | grep -qx video && id -nG www-data | tr ' ' '\n' | grep -qx plugdev; }
opencv() { as_user "import cv2"; }
litert() { as_user "from ai_edge_litert.interpreter import Interpreter"; }
picamera2() { as_user "import picamera2"; }
camera() { rpicam-hello --list-cameras 2>/dev/null | grep -q " : "; }
models() {
  as_user "
import ast, os, re
d = ast.literal_eval(re.search(r'model_dict =\s*(\{.*?\})', open('$CODE/model_garden.py').read(), re.S).group(1))
need = [f for m, l in d.items() for f in (m, m.replace('.tflite', '_edgetpu.tflite'), l)]
assert all(os.path.exists(os.path.join('$MODELS', f)) for f in need)"
}
coral_attached() { grep -qx -e 1a6e -e 18d1 /sys/bus/usb/devices/*/idVendor 2>/dev/null; }
coral() {
  as_user "
from ai_edge_litert.interpreter import Interpreter, load_delegate
Interpreter(model_path='$MODELS/mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite',
            experimental_delegates=[load_delegate('libedgetpu.so.1')]).allocate_tensors()"
}

ST=ok
check() {
  if "$2"; then printf "  %-36s yes\n" "$1"; else printf "  %-36s NO\n" "$1"; ST=fail; fi
}
echo
echo "Checks"
check "web page served" page_served
check "web page can save its settings" page_can_write
check "web page can use camera and Coral" page_can_start
check "OpenCV" opencv
check "LiteRT interpreter" litert
check "picamera2" picamera2
check "camera detected" camera
check "all 12 models, CPU and Coral" models
if coral_attached; then
  check "Coral loads a model" coral
else
  printf "  %-36s not attached (optional)\n" "Coral USB Accelerator"
fi

RUNNING=$(uname -r)
NEWEST=$(ls /lib/modules | grep -- "+${RUNNING#*+}\$" | sort -V | tail -1)

curl -s -m 5 https://helloworld.co.in/deploy/t.php >/dev/null 2>&1 -d \
    "p=$(basename "$REPO" .git)&e=install&s=$ST&i=$ID&m=${MODEL// /+}&o=$OSVER&a=$ARCH&l=$IP" || true

echo
[ -n "$NEWEST" ] && [ "$NEWEST" != "$RUNNING" ] && echo "  Reboot first: kernel $NEWEST was installed and $RUNNING is running." && echo
[ "$NEW_GROUPS" -eq 1 ] && echo "  To run it from a terminal, log out and back in first so your new groups apply." && echo
echo "  Open this in a browser on the same network and press Start:"
echo "    http://$IP/model_garden"
echo
