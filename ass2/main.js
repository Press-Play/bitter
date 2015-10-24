$('.bleat_button_expand').click(function(){
	// console.log('Expand button pressed.');
	var self = $(this);
	var mainCard = $(this).closest('.placemarker').find('.select_me');
	var otherMainCards = $(this).closest('.placemarker').parent().find('.select_me');
	var subCards = $(this).closest('.placemarker').find('.sub');
	var otherCards = $(this).closest('.placemarker').parent().find('.sub');

	if (subCards.hasClass('minimise')) {
		otherCards.addClass('minimise');
		otherMainCards.removeClass('bleat_selected');
		mainCard.addClass('bleat_selected');
		self.addClass('flipV');
		subCards.removeClass('minimise');
	} else {
		subCards.addClass('minimise');
		self.removeClass('flipV');
		mainCard.removeClass('bleat_selected');
	}
});

$('.upload').change(function () {
	var self = $(this);
    self.closest('.placemarker').find('.upload_file').val(self.val());
});

//https://maps.googleapis.com/maps/api/geocode/json?latlng=40.714224,-73.961452&location_type=ROOFTOP&result_type=country&key=AIzaSyCyhbfhlGEP5jDmWBXQs2PBaNw3LrJEru4
$(document).ready(function(){
    $('.loc').each(function(){
        var self = $(this);
        var latlng = self.html();
        var req_url = "https://maps.googleapis.com/maps/api/geocode/json?" + latlng + "&location_type=ROOFTOP&result_type=street_address&key=AIzaSyCyhbfhlGEP5jDmWBXQs2PBaNw3LrJEru4";
        console.log('Location card ready to go:', req_url);
        if (latlng == "") {
            self.html("No location");
            return;
        } else {
            $.ajax({
                url: req_url
            }).done(function(data) {
                console.log(data.results[0]);
                // Go through formatted and get the country?
                self.html(data.results[0]["formatted_address"]);
            });
        }
    });
});
