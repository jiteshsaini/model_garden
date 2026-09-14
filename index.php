<!--
Project: Model Garden
Author: Jitesh Saini
Github: https://github.com/jiteshsaini
website: https://helloworld.co.in

Watch this video to see this code in action:-
https://youtu.be/7gWCekMy1mw
-->
<?php
// The Coral USB Accelerator enumerates as Global Unichip until firmware is
// pushed to it, then as Google.
function coral_attached() {
	foreach (glob("/sys/bus/usb/devices/*/idVendor") as $vendor_file) {
		$vid = trim(@file_get_contents($vendor_file));
		$pid = trim(@file_get_contents(dirname($vendor_file) . "/idProduct"));
		if (in_array("$vid:$pid", ["1a6e:089a", "18d1:9302"], true)) {
			return true;
		}
	}
	return false;
}

$coral = coral_attached();
$on_coral = $coral && trim(@file_get_contents(__DIR__ . "/web/edgetpu.txt")) === "1";
$current_model = trim(@file_get_contents(__DIR__ . "/web/model.txt"));

// The address the browser used, so the video frame works from another machine
// and through a hostname as well as an IP.
$host = preg_replace('/:\d+$/', '', $_SERVER['HTTP_HOST'] ?? $_SERVER['SERVER_ADDR']);
$link_vid = 'http://' . htmlspecialchars($host, ENT_QUOTES) . ':2205';
?>
<html>
<head>        
   <title>Model Garden</title>
   <style>
   #box_outer{
		width:100%;
		overflow:auto;
		float:left;
		border:1px solid grey;
	}
	#box_header{
		width:100%;
		overflow:auto;
		float:left;
		border:1px solid lightgrey;
	}
	#box_header b{
		font-size:32px;
		color:darkblue;
	}
	#box_header txt{
		margin-right:3%;
		float:right;
	}
	
	#run_box{
		margin-left:3%;
		float:left;
		font-size:17px;
	}
	#run_box input{
		font-size:17px;
		min-width:80px;
	}
	#video_msg{
		margin:20% 5%;
		font-size:22px;
		color:grey;
	}
	
	#box_camera{
		width:60%;
		overflow:auto;
		float:left;
		border:0px solid orange;
	}
	.box_models{
		width:18%;
		float:left;
		overflow:auto;
		border:0px solid blue;
		overflow:auto;
		margin-top:3%;
		
	}
	
	.div_txt{
		width:100%;
		font-size:24px;
		font-weight:bold;
	}
	
	.box_models input{
		width:100%;
		height:30px;
		background-color:#011f61;
		color:white;
		font-size: 17px;
		margin-top:6%;
	}
	.box_models input[type="submit"]:hover {
		color:green;
	}
	
   </style>
   <script src="web/js/jquery.min.js"></script>            
   <script>
	   var model = {
		    b1:"mobilenet_v1_1.0_224_quant.tflite",
			b2:"mobilenet_v2_1.0_224_quant.tflite",
			b3:"mobilenet_v2_1.0_224_inat_bird_quant.tflite",
			b4:"mobilenet_v2_1.0_224_inat_insect_quant.tflite",
			b5:"mobilenet_v2_1.0_224_inat_plant_quant.tflite",
			b6:"inception_v1_224_quant.tflite",
			b7:"inception_v2_224_quant.tflite",
			b8:"inception_v3_299_quant.tflite",
			b9:"inception_v4_299_quant.tflite",
			b10:"mobilenet_ssd_v1_coco_quant_postprocess.tflite",
			b11:"mobilenet_ssd_v2_coco_quant_postprocess.tflite",
			b12:"mobilenet_ssd_v2_face_quant_postprocess.tflite"
		   };
	var current_model = <?php echo json_encode($current_model); ?>;
	var stream_url = <?php echo json_encode($link_vid); ?>;
	var stream_shown = false;
	
	function init(){
		console.log("started..");
		$.post("web/misc/hw.php",{page: 'index.php'});
		
		refresh_status();
		setInterval(refresh_status, 5000);
		
		for (var id in model) {
			if (model[id] == current_model) {
				highlight(id);
			}
		}
	}
	
	function highlight(id)
	{
		var len = Object.keys(model).length
		var i;
		for (i = 1; i <= len; i++) {
			id1='b'+i;
			document.getElementById(id1).style.backgroundColor="#011f61";
			document.getElementById(id1).style.color="white";
			
		}
		
		document.getElementById(id).style.backgroundColor="#00ff00";
		document.getElementById(id).style.color="black";
	}
	
	function button_action(id)
	{
		var mdl = model[id]
		console.log("mdl:" + mdl);
		$.post("web/comm.php",{model_file: mdl});
		
		$.post("web/comm.php",{command_generated:1});
		
		highlight(id);
	}
	
	function button_coral(){
		console.log("coral button");
		var id = 'coral';
		button_caption=document.getElementById(id).value;
		
		if(button_caption=="connected"){
			document.getElementById(id).value="disconnected";
			document.getElementById(id).style.backgroundColor="white";
			$.post("web/comm.php",{edgetpu:0});
			$.post("web/comm.php",{command_generated:1});
			console.log("edgetpu = 0");
		}
		if(button_caption=="disconnected"){
			document.getElementById(id).value="connected";
			document.getElementById(id).style.backgroundColor="#66ff66";
			$.post("web/comm.php",{edgetpu:1});
			$.post("web/comm.php",{command_generated:1});
			console.log("edgetpu = 1");
		}
		
	}
	
	
	function refresh_status(){
		$.getJSON("web/control.php", show_status);
	}
	
	function show_status(s){
		var btn = document.getElementById('run');
		var frame = document.getElementById('video');
		var note = document.getElementById('video_msg');
		
		document.getElementById('run_msg').textContent = s.message;
		
		if (s.running) {
			btn.value = "Stop";
			btn.disabled = !s.owned;
			if (!stream_shown) {
				frame.src = stream_url;
				frame.style.display = "inline";
				note.style.display = "none";
				stream_shown = true;
			}
		} else {
			btn.value = "Start";
			btn.disabled = s.starting;
			if (stream_shown) {
				frame.src = "about:blank";
				frame.style.display = "none";
				stream_shown = false;
			}
			note.style.display = "block";
			note.textContent = s.starting ? "Starting - loading the camera and the model..." : s.message;
			if (s.starting) {
				setTimeout(refresh_status, 1000);
			}
		}
	}
	
	function button_run(){
		var btn = document.getElementById('run');
		var action = (btn.value == "Start") ? "start" : "stop";
		btn.disabled = true;
		$.post("web/control.php", {action: action}, show_status, "json");
	}
	
   </script>
