/**
 * Used by contact() in private/templates/AidIQ/controllers.py
 */
$(document).ready(function() {
    $('#mailform').validate({
        errorClass: 'error-text',
        rules: {
            name: {
                required: true
            },
            subject: {
                required: true
            },
            message: {
                required: true
            },
            name: {
                required: true
            },
            address: {
                required: true,
                email: true
            }
        },
        messages: {
            // @ToDo: i18n if-required
            name: "Enter your name",
            subject: "Enter a subject",
            message: "Enter a message",
            address: {
                required: "Please enter a valid email address",
                email: "Please enter a valid email address"
            }
        },
        errorPlacement: function(error, element) {
            var controls = element.closest('.controls');
            element.closest('.controls').find('.error').remove();
            var wrapper = $('<div class="error_wrapper">').append($('<div class="error">').html(error.text()));
            wrapper.insertAfter(element);
        },
        submitHandler: function(form) {
            form.submit();
        }
    });
});