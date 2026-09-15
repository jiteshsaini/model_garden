# Model Garden

**Updated to work with the latest Raspberry Pi OS (Trixie, Debian 13).**

<p align="left">
Read the article: <a href='https://helloworld.co.in/article/model-garden-testing-20-machine-learning-models-raspberry-pi' target='_blank'>
   <img src='https://raw.githubusercontent.com/jiteshsaini/files/main/img/logo3.gif' height='40px'>
</a> Watch the video on Yotube:
<a href='https://youtu.be/7gWCekMy1mw' target='_blank'>
   <img src='https://raw.githubusercontent.com/jiteshsaini/files/main/img/btn_youtube.png' height='40px'>
</a>
</p>

This project has been awarded TensorFlow Community Spotlight winner in June 2021. I am thankful for this <a href='https://x.com/TensorFlow/status/1405601120966303746' target='_blank'>Tweet by TensorFlow</a> mentioning this achievement and gifting these TensorFlow souvenirs.

<p align="center">
   <img src="https://raw.githubusercontent.com/jiteshsaini/files/main/img/tensorflow-contributer-jitesh-saini.jpeg">
</p>

### About the Project
Model Garden is an educational tool for understanding how machine learning models behave. It runs a model on a live camera feed on a Raspberry Pi, and a web page lets you switch to a different model while it runs. Point the camera at something and step through the models: you see straight away how their answers, their confidence and their speed differ, and how much a Coral USB Accelerator changes.

The models are pre-trained computer-vision models published by Google, packaged as canned models at https://dl.google.com/coral/canned_models/all_models.tar.gz: nine for image classification and three for object detection, each in a version for the Raspberry Pi's CPU and a version compiled for the Coral.

<p align="center">
   <img src="https://raw.githubusercontent.com/jiteshsaini/files/main/img/model_garden.gif">
</p>

### Image Classification Models
```
inception_v1_224_quant_edgetpu.tflite, imagenet_labels.txt
inception_v2_224_quant_edgetpu.tflite, imagenet_labels.txt
inception_v3_299_quant_edgetpu.tflite, imagenet_labels.txt
inception_v4_299_quant_edgetpu.tflite, imagenet_labels.txt
mobilenet_v1_1.0_224_quant_edgetpu.tflite, imagenet_labels.txt
mobilenet_v2_1.0_224_quant_edgetpu.tflite, imagenet_labels.txt

mobilenet_v2_1.0_224_inat_bird_quant_edgetpu.tflite, inat_bird_labels.txt
mobilenet_v2_1.0_224_inat_insect_quant_edgetpu.tflite, inat_insect_labels.txt
mobilenet_v2_1.0_224_inat_plant_quant_edgetpu.tflite, inat_plant_labels.txt
```

### Object Detection Models
```
mobilenet_ssd_v1_coco_quant_postprocess_edgetpu.tflite, coco_labels.txt
mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite, coco_labels.txt
mobilenet_ssd_v2_face_quant_postprocess_edgetpu.tflite, coco_labels.txt
```

## Hardware

- A Raspberry Pi
- A Raspberry Pi camera or a USB webcam
- Optional: a Coral USB Accelerator

> A Raspberry Pi 3A+ cannot supply the current a Coral draws under load, and
> resets partway through the larger models. Power the accelerator from a powered
> USB hub or a power-injector cable.

## Install

Two commands on a fresh Raspberry Pi OS.

```bash
curl -fsSL https://raw.githubusercontent.com/jiteshsaini/model_garden/main/setup_model_garden.sh -o setup_model_garden.sh
```

```bash
sudo bash setup_model_garden.sh
```

Downloading first, rather than piping into `sudo bash`, lets you read the script
before running it as root.

The script updates the OS first and downloads 185 MB of models, so it can take a
while. Run it again any time to update: it moves your existing copy to
`model_garden.backup_<date>` rather than overwriting it.

Tested on **Raspberry Pi OS Trixie (Debian 13)** on a Raspberry Pi 3A+, with the
Raspberry Pi camera and a Coral USB Accelerator.

## Run it

On a laptop or phone on the same network, open:

```
http://<your-pi-ip>/model_garden
```

and press **Start**. The first frame takes a few seconds while the camera and
the model load. **Stop** ends it and frees the camera.

