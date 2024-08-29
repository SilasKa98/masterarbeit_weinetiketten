<?php
$env = parse_ini_file('../.env');
if($_POST["called_from"] == "admin"){
   $path = $env["IMAGES_PATH"]; 
}elseif($_POST["called_from"] == "eval"){
    $path = $env["EVALUATION_TEXTS_PATH"]; 
}

$comb_path = realpath(__DIR__ . '/'.$path);
$directories = glob($comb_path . '/*' , GLOB_ONLYDIR);

array_unshift($directories, $comb_path);


// Pfade für JSON enkodieren (Backslashes korrekt behandeln)
$directories = array_map('str_replace', array_fill(0, count($directories), '\\'), array_fill(0, count($directories), '/'), $directories);

$json_data = json_encode($directories);


print $json_data;

?>