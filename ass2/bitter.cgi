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
# Start the timer
use Time::HiRes qw/gettimeofday/;$timer_start=gettimeofday();

# ------------------------------------------------------------
# 	MODULES AND SETUP
# ------------------------------------------------------------
use CGI 		qw/:all/;
use CGI::Carp 	qw/fatalsToBrowser warningsToBrowser/;
use CGI::Cookie;
use Data::Dumper;
use HTML::Template;
use Storable;
use Net::SMTP;

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
	C_NONE			=> 6,

	# Database modes
	DB_DROP			=> 0,	# Start from scratch; use text files
	DB_MIGRATE		=> 1,	# Use existing persisting data is available
	DB_NONE			=> 2,	# Dont use database hash at all

	# Parameter variable array indices
	# P_USERNAME 		=> 0,
	# P_PASSWORD 		=> 1,
	# P_ACTION 			=> 2,
	# P_PAGE 			=> 3,
	# P_PROFILE 		=> 4,
};

# Variable configurations set inside the cgi script
$CONFIG_DEBUG 		= FALSE;
$PATH_ROOT_HTML		= "";
$DATASET_SIZE 		= "large";
$DATASET_PATH_CGI 	= "dataset-${DATASET_SIZE}";#"dataset-${DATASET_SIZE}";
$DATASET_PATH_HTML	= "dataset-${DATASET_SIZE}";#"../dataset-${DATASET_SIZE}";
$DATASET_MODE		= DB_MIGRATE;

# Global database storage
%store = ();
$store_updated	= FALSE;	# Set to true if the store is updated

# Parameter declarations
# POST - Sensitive information
$param_email		= param('email');
$param_name 		= param('name');
$param_username 	= param('username');
$param_password 	= param('password');
$param_bleat 		= param('bleat');			# Posting a bleat
$param_query		= param('query');			# Query search string
$param_dir			= param('dir');				# Back and next buttons on pagination console
$param_reply_to		= param('reply_to');		# If a bleat is being replied to - send id of it
$param_key			= param('key');				# Signup confirmation key
$param_description	= param('description');		# About me
$param_home_loc		= param('home_suburb');
$param_home_lat		= param('home_latitude');
$param_home_long	= param('home_longitude');
$param_new_username = param('new_username');
$param_file_photo	= param('file_photo');
$param_file_ground	= param('file_background');
$param_delete       = param('delete');
$param_suspend      = param('suspend');
$param_notification = param('notification');
# GET - Sent in url
$param_action		= param('action');      if (!$param_action) { $param_action = 'none' };
$param_page			= param('page');        if (!$param_page)   { $param_page = 'none' };
$param_profile		= param('profile');		# Username
$param_pagination 	= param('n');			#if (!$param_pagination) { $param_pagination = '10' };
$param_set 			= param('p');			if (!$param_set) 		{ $param_set 		= '0'; }; 	# Apparently, the whole concept of "or" doesnt work, idk
$param_constraint	= param('search');		if (!$param_constraint) { $param_constraint = 'username'; };
$param_bid          = param('bid');         # Id of bleat for bleat page
# Any hidden ones
$param_profile	= param('profile_username') if (!$param_profile);
# File handles
# $query = new CGI;
# $upload_photo 	= $query->upload('file_photo');
# $upload_ground 	= $query->upload('file_background');
# $cgi_error		= $query->cgi_error();
# debug("$cgi_error") if $cgi_error;


# TODO: FULLY REFACTOR
%param	= ();
$param{'email'} 		= $param_email;
$param{'name'}			= $param_name;
$param{'username'} 		= $param_username;
$param{'password'} 		= $param_password;
$param{'bleat'} 		= $param_bleat;
$param{'query'} 		= $param_query;
$param{'dir'}			= $param_dir;
$param{'reply_to'}  	= $param_reply_to;
$param{'key'} 			= $param_key;
$param{'action'}		= $param_action;
$param{'page'}			= $param_page;
$param{'profile'} 		= $param_profile;
$param{'n'} 			= $param_pagination;
$param{'p'} 			= $param_set;
$param{'constraint'}	= $param_constraint;
$param{'description'}	= $param_description;
$param{'home_loc'}		= $param_home_loc;
$param{'home_lat'}		= $param_home_lat;
$param{'home_long'}		= $param_home_long;
$param{'new_username'}	= $param_new_username;

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
$template->param(PROFILE_PICTURE 	=> $PATH_ROOT_HTML."/images/icon_default_256.png");
$template->param(PROFILE_BACKGROUND => "");
$template->param(PROFILE_BLEATS 	=> 0);
$template->param(PROFILE_LISTENERS 	=> 0);
$template->param(PROFILE_LISTENING 	=> 0);

$template->param(LISTENS_TO 		=> FALSE);	# True if the logged-in user listens to the profile page we're on
$template->param(PROFILE_PROFILE 	=> FALSE);	# True if the logged-in user is the same as the profile page we're on

$template->param(PAGE_HOME => TRUE);	# Home page always set to true unless overidden
$template->param(PAGE_LOGIN => TRUE);	# Same with login page (if not logged in)

$template->param(PAGINATION_SET => "$param_set");

$template->param(PARAM_PAGE 	=> $param_page);		# Keep the page we're on
$template->param(PARAM_PROFILE 	=> $param_profile);		# Keep the profile we may be on
$template->param(PARAM_QUERY 	=> $param_query);		# Keep the search query when changing pages
$template->param(PARAM_ACTION 	=> $param_action);		# Double action on page next but also searching

