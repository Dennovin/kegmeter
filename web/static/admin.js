var search_timeout;

function hide_search_boxes() {
    $(".searchbox").hide().val("");
    $(".options").empty().hide();
    $(".currentname").show();
}

function update_row($row) {
    lookup_tap($row.attr("beer_id"), function(response) {
        data = response.data;
        if(data) {
            $row = $(".input-row[beer_id=" + data["id"] + "]");
            $row.find(".currentname").text(data["name"]).removeClass("empty");
        }
    });
}

function update_db(e) {
    var tap_id = $(this).parents(".input-row").attr("tap_id");
    var beer_id = $(this).attr("beer_id");
    hide_search_boxes();

    $.ajax({
        "url": "/admin/update",
        "type": "POST",
        "data": {
            "tap_id": tap_id,
            "beer_id": beer_id
        },
        "dataType": "json",
        "success": function(response) {
            $row = $(".input-row[tap_id=" + response["tap_id"] + "]");
            $row.attr("beer_id", response["beer_id"]);
            update_row($row);
        }
    });

}

function show_search_box(e) {
    hide_search_boxes();

    $(this).hide();
    $(this).parents(".input-row").children(".searchbox").val("").show().focus();
    $(this).parents(".input-row").children(".options").empty().show();
}

function search(elem) {
    if(!$(elem).val() || $.trim($(elem).val()) == "") {
        return;
    }

    get_matching_beers($(elem).val(), function(response) {
        var data = response.data;
        var $list = $(".options:visible");
        $list.empty();

        if(!data) {
            var $entry = $("<li />");
            $entry.addClass("no-results").text("No matching beers found.").appendTo($list);
            return;
        }

        data.sort(function(a, b) {
            if(a["breweries"] && b["breweries"]) {
                return a["breweries"][0]["name"].localeCompare(b["breweries"][0]["name"]);
            }

            if(a["breweries"]) {
                return 1;
            }

            if(b["breweries"]) {
                return -1;
            }

            return a["name"].localeCompare(b["name"]);
        });

        for(k in data) {
            var $entry = $("<li />")
                .attr("beer_id", data[k]["id"])
                .click(update_db)
                .addClass("option");

            var $name = $("<span />")
                .addClass("name")
                .text(data[k]["name"])
                .appendTo($entry);

            if(data[k]["breweries"]) {
                var $brewery = $("<span />")
                    .addClass("brewery")
                    .text(data[k]["breweries"][0]["name"])
                    .appendTo($entry);
            }

            $list.append($entry);
        }
    });
}

function search_key_up(e) {
    if(search_timeout) {
        window.clearTimeout(search_timeout);
    }

    search_timeout = window.setTimeout(search, 200, this);
}

$("document").ready(function() {
    var search_timeout;

    $(".input-row").each(function() {
        if($(this).attr("beer_id")) {
            update_row($(this));
        } else {
            $(this).find(".currentname").text("Empty").addClass("empty");
        }
    });

    $(".currentname").click(show_search_box);
    $(".searchbox").keyup(search_key_up);
    $("body").click(hide_search_boxes);
    $(".input-row").click(function(e) {
        e.stopPropagation();
    });
});

