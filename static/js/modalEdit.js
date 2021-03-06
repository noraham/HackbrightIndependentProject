"use strict";

var locId, locName, new_name;
var loc, itemId, itemName, pantryId, name, shopping, purch, loc, exp, description, pantry;

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
    console.log(results.isShopping);

    // Goes through each field in form, filling placeholder info from db
    $('#nameField').attr('placeholder', results.itemName);

    if(results.isPantry == true) {
        $('#pantryTrue').prop('checked', 'true').trigger("click");
    }
    else {
        $('#pantryFalse').prop('checked', "true").trigger("click");
    }

    if(results.isShopping == true) {
        $('#shoppingTrue').prop('checked', 'true').trigger("click");
    }
    else {
        $('#shoppingFalse').prop('checked', "true").trigger("click");
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
    
    // Return to this later, change so jQuery reveals a flash message
    // Also necessitates re-working all flash handling for this route
    // For now, just reload page
    location.reload(true);
}

function foodUpdate(evt) {

    pantryId = $(this).data("pantryid");
    // get all fields from form, put in formInput
    name = $('input[name=name]').val();
    pantry = $('input[name=pantry]:checked').val();
    shopping = $('input[name=shop]:checked').val();
    purch = $('input[name=last_purch]').val();
    loc = $('input[name=location]:checked').val();
    exp = $("#exp").val();
    description = $("#descript").val();

    let formInput = {
        "pantry_id": pantryId,
        "name": name,
        "pantry": pantry,
        "shop": shopping,
        "last_purch": purch,
        "location": loc,
        "exp": exp,
        "description": description
    }

    $.post("/updatepantryitem", formInput, updatePantryPageFood)
}

$("#foodSubmit").on('click', foodUpdate);