$template->param(SEARCH_QUERY 			=> FALSE);				# True if search query defined (false also if no results)
$template->param(SEARCH_CONSTRAINT 		=> $param_constraint);
$template->param(CONSTRAINT_USERNAME 	=> FALSE);
$template->param(CONSTRAINT_NAME 		=> FALSE);
$template->param(CONSTRAINT_BLEAT 		=> FALSE);



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
sub max_key {
	my $_hash = $_[0];

	$_max_key = 0;
	foreach $_key (keys %{$_hash}) {
		if (int($_key) > int($_max_key)) {
			debug("KEY: $_key");
			$_max_key = $_key;
		}
	}
	return $_max_key;
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

	# Time how long it takes
	$timer_start_store = gettimeofday();

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
				# Count people listening
				@listening = @{parameters_get_listening($key)};
				# debug(Dumper(\@listening));
				foreach $listener (@listening) {
					if (!exists $store{'users'}{$listener}{'listening'}) {
						$store{'users'}{$listener}{'listening'} = 1;
					} else {
						$store{'users'}{$listener}{'listening'}++;
					}
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
			# %result = ();
			foreach $_deet (@_details) {
				@_props = split ":", $_deet;
				$_setty = $_props[0];
				# debug("@_props");
				shift @_props;
				$_propy = join  "", @_props;
				chomp $_propy;
				$_propy =~ s/^\s+//;	# WHITESPACE_LEADING
				$_propy =~ s/\s+$//;	# WHITESPACE_TRAILING
				# $result{$_setty} = $_propy;
				$store{"bleats"}{$key}{$_setty} = $_propy;
			}
			# Check for bleat reply to
			if (exists $store{'bleats'}{$key}{'in_reply_to'}) {
				$replying_to = $store{'bleats'}{$key}{'in_reply_to'};
				push(@{$store{'bleats'}{$replying_to}{'replies'}}, $key);
			}
		close(F);
		} else {
			debug("You fucked up");
		}
	}
	debug("---- All $count bleats found.");

	# Now set up better indexing for speed optimisation
	# foreach $bleat (keys %{$store{'bleats'}}) {
	# 	foreach $bleat_reply (keys %{$store{'bleats'}}) {
	# 		if (exists $store{'bleats'}{$bleat_reply}{'in_reply_to'}) {
	# 			if ($store{'bleats'}{$bleat_reply}{'in_reply_to'} eq $bleat) {
	# 				push(@{$store{'bleats'}{$bleat}{'replies'}}, $bleat_reply);
	# 			}
	# 		}
	# 	}
	# 	# debug("------ For bleat $bleat, we found it had replies");
	# 	# debug(Dumper($store{'bleats'}{$bleat}{'replies'}));
	# }
	# debug("---- Bleat replies sorted.");
	# debug("---- Listeners added users.");

	$timer_finish_store = gettimeofday();
	$timer_elapsed_store = int(($timer_finish_store - $timer_start_store) * 100);
	debug("Setting up the store took ${timer_elapsed_store}ms");

	# debug(Dumper(\%store));
	store \%store, 'store.db';
}

# Get existing hash
sub storable_retrieve {
	if (!-e "store.db") { storable_new(); return }

	debug("============================== Retrieving existing hash database. ==============================");
	$store_hashref = retrieve('store.db');
	%store = %$store_hashref;

	# Set persisted settings/params
	if (!$store{'persists'}{'pagination'}) {
	    $param_pagination 	= '10';
	} else {
	    $param_pagination 	= $store{'persists'}{'pagination'} 	if (!$param_pagination);
	}
	if ($param_pagination == 10)  { $template->param(PAGINATION_10  => TRUE); } else { $template->param(PAGINATION_10  => FALSE); }
	if ($param_pagination == 25)  { $template->param(PAGINATION_25  => TRUE); } else { $template->param(PAGINATION_25  => FALSE); }
	if ($param_pagination == 50)  { $template->param(PAGINATION_50  => TRUE); } else { $template->param(PAGINATION_50  => FALSE); }
	if ($param_pagination == 100) { $template->param(PAGINATION_100 => TRUE); } else { $template->param(PAGINATION_100 => FALSE); }
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
    return FALSE if ($param_page eq "signup");
	return (logged_in_credentials() or logged_in_cookie());
}

#
#	CREDENTIALS
#
sub no_credentials {
	return (!$param_username and !$param_password);
}

sub missing_credentials {
	return ((!$param_username and $param_password) or (!$param_password and $param_username));
}

sub valid_credentials {
	if (no_credentials()) 							{ return C_NONE; }
	if (missing_credentials()) 						{ return C_MISSING; }
	if (!exists $store{'users'}{$param_username}) 	{ return C_BAD_USERNAME; }

    # if (!$store{'users'}{$param_username}{'password'}) { return C_BAD_PASSWORD; }
	if ($param_password eq $store{'users'}{$param_username}{'password'}) {
		return C_VALID;
	} else {
		return C_BAD_PASSWORD;
	}

	return C_ERROR;
}

#
#	SIGN UP
#
sub signup_complete {
	return ($param_username and $param_email and $param_password);
}

sub signup_exists_username {
	return (exists $store{'users'}{$param_username});
}

sub signup_valid_username {
	$_result = TRUE;
	if ((length $param_username < 4)
	or 	($param_username !~ m/[a-zA-Z0-9]+/g))
		{ $_result = FALSE; }
	return $_result;
}