<p align="center">
   <img src="https://raw.githubusercontent.com/jiteshsaini/files/main/img/model_garden_gui.jpg">
</p>

You should see the camera video with overlays. Switch between the models with
the buttons: the selected model and its labels are loaded while the script keeps
running, so you can compare their inference speeds directly.

If a Coral USB Accelerator is plugged in, a button at the top right switches to
the `_edgetpu` version of the selected model. The button only appears when a
Coral is plugged in; if you plug one in later, reload the page.

If the picture is upside down, set `ROTATE_180 = True` at the top of `camera.py`.

You can also run it from a terminal, to watch its output:

```bash
cd /var/www/html/model_garden && python3 model_garden.py
```

The page then shows it as running, but it has to be stopped in that terminal,
with Ctrl+C. A copy started from the page logs to `logs/model_garden.log`.

## What the script did

Worth knowing, both to understand the machine you now have and to do it by hand
if you prefer:

1. Updated the OS, then installed Apache and PHP, and Python's NumPy, Pillow,
   Flask and picamera2 from the OS packages.
2. Installed two Python packages from PyPI: `opencv-python-headless` 4.x and
   `ai-edge-litert`, the successor to `tflite_runtime`, which has no build for
   this Python.
3. Installed the Coral library, `libedgetpu`, from a community build made for
   `ai-edge-litert`. Google's own package crashes with it.
4. Downloaded the canned models to `/var/www/html/coralai_models`.
5. Copied the code to `/var/www/html/model_garden` and gave it to the web
   server's user, `www-data`.
6. Added `www-data` to the `video` and `plugdev` groups, so the page can start
   the script with access to the camera and the Coral. Added you to the same
   groups and to `www-data`, so a copy started from a terminal works too.
7. Restarted Apache.

No `chmod 777`, and nothing added to `/etc/sudoers`.

## Performance

Measured on Raspberry Pi OS Trixie, on a Raspberry Pi 3A+ with the Raspberry Pi
camera at 640x480. Frames per second include reading the camera, drawing the
results and encoding the video stream, not just the model.

| Model | CPU inference | CPU FPS | Coral inference | Coral FPS |
|---|---|---|---|---|
| mobilenet_v1 | 360 ms | 2.5 | 10 ms | 19.1 |
| mobilenet_v2 | 220 ms | 3.8 | 12 ms | 17.7 |
| mobilenet_v2 bird / insect / plant | 220 ms | 3.8 | 12 ms | 18.5 |
| inception_v1 | 880 ms | 1.1 | 19 ms | 14.9 |
| inception_v2 | 1150 ms | 0.8 | 154 ms | 5.2 |
| inception_v3 | 3250 ms | 0.3 | 500 ms | 1.9 |
| inception_v4 | 7050 ms | 0.1 | 1020 ms | 1.0 |
| mobilenet_ssd_v1 (objects) | 760 ms | 1.2 | 42 ms | 16.2 |
| mobilenet_ssd_v2 (objects) | 540 ms | 1.7 | 48 ms | 14.6 |
| mobilenet_ssd_v2 (faces) | 550 ms | 1.7 | 26 ms | 21.9 |

The original measurements, made on Raspberry Pi OS Buster in 2021:

<p align="center">
   <img src="https://raw.githubusercontent.com/jiteshsaini/files/main/img/graph_pi4.jpeg">
</p>

<p align="center">
   <img src="https://raw.githubusercontent.com/jiteshsaini/files/main/img/graph_pi3a.jpeg">
</p>

## How it works

The web page starts and stops the Python script. The script reads the camera,
runs the selected model on each frame, draws the results and serves the frames
as a video stream on port 2205. The page shows that stream and writes your
choices to small text files that the script checks after every frame.

| File | Role |
|---|---|
| `model_garden.py` | Camera, inference, overlays, and the video stream |
| `camera.py` | Frames from a USB webcam or the Raspberry Pi camera |
| `index.php` | The web page |
| `web/control.php` | Starts and stops `model_garden.py`, and reports whether it is running |
| `web/comm.php` | Saves the page's choices to `web/model.txt`, `web/edgetpu.txt` and `web/command_received.txt` |
| `templates/index.html` | The page the video stream is served in |
| `setup_model_garden.sh` | The installer above |
