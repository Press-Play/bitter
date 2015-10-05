#!/usr/bin/perl -w

# ============================================================
#
# 		BITTER.CGI
#
#		Khanh Nguyen
#		z3462277
#
# ============================================================


# ------------------------------------------------------------
# 	MODULES AND SETUP
# ------------------------------------------------------------
use CGI 		qw/:all/;
use CGI::Carp 	qw/fatalsToBrowser warningsToBrowser/;
use CGI::Cookie;
use HTML::Template;

warningsToBrowser(1);

# ------------------------------------------------------------
# 	CONFIGURATION AND GLOBALS
# ------------------------------------------------------------
# Parameter declarations
$param_email	= param('email')	|| '';
$param_username = param('username') || '';
$param_password = param('password') || '';


# ------------------------------------------------------------
# 	MAIN RESPONSE HANDLER
# ------------------------------------------------------------
# print header(-cookie => $cookie_variable);
# $cookie_variable -> bake;

# if 		(!logged_In()) 			{}
# elsif	(incorrectPassword()) 	{}
# else							{}

# TEST
print 	header,                    # create the HTTP header
		start_html('hello world'), # start the HTML
		h1('hello world'),         # level 1 header
		end_html;                  # end the HTML