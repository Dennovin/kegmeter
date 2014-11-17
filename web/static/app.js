$(".tap").click(function(e) {
    if($(this).hasClass("active")) {
        $(".active").removeClass("active");
        $(".inactive").removeClass("inactive");
    } else {
        $(".tap").addClass("inactive");
        $(this).removeClass("inactive").addClass("active");
        $(".tap-id").addClass("inactive");
        $(".tap-id[tap_id=" + $(this).attr("tap_id") + "]").removeClass("inactive").addClass("active");
    }
});

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
                    $tap.find(".beerimg").attr("src", response["beer_label"]);
                    $tap.find(".breweryimg").attr("src", response["brewery_label"]);
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