</head> 
<body onload="init()">
<?php

echo"<div id='box_outer'>";//------------------------
	echo"<div align='center' id='box_header'>";
		echo"<b>Model Garden</b><br>";
		
		echo"<txt id='run_box'>
				<input id='run' type='submit' onclick=button_run(); value='Start' disabled/> <span id='run_msg'>Checking...</span>
			</txt>";
		
		if ($coral) {
			$caption = $on_coral ? "connected" : "disconnected";
			$colour = $on_coral ? "#66ff66" : "white";
			echo"<txt>
				Coral USB Accelerator: <input id='coral' type='submit' onclick=button_coral(); value='$caption' style='background-color:$colour'/>
			</txt>";
		}
		
		
	echo"</div>";
	
	echo"<div align='center' class='box_models'>";//------------------------

		echo"<div class='div_txt'>Classification</div>";
		echo"<input id='b1' type='submit' onclick=button_action('b1'); value='image (mobilenet_v1)'/>";
		echo"<input id='b2' type='submit' onclick=button_action('b2'); value='image (mobilenet_v2)'/>";
			
			
		echo"<input id='b6' type='submit' onclick=button_action('b6'); value='image (inception_v1)'/>";
		echo"<input id='b7' type='submit' onclick=button_action('b7'); value='image (inception_v2)'/>";
		echo"<input id='b8' type='submit' onclick=button_action('b8'); value='image (inception_v3)'/>";
		echo"<input id='b9' type='submit' onclick=button_action('b9'); value='image (inception_v4)'/>";
		
		echo"<hr>";
		
		echo"<input id='b3' type='submit' onclick=button_action('b3'); value='bird (mobilenet_v2)'/>";
		echo"<input id='b4' type='submit' onclick=button_action('b4'); value='insect (mobilenet_v2)'/>";
		echo"<input id='b5' type='submit' onclick=button_action('b5'); value='plant (mobilenet_v2)'/>";
			
	echo"</div>";
	
	echo"<div align='center' id='box_camera'>";
		echo"<div id='video_msg'>Checking whether Model Garden is running...</div>";
		echo"<iframe id='video' height='650px' width='95%' style='display:none'></iframe>";
	echo"</div>";
	
	
	echo"<div align='center' class='box_models'>";
		echo"<div class='div_txt'>Detection</div>";
		echo"<input id='b10' type='submit' onclick=button_action('b10'); value='object (mobilenet_ssd_v1)'/>";
		echo"<input id='b11' type='submit' onclick=button_action('b11'); value='object (mobilenet_ssd_v2)'/>";
		echo"<input id='b12' type='submit' onclick=button_action('b12'); value='face (mobilenet_ssd_v2)'/>";	
	echo"</div>";
	
echo"</div>";

?>

</body>
</html>
