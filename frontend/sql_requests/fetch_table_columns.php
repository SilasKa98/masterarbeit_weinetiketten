<?php
include_once "db_connector.php";
$table = preg_replace('/[^a-zA-Z0-9_]/', '', $_POST["table"]);

$sql= "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = ?;";
	$stmt = mysqli_stmt_init($connection);
	if(!mysqli_stmt_prepare($stmt, $sql)){
		echo "SQL Statement failed";
	}else{
		mysqli_stmt_bind_param($stmt, "s", $table);
		mysqli_stmt_execute($stmt);
		$result = mysqli_stmt_get_result($stmt);
        $cols = [];
		while ($row= $result->fetch_assoc()) {
            array_push($cols, $row);
		}
	}

print_r(json_encode($cols));
$stmt->close();
$connection->close();
?>