const usernameTxt = document.getElementById("username");
const passwordTxt = document.getElementById("password");
const formElement = document.getElementById("loginForm");



function custom_submit() {
    var formFields  = formElement.getElementsByTagName("input");
    console.log(formFields)
    formFields.forEach(element => {
        element.valid();
    });
}