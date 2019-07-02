// Converts our main users table into an interactive DataTable
$('#users_table').DataTable();

// Streamlines how notifications are pushed to screen
function display_notification(response) {
    $.notify({
        message: response["message"]
    }, {
        type: (response["status"] ? 'success' : 'danger'), 
        placement: {
            from: "bottom",
            align: "center"
        }
    })
}

function changeUserDepartment() {
    netID = $("#change_department_netid").val()
    department = $("#change_department_department").val()

    url = '/change_user_department'

    payload = {
        "netID": netID,
        "department": department
    }

    $.post(url, payload, function (response) { display_notification(response) })
}

function changeUserAuthentication() {
    netID = $("#change_authorization_netid").val()
    authorization = $("#change_authorization_level").val()

    url = '/change_user_authentication'

    payload = {
        "netID": netID,
        "authorization": authorization
    }

    $.post(url, payload, function (response) { display_notification(response) })
}

// Example starter JavaScript for disabling form submissions if there are invalid fields
(function () {
    'use strict';
    window.addEventListener('load', function () {
        // Fetch all the forms we want to apply custom Bootstrap validation styles to
        var forms = document.getElementsByClassName('new_user_form');
        
        // Loop over them and prevent submission
        var validation = Array.prototype.filter.call(forms, function (form) {
            form.addEventListener('submit', function (event) {
                if (form.checkValidity() === false) {
                    event.preventDefault();
                    event.stopPropagation();
                } else {
                    $("#newAdminModal").modal('hide')
                    event.preventDefault()
                    var $form = $("#new_user_form")
                    var url = $form.attr('action')

                    var payload = {
                        "firstname": $('#new_user_first_name').val(),
                        "lastname": $('#new_user_last_name').val(),
                        "netID": $('#new_user_netID').val(),
                        "department": $('#new_admin_department').val(),
                        "authorization_level": $('#new_admin_authorization').val()
                    }

                    $.post(url, payload, function (response) { display_notification(response) });
                }
                form.classList.add('was-validated');
            }, false);
        });
    }, false);
})();

(function () {
    'use strict';
    window.addEventListener('load', function () {
        // Fetch all the forms we want to apply custom Bootstrap validation styles to
        var forms = document.getElementsByClassName('change_password_form');
        // Loop over them and prevent submission
        var validation = Array.prototype.filter.call(forms, function (form) {
            form.addEventListener('submit', function (event) {
                if (form.checkValidity() === false) {
                    event.preventDefault();
                    event.stopPropagation();
                } else {
                    $("#change_password_modal").modal('hide')
                    event.preventDefault()
                    var $form = $("#change_password_form")
                    var url = $form.attr('action')

                    var payload = {
                        "old_password": $("#old_password").val(),
                        "new_password": $("#new_password").val(),
                        "confirm_password": $("#confirm_password").val()
                    }

                    $.post(url, payload, function (response) { display_notification(response) });
                }
                form.classList.add('was-validated');
            }, false);
        });
    }, false);
})();