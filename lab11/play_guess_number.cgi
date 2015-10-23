#!/usr/bin/perl -w
# Simple CGI script written by andrewt@cse.unsw.edu.au
# Outputs a form which will rerun the script
# An input field of type hidden is used to pass an integer
# to successive invocations
# Two submit buttons are used to produce different actions

use CGI qw/:all/;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);

print <<eof;
Content-Type: text/html

<!DOCTYPE html>
<html lang="en">
<head>
    <title>Handling Multiple Submit Buttons</title>
</head>
<body>
eof
warningsToBrowser(1);

$hidden_variable = param("x") || 50;
$guess_max  = param("max") || 100;
$guess_min  = param("min") || 1;
$correct    = param("correct") || '';
$play_again = param("play") || '';

if ($correct) {
    print <<eof;
<h2>$hidden_variable</h2>
<form method="post" action="">
<p>I win</p>
<input type="submit" name="play" value="Play Again">
</form>
</body>
</html>
eof
exit;
}

if (defined param("increment")) {
    # Value is between x and max
    $guess_min = $hidden_variable;
	$hidden_variable = int(($hidden_variable + $guess_max)/2);
} elsif (defined param("decrement")) {
    # Value is between min and x
	$guess_max = $hidden_variable;
	$hidden_variable = int(($guess_min + $hidden_variable)/2);
}

print <<eof;
<form method="post" action="">
<p>My guess is: <h2>$hidden_variable</h2></p>
<input type=hidden name="x" value="$hidden_variable">
<input type=hidden name="max" value="$guess_max">
<input type=hidden name="min" value="$guess_min">
<input type="submit" name="increment" value="Higher">
<input type="submit" name="correct" value="Correct">
<input type="submit" name="decrement" value="Lower">
</form>
</body>
</html>
eof
