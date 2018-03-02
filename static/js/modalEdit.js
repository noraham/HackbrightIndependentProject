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

    $.post("/updatelocationformhandle", formInput, updatePantryPage)
}

$("#locSubmit").on('click', locationUpdate);


// need to clear modal between clicks, NOT WORKING
$('locEditModal').on('hidden.bs.modal', function () {
    $(this).find('.locid').trigger('reset');
})


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
    let loc = results.locationId;
    $('#locButt-'+loc).prop('checked', 'true').trigger("click");
    $('#exp').attr('placeholder', results.exp);
    $('#descript').attr('placeholder', results.description);
    

    // $("#foodform").show();
}


function foodEditDisplay(evt) {
    let itemId = $(this).data("itemid");
    let itemName = $(this).data("itemname");

    let formInput = {
        "pantry_id": itemId
    }

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
