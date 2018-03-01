"use strict";

$("#locform").hide();

function locationEditDisplay(evt) {
    evt.preventDefault();

    let locId = $(this).data("locid");
    let locName = $(this).data("locname");

    $('input').attr('placeholder', locName);
    $('button').attr('data-locid', locId);
    $("#locform").show();
}

$(".locEventListener").on('click', locationEditDisplay);


function updatePantryPage(result) {
    alert(result);
}


function locationUpdate(evt) {
    evt.preventDefault();

    let locId = $(this).data("locid");
    let new_name = $("#new_name").val()
    let formInput = {
        "new_name": new_name,
        "loc_id": locId
    }
    console.log(formInput)

    $.post("/updatelocationformhandle", formInput, updatePantryPage)
    $(".locEventListener").html(new_name);
}

$(".locSubmit").on('click', locationUpdate);

$('locEditModal').on('hidden.bs.modal', function () {
    $(this).find('.locid').trigger('reset');
})