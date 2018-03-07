"use strict";

var locId;

// Listener and function to display ADD form in modal on PANTRY
function addDisplay(evt) {

    // Grab locId, use to pre-select location radio button
    locId = $(this).data("addlocid");
    $('#locAddButt-'+locId).prop('checked', 'true').trigger("click");
}

$(".addModalButt").on('click', addDisplay);

// listener and functions to handle ADD form submission - update db and reload
function addFoodstuff(result) {

    // Manually clear form input box
    $("#add_name").val("");
    $("#add_exp").val("");

    // Reload page because too many things to manually change
    location.reload(true);
}

function getFoodstuff(evt) {

    // get all fields from form, put in formInput
    name = $('input[name=add_name]').val();
    loc = $('input[name=add_loc]:checked').val();
    exp = $("#add_exp").val();

    let formInput = {
        "pantry": "True",
        "shop": "False",
        "name": name,
        "location": loc,
        "exp": exp,
    }
    console.log(formInput);
    $.post("/add_item", formInput, addFoodstuff)
}

$("#addSubmit").on('click', getFoodstuff);

// Listener and function to display ADD form in modal on SHOPPING
// Not required, there are no fields with placeholders!

// listener and functions to handle ADD form submission - update db and reload
function addShop(result) {

    // Manually clear form input box
    $("#shop_name").val("");
    $("#shop_exp").val("");

    // Reload page because too many things to manually change
    location.reload(true);
}

function getShop(evt) {

    // get all fields from form, put in formInput
    name = $('input[name=shop_name]').val();
    loc = $('input[name=shop_loc]:checked').val();
    exp = $("#shop_exp").val();

    let formInput = {
        "pantry": "False",
        "shop": "True",
        "name": name,
        "location": loc,
        "exp": exp,
    }
    console.log(formInput);
    $.post("/add_item", formInput, addShop)
}

$("#shopSubmit").on('click', getShop);

// Listener and function to display LOCATION ADD form in modal on PANTRY
// Not required, there are no fields with placeholders!

// listener and functions to handle LOCATION ADD form submission - update db and reload
function addLocation(result) {

    // Manually clear form input box
    $("#newLoc").val("");

    // Reload page because too many things to manually change
    location.reload(true);
}

function getLocation(evt) {

    // get all fields from form, put in formInput
    loc = $('input[name=loc]').val();

    let formInput = {
        "loc": loc
    }

    $.post("/add_loc", formInput, addLocation)
}

$("#addLocSubmit").on('click', getLocation);
