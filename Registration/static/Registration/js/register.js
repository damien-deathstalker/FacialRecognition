var facialFeatures = Array();
var savedFacialFeatures = Array();
const captureBtn = document.getElementById("captureBtn");
const submitBtn = document.getElementById("submitBtn");
const registrationForm = document.getElementById("registrationForm");
const videoElement = document.getElementById("videoCapture");
const canvasElement = document.getElementById("overlay");
const videoContainer = document.getElementById("videoContainer");
const saveBtn = document.getElementById("saveBtn");
const saveNotificationElement = document.getElementById("saveNotification");
const awatingResponseElement = document.getElementById("awaitingResponse");
const awatingCameraElement = document.getElementById("awatingCamera");
const _url = registrationForm.getAttribute("url");
const _recognizeurl = registrationForm.getAttribute("recognizeurl");
const clockElement = document.getElementById("clock");
const WEIGHTS_URL = "/static/Registration/weights";
const csrfmiddlewaretoken = document.getElementsByName("csrfmiddlewaretoken")[0].defaultValue;
var ready = null;
var capture = null;

document.addEventListener("DOMContentLoaded", load_faceapi_models, false);
document.addEventListener("DOMContentLoaded", showTime, false);
window.addEventListener("resize", resizeCanvas, false);
videoElement.addEventListener("play", resizeCanvas, false);


function custom_submit() {
    //Override the Regular Submit to ensure the form is valid and facial features have been collected
    if (validate_form(registrationForm)) {
        stop_capture();
        if (savedFacialFeatures.length > 3) {
            // Submit the form with the facialFeatures array
            awatingResponseElement.innerHTML = '<span class="spinner-border spinner-border-sm text-primary" role="status"aria-hidden="true"></span>&nbsp; Processing data... Please wait.';
            awatingResponseElement.style.display = "inline";
            var ajax_dict = prepare_data(registrationForm);
            ajax_call(ajax_dict);
        } else {
            // alert user not enough facial features have been collected
            Swal.fire(
                'Not Enough Facial Features!',
                'Please make sure you save at least 4 Facial Features',
                'info'
            );
        }
    } else {
        // alert user form is not valid and highlight invalid fields
        Swal.fire(
            'Please fill all fields!',
            'Please ensure all fields are filled in the form.',
            'error'
        )
    }
    return;
}

function onlyNumberKey(evt) {

    // Only ASCII character in that range allowed
    var ASCIICode = (evt.which) ? evt.which : evt.keyCode
    if (ASCIICode > 31 && (ASCIICode < 48 || ASCIICode > 57))
        return false;
    return true;
}

function validate_form(formElement) {
    // check if form is valid => [True | False]
    var retval = false;
    if (formElement['v_name'].value == "") {
        document.getElementById("v_name_error").className = "error";
        document.getElementById("v_name_error").innerHTML = formElement['v_name'].validationMessage;
        return false;
    } else {
        document.getElementById("v_name_error").className = "error hidden";
        retval = true
    }
    if (formElement['v_tel'].value.length < 10) {
        document.getElementById("v_tel_error").className = "error";
        document.getElementById("v_tel_error").innerHTML = formElement['v_tel'].validationMessage;
        return false;
    } else {
        document.getElementById("v_tel_error").className = "error hidden";
        retval = true
    }
    if (formElement['v_person_to_see'].value == "") {
        document.getElementById("v_person_to_see_error").className = "error";
        document.getElementById("v_person_to_see_error").innerHTML = formElement['v_person_to_see'].validationMessage;
        return false;
    } else {
        document.getElementById("v_person_to_see_error").className = "error hidden";
        retval = true
    }
    if (formElement['v_purpose'].value == "") {
        document.getElementById("v_purpose_error").className = "error";
        document.getElementById("v_purpose_error").innerHTML = formElement['v_purpose'].validationMessage;
        return false;
    } else {
        document.getElementById("v_purpose_error").className = "error hidden";
        retval = true
    }
    return retval;
}

function toggle_capture() {
    // begin capture of frames with visitors face
    if (capture == null) {
        awatingCameraElement.style.display = "inline";
        start_capture();
    } else {
        stop_capture();
    }
    resizeCanvas();
}

function start_capture() {
    saveBtn.style.display = "inline";
    if (navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(function (stream) {
                videoElement.srcObject = stream;
                capture = true;
                captureBtn.className = "btn btn-danger";
                captureBtn.value = "Stop Capture";
            })
            .catch(function (err0r) {
                console.log("Something went wrong! " + err0r);
            });
    }
}

function stop_capture() {
    // Stop Video Capture from Webcam
    saveBtn.style.display = "none";
    if (!capture) {
        return;
    }
    ready = null;
    capture = null;
    var stream = videoElement.srcObject;
    var tracks = stream.getTracks();
    tracks.forEach(element => {
        element.stop();
    });
    videoElement.srcObject = null;
    captureBtn.className = "btn btn-primary";
    captureBtn.value = "Start Capture";
    savedFacialFeatures = facialFeatures;
    facialFeatures = Array();
    var context = canvasElement.getContext('2d');
    context.clearRect(0, 0, canvasElement.width, canvasElement.height);
}

