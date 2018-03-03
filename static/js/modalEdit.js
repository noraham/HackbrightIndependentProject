"use strict";

var locId, locName, new_name;
var loc, itemId, itemName, pantryId, name, shopping, purch, loc, exp, description;

$("#locform").hide();

// Listener and function to display LOCATION form in modal
function locationEditDisplay(evt) {
    evt.preventDefault();
    console.log("this one works")

    locId = $(this).data("locid");
    locName = $(this).data("locname");

    $('#new_name').attr('placeholder', locName);
    // Assign id to button, this is how we pass it to next function
    $('#locSubmit').attr('data-locid', locId);
    $("#locform").show();
}

$(".locEventListener").on('click', locationEditDisplay);


// listener and functions to handle LOCATION form submission - update db and change view
function updatePantryPage(result) {
    // Manually clear form input box
    $("#new_name").val("");

    locId = result.locId;

    // Change display on pantry page
    $("#locname-"+locId).html(result.newName);
}

function locationUpdate(evt) {

    // locId is now a global variable, can just call
    new_name = $("#new_name").val()
    let formInput = {
        "new_name": new_name,
        "loc_id": locId
    }

    $.post("/updatelocationformhandle", formInput, updatePantryPage)
}

$("#locSubmit").on('click', locationUpdate);


// Listener and function to display FOOD form in modal
function foodEditPrefills(results) {

    // Goes through each field in form, filling placeholder info from db
    $('#nameField').attr('placeholder', results.itemName);

    if(results.isShopping == true) {
        $('#pantryTrue').prop('checked', 'true').trigger("click");
    }
    else {
        $('#pantryFalse').prop('checked', "true").trigger("click");
    }

    $('#lastPurch').html(results.lastPurch);

    loc = results.locationId;
    $('#locButt-'+loc).prop('checked', 'true').trigger("click");

    $('#exp').attr('placeholder', results.exp);

    $('#descript').attr('placeholder', results.description);

    $('#foodSubmit').attr('data-pantryid', results.pantryId);
}

function foodEditDisplay(evt) {

    // Need to clear any previous values from form
    $('input[name=name]').val("");
    $('input[type=date][name=last_purch]').val("");
    $("#exp").val("");
    $("#descript").val("");

    itemId = $(this).data("itemid");

    let formInput = {
        "pantry_id": itemId
    }

    // Shuttle this to Python function that will pull all info from SQL db and pass to callback
    $.get("/editpantryitem", formInput, foodEditPrefills)
}

$(".editFoodLink").on('click', foodEditDisplay);

// listener and functions to handle FOOD form submission - update db and change view
function updatePantryPageFood(result) {
    // if location changed, have to relaod page
    if(result.locChange != false) {
        location.reload(true);
    }

    // If name changed, update on pantry page
    if(result.nameChange != false) {
        $("#foodLink-"+result.pantryId).html(result.nameChange);
    }
}

function foodUpdate(evt) {

    pantryId = $(this).data("pantryid");
    // get all fields from form, put in formInput
    name = $('input[name=name]').val();
    shopping = $('input[name=shop]:checked').val();
    purch = $('input[name=last_purch]').val();
    loc = $('input[name=location]:checked').val();
    exp = $("#exp").val();
    description = $("#descript").val();

    let formInput = {
        "pantry_id": pantryId,
        "name": name,
        "shop": shopping,
        "last_purch": purch,
        "location": loc,
        "exp": exp,
        "description": description
    }

    $.post("/updatepantryitem", formInput, updatePantryPageFood)
}

$("#foodSubmit").on('click', foodUpdate);


// need to clear modal between clicks, NOT WORKING
// $('#locEditModal').on('show.bs.modal', function () {
//     console.log("hidden trigger");
//     $(this).find('form')[0].reset();
// });
