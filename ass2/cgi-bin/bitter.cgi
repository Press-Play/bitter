#!/usr/bin/perl -w

# ============================================================
#
# 		BITTER.CGI
#
#		Khanh Nguyen
#		z3462277
#
# ============================================================


# Clear the terminal before starting
for($i=0;$i<45;$i++){$CONFIG_DEBUG=TRUE;debug("");}

# ------------------------------------------------------------
# 	MODULES AND SETUP
# ------------------------------------------------------------
use CGI 		qw/:all/;
use CGI::Carp 	qw/fatalsToBrowser warningsToBrowser/;
use CGI::Cookie;
use Data::Dumper;
use HTML::Template;
use Storable;

warningsToBrowser(1);

$template = HTML::Template->new(filename => 'index.tmpl');

# ------------------------------------------------------------
# 	CONFIGURATION AND GLOBALS
# ------------------------------------------------------------
# POSIX
use POSIX qw(strftime);

# Constants
use constant {
	# Boolean values
	FALSE 			=> 0,
	TRUE			=> !0,

	# Credential identifiers
	C_BAD_USERNAME	=> 0,
	C_BAD_PASSWORD	=> 1,
	C_VALID			=> 2,
	C_MISSING		=> 3,
	C_TIMEOUT		=> 4,
	C_ERROR			=> 5,

	# Database modes
	DB_DROP			=> 0,	# Start from scratch; use text files
	DB_MIGRATE		=> 1,	# Use existing persisting data is available
	DB_NONE			=> 2,	# Dont use database hash at all
};

# Variable configurations set inside the cgi script
$CONFIG_DEBUG 		= TRUE;
$DATASET_SIZE 		= "huge";
$DATASET_PATH_CGI 	= "dataset-${DATASET_SIZE}";
$DATASET_PATH_HTML	= "../dataset-${DATASET_SIZE}";
$DATASET_MODE		= DB_MIGRATE;

# Global database storage
%store = ();
$store_updated	= FALSE;	# Set to true if the store is updated

# Parameter declarations
# POST - Sensitive information
# $param_email	= param('email');
$param_username = param('username');
$param_password = param('password');
# GET - Sent in url
$param_action	= param('action');
$param_page		= param('page');
$param_profile	= param('profile');				# username
# Any hidden ones
$param_profile	= param('profile_username') if (!$param_profile);

# Cookie declarations
%cookies 			= CGI::Cookie->fetch;
$cookie_session 	= $cookies{'session'} 			if $cookies{'session'};
$cookie_username	= $cookies{'session'}->value() 	if $cookies{'session'};
@cookie_send		= "";	# Cookies to send in response header

# Template variables
# LOGGED_IN
# Reset all template variables to defaults
$template->param(LOGGED_IN 			=> FALSE);
$template->param(PROFILE_USERNAME 	=> "Default");
$template->param(PROFILE_PICTURE 	=> $DATASET_PATH_HTML."/users/DaisyFuentes/profile.jpg");
$template->param(PROFILE_BLEATS 	=> 0);
$template->param(PROFILE_LISTENERS 	=> 0);
$template->param(PROFILE_LISTENING 	=> 0);

$template->param(LISTENS_TO 		=> FALSE);	# True if the logged-in user listens to the profile page we're on
$template->param(PROFILE_PROFILE 	=> FALSE);	# True if the logged-in user is the same as the profile page we're on



# ------------------------------------------------------------
# 	DEBUG FUNCTIONS
# ------------------------------------------------------------
sub debug {
	if ($CONFIG_DEBUG) {
		$t = strftime "%H:%M:%S", localtime;
		$_debug_arg = $_[0];
		$_debug_arg =~ s/([\%])/\%\%/g;
	    #$_debug_arg =~ s/([^ a-zA-Z0-9\%])/\\$1/g;
		printf STDERR "[%s] DEBUG   : $_debug_arg\n", $t;
	}
}

# ------------------------------------------------------------
# 	HELPER FUNCTIONS FOR HELPER FUNCTIONS
# ------------------------------------------------------------
# Finds the key in a hash with the max magnitude
sub max_key(\%) {
	my $_hash = shift;
	keys %$_hash;       # reset the each iterator

	my ($large_key, $large_val) = each %$_hash;

	while (my ($key, $val) = each %$_hash) {
		if ($val > $large_val) {
			# $large_val = $val;
			$large_key = $key;
		}
	}
	return $large_key;
}

