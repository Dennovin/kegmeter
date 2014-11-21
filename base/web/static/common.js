function get_taps(callback) {
    $.ajax({
        "url": "/json",
        "dataType": "json",
        "success": callback
    });
}

function lookup_tap(beer_id, callback) {
    $.ajax({
        "url": "/api/beer/" + beer_id,
        "dataType": "json",
        "success": callback
    });
}

function get_matching_beers(name, callback) {
    $.ajax({
        "url": "/api/search",
        "data": {
            "q": name,
        },
        "dataType": "json",
        "success": callback
    });
}
