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
                    console.log(response);
                    data = response.data;
                    if(data) {
                        loc = data["breweries"][0]["locations"][0];
                        $tap = $(".tap[beer_id=" + data["id"] + "]");
                        $tap.find(".name").text(data["name"]);
                        $tap.find(".brewery").text(data["breweries"][0]["name"]);
                        $tap.find(".location").text(loc["locality"] + ", " + loc["region"] + ", " + loc["country"]["isoThree"]);
                        $tap.find(".style").text(data["style"]["name"]);
                        $tap.find(".abv").text(data["abv"] + "%");
                        $tap.find(".description").text(data["description"]);
                        $tap.find(".brewerydescription").text(data["breweries"][0]["description"]);

                        if(data["labels"]) {
                            img_url = data["labels"]["large"];
                        } else {
                            img_url = "/static/mysterybeer.png";
                        }

                        $tap.find(".beerimg").attr("src", img_url);
                    }
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