# Pushes an array (1) onto the end of another array (0)
sub push_array(\@; \@) {
	for $_item (@{$_[1]}) {
		push(@{$_[0]}, $_item);
	}
	return $_[0];
}

# ------------------------------------------------------------
# 	HELPER FUNCTIONS
# ------------------------------------------------------------
#
#	STORABLES
#
sub storable_init {
	if 		($DATASET_MODE == DB_DROP) 		{ storable_new(); } 
	elsif 	($DATASET_MODE == DB_MIGRATE)	{ storable_retrieve(); } 
	elsif	($DATASET_MODE == DB_NONE)		{ }
	else 	{ die; }
}

# Create new hash from given text files
sub storable_new {
	debug("============================== Creating a new hash database. ==============================");
	# Go through every file in /users/{u-name} and /bleats and create hash

	# For /users/{u-name}
	opendir (D, $DATASET_PATH_CGI."/users") or die;
		@files = readdir(D);
	closedir (D);

	$count = 0;
	foreach $key (@files) {
		next if ($key eq ".");
		next if ($key eq "..");
		if (-d $DATASET_PATH_CGI."/users/${key}") {
			$count++;
			# debug("-------- User found: $key");
			open(F, "<", $DATASET_PATH_CGI."/users/${key}/bleats.txt") or die;
				my @_bleats = <F>;
				@_bleats = grep { $_ =~ /[0-9]+/ } @_bleats;
				foreach $_b (@_bleats) {chomp $_b}
				$store{"users"}{$key}{"bleats"} = \@_bleats;
			close(F);
			open(F, "<", $DATASET_PATH_CGI."/users/${key}/details.txt") or die;
				my @_details = <F>;
				foreach $_deet (@_details) {
					@_props = split ":", $_deet;
					$_setty = $_props[0];
					shift @_props;
					$_propy = join  "", @_props;
					chomp $_propy;
					$_propy =~ s/^\s+//;	# WHITESPACE_LEADING
					$_propy =~ s/\s+$//;	# WHITESPACE_TRAILING
					$store{"users"}{$key}{$_setty} = $_propy;
				}
			close(F);
		}
	}
	debug("---- All $count users found.");

	# For /bleats
	opendir (D, $DATASET_PATH_CGI."/bleats") or die;
		@files = readdir(D);
	closedir (D);

	$count = 0;
	foreach $key (@files) {
		next if ($key eq ".");
		next if ($key eq "..");
		if (-e $DATASET_PATH_CGI."/bleats/${key}") {
			$count++;
			# debug("-------- Bleat found: $key");
			open(F, "<", $DATASET_PATH_CGI."/bleats/${key}") or die;
			@_details = <F>;
			%result = ();
			foreach $_deet (@_details) {
				@_props = split ":", $_deet;
				$_setty = $_props[0];
				# debug("@_props");
				shift @_props;
				$_propy = join  "", @_props;
				chomp $_propy;
				$_propy =~ s/^\s+//;	# WHITESPACE_LEADING
				$_propy =~ s/\s+$//;	# WHITESPACE_TRAILING
				$result{$_setty} = $_propy;
				$store{"bleats"}{$key}{$_setty} = $_propy;
			}
		close(F);
		} else {
			debug("You fucked up");
		}
	}
	debug("---- All $count bleats found.");

	# debug(Dumper(\%store));
	store \%store, 'store.db';
}

# Get existing hash
sub storable_retrieve {
	if (!-e "store.db") { storable_new(); return }

	debug("============================== Retrieving existing hash database. ==============================");
	$store_hashref = retrieve('store.db');
	%store = %$store_hashref;
}

sub storable_update {
	if ($store_updated) {
		debug("============================== Updating existing hash database. ==============================");
		store \%store, 'store.db';
	}
}

#
#	LOGGED_IN
#
sub logged_in_cookie {
	return FALSE if (!$cookie_session);
	return ($cookie_session ne '');
}

sub logged_in_credentials {
	return (valid_credentials() == C_VALID);
}

sub logged_in {
	return (logged_in_credentials() or logged_in_cookie());
}

#
#	CREDENTIALS
#
sub missing_credentials {
	return (!$param_username  or !$param_password);
}

sub valid_credentials {
	if (missing_credentials()) { return C_MISSING; }
	open(F, "<", $DATASET_PATH_CGI."/users/${param_username}/details.txt") or return C_BAD_USERNAME;
		$_result = C_ERROR;
		@_details = <F>;
		@_listens = grep { $_ =~ /password\:/ } @_details;
		# debug("password for $param_username:", chomp $_listens[0]);
		@_listens = split " ", $_listens[0];
		if ($_listens[1] eq $param_password) {
			$_result = C_VALID;
		} else {
			$_result = C_BAD_PASSWORD;
		}
	# C_TIMEOUT
	close(F);
	return $_result;
}

