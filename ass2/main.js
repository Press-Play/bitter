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