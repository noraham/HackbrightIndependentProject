"use strict";

$("#locform").hide();
// $("#foodform").hide();

// Listener and function to display LOCATION form in modal
function locationEditDisplay(evt) {
    evt.preventDefault();

    let locId = $(this).data("locid");
    let locName = $(this).data("locname");

    $('#new_name').attr('placeholder', locName);
    $('#locSubmit').attr('data-locid', locId);
    $("#locform").show();
}

$(".locEventListener").on('click', locationEditDisplay);


// listener and functions to handle LOCATION form submission - update db and change view
function updatePantryPage(result) {
    $("#new_name").val("");
    let locId = result.locId;
    $("#locname-"+locId).html(result.newName);
}

function locationUpdate(evt) {
    // evt.preventDefault();

    let locId = $(this).data("locid");
    let new_name = $("#new_name").val()
    let formInput = {
        "new_name": new_name,
        "loc_id": locId
    }
    console.log(formInput)

    $.post("/updatelocationformhandle", formInput, updatePantryPage)
}

$("#locSubmit").on('click', locationUpdate);


// need to clear modal between clicks, NOT WORKING
$('locEditModal').on('hidden.bs.modal', function () {
    $(this).find('.locid').trigger('reset');
})


// Listener and function to display FOOD form in modal
function foodEditPrefills(results) {
    // $('#new_name').attr('placeholder', locName);
    $('#nameField').attr('placeholder', results.itemName);
    if(results.isPantry == true) {
        console.log("pantry is true")
        $('#stockTrue').prop('checked', 'true').trigger("click");
    }
    else {
        $('#stockFalse').prop('checked', "true").trigger("click");
    }
    // $("#foodform").show();
}


function foodEditDisplay(evt) {
    let itemId = $(this).data("itemid");
    let itemName = $(this).data("itemname");

    let formInput = {
        "pantry_id": itemId
    }
    console.log(formInput)

    $.get("/editpantryitem", formInput, foodEditPrefills)

    // $("#foodform").show();
}

$(".editFoodLink").on('click', foodEditDisplay);

// listener and functions to handle FOOD form submission - update db and change view
function updatePantryPageFood(result) {
    alert(result);
}

function foodUpdate(evt) {
    evt.preventDefault();

    // // get all fields from form, put in formInput
    // let locId = $(this).data("locid");
    // let new_name = $("#new_name").val()
    // let formInput = {
    //     "new_name": new_name,
    //     "loc_id": locId
    // }
    // console.log(formInput)

    // $.post("/edit/<int:pantry_id>", formInput, updatePantryPageFood)
    // // change name and whether is still on page
    // $(".locEventListener").html(new_name);
    // // move this to upper function?
}

$(".foodSubmit").on('click', foodUpdate);