#
#	BLEAT/USER HELPERS
#
# Returns true iff user1 (0) listens to (1)
sub user_listens_to {
	$_user_a = $_[0];
	$_user_b = $_[1];
	die if (!$_user_a or !$_user_b);

	$_a_listens = $store{'users'}{$_user_a}{'listens'};
	@_list = split " ", $_a_listens;
	foreach $_l (@_list) {
		if ($_l eq $_user_b) {
			return TRUE;
		}
	}
	return FALSE;
}

#
#	PARAMETERS - WRITING (to store)
#
# Post a bleat
# TODO
sub parameters_put_new_bleat {
	# Get the bleat_id with biggest value.
	$_bleats_ref = \%{$store{'bleats'}};
	debug("_bleat_ref = $_bleats_ref");
	debug(Dumper($_bleat_ref));
	# $_m = max_key(\%{$store{'bleats'});
	# debug("$_m");
	# $store{'users'}{$param_username}{'listens'}
}

# Listen to a new person (by username)
sub parameters_put_new_listen {
	$store{'users'}{$param_username}{'listens'} .= " ".$_[0];
	$store_updated = TRUE;
}

# Unlisten someone (by username)
sub parameters_del_listen {
	# debug("Trying to delete $_[0]");
	@_listens_old = split " ", $store{'users'}{$param_username}{'listens'};
	$_listens_new = "";
	foreach $_l (@_listens_old) {
		$_listens_new .= $_l." " if ($_l ne $_[0]);
	}
	$_listens_new =~ s/\s+$//;
	$store{'users'}{$param_username}{'listens'} = $_listens_new;
	$store_updated = TRUE;
}

#
#	PARAMETERS - READING (from store)
#
# Returns an array of the ids of the bleats the given user has posted
sub parameters_get_bleat_ids {
	$_given_user = $_[0];
	# Go through bleats.txt and count how many lines (with a bleat id)
	open(F, "<", $DATASET_PATH_CGI."/users/${_given_user}/bleats.txt") or die;
		@_bleats = <F>;
		@_bleats = grep( /[0-9]+/, @_bleats );
	close(F);
	return \@_bleats;
}

# Returns array of the people that the given user is listening to
sub parameters_get_listening {
	$_given_user = $_[0];
	@_listens = split " ", $store{'users'}{$_given_user}{'listens'};
	return \@_listens;
}

# Returns the full name of the given user
sub parameters_get_name {
	$_given_user = $_[0];
	return $store{'users'}{$_given_user}{'full_name'};
}

# Returns all the information related to a given bleat id
sub parameters_get_bleatdata {
	$_bleat_id = $_[0];
	# debug("Trying to open bleat with id: $_bleat_id");
	open(F, "<", $DATASET_PATH_CGI."/bleats/${_bleat_id}") or die;
		@_details = <F>;
		%result = ();
		foreach $_deet (@_details) {
			@_props = split ":", $_deet;
			$_setty = $_props[0];
			# debug("@_props");
			shift @_props;
			$_propy = join  "", @_props;
			chomp $_propy;
			$result{$_setty} = $_propy;
		}
	close(F);
	# debug(Dumper(\%result));
	return \%result;
}

sub parameters_count_bleats {
	$_given_user = $_[0];
	return scalar @{parameters_get_bleat_ids($_given_user)};
}
sub parameters_count_listeners {
	$_given_user = $_[0];
	# TODO, IF USING THIS STOREAGE METHOD, NEED TO UPDATE ON ADD AND DELETE LISTENS
	# $_count = 0;
	# if (exists $store{'users'}{$param_username}{'listeners'}) {
	# 	return $store{'users'}{$param_username}{'listeners'};
	# } else {
	# 	foreach $_db_user ($store{'users'}) {
	# 		if ($_db_user eq $param_username) { next; }
	# 		@_temp_listens = @{parameters_get_listening($_db_user)};
	# 		if (!@_temp_listens) { next; }
	# 		if ( grep( /^${param_username}$/, @_temp_listens ) ) {
	# 			$_count++;
	# 			debug("Found that $_db_user follows $param_username");
	# 		}
	# 	}
	# 	$store{'users'}{$param_username}{'listeners'} = $_count;
	# 	return $_count;
	# }

	# Somehow, if these things don't work, return 0
	return 0;
}
sub parameters_count_listening {
	$_given_user = $_[0];
	return scalar @{parameters_get_listening($_given_user)};
}

# This function is for the logged in user only
# It sets the username parameter variable and also the one on the template
sub parameters_set_username {
	# If the cookie is set, get the username from here
	# otherwise, the username will come from the input field
	if (logged_in_cookie()) {
		$param_username = $cookie_username;
		$template->param(PROFILE_USERNAME => $param_username);
	} else {
		# Username parameter variable already set by default from input field
		$template->param(PROFILE_USERNAME => $param_username);
	}
}

sub parameters_set_bleatfeed {
	my @_bleatfeed_ids = ();

	# Find last 'n' bleat ids that
	#	- current user posted
	push(@_bleatfeed_ids, @{parameters_get_bleat_ids($param_username)});
	#	- current user listens to
	foreach $_list (@{parameters_get_listening($param_username)}) {
		push_array(@_bleatfeed_ids, @{parameters_get_bleat_ids($_list)});
	}
	#	- current user mentioned in
	foreach $_id (keys %{$store{'bleats'}}) {
		# debug("$_id");
		# debug(Dumper(\$store{'bleats'}{$_id}{'bleat'}));
		# Split by space delimeter
		@_mentions = split " ", $store{'bleats'}{$_id}{'bleat'};
		# grep for "@" and "username"
		if (grep /\@${param_username}/, @_mentions) {
			push(@_bleatfeed_ids, $_id);
		}
	}

	# Order the bleat ids, get bleat info and then put into template params
	@bleat_data = ();
	$previous_id = 0;
	foreach $bleat_id (reverse @_bleatfeed_ids) {
		chomp $bleat_id;
		# Check for duplicate ids
		next if ($bleat_id == $previous_id);
		$previous_id = $bleat_id;

		my %temp_data;	# "my" keyword needed for a fresh hash
		my %bleat_me = %{$store{'bleats'}{$bleat_id}};
		# debug(Dumper(\%bleat_me));
		$temp_data{BLEAT_TEXT} 			= $bleat_me{'bleat'};
		$temp_data{BLEAT_TIME} 			= $bleat_me{'time'};
		$temp_data{BLEAT_LOCATION} 		= "lat:".$bleat_me{'latitude'}."<br>long:".$bleat_me{'longitude'} if ($bleat_me{'latitude'} and $bleat_me{'longitude'});
		$temp_data{PROFILE_USERNAME} 	= $bleat_me{'username'};
		$temp_data{PROFILE_PICTURE} 	= $DATASET_PATH_HTML."/users/${bleat_me{'username'}}/profile.jpg";
		push(@bleat_data, \%temp_data);
	}
	$template->param(LOOP_BLEATS => \@bleat_data);
	#delete @bleat_data;

}

# All the parameters on the template to do with and profile page for a given user
sub parameters_set_profile {
	$_given_user = $_[0];
	$template->param(PROFILE_USERNAME => $_given_user);
	parameters_set_base($_given_user);

	if ($_given_user eq $param_username) {
		$template->param(PROFILE_PROFILE => TRUE);
	} else {
		if (user_listens_to($param_username, $_given_user)) {
			$template->param(LISTENS_TO => TRUE);
		} else {
			# Should already be set, but just make sure
			$template->param(LISTENS_TO => FALSE);
		}
	}

	@bleat_data = ();
	foreach $bleat_id (@{parameters_get_bleat_ids($_given_user)}) {
		chomp $bleat_id;
		my %temp_data;	# "my" keyword needed for a fresh hash
		my %bleat_me = %{parameters_get_bleatdata($bleat_id)};
		# debug(Dumper(\%bleat_me));
		$temp_data{BLEAT_TEXT} 			= $bleat_me{'bleat'};
		$temp_data{BLEAT_TIME} 			= $bleat_me{'time'};
		$temp_data{BLEAT_LOCATION} 		= "lat:".$bleat_me{'latitude'}."<br>long:".$bleat_me{'longitude'} if ($bleat_me{'latitude'} and $bleat_me{'longitude'});
		$temp_data{PROFILE_USERNAME} 	= $_given_user;
		$temp_data{PROFILE_PICTURE} 	= $DATASET_PATH_HTML."/users/${_given_user}/profile.jpg";
		push(@bleat_data, \%temp_data);
	}
	$template->param(LOOP_BLEATS => \@bleat_data);
	#delete @bleat_data;

	# Get the users that they listen to
	@listening_data = ();
	foreach $username (@{parameters_get_listening($_given_user)}) {
		my %temp_data;	# "my" keyword needed for a fresh hash
		$temp_data{USERNAME} = "$username";
		push(@listening_data, \%temp_data);
	}
	$template->param(LOOP_LISTENS => \@listening_data);
}

