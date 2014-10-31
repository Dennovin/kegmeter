function get_taps(callback) {
    $.ajax({
        "url": "/json",
        "dataType": "json",
        "success": callback
    });
}

function lookup_tap(beer_id, callback) {
    $.ajax({
        "url": "/brewerydb/beer/" + beer_id,
        "data": {
            "withBreweries": "Y"
        },
        "dataType": "json",
        "success": callback
    });
}

function get_matching_beers(name, callback) {
    $.ajax({
        "url": "/brewerydb/search?type=beer",
        "data": {
            "q": name,
            "withBreweries": "Y"
        },
        "dataType": "json",
        "success": callback
    });
}
