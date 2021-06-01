<?php

$model=@$_POST["model_file"];
$cmd_generated=@$_POST["command_generated"];
$edgetpu=@$_POST["edgetpu"];

//$model=@$_GET["mm"];
//$cmd_rx=@$_GET["cc"];

if($model!=''){
	$myfile = fopen("model.txt", "w") or die("Unable to open file!");
	fwrite($myfile, $model);
	fclose($myfile);
	echo"model<br>";
}

if($cmd_generated!=''){
	$myfile = fopen("command_received.txt", "w") or die("Unable to open file!");
	fwrite($myfile, $cmd_generated);
	fclose($myfile);
	echo"command<br>";
}

if($edgetpu!=''){
	$myfile = fopen("edgetpu.txt", "w") or die("Unable to open file!");
	fwrite($myfile, $edgetpu);
	fclose($myfile);
	echo"command<br>";
}

?>
