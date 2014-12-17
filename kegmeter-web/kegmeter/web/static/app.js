$("[tap_id]").click(function(e) {
    if($(this).hasClass("active")) {
        clear_active();
    } else {
        make_active($(this).attr("tap_id"));
    }
});

$(".checkin-link").click(function(e) {
    e.stopPropagation();
});

function clear_active() {
    $(".active").removeClass("active");
    $(".inactive").removeClass("inactive");
    $(".has-active").removeClass("has-active");
}

function make_active(tap_id) {
    $(".active").removeClass("active");
    $(".tap, .tap-id").addClass("inactive");
    $("[tap_id=" + tap_id + "]").removeClass("inactive").addClass("active");
    $("body").addClass("has-active");
}

function check_current() {
    get_taps(function(data) {
        for(k in data) {
            var $tap = $(".tap[tap_id=" + data[k]["tap_id"] + "]");
            if($tap.attr("beer_id") != data[k]["beer_id"]) {
                $tap.attr("beer_id", data[k]["beer_id"]);
                lookup_tap(data[k]["beer_id"], function(response) {
                    if(!response) {
                        return;
                    }

                    $tap = $(".tap[beer_id=" + response["beer_id"] + "]");
                    $tap.find(".name").text(response["beer_name"]);
                    $tap.find(".brewery").text(response["brewery_name"]);
                    $tap.find(".location").text(response["brewery_loc"]);
                    $tap.find(".style").text(response["beer_style"]);
                    $tap.find(".abv").text(response["abv"] + "%");
                    $tap.find(".description").text(response["description"]);
                    $tap.find(".breweryimg").attr("src", response["brewery_label"]);
                    $tap.find(".checkin-link").attr("href", "https://untappd.com/qr/beer/" + response["beer_id"]);
                    $(".beerimg[tap_id=" + $tap.attr("tap_id") + "]").css("background-image", "url('" + response["beer_label"] + "')");
                });
            }
        }
    });
}

$("document").ready(function() {
    check_current();
    window.setInterval(check_current, 60000);
    window.scrollTo(0, 1);
});