# Use the username to get all other information
sub parameters_set_base {
	$_given_user = $_[0];
	# Dashboard profile card
	$template->param(PROFILE_PICTURE 	=> $DATASET_PATH_HTML."/users/${_given_user}/profile.jpg");
	$template->param(PROFILE_NAME 		=> parameters_get_name($_given_user));
	$template->param(PROFILE_BLEATS 	=> parameters_count_bleats($_given_user));
	$template->param(PROFILE_LISTENERS 	=> parameters_count_listeners($_given_user));
	$template->param(PROFILE_LISTENING 	=> parameters_count_listening($_given_user));
}

#
#	COOKIES
#
sub cookie_login_session {
	if (logged_in_cookie()) { return; }
	$_c = CGI::Cookie->new(
		-name    =>  'session',
		-value   =>  $param_username,
		-expires =>  '+120m'
	);
	#$_c->bake;
	push(@cookie_send, $_c);
	debug("Cookie set: $_c");
}

sub cookie_logout_session {
	if (!logged_in_cookie()) { return; }
	$_c = CGI::Cookie->new(
		-name    =>  'session',
		-value   =>  $param_username,
		-expires =>  'now'
	);
	#$_c->bake;
	push(@cookie_send, $_c);
	debug("Cookie set: $_c");
}

sub cookie_output {
	$_result = "";
	foreach $_bake_me (@cookie_send) {
		$_result .= "Set-Cookie: $_bake_me\n";
	}
	return $_result;
}


# ------------------------------------------------------------
# 	SUB-SUB RESPONSE HANDLERS
# ------------------------------------------------------------
#
#	ACTION HANDLES
#
# Called when logout parameter is set from request
sub handle_logout {
	return if (!$param_page);
	return if ($param_page ne "logout");
	cookie_logout_session();
	$template->param(LOGGED_IN => FALSE);
}

sub handle_listen {
	return if (!$param_action);
	
	if ($param_action eq "listen") {
		parameters_put_new_listen($param_profile);
	} elsif ($param_action eq "unlisten") {
		parameters_del_listen($param_profile);
	} else {
		# Nothing happens, just return
	}
}

sub handle_bleat {
	return if (!$param_action);
	return if ($param_action ne "bleat");

	debug("User attempted to bleat! (To bad it's not implemented yet)");
	parameters_put_new_bleat();
}

#
#	PAGE HANDLES
#
# Called when profile parameter is set from request
sub handle_page_profile {
	return if (!$param_profile);
	return if (!$param_page);
	return if ($param_page ne "profile");
	$template->param(PAGE_PROFILE => TRUE);
	#if (!-d $DATASET_PATH_CGI."/users/${param_username}")
	parameters_set_profile($param_profile);
}

sub handle_page_search {

}

sub handle_page_settings {

}


# ------------------------------------------------------------
# 	SUB RESPONSE HANDLERS
# ------------------------------------------------------------
# Run this when we're logged in
sub handle_yes {
	debug("HANDLE_YES: LOGGED IN"); 

	storable_init();

	$template->param(LOGGED_IN => TRUE);
	cookie_login_session();

	# Always make sure username parameter variable set
	parameters_set_username();

	if (!$param_page or ($param_page eq "home")) {
		parameters_set_base($param_username);
		parameters_set_bleatfeed();
	}

	# Handles (actions first, then page)
	handle_listen();
	handle_bleat();
	handle_logout();

	handle_page_profile();
}

# Run this when NOT logged in
sub handle_no {
	debug("HANDLE_NO: NOT LOGGED IN");
	$template->param(LOGGED_IN => FALSE);
	$template->param(PAGE_SIGNUP => TRUE) if ($param_page eq "signup");
}

# Run this for all error responses
sub handle_err {
	debug("HANDLE_ERR: WHAT HAPPENED?");
}
# ------------------------------------------------------------
# 	MAIN RESPONSE HANDLER
# ------------------------------------------------------------
if 		( logged_in() ) 			{ handle_yes(); }
elsif	( missing_credentials() ) 	{ handle_no() ; }
else								{ handle_err(); }

print cookie_output() if cookie_output();
print "Content-Type: text/html\n\n";
print $template->output;

storable_update();



