$(document).ready(function() {
    $('#mailform').validate({
        errorClass: 'error-text',
        rules: {
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
            message: "Please enter a message",
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
