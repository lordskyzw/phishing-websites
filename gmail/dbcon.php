<?php
	
	$conn = mysqli_connect('localhost','root','','gmail');

	if ($conn == false) 
	{
		echo "Database connection failed";
	}
?>