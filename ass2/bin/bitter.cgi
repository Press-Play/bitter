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

$template = HTML::Template->new(filename => 'index.tmpl');

# ------------------------------------------------------------
# 	CONFIGURATION AND GLOBALS
# ------------------------------------------------------------

use constant {
	# Boolean values
	FALSE 			=> 0,
	TRUE			=> !0,
};

# Parameter declarations
$param_email	= param('email')	|| '';
$param_username = param('username') || '';
$param_password = param('password') || '';

# Template variables
# LOGGED_IN
# Reset all template variables
$template->param(LOGGED_IN => TRUE);
$template->param(PROFILE_USERNAME => "TestUsername");
$template->param(PROFILE_PICTURE => "../dataset-small/users/DaisyFuentes/profile.jpg");
$template->param(PROFILE_BLEATS => 7);
$template->param(PROFILE_LISTENERS => 45);
$template->param(PROFILE_LISTENING => 60);

# ------------------------------------------------------------
# 	MAIN RESPONSE HANDLER
# ------------------------------------------------------------
print header, $template->output;
# print header(-cookie => $cookie_variable);
# $cookie_variable -> bake;

# if 		(!logged_In()) 			{}
# elsif	(incorrectPassword()) 	{}
# else							{}

# TEST
# print 	header,                    # create the HTTP header
# 		start_html('hello world'), # start the HTML
# 		h1('hello world'),         # level 1 header
# 		end_html;                  # end the HTML





