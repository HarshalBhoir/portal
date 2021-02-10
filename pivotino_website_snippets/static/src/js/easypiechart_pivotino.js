$(function() {
    $('.chart_skill > .chart > span.percent').bind('DOMSubtreeModified', function(ev) {
        ev.target.parentNode.setAttribute('data-percent', ev.target.innerText);
    });

    $(window).scroll(function() {
        $('.chart').each(function() {

            var bottom_of_object = $(this).offset().top + $(this).outerHeight();
            var bottom_of_window = $(window).scrollTop() + $(window).height();
            var color = $(this).data('color');
            var color2 = $(this).data('color2');
            if( bottom_of_window > bottom_of_object ) {
                //create instance
                $('.chart').easyPieChart({
                    animate: 2000,
                    scaleColor: false,
                    barColor: function(percent) {
                        var ctx = this.renderer.getCtx();
                        var canvas = this.renderer.getCanvas();
                        var gradient = ctx.createLinearGradient(0,0,canvas.width,0);
                            gradient.addColorStop(0, color);
                            gradient.addColorStop(1, color2);
                        return gradient;
                    },
                    size: 180,
                    lineWidth: 20,
                    trackColor: '#f2f2f2',
                    onStep: function(from, to, percent) {
                        $(this.el).find('.percent').text(Math.round(percent));
                    },
                });
            }

        });

    });
});
