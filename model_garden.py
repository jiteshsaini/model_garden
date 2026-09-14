'''
The code is built using the help of examples provided by the following resources:-
https://coral.ai/examples/
https://www.tensorflow.org/lite/examples


Project: Model Garden
Author: Jitesh Saini
Github: https://github.com/jiteshsaini
website: https://helloworld.co.in

The code captures video frames from a PiCamera or USB Camera and performs Image Classification 
or Object Detection based on the Model selected. 

You can switch the currently loaded model using a Web GUI during run time. 

Watch this video to see this code in action:-
https://youtu.be/7gWCekMy1mw

'''

import collections
import ctypes
import glob
import os
import re
import threading
import time

import numpy as np

from PIL import Image

# tflite_runtime has no wheel for the Python on current Raspberry Pi OS.
# ai-edge-litert is its successor and keeps the same Interpreter API.
from ai_edge_litert.interpreter import Interpreter, load_delegate

import cv2

import camera

HERE = os.path.dirname(os.path.realpath(__file__))
WEB = os.path.join(HERE, 'web')

fps=1
inference_time_ms=0.0

model=''
model_dir = '/var/www/html/coralai_models'
default_model = 'mobilenet_v1_1.0_224_quant.tflite'
  
model_dict =	{
  "mobilenet_v1_1.0_224_quant.tflite": "imagenet_labels.txt",
  "mobilenet_v2_1.0_224_quant.tflite": "imagenet_labels.txt",
  "mobilenet_v2_1.0_224_inat_bird_quant.tflite":"inat_bird_labels.txt",
  "mobilenet_v2_1.0_224_inat_insect_quant.tflite":"inat_insect_labels.txt",
  "mobilenet_v2_1.0_224_inat_plant_quant.tflite":"inat_plant_labels.txt",
  "inception_v1_224_quant.tflite": "imagenet_labels.txt",
  "inception_v2_224_quant.tflite": "imagenet_labels.txt",
  "inception_v3_299_quant.tflite": "imagenet_labels.txt",
  "inception_v4_299_quant.tflite": "imagenet_labels.txt",
  "mobilenet_ssd_v1_coco_quant_postprocess.tflite": "coco_labels.txt",
  "mobilenet_ssd_v2_coco_quant_postprocess.tflite": "coco_labels.txt",
  "mobilenet_ssd_v2_face_quant_postprocess.tflite": "coco_labels.txt"
}

        
#---------Flask----------------------------------------
from flask import Flask, Response
from flask import render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/video_feed')
def video_feed():
    return Response(stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
                    
#-------------------------------------------------------------

def input_image_size(interpreter):
    """Returns input image size as (width, height, channels) tuple."""
    _, height, width, channels = interpreter.get_input_details()[0]['shape']
    return width, height, channels
    
def set_input_tensor(interpreter, image):
  """Sets the input tensor."""
  image = image.resize((input_image_size(interpreter)[0:2]), resample=Image.NEAREST)
    
  tensor_index = interpreter.get_input_details()[0]['index']
  input_tensor = interpreter.tensor(tensor_index)()[0]
  input_tensor[:, :] = image


def get_output_tensor(interpreter, index):
  """Returns the output tensor at the given index."""
  output_details = interpreter.get_output_details()[index]
  tensor = np.squeeze(interpreter.get_tensor(output_details['index']))
  return tensor

def invoke_interpreter(interpreter):
  global inference_time_ms
  
  t1=time.time()
  interpreter.invoke()
  inference_time_ms = (time.time() - t1) * 1000
  print("****Inference time = ", inference_time_ms)
  
#--------------------object detection--------------------------------------------------
#this technique is by google-coral API at 
#https://github.com/google-coral/pycoral/blob/master/pycoral/adapters/detect.py
Object = collections.namedtuple('Object', ['id', 'score', 'bbox'])

class BBox(collections.namedtuple('BBox', ['xmin', 'ymin', 'xmax', 'ymax'])):
    """Bounding box.
    Represents a rectangle which sides are either vertical or horizontal, parallel
    to the x or y axis.
    """
    __slots__ = ()

def detect_objects(interpreter, image, score_threshold=0.6, top_k=6):
    """Returns list of detected objects."""
    set_input_tensor(interpreter, image)
    invoke_interpreter(interpreter)
    
    boxes = get_output_tensor(interpreter, 0)
    class_ids = get_output_tensor(interpreter, 1)
    scores = get_output_tensor(interpreter, 2)

    def make(i):
        ymin, xmin, ymax, xmax = boxes[i]
        return Object(
            id=int(class_ids[i]),
            score=scores[i],
            bbox=BBox(xmin=np.maximum(0.0, xmin),
                      ymin=np.maximum(0.0, ymin),
                      xmax=np.minimum(1.0, xmax),
                      ymax=np.minimum(1.0, ymax)))

    return [make(i) for i in range(top_k) if scores[i] >= score_threshold]


#--------------------------------------------------------------------

#----------------image classfication--------------------------------
#this technique is by tensorflow.org API at 
#https://github.com/tensorflow/examples/blob/master/lite/examples/image_classification/raspberry_pi/classify_picamera.py

def classify_image(interpreter, image, top_k=3):
  """Returns a sorted array of classification results."""
  set_input_tensor(interpreter, image)
  invoke_interpreter(interpreter)
  
  output_details = interpreter.get_output_details()[0]
  output = np.squeeze(interpreter.get_tensor(output_details['index']))

  # If the model is quantized (uint8 data), then dequantize the results
  if output_details['dtype'] == np.uint8:
    scale, zero_point = output_details['quantization']
    output = scale * (output - zero_point)

  ordered = np.argsort(output)[::-1][:top_k]
  return [(i, output[i]) for i in ordered[:top_k]]

#--------------------------------------------------------------------------

def overlay_text_common(cv2_im):
  height, width, channels = cv2_im.shape
  font=cv2.FONT_HERSHEY_SIMPLEX
  
  global model, fps, inference_time_ms
  str1="FPS: " + str(fps)
  cv2_im = cv2.putText(cv2_im, str1, (width-180, height-55),font, 0.7, (255, 0, 0), 2)
  
  str2="Inference: " + str(round(inference_time_ms,1)) + " ms"
  cv2_im = cv2.putText(cv2_im, str2, (width-240, height-25),font, 0.7, (255, 0, 0), 2)
  
  cv2_im = cv2.rectangle(cv2_im, (0,height-20), (width, height), (0,0,0), -1)
  cv2_im = cv2.putText(cv2_im, model, (10, height-5),font, 0.6, (0, 255, 0), 2)
  
  return cv2_im
    
def overlay_text_classification(results, labels, cv2_im):
    height, width, channels = cv2_im.shape
    font=cv2.FONT_HERSHEY_SIMPLEX
    
    j=0
    for result in results:

      lbl=labels[result[0]]
      pred=result[1]
      
      print(lbl, "=", pred)
                    
      txt1=lbl + " ({:.2f})".format(pred)
      cv2_im = cv2.rectangle(cv2_im, (15,45 + j*35), (160, 65 + j*35), (0,0,0), -1)
      cv2_im = cv2.putText(cv2_im, txt1, (20, 60 + j*35),font, 0.5, (255, 255, 255), 1)
      
      
      if(j==0 and pred>0.4): #the first result has max prediction value. If it is more than this pred value, then show it in different colour 
        percent=round(pred*100)
        text_overlay= lbl + " (" + str(percent) + "% )"
        cv2_im = cv2.putText(cv2_im, text_overlay, (20, 30),font, 0.8, (0, 0, 255), 2)
      
      j=j+1

    return cv2_im
  
def overlay_text_detection(objs, labels, cv2_im):
    height, width, channels = cv2_im.shape
    font=cv2.FONT_HERSHEY_SIMPLEX
  
    for obj in objs:
        x0, y0, x1, y1 = list(obj.bbox)
        x0, y0, x1, y1 = int(x0*width), int(y0*height), int(x1*width), int(y1*height)
        percent = int(100 * obj.score)
        
        if (percent>=60):
            box_color, text_color, thickness=(0,255,0), (0,0,0),2
        elif (percent<60 and percent>40):
            box_color, text_color, thickness=(0,0,255), (0,0,0),2
        else:
            box_color, text_color, thickness=(255,0,0), (0,0,0),1
            
       
        text3 = '{}% {}'.format(percent, labels.get(obj.id, obj.id))
        print(text3)
        
        try:
          cv2_im = cv2.rectangle(cv2_im, (x0, y0), (x1, y1), box_color, thickness)
          cv2_im = cv2.rectangle(cv2_im, (x0,y1-20), (x1, y1), (255,255,255), -1)
          cv2_im = cv2.putText(cv2_im, text3, (x0, y1-5),font, 0.6, text_color, thickness)
        except Exception:
          pass
    
    return cv2_im

#------Coral USB Accelerator---------------------------------------------------------

EDGETPU_SHARED_LIB = 'libedgetpu.so.1'

# The accelerator enumerates as Global Unichip until firmware is pushed to it,
# then as Google. Both mean it is attached.
CORAL_USB_IDS = {("1a6e", "089a"), ("18d1", "9302")}

def coral_attached():
    """True if a Coral USB Accelerator is plugged in and its runtime is installed.

    Checked before load_delegate is ever called: without the accelerator that
    call fails, and against a mismatched runtime it crashes the process
    outright, which no try/except can catch.
    """
    for vendor_file in glob.glob('/sys/bus/usb/devices/*/idVendor'):
        try:
            vid = open(vendor_file).read().strip()
            pid = open(vendor_file[:-len('idVendor')] + 'idProduct').read().strip()
        except OSError:
            continue
        if (vid, pid) in CORAL_USB_IDS:
            try:
                ctypes.CDLL(EDGETPU_SHARED_LIB)
                return True
            except OSError:
                print("Coral attached, but libedgetpu is not installed")
                return False
    return False

def edgetpu_filename(path):
  return path.split(".tflite")[0] + "_edgetpu.tflite"

#--------------------------------------------------------------------------

#----------Loading Labels----------------------------------------------------

def load_labels(path):
  """Loads the labels file. Supports files with or without index numbers."""
  
  with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    labels = {}
    for row_number, content in enumerate(lines):
      pair = re.split(r'[:\s]+', content.strip(), maxsplit=1)
      if len(pair) == 2 and pair[0].strip().isdigit():
        labels[int(pair[0])] = pair[1].strip()
      else:
        labels[row_number] = pair[0].strip()
  return labels

def get_model_type(model):
  if "ssd" in model:
    return 1 #detection
  else:
    return 0 #classification

#----------Files written by the Web GUI (web/comm.php)------------------------------

def read_web_file(name, default):
  try:
    with open(os.path.join(WEB, name)) as f:
      return f.read().strip() or default
  except OSError:
    return default

def write_web_file(name, value):
  try:
    with open(os.path.join(WEB, name), 'w') as f:
      f.write(value)
  except OSError as e:
    print("cannot write web/" + name, e)

#--------------------------------------------------------------------------
def load_model():
  global model
  
  selected = read_web_file('model.txt', default_model)
  if selected not in model_dict:
    print("unknown model in web/model.txt:", selected)
    selected = default_model
  
  label = model_dict[selected]
  model_path = os.path.join(model_dir, selected)
  interpreter = None
  
  if read_web_file('edgetpu.txt', '0') == '1':
    if coral_attached():
      try:
        interpreter = Interpreter(model_path=edgetpu_filename(model_path),
                                  experimental_delegates=[load_delegate(EDGETPU_SHARED_LIB)])
        model_path = edgetpu_filename(model_path)
      except (ValueError, RuntimeError, OSError) as e:
        print("Coral could not load the model, using the CPU:", e)
    else:
      print("No Coral USB Accelerator attached, using the CPU")
    if interpreter is None:
      write_web_file('edgetpu.txt', '0')
  
  if interpreter is None:
    interpreter = Interpreter(model_path=model_path)
  
  interpreter.allocate_tensors()
  model = os.path.basename(model_path)
  print('Loading Model: {} '.format(model_path))
  
  labels = load_labels(os.path.join(model_dir, label))
  return interpreter, labels, get_model_type(selected)

def command_received():
  if read_web_file('command_received.txt', '0') == '1':
    write_web_file('command_received.txt', '0')
    print("################# Loading Model ##########################")
    return True
  return False

#----------One inference loop, shared by every browser viewing the stream-----------

# Each viewer used to start its own loop, so a second browser tab doubled the
# work on the same camera. Now one worker produces frames and each viewer
# receives the latest one; the worker idles while nobody is watching.
frame_ready = threading.Condition()
latest_jpeg = None
viewers = 0

def worker():
  global fps, latest_jpeg
  
  cap = camera.VideoCapture()
  interpreter = None
  
  while True:
    with frame_ready:
      while viewers == 0:
        frame_ready.wait()
    
    if interpreter is None or command_received():
      # release the previous model, and the Coral with it, before loading the next
      interpreter = None
      interpreter, labels, model_type = load_model()
    
    start_time=time.time()
    
    ret, frame = cap.read()
    if not ret:
      time.sleep(0.5)
      continue
    
    cv2_im = frame
    cv2_im_rgb = cv2.cvtColor(cv2_im, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(cv2_im_rgb)
    
    if(model_type==0):
      results = classify_image(interpreter, image)
      cv2_im = overlay_text_classification(results, labels, cv2_im)
    else:
      results = detect_objects(interpreter, image)
      cv2_im = overlay_text_detection(results, labels, cv2_im)
    
    cv2_im = overlay_text_common(cv2_im)
    
    ret, jpeg = cv2.imencode('.jpg', cv2_im)
    with frame_ready:
      latest_jpeg = jpeg.tobytes()
      frame_ready.notify_all()
    
    elapsed_ms = (time.time() - start_time) * 1000
    fps=round(1000/elapsed_ms,1)
    print("--------fps: ",fps,"---------------")

def stream():
  global viewers
  
  with frame_ready:
    viewers += 1
    frame_ready.notify_all()
  try:
    sent = None
    while True:
      with frame_ready:
        frame_ready.wait_for(lambda: latest_jpeg is not sent, timeout=5)
        pic = latest_jpeg
      if pic is None or pic is sent:
        continue
      sent = pic
      #Flask streaming
      yield (b'--frame\r\n'
             b'Content-Type: image/jpeg\r\n\r\n' + pic + b'\r\n\r\n')
  finally:
    with frame_ready:
      viewers -= 1

if __name__ == '__main__':
  # always start on the CPU; the Web GUI switches to the Coral
  write_web_file('edgetpu.txt', '0')
  threading.Thread(target=worker, daemon=True).start()
  app.run(host='0.0.0.0', port=2205, threaded=True) # Run FLASK
