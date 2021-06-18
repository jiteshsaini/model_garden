# Model Garden

<p align="left">
Article: <a href='https://helloworld.co.in/article/model-garden-testing-20-machine-learning-on-models-raspberry-pi' target='_blank'>
   <img src='https://github.com/jiteshsaini/files/blob/main/img/logo3.gif' height='40px'>
</a> Watch the video on Yotube: 
<a href='https://youtu.be/7gWCekMy1mw' target='_blank'>
   <img src='https://github.com/jiteshsaini/files/blob/main/img/btn_youtube.png' height='40px'>
</a>
</p>

<p align="center">
   <img src="https://github.com/jiteshsaini/files/blob/main/img/model_garden.gif">
</p>

Google has published a large number of Pre-trained Machine Learning Models for anyone to download and experiment. You can check the complete list of freely available models here https://coral.ai/models/all/.
Some of the computer vision models have been packaged as canned models and can be downloaded from this link https://dl.google.com/coral/canned_models/all_models.tar.gz.<br>
This repo contains the code for testing following canned models using a single python script.<br>

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

All you need is a Raspberry Pi and a Picamera or a USB Camera to run this project.

## Configure your Raspberry Pi to Run this Project
Download this repo on your Raspberry Pi and run the bash script "install.sh" using command ```sudo sh install.sh```.
This bash script will download all the necessary packages/libraries required for this project. Also, the all the Models and the source code will be downloaded automatically and placed in the correct path. <br>
You need to wait patiently as the script can take upto 20 minutes (depending on your internet speed) to complete the task.

The script perfoms following actions on your Raspberry Pi automatically:- 

- Update & upgrade Raspberry Pi OS
- Install Apache Webserver and PHP
- Install Tensorflow Lite and Google Coral USB Accelerator Libraries
- Install OpenCV
- Download pre-trained Models from google coral repository
- Download the model_garden source code 
- Move the models and code to desired location in your Raspbrerry Pi and set permissions.

## How to run the code
Open terminal in Raspberry Pi and type the following commands:-
```
cd /vars/www/html/model_garden

python3 model_garden.py
```

you should see the following message on terminal
<p align="center">
   <img src="https://github.com/jiteshsaini/files/blob/main/img/terminal.jpg">
</p>


- check the ip of your Raspberry Pi using command ```hostname -I```
- For example, if it is 192.168.1.12, then using any Laptop/mobile open a browser and type the following URL:-<br>
```
192.168.1.12/model_garden
```

<p align="center">
   <img src="https://github.com/jiteshsaini/files/blob/main/img/model_garden_gui.jpg">
</p>


Now, you should start seeing the camera video with overlays on the Web GUI.
You can switch between the various models using the buttons provided on Web GUI. Based on your selection the respective model along with its label file gets loaded in the background during run time itself. This allows you to quickly change the models and appreciate the inferencing speeds<br>

## Attaching USB Coral Accelerator
If you have a USB Coral Accelerator, then attach it to Raspberry Pi. Now you can press the button at top right corner of Web GUI to run the models which are compiled to run on Coral Accelerator. These models have ```_edgetpu``` in their labels.
Do not press this button if you haven't connected USB Coral Accelerator to Raspberry Pi. Otherwise the script will halt and you will have to restart the script.

## Performance on Raspberry Pi 4

<p align="center">
   <img src="https://github.com/jiteshsaini/files/blob/main/img/graph_pi4.jpeg">
</p>

## Performance on Raspberry Pi 3A +

<p align="center">
   <img src="https://github.com/jiteshsaini/files/blob/main/img/graph_pi3a.jpeg">
</p>
