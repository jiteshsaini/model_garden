<!--
Project: Model Garden
Author: Jitesh Saini
Github: https://github.com/jiteshsaini
website: https://helloworld.co.in

Watch this video to see this code in action:-
https://youtu.be/7gWCekMy1mw
-->
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
		//float:left;
		font-size: 17px;
		margin-top:6%;
	}
	.box_models input[type="submit"]:hover {
		//background-color: blue;
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
	
	function init(){
		console.log("started..");
		$.post("/model_garden/web/misc/hw.php",{entry_by: 'model_garden',page: 'index.php'});
	}
	
	function button_action(id)
	{
		var len = Object.keys(model).length
		console.log("len:" + len);
		
		label=document.getElementById(id).value
		label=label.toLowerCase(label);
		console.log("label:" + label);
		var mdl = model[id]
		console.log("mdl:" + mdl);
		$.post("web/comm.php",{model_file: mdl});
		
		$.post("web/comm.php",{command_generated:1});
		
		console.log("id:" + id);
		var i;
		for (i = 1; i <= len; i++) {
			id1='b'+i;
			document.getElementById(id1).style.backgroundColor="#011f61";
			document.getElementById(id1).style.color="white";
			
		}
		
		document.getElementById(id).style.backgroundColor="#00ff00";
		document.getElementById(id).style.color="black";
		
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
	
	
   </script>
</head> 
<body onload="init()">
<?php

$host=$_SERVER['SERVER_ADDR'];//192.168.1.20

$link_vid= 'http://'.$host.':2205';

echo"<div id='box_outer'>";//------------------------
	echo"<div align='center' id='box_header'>";
		echo"<b>Model Garden</b><br>";
		
		echo"<txt>
				Coral USB Accelerator: <input id='coral' width='200px' type='submit' onclick=button_coral(); value='disconnected'/>
			</txt>";
		
		
	echo"</div>";
	
	//echo"<b id='info'></b>";
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
		echo"<iframe src='$link_vid' height='650px' width='95%'></iframe>";
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
