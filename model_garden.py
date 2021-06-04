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

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re
import time

import numpy as np

from PIL import Image

import tflite_runtime.interpreter as tflite

import os
import cv2

cap = cv2.VideoCapture(0)

fps=1
inference_time_ms=''

interpreter=''
labels=''
model=''
model_type=''
model_dir = '/var/www/html/coralai_models'
  
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
    #return "Default Message"
    return render_template("index.html")

@app.route('/video_feed')
def video_feed():
    #global cap
    return Response(main(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
                    
#-------------------------------------------------------------

def input_image_size(interpreter):
    """Returns input image size as (width, height, channels) tuple."""
    _, height, width, channels = interpreter.get_input_details()[0]['shape']
    return width, height, channels
    
def set_input_tensor(interpreter, image):
  """Sets the input tensor."""
  image = image.resize((input_image_size(interpreter)[0:2]), resample=Image.NEAREST)
  #input_tensor(interpreter)[:, :] = image
    
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
import collections
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
    #interpreter.invoke()
    invoke_interpreter(interpreter)
    
    boxes = get_output_tensor(interpreter, 0)
    class_ids = get_output_tensor(interpreter, 1)
    scores = get_output_tensor(interpreter, 2)
    count = int(get_output_tensor(interpreter, 3))

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
  #interpreter.invoke()
  invoke_interpreter(interpreter)
  
  output_details = interpreter.get_output_details()[0]
  output = np.squeeze(interpreter.get_tensor(output_details['index']))

  # If the model is quantized (uint8 data), then dequantize the results
  if output_details['dtype'] == np.uint8:
    scale, zero_point = output_details['quantization']
    output = scale * (output - zero_point)

  #ordered = np.argpartition(-output, top_k)
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
                    
      txt1=lbl + "(" + str(pred) + ")"
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
        except:
          #log_error()
          pass
    
    return cv2_im

#------Making Interpreter---------------------------------------------------------
import platform

EDGETPU_SHARED_LIB = {
  'Linux': 'libedgetpu.so.1',
  'Darwin': 'libedgetpu.1.dylib',
  'Windows': 'edgetpu.dll'
}[platform.system()]
      
def make_interpreter(path, edgetpu):
    
    if(edgetpu=='0'):
        interpreter = tflite.Interpreter(model_path=path)
    else:
      path, *device = path.split('@')
      path = modify_filename(path)
      interpreter = tflite.Interpreter(model_path=path,experimental_delegates=[tflite.load_delegate(EDGETPU_SHARED_LIB,{'device': device[0]} if device else {})])
        
        
    print('Loading Model: {} '.format(path))
    
    return interpreter

def modify_filename(path):
  global model
  
  arr=path.split(".tflite")
  path1=arr[0] + "_edgetpu.tflite"
  
  arr1=path1.split("/")
  model = arr1[len(arr1)-1]
  
  return path1

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
#--------------------------------------------------------------------------
def init():
  global interpreter, labels, model_type, model, model_dir
  
  with open('web/edgetpu.txt','r') as f:
    edgetpu=f.read()
  
  with open('web/model.txt','r') as f:
    model=f.read()
  
  print (model, ">>>>>>>>>>>>>>>>>>>")
  
  label = model_dict[model]
  print (label, "******************")
  
  model_type=get_model_type(model)
  print (model_type, "^^^^^^^^^^^^^")
  
  model_path=os.path.join(model_dir,model)
  interpreter = make_interpreter(model_path, edgetpu)
  
  interpreter.allocate_tensors()
  
  
  '''
  _, input_height, input_width, _ = interpreter.get_input_details()[0]['shape']
  print (input_height,input_width)
 
  name = interpreter.get_input_details()[0]['name']
  print (name)
 
  input_details = interpreter.get_input_details()
  print (input_details)
  '''
  
  label_path=os.path.join(model_dir,label)
  labels = load_labels(label_path)

def check_command_file():
  f = open("web/command_received.txt", "r")
  cmd=f.read()
  f.close()
        
  if (cmd=="1"):
    f = open("web/command_received.txt", "w")
    f.write("0")
    f.close()
    print("################# Loading Model ##########################")
    init()

def reset_edgetpu():
  f = open("web/edgetpu.txt", "w")
  f.write("0")
  f.close()
  print("----Set No hardware Acceleration during initial run------")
  
def main():
  global fps
  global interpreter, labels, model_type
  
  reset_edgetpu()
  
  init()
  
  #while cap.isOpened():
  while True:
    
        start_time=time.time()
        
        ret, frame = cap.read()
        if not ret:
            break
        
        cv2_im = frame
        #cv2_im = cv2.flip(cv2_im, 0)
        #cv2_im = cv2.flip(cv2_im, 1)

        cv2_im_rgb = cv2.cvtColor(cv2_im, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(cv2_im_rgb)
       
        if(model_type==0):
          results = classify_image(interpreter, image)
          label_id, prob = results[0]
          print(results)
          cv2_im = overlay_text_classification(results, labels, cv2_im)
          
        else:
          results = detect_objects(interpreter, image)
          cv2_im = overlay_text_detection(results, labels, cv2_im)
        

        cv2_im = overlay_text_common(cv2_im)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
        #cv2.imshow('Model Garden', cv2_im)
        ret, jpeg = cv2.imencode('.jpg', cv2_im)
        pic = jpeg.tobytes()
        
        #Flask streaming
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + pic + b'\r\n\r\n')
               

        check_command_file()
        
        elapsed_ms = (time.time() - start_time) * 1000
        fps=round(1000/elapsed_ms,1)
        print("--------fps: ",fps,"---------------")
        
if __name__ == '__main__':
  app.run(host='0.0.0.0', port=2205, threaded=True) # Run FLASK
  main()