function prepare_data(registrationForm) {
    // send data to API for processing and saving to database
    var dataDict = {};
    dataDict['facial_features'] = JSON.stringify(savedFacialFeatures);
    dataDict['name'] = registrationForm['v_name'].value;
    dataDict['telephone'] = registrationForm['v_tel'].value;
    dataDict['person_to_see'] = registrationForm['v_person_to_see'].value;
    dataDict['purpose'] = registrationForm['v_purpose'].value;
    dataDict['csrfmiddlewaretoken'] = csrfmiddlewaretoken;
    return dataDict;
}

function ajax_call(ajaxdict) {
    $.ajax({
        url: _url,
        type: "POST",
        dataType: 'json',
        data: ajaxdict,
        success: function (data) {
            //data - response from server
            awatingResponseElement.style.display = "none";
            if (data['status'] == 'ok') {
                Swal.fire(
                    'Saved!',
                    'Visitor has been logged!',
                    'success'
                );
                registrationForm.reset();
            } else {
                Swal.fire(
                    'Whoops! Hold On...',
                    data['message'],
                    'error'
                );
            }
        },
        error: function (data) {
            // Error Message
            var status = data.status;
            var statusText = data.statusText;
            awatingResponseElement.innerHTML = `Error Code - ${status}: ${statusText}`;
        }
    });
}

function try_recognize(params) {
    var dataDict = {};
    dataDict['facial_features'] = JSON.stringify(facialFeatures);
    dataDict['csrfmiddlewaretoken'] = csrfmiddlewaretoken;
    $.ajax({
        url: _recognizeurl,
        type: "POST",
        dataType: 'json',
        data: dataDict,
        success: function (data) {
            //data - response from server
            if (data['status'] == 'recognized') {
                Swal.fire({
                    title: 'We know this person!',
                    html: `<p>This is <b>${data["visitor_name"]}</b>.</p><p>Automatically their provide info?</p>`,
                    icon: 'question',
                    showCancelButton: true,
                    confirmButtonColor: '#3085d6',
                    cancelButtonColor: '#d33',
                    confirmButtonText: 'Yes',
                    cancelButtonText: 'No',
                }).then((result) => {
                    if (result.isConfirmed) {
                        registrationForm['v_name'].value = data["visitor_name"];
                        registrationForm['v_tel'].value = data["visitor_telephone"];
                        registrationForm['v_name'].className = registrationForm['v_name'].className + ' active'
                        registrationForm['v_tel'].className = registrationForm['v_tel'].className + ' active'
                    }
                })
            }
        },
        error: function () {
            setTimeout(() => {
                ready = null;
            }, 60000);
        }
    });
}

async function load_faceapi_models() {
    console.log("Loading Models");
    await faceapi.loadMtcnnModel(WEIGHTS_URL)
    await faceapi.loadFaceRecognitionModel(WEIGHTS_URL)
    console.log("Models Loaded");
}

async function _autoplay(videoEl) {
    awatingCameraElement.style.display = "none";
    const mtcnnForwardParams = {
        minFaceSize: 90
    }
    if (capture) {
        const mtcnnResults = await faceapi.mtcnn(videoEl, mtcnnForwardParams)
        if (mtcnnResults) {
            const dims = faceapi.matchDimensions(canvasElement, videoEl, true)
            const resizedResults = faceapi.resizeResults(mtcnnResults, dims)
            faceapi.draw.drawDetections(canvasElement, resizedResults, {})
            faceapi.draw.drawFaceLandmarks(canvasElement, resizedResults, {})
            if (mtcnnResults.length == 1) {
                saveBtn.removeAttribute("disabled");
                if (ready == null) {
                    add_facial_feature(videoEl);
                    if (facialFeatures.length > 2) {
                        ready = true;
                        try_recognize();
                    }
                };
            } else {
                saveBtn.setAttribute("disabled", "true");
            }
        }
    }
    setTimeout(() => {
        _autoplay(videoEl)
    });
}

function save_facial_feature() {
    video = videoElement;
    add_facial_feature(video);
    saved_notification();
}

function add_facial_feature(video) {
    var type = "image/png"
    var frame = develop_frame(video);
    var data = frame.toDataURL(type);
    facialFeatures.push(data);
}

function develop_frame(video, scaleFactor) {
    if (scaleFactor == null) {
        scaleFactor = 1;
    }
    var w = video.videoWidth * scaleFactor;
    var h = video.videoHeight * scaleFactor;
    var canvas = document.createElement('canvas');
    canvas.width = w;
    canvas.height = h;
    var ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, w, h);
    return canvas;
}

function saved_notification() {
    saveNotificationElement.innerHTML = "Facial Feature Saved!";
    if (facialFeatures.length > 3) {
        saveNotificationElement.innerHTML = "Enough Facial Features have been saved!";
    }
    setTimeout(() => {
        saveNotificationElement.innerHTML = "&nbsp";
    }, 5000);
}

function resizeCanvas() {
    canvasElement.width = videoContainer.clientWidth;
    canvasElement.height = videoContainer.clientHeight;
}

function showTime() {
    var date = new Date();
    var h = date.getHours(); // 0 - 23
    var m = date.getMinutes(); // 0 - 59
    var s = date.getSeconds(); // 0 - 59
    var session = "AM";
    if (h == 0) {
        h = 12;
    }
    if (h > 12) {
        h = h - 12;
        session = "PM";
    }
    h = (h < 10) ? "0" + h : h;
    m = (m < 10) ? "0" + m : m;
    s = (s < 10) ? "0" + s : s;
    var time = h + ":" + m + ":" + s + ":" + session;
    clockElement.innerHTML = time;
    setTimeout(showTime, 1000);
}
