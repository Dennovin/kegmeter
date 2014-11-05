var search_timeout;

function hide_search_boxes() {
    $(".searchbox").hide().val("");
    $(".options").empty().hide();
    $(".currentname").show();
}

function update_row($row) {
    lookup_tap($row.attr("beer_id"), function(response) {
        if(response) {
            $row = $(".input-row[beer_id=" + response["beer_id"] + "]");
            $row.find(".currentname").text(response["beer_name"]).removeClass("empty");
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
        var $list = $(".options:visible");
        $list.empty();

        if(!response) {
            var $entry = $("<li />");
            $entry.addClass("no-results").text("No matching beers found.").appendTo($list);
            return;
        }

        for(k in response) {
            var $entry = $("<li />")
                .attr("beer_id", response[k]["beer_id"])
                .click(update_db)
                .addClass("option");

            var $name = $("<span />")
                .addClass("name")
                .text(response[k]["beer_name"])
                .appendTo($entry);

            if(response[k]["brewery_name"]) {
                var $brewery = $("<span />")
                    .addClass("brewery")
                    .text(response[k]["brewery_name"])
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