sub signup_valid_email {
	$_result = TRUE;
	if ($param_email !~ m/@/g)
		{ $_result = FALSE; }
	return $_result;
}

sub signup_valid_password {
	$_result = TRUE;
	if ((length $param_password < 5)
	or 	($param_password !~ m/[a-zA-Z0-9]+/g))
		{ $_result = FALSE; }
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
sub parameters_put_new_bleat {
	return if (!$_[0]);
	# Get the bleat_id with biggest value.
	$_id = max_key($store{'bleats'});
	debug("Highest bleat id: $_id");
	$_id++;
	
	# Write the bleat id to to user's thing
	push(@{$store{'users'}{$param_username}{'bleats'}}, $_id);

	# Set the bleat data
	# $_bleat_ref = $store{'bleats'}{$_id};
	$the_time = time();
	$store{'bleats'}{$_id}{'bleat'} 		= $_[0];
	$store{'bleats'}{$_id}{'username'} 		= $param_username;
	$store{'bleats'}{$_id}{'time'} 			= "$the_time";
	$store{'bleats'}{$_id}{'in_reply_to'} 	= $param_reply_to if ($param_reply_to);
	push(@{$store{'bleats'}{$param_reply_to}{'replies'}}, $_id) if ($param_reply_to);
	# debug(Dumper($store{'bleats'}{$_id}));
	# debug(Dumper($store{'bleats'}{$param_reply_to}));
	$store_updated = TRUE;
	
	# Send the email as a notification if they have it turnt on
	# Need to check if a user is mentioned and also the person being replied to
	@_bleat_words = split " ", $_[0];
	foreach $_mention (@_bleat_words) {
	    next if (!$_mention =~ m/^\@/);
	    $_mention =~ s/^\@//;
	    next if (!$store{'users'}{$_mention}{'notifications'});
	    $_email = $store{'users'}{$_mention}{'email'};
        open MUTT, "|mutt -s Bitter -e 'set copy=no' -- '$_email'" or die "Cannot email";
	        print MUTT "Someone mentioned you in bleat!";
        close MUTT or die "not right: $?\n";
	}
	if ($param_reply_to) {
	    $_user = $store{'bleats'}{$param_reply_to}{'username'};
	    return if (!$store{'users'}{$_user}{'notifications'});
	    $_email = $store{'users'}{$_user}{'email'};
        open MUTT, "|mutt -s Bitter -e 'set copy=no' -- '$_email'" or die "Cannot email";
	        print MUTT "Someone replied to your bleat!";
        close MUTT or die "not right: $?\n";
	}
	
}

# Listen to a new person (by username)
sub parameters_put_new_listen {
	$store{'users'}{$param_username}{'listens'} .= " ".$_[0];
	$store{'users'}{$_[0]}{'listening'}++;
	$store_updated = TRUE;
	
	# Send the email as a notification if they have it turnt on
	return if (!$store{'users'}{$_[0]}{'notifications'});
	$_email = $store{'users'}{$_[0]}{'email'};
    open MUTT, "|mutt -s Bitter -e 'set copy=no' -- '$_email'" or die "Cannot email";
	    print MUTT "You got a new listener!";
    close MUTT or die "not right: $?\n";
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
	$store{'users'}{$_[0]}{'listening'}--;
	$store_updated = TRUE;
}

#
#	PARAMETERS - READING (from store)
#
# Returns an array of the ids of the bleats the given user has posted
sub parameters_get_bleat_ids {
	$_given_user = $_[0];
	return \@{$store{'users'}{$_given_user}{'bleats'}};
}

# Returns array of the people that the given user is listening to
sub parameters_get_listening {
	$_given_user = $_[0];
	my @_listens = ();
	return \@_listens if (!$store{'users'}{$_given_user}{'listens'});
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
	# debug(Dumper(\%result));
	return $store{'bleats'}{$_bleat_id};
}

sub parameters_count_bleats {
	$_given_user = $_[0];
	return scalar @{parameters_get_bleat_ids($_given_user)};
}
sub parameters_count_listeners {
	$_given_user = $_[0];
	if (!exists $store{'users'}{$_given_user}{'listening'}) {
	    # TODO: Count instead of returning 0
		return 0;
	} else {
		return $store{'users'}{$_given_user}{'listening'};
	}
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

# Takes in the length of the feed needed to be displayed
# and returns begining and end index to show
sub parameters_set_pagination {
	$_arr_len = $_[0];
	# Go through fail-safes to make sure numbers are good
	if ($param_set < 0) {
		$param_set = 0;
	}
	$_begin = $param_set * $param_pagination;
	$_end 	= (($param_set + 1) * $param_pagination) - 1;
	if ($_begin >= $_arr_len) {
		$_begin 	= 0;
		$_end 		= $param_pagination;
		$param_set 	= 0;
	}
	if ($_end >= $_arr_len) {
		$_end = ($_arr_len) - 1;
	}
	$template->param(PAGINATION_SET => "$param_set");
	return ($_begin, $_end);
}

# This is an important function
# Given an array (ref) of bleat ids, set all the things to do with bleats
# This doesn't really need to return anything - maybe boolean for function completion
sub parameters_set_feeds {
	@_feed_ids = @{$_[0]};

	# Order the bleat ids, get bleat info and then put into template params
	@bleat_data = ();
	$previous_id = 0;
	# chomp @_bleatfeed_ids;
	# @_bleatfeed_ids = sort {$b <=> $a} @_bleatfeed_ids;

	($begin, $end) = parameters_set_pagination(scalar @_feed_ids);

	debug("Displaying bleats with index $begin to $end");
	foreach $index ($begin..$end) {
		$bleat_id = $_feed_ids[$index];

		# Check for duplicate ids
		next if ($bleat_id == $previous_id);
		$previous_id = $bleat_id;

		my %temp_data;	# "my" keyword needed for a fresh hash
		my %bleat_me = %{parameters_get_bleatdata($bleat_id)};

		# Fix up time formatting
		($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = gmtime($bleat_me{'time'});
		$year = $year + 1900;
		$mon += 1;

		# debug(Dumper(\%bleat_me));
		$temp_data{BLEAT_ID} 			= $bleat_id unless ($param_action eq "search");
		$temp_data{BLEAT_TEXT} 			= $bleat_me{'bleat'};
		$temp_data{BLEAT_TIME} 			= "$mday/$mon/$year";
		$temp_data{BLEAT_LOCATION} 		= "latlng=$bleat_me{'latitude'},$bleat_me{'longitude'}" if ($bleat_me{'latitude'} and $bleat_me{'longitude'});
		$temp_data{PROFILE_USERNAME} 	= $bleat_me{'username'};
		if (-e $DATASET_PATH_CGI."/users/${bleat_me{'username'}}/profile.jpg") {
			$temp_data{PROFILE_PICTURE} = $DATASET_PATH_HTML."/users/${bleat_me{'username'}}/profile.jpg";
		} else {
			$temp_data{PROFILE_PICTURE} = $PATH_ROOT_HTML."images/icon_default_256.png";
		}

		# Need to do these again since we're in a template variable loop
		$temp_data{PARAM_PAGE} 		=  $param_page      unless ($param_action eq "search");
		$temp_data{PARAM_PROFILE} 	=  $param_profile   unless ($param_action eq "search");

		# -------------------- Set replied bleats --------------------
		# Go through every bleat and push it if it is a reply
		if (!$param_page or $param_page ne "search") {
			my @bleat_data_reply;	# Need a new hash here
			
			# debug(Dumper($store{'bleats'}{$bleat_id}));
			foreach $reply (@{$store{'bleats'}{$bleat_id}{'replies'}}) {
				# debug("Setting reply for $bleat_id - $reply");
				my %temp_data_reply;
				my %bleat_me_reply = %{parameters_get_bleatdata($reply)};
				# Fix up time formatting
				($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = gmtime($bleat_me_reply{'time'});
				$year = $year + 1900;
				$mon += 1;
				$temp_data_reply{REPLY_ID}   		= $reply;
				$temp_data_reply{REPLY_TEXT} 		= $bleat_me_reply{'bleat'};
				$temp_data_reply{REPLY_USERNAME} 	= $bleat_me_reply{'username'};
				if (-e $DATASET_PATH_CGI."/users/${bleat_me_reply{'username'}}/profile.jpg") {
					$temp_data_reply{REPLY_PICTURE} = $DATASET_PATH_HTML."/users/${bleat_me_reply{'username'}}/profile.jpg";
				} else {
					$temp_data_reply{REPLY_PICTURE} = $PATH_ROOT_HTML."images/icon_default_256.png";
				}
				$temp_data_reply{REPLY_TIME} 		= "$mday/$mon/$year";
				$temp_data_reply{REPLY_LOCATION} 	= "latlng=$bleat_me_reply{'latitude'},$bleat_me_reply{'longitude'}" if ($bleat_me_reply{'latitude'} and $bleat_me_reply{'longitude'});
				push(@bleat_data_reply, \%temp_data_reply);
			}

			$temp_data{LOOP_REPLIES} = \@bleat_data_reply;
		}
		push(@bleat_data, \%temp_data);
	}
	$template->param(LOOP_BLEATS 	=> \@bleat_data);
	# debug(Dumper(\@bleat_data));
	#delete @bleat_data;
}

# Sets the bleats for the homepage
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
	chomp @_bleatfeed_ids;
	@_bleatfeed_ids = sort {$b <=> $a} @_bleatfeed_ids;

	parameters_set_feeds(\@_bleatfeed_ids);
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

	# Order the bleat ids, get bleat info and then put into template params
	my @_bleatfeed_ids = ();
	@_bleatfeed_ids = @{parameters_get_bleat_ids($_given_user)};
	chomp @_bleatfeed_ids;
	@_bleatfeed_ids = sort {$b <=> $a} @_bleatfeed_ids;

	parameters_set_feeds(\@_bleatfeed_ids);

	# Get the users that they listen to
	@listening_data = ();
	foreach $username (@{parameters_get_listening($_given_user)}) {
		my %temp_data;	# "my" keyword needed for a fresh hash
		$temp_data{USERNAME} = "$username";
		push(@listening_data, \%temp_data);
	}
	$template->param(LOOP_LISTENS => \@listening_data);
}

# This is for the search feed
sub parameters_set_searchfeed {
	# There are 3 things the user can be searching by
	#	- username
	#	- actual name
	#	- bleat (content)

	# Make sure the search query has no funnies
	$param_query =~ s/[^0-9a-z]//gi;

	# Set the constraint and perform the search
	# return results as username or bleatid in the following array
	@resulting_arr = ();
	#
	#	Username search
	#
	if ($param_constraint eq "username") {
		# Go through all usernames and find partial matches with regex
		foreach $u (%{$store{'users'}}) {
			if ($u =~ m/${param_query}/i) {
				debug("Result for search found: $u");
				push @resulting_arr, $u;
			}
		}
	#
	#	Name search
	#
	} elsif ($param_constraint eq "name") {
		# Go through all usernames and find partial matches with regex of NAME
		foreach $n (%{$store{'users'}}) {
			next if (!$store{'users'}{$n}{'full_name'});
			if ($store{'users'}{$n}{'full_name'} =~ m/${param_query}/i) {
				debug("Result for search found: $n");
				push @resulting_arr, $n;
			}
		}
	#
	#	Bleat search
	#
	} elsif ($param_constraint eq "bleat") {
		foreach $b (keys %{$store{'bleats'}}) {
			if ($store{'bleats'}{$b}{'bleat'} =~ m/${param_query}/i) {
				debug("Result for search found: $b");
				push @resulting_arr, $b;
			}
		}

		# CLOSING STATEMENT
		# Check to see if results were generated
		if (!@resulting_arr) {
			$template->param(SEARCH_QUERY => FALSE);
			return;
		} else {
			@resulting_arr = sort @resulting_arr;
			parameters_set_feeds(\@resulting_arr);
			return;
		}
	} else {
		die "You pooped up";
	}



	# Check to see if results were generated
	if (!@resulting_arr) {
		$template->param(SEARCH_QUERY => FALSE);
		return;
	}

	@bleat_data = ();
	@resulting_arr = sort @resulting_arr; # So that results display same everytime - perl hashes go random and shit
	($begin, $end) = parameters_set_pagination(scalar @resulting_arr);
	foreach $_i ($begin..$end) {
		$_elem = $resulting_arr[$_i];
		my %temp_data;	# "my" keyword needed for a fresh hash
		$temp_data{USERNAME} 	= $_elem;
		$temp_data{NAME} 		= $store{'users'}{$_elem}{'full_name'};
		if (-e $DATASET_PATH_CGI."/users/$_elem/profile.jpg") {
			$temp_data{PICTURE} = $DATASET_PATH_HTML."/users/$_elem/profile.jpg";
		} else {
			$temp_data{PICTURE} = $PATH_ROOT_HTML."images/icon_default_256.png";
		}
		$temp_data{LISTENERS} 	= parameters_count_listeners($_elem);
		$temp_data{LISTENING} 	= parameters_count_listening($_elem);
		push(@bleat_data, \%temp_data);
	}
	$template->param(LOOP_SEARCH => \@bleat_data);
}

# Use the username to get all other information
sub parameters_set_base {
	$_given_user = $_[0];
	# Dashboard profile card
	if (-e $DATASET_PATH_CGI."/users/${_given_user}/profile.jpg") {
		$template->param(PROFILE_PICTURE 	=> $DATASET_PATH_HTML."/users/${_given_user}/profile.jpg");
	} else {
		$template->param(PROFILE_PICTURE 	=> $PATH_ROOT_HTML."images/icon_default_256.png");
	}
	$template->param(PROFILE_NAME 			=> parameters_get_name($_given_user));
	$template->param(PROFILE_EMAIL 			=> $store{'users'}{$_given_user}{'email'});
	# Only need to sanitise if in the form
	$sanitise_description = $store{'users'}{$_given_user}{'description'};
	$sanitise_description =~ s/<.*?>//g if ($param_page eq "settings");
	$template->param(PROFILE_DESCRIPTION 	=> $sanitise_description);
	$template->param(PROFILE_HOME_LOC		=> $store{'users'}{$_given_user}{'home_suburb'});
	$template->param(PROFILE_HOME_LAT		=> $store{'users'}{$_given_user}{'home_latitude'});
	$template->param(PROFILE_HOME_LONG		=> $store{'users'}{$_given_user}{'home_longitude'});
	$template->param(PROFILE_BLEATS 		=> parameters_count_bleats($_given_user));
	$template->param(PROFILE_LISTENERS 		=> parameters_count_listeners($_given_user));
	$template->param(PROFILE_LISTENING 		=> parameters_count_listening($_given_user));
	$template->param(PROFILE_BACKGROUND 	=> $DATASET_PATH_HTML."/users/${_given_user}/background.jpg");
	$template->param(PROFILE_NOTIFICATIONS 	=> $store{'users'}{$_given_user}{'notifications'}) if ($store{'users'}{$_given_user}{'notifications'});
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
	    next if (!$_bake_me);
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
sub handle_action_logout {
	return if (!$param_page);
	return if ($param_page ne "logout");
	cookie_logout_session();
	$template->param(LOGGED_IN => FALSE);
}

sub handle_action_listen {
	return if (!$param_action);
	
	if ($param_action eq "listen") {
		parameters_put_new_listen($param_profile);
	} elsif ($param_action eq "unlisten") {
		parameters_del_listen($param_profile);
	} else {
		# Nothing happens, just return
	}
}

sub handle_action_bleat {
	return if (!$param_action);
	return if ($param_action ne "bleat");

	parameters_put_new_bleat($param_bleat);
}

sub handle_action_next {
	return if (!$param_dir);
	return if ($param_dir ne "next");
	$param_set++;
}

sub handle_action_back {
	return if (!$param_dir);
	return if ($param_dir ne "back");
	$param_set--;
}

sub handle_action_search {
	return if (!$param_action);
	return if ($param_action ne "search");
	return if (!$param_query);
	return if (!$param_constraint);
	$template->param(SEARCH_QUERY => TRUE);

	parameters_set_searchfeed();
}

sub handle_action_signup {
	return if (!$param_action);
	return if ($param_action ne "signup");
	return if (logged_in());

	# Needs all 3 fields to be set or throw poop at the user
	# Then, the email needs to be confirmed to complete registration
	if (signup_complete()) {
		# Check validity of fields
		if (signup_exists_username()) 	{ $template->param(MESSAGE => "Sorry, this username already exists"); return; }
		if (!signup_valid_username()) 	{ $template->param(MESSAGE => "Username must be at least 4 characters and only contain alphanumerics"); return; };
		if (!signup_valid_email()) 		{ $template->param(MESSAGE => "Not a valid email"); return; };
		if (!signup_valid_password()) 	{ $template->param(MESSAGE => "Password must be at least 5 characters and only contain alphanumerics"); return; };
		# Reaching here means all fields correctly set
		$template->param(PAGE_CONFIRM => TRUE);
		$template->param(PAGE_LOGIN => FALSE);
		$template->param(PAGE_SIGNUP => FALSE);
		$template->param(EMAIL => $param_email);
		# Generate a key and send to user
		@chars = ("a".."z", "0".."9");
		$key_confirm = "";
		$key_confirm .= $chars[rand @chars] for 1..8;
		debug("Generated confirmation key: $key_confirm");
		# Save the signup details with key for later
		$store{'new_user'}{'name'} 			= $param_name;
		$store{'new_user'}{'username'} 		= $param_username;
		$store{'new_user'}{'email'} 		= $param_email;
		$store{'new_user'}{'password'} 		= $param_password;
		$store{'new_user'}{'key'} 			= $key_confirm;
		$store_updated = TRUE;
		# Send the email
		debug("Attempting to email $param_email");
		open MUTT, "|mutt -s Bitter -e 'set copy=no' -- '$param_email'" or die "Cannot email";
			print MUTT "Your user confirmation key is ".$key_confirm;
		close MUTT or die "not right: $?\n";
		# my $smtp = Net::SMTP->new('$mailserver_url') or die $!;
		# $smtp->mail( $from );
		# $smtp->to( $to );
		# $smtp->data();
		# $smtp->datasend("To: $to\n");
		# $smtp->datasend("From: $from\n");
		# $smtp->datasend("Subject: $subject\n");
		# $smtp->datasend("\n"); # done with header
		# $smtp->datasend($message);
		# $smtp->dataend();
		# $smtp->quit(); # all done. message sent.
	} else {
		debug("Signup tried and failed - all fields were not filled in properly");
	}
}

sub handle_action_confirm {
	return if (!$param_action);
	return if ($param_action ne "confirm");
	return if (logged_in());

	# Check that entry exists for new user in store
	if (!defined $store{'new_user'}) {
		debug("BAD BAD BAD");
		die;
	}

	# Check that the given key matches
	if ($param_key eq $store{'new_user'}{'key'}) {
		# Create db entry, auto login and redirect to home page
		debug("Key checks out.");
		$template->param(PAGE_CONFIRM => FALSE);
		$template->param(PAGE_LOGIN => FALSE);
		$new_username = $store{'new_user'}{'username'};
		$store{'users'}{$new_username}{'full_name'} = $store{'new_user'}{'name'};
		$store{'users'}{$new_username}{'username'} 	= $new_username;
		$store{'users'}{$new_username}{'email'} 	= $store{'new_user'}{'email'};
		$store{'users'}{$new_username}{'password'} 	= $store{'new_user'}{'password'};
		$param_username = $store{'users'}{$new_username}{'username'};
		$param_password = $store{'users'}{$new_username}{'password'};

		handle_yes();
	} else {
		# Redirect back to signup page and make them do it again cause suck one
		debug("Confirmation key did not match");
		$template->param(PAGE_CONFIRM => FALSE);
		$template->param(PAGE_LOGIN => FALSE);
		$template->param(PAGE_SIGNUP => TRUE);
		$template->param(MESSAGE => "Incorrect confirmation key, please try again");
	}

	# Delete new user entry in store no matter what
	$store{'new_user'} = undef;
}

sub handle_action_save {
	return if (!$param_action);
	return if ($param_action ne "save");
	debug("Saving new users settings");
	# TODO
	if ($param_new_username) { debug("new_username implementation has not been done"); }
	$store{'users'}{$param_username}{'full_name'} = $param_name if ($param_name);
	$store{'users'}{$param_username}{'email'} = $param_email if ($param_email);
	$store{'users'}{$param_username}{'password'} = $param_password if ($param_password);

	$store{'users'}{$param_username}{'description'} = $param_description if ($param_description);

	$store{'users'}{$param_username}{'home_suburb'} = $param_home_loc if ($param_home_loc);
	$store{'users'}{$param_username}{'home_latitude'} = $param_home_lat if ($param_home_lat);
	$store{'users'}{$param_username}{'home_longitude'} = $param_home_long if ($param_home_long);
	
	# Handle account settings suspend/delete/notifications
	if ($param_suspend) {
	    if ($param_suspend eq $store{'users'}{$param_username}{'password'}) {
	        $store{'users'}{$param_username}{'suspended'} = TRUE;
	        $param_action = "logout";
	        handle_action_logout();
	        $param_action = "forcelog";
	        return;
	    } else {
	        $template->param(MESSAGE => "Incorrect password");
	    }
	}
	if ($param_delete) {
	    if ($param_delete eq $store{'users'}{$param_username}{'password'}) {
	        # $store{'users'}{$param_username} = undef;
	        delete $store{'users'}{$param_username};
	        $store_updated = TRUE;
	        # Also delete pics
	        $param_action = "deletephoto";
	        handle_action_delete();
	        $param_action = "deletebackground";
	        handle_action_delete();
	        $param_action = "logout";
	        handle_action_logout();
	        $param_action = "forcelog";
	        return;
	    } else {
	        $template->param(MESSAGE => "Incorrect password");
	    }
	}
	if ($param_notification) {
	    #$template->param(MESSAGE => "param_notification: $param_notification");
	    $store{'users'}{$param_username}{'notifications'} = TRUE;
	} else {
	     $store{'users'}{$param_username}{'notifications'} = FALSE;
	}
}

sub handle_action_reset {
	return if (!$param_action);
	return if ($param_action ne "reset");
	debug("Clearing the form without saving anything");
	# Don't think we actually need to do anything here
}

sub handle_action_upload {
	return if (!$param_action);
	return if ($param_action ne "upload");

	# Upload profile picture
	if ($param_file_photo) {
		# Create the path to the image if it does not exists
		$pathname = "$DATASET_PATH_CGI/users/$param_username";
		if (!-d $pathname) {
			mkdir $pathname;
		}

		# If a file already exists, delete it
		if (-e "$pathname/profile.jpg") {
			unlink "$pathname/profile.jpg";
		}

		debug("Attempting to open $param_file_photo");
		open $UPLOADFILE, ">>$pathname/profile.jpg" or die "Could not open path for photo";
			# die "The file handle is empty" if (!defined $upload_photo);
			# binmode UPLOADFILE;
			while ( $line = <$param_file_photo> ) {
				print $UPLOADFILE $line;
			}
		close $UPLOADFILE;
		debug('Uploaded new photo for the user');
	}

	# Upload background picture
	if ($param_file_ground) {
		# Create the path to the image if it does not exists
		$pathname = "$DATASET_PATH_CGI/users/$param_username";
		mkdir $pathname;
		if (!-d $pathname) {
			mkdir $pathname;
		}

		# If a file already exists, delete it
		if (-e "$pathname/background.jpg") {
			unlink "$pathname/background.jpg";
		}

		debug("Attempting to open $param_file_ground");
		open $UPLOADFILE, ">>$pathname/background.jpg" or die "Could not open path for photo";
			# die "The file handle is empty" if (!defined $upload_photo);
			# binmode UPLOADFILE;
			while ( $line = <$param_file_ground> ) {
				print $UPLOADFILE $line;
			}
		close $UPLOADFILE;
		debug('Uploaded new background for the user');
	}
}

sub handle_action_delete {
	return if (!$param_action);
	# return if ($param_action ne "deletephoto");
	# return if ($param_action ne "deletebackground");

	$pathname = "$DATASET_PATH_CGI/users/$param_username";
	if (!-d $pathname) {
		debug("Cant delete something that is not even there");
		return;
	}

	if ($param_action eq "deletephoto") {
		if (-e "$pathname/profile.jpg") {
			unlink "$pathname/profile.jpg";
		}
	} elsif ($param_action eq "deletebackground") {
		if (-e "$pathname/background.jpg") {
			unlink "$pathname/background.jpg";
		}
	}
	debug("Deletes success");
}

sub handle_action_recover {
    return if (!$param_action);
	return if ($param_action ne "recover");
	
	# To recover an account, the password should get changed to something random
	# Then the user can change it to something personal later
	
	# First look for the user with this email (return bs if not there)
	if (!$param_email) {
	    $template->param(MESSAGE => "No email given fool");
	    return;
	} else {
	    $associated_user = undef;
	    foreach $user (%{$store{'users'}}) {
	        next if (!$store{'users'}{$user}{'email'});
	        if ($store{'users'}{$user}{'email'} eq $param_email) {
	            $associated_user = $user;
	            last;
	        }
	    }
	    if (!$associated_user) {
	        $template->param(MESSAGE => "No user associated with this email.");
	        return;
	    }
	    
	}
	# Reaching here means all fields correctly set
	$template->param(PAGE_SUCCESS => TRUE);
	$template->param(PAGE_LOGIN => FALSE);
	$template->param(PAGE_SIGNUP => FALSE);
	$template->param(PAGE_FORGOT => FALSE);
	$template->param(EMAIL => $param_email);
	# Generate a key and use as password
	@chars = ("a".."z", "0".."9");
	$key_password = "";
	$key_password .= $chars[rand @chars] for 1..8;
	debug("Generated password via keygen: $key_password");
	# Change the user's password in the hash db
	$store{'users'}{$associated_user}{'password'} = $key_password;
	$store_updated = TRUE;
	# Send the email
	debug("Attempting to email $param_email");
	open MUTT, "|mutt -s Bitter -e 'set copy=no' -- '$param_email'" or die "Cannot email";
		print MUTT "Your new password for $associated_user is $key_password \n";
		print MUTT "Please login using these credentials and change your password ASAP.";
	close MUTT or die "not right: $?\n";
	debug("Should be successful recovery");
}

sub handle_action_reactivate() {
    return if (!$param_action);
	return if ($param_action ne "reactivate");
	$store{'users'}{$param_username}{'suspended'} = FALSE;
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
	$template->param(PAGE_HOME => FALSE);
	#if (!-d $DATASET_PATH_CGI."/users/${param_username}")
	parameters_set_profile($param_profile);
}

sub handle_page_search {
	return if (!$param_page);
	return if ($param_page ne "search");
	return if (!$param_constraint);
	$template->param(PAGE_SEARCH => TRUE);
	$template->param(PAGE_HOME => FALSE);

	if ($param_constraint eq "username") {
		$template->param(CONSTRAINT_USERNAME 	=> TRUE);
	} elsif ($param_constraint eq "name") {
		$template->param(CONSTRAINT_NAME 		=> TRUE);
	} elsif ($param_constraint eq "bleat") {
		$template->param(CONSTRAINT_BLEAT 		=> TRUE);
	} else {
		die "Good gracious";
	}
}

sub handle_page_settings {
	return if (!$param_page);
	return if ($param_page ne "settings");
	$template->param(PAGE_SETTINGS => TRUE);
	$template->param(PAGE_HOME => FALSE);
}

sub handle_page_bleat {
	return if (!$param_page);
	return if ($param_page ne "bleat");
	return if (!$param_bid);

    @biddy = ();
    push(@biddy, $param_bid);
    parameters_set_feeds(\@biddy);
    
    # Render a bleat feed with just the one bleat
	$template->param(PAGE_BLEAT => TRUE);
	$template->param(PAGE_HOME => FALSE);
}

#
#	PERSISTENCE/STOREABLE HANDLES
#
sub handle_persistence {
	# Persist pagination settings
	$store{'persists'}{'pagination'} 	= $param_pagination;
	$store_updated = TRUE;
}

#
#	SUSPENSION HANDLES
#
sub account_suspended() {
    if (!$store{'users'}{$param_username}{'suspended'}) { return FALSE; }
    return $store{'users'}{$param_username}{'suspended'};
}

sub handle_suspended() {
    $template->param(PAGE_SUSPENDED => TRUE);
}

# ------------------------------------------------------------
# 	SUB RESPONSE HANDLERS
# ------------------------------------------------------------
# Run this when we're logged in
sub handle_yes {
	debug("HANDLE_YES: LOGGED IN"); 

	$template->param(LOGGED_IN => TRUE);
	cookie_login_session();

	# Always make sure username parameter variable set
	parameters_set_username();

    # Suspended accounts can go nowhere until they confirm activation
    if (account_suspended()) {
        handle_suspended();
        return;
    }

	# Handles (actions)
	handle_action_next();	# These guys need to be first
	handle_action_back();

	handle_action_listen();
	handle_action_bleat();
	handle_action_logout();
	handle_action_search();
	handle_action_save();
	handle_action_reset();
	handle_action_upload();
	handle_action_delete();
	
	# Some actions log the user out
	if ($param_action eq "forcelog") {
	    debug("An action logged us out");
	    handle_no();
	    return;
	}

	parameters_set_base($param_username);
	if (!$param_page or ($param_page eq "home")) {
		parameters_set_bleatfeed();
	}

	# Handles (pages)
	handle_page_profile();
	handle_page_search();
	handle_page_settings();
	handle_page_bleat();

	# Persistence
	handle_persistence();
}

# Run this when NOT logged in
sub handle_no {
	debug("HANDLE_NO: NOT LOGGED IN");
	$template->param(LOGGED_IN => FALSE);
	if ($param_page eq "signup") {
		$template->param(PAGE_SIGNUP => TRUE);
		$template->param(PAGE_LOGIN => FALSE);
	} elsif ($param_page eq "forgot") {
		$template->param(PAGE_FORGOT => TRUE);
		$template->param(PAGE_LOGIN => FALSE);
	} else {
		# Display user a message
		$credential_identifier = valid_credentials();
		if 		($credential_identifier == C_BAD_USERNAME) 	{ $template->param(MESSAGE => "Invalid username"); }
		elsif	($credential_identifier == C_BAD_PASSWORD) 	{ $template->param(MESSAGE => "Invalid password"); }
		elsif	($credential_identifier == C_VALID) 		{ die "This is impossible"; }
		elsif	($credential_identifier == C_NONE) 			{ $template->param(MESSAGE => ""); }
		elsif	($credential_identifier == C_MISSING) 		{ $template->param(MESSAGE => "Missing field"); }
		elsif	($credential_identifier == C_TIMEOUT) 		{ $template->param(MESSAGE => "Login timeout"); }
		else											 	{ $template->param(MESSAGE => "Unknown error"); }
	}

	handle_action_signup();
	handle_action_confirm();
	handle_action_recover();
}

# Run this for all error responses
sub handle_err {
	debug("HANDLE_ERR: WHAT HAPPENED?");
}



# ------------------------------------------------------------
# 	MAIN RESPONSE HANDLER
# ------------------------------------------------------------
debug("Parameters set for this request");
foreach $p (keys %param) {
	debug("-------- $p = $param{$p}") if ($param{$p});
}

storable_init();

if 		( logged_in()  ) 			{ handle_yes(); }
elsif	( !logged_in() ) 			{ handle_no() ; }
else								{ handle_err(); }

print cookie_output() if cookie_output();
# Need to hard reload to show chnages to profile and background pictures
if ($param_file_ground or $param_file_photo) {
	print "Expires: 0\n";                # Expire immediately
	print "Pragma: no-cache\n";          # Work as NPH
}
print "Content-Type: text/html\n\n";
print $template->output if (!$CONFIG_DEBUG);

storable_update();

$timer_finish 	= gettimeofday();
$timer_elapsed 	= int(($timer_finish - $timer_start) * 100);
debug("Response took ${timer_elapsed}ms");




