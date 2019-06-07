$('#users_table').DataTable();

function createNewUser() {
    url = '/create_new_user'

    firstname = $("#new_admin_first_name").val()
    lastname = $("#new_admin_last_name").val()
    netID = $("#new_admin_netID").val()
    department = $("#new_admin_department").val()
    authorization_level = $("#new_admin_authorization").val()

    payload = {
        "firstname": firstname,
        "lastname": lastname,
        "netID": netID,
        "department": department,
        "authorization_level": authorization_level
    }

    $.post(url, payload, function (response) {
        if (response["status_code"] == 400) {
            $.notify({
                message: 'User successfully created!'
            }, {
                    type: 'success',
                    placement: {
                        from: "bottom",
                        align: "center"
                    }
                });
        } else {
            $.notify({
                message: 'User failed to be created!'
            }, {
                    type: 'danger',
                    placement: {
                        from: "bottom",
                        align: "center"
                    }
                });
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

    $.post(url, payload, function (response) {
        if (response["status_code"] == 400) {
            $.notify({
                message: 'User department successfully changed!'
            }, {
                    type: 'success',
                    placement: {
                        from: "bottom",
                        align: "center"
                    }
                });
        } else if (response["status_code"] == 401) {
            $.notify({
                message: 'Error'
            }, {
                    type: 'danger',
                    placement: {
                        from: "bottom",
                        align: "center"
                    }
                });
        } else {
            $.notify({
                message: 'Improper credentials'
            }, {
                    type: 'danger',
                    placement: {
                        from: "bottom",
                        align: "center"
                    }
                });
        }
    })
}

function changeUserAuthentication() {
    netID = $("#change_authorization_netid").val()
    authorization = $("#change_authorization_level").val()

    url = '/change_user_authentication'

    payload = {
        "netID": netID,
        "authorization": authorization
    }

    $.post(url, payload, function (response) {
        if (response["status_code"] == 400) {
            $.notify({
                message: 'User authentication successfully changed!'
            }, {
                    type: 'success',
                    placement: {
                        from: "bottom",
                        align: "center"
                    }
                });
        } else if (response["status_code"] == 401) {
            $.notify({
                message: 'Error'
            }, {
                    type: 'danger',
                    placement: {
                        from: "bottom",
                        align: "center"
                    }
                });
        } else {
            $.notify({
                message: 'Improper credentials'
            }, {
                    type: 'danger',
                    placement: {
                        from: "bottom",
                        align: "center"
                    }
                });
        }
    })
}

// /* attach a submit handler to the form */
// $("#new_user_form").submit(function (event) {

//     /* stop form from submitting normally */
//     event.preventDefault();

//     /* get the action attribute from the <form action=""> element */
//     var $form = $(this),
//         url = $form.attr('action');

//     payload = {
//         "firstname": $('#new_user_first_name').val(),
//         "lastname": $('#new_user_last_name').val(),
//         "netID": $('#new_user_netID').val(),
//         "department": $('#new_admin_department').val(),
//         "authorization_level": $('#authorization_level').val()
//     }

//     $.post(url, payload, function (response) {
//         if (response["status_code"] == 400) {
//             $.notify({
//                 message: response["message"]
//             }, {
//                     type: 'success',
//                     placement: {
//                         from: "bottom",
//                         align: "center"
//                     },
//                 });
//         } else if (response["status_code"] == 401) {
//             $.notify({
//                 message: response["message"]
//             }, {
//                     type: 'danger',
//                     placement: {
//                         from: "bottom",
//                         align: "center"
//                     }
//                 });
//         } else {
//             $.notify({
//                 message: response["message"]
//             }, {
//                     type: 'danger',
//                     placement: {
//                         from: "bottom",
//                         align: "center"
//                     }
//                 });
//         }
//     });

// });


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

                    console.log(url)

                    $.post(url, payload, function (response) {
                        if (response["status_code"] == 400) {
                            $.notify({
                                message: response["message"]
                            }, {
                                    type: 'success',
                                    placement: {
                                        from: "bottom",
                                        align: "center"
                                    }
                                });
                        } else if (response["status_code"] == 401) {
                            $.notify({
                                message: response["message"]
                            }, {
                                    type: 'danger',
                                    placement: {
                                        from: "bottom",
                                        align: "center"
                                    }
                                });
                        } else {
                            $.notify({
                                message: response["message"]
                            }, {
                                    type: 'danger',
                                    placement: {
                                        from: "bottom",
                                        align: "center"
                                    }
                                });
                        }
                    });
                }
                form.classList.add('was-validated');
            }, false);
        });
    }, false);
})();