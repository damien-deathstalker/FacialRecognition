var facialFeatures = Array();
var savedFacialFeatures = Array();
const videoElement = document.getElementById("videoCapture");
const canvasElement = document.getElementById("overlay");
const videoContainer = document.getElementById("videoContainer");
const saveNotificationElement = document.getElementById("saveNotification");
const awatingResponseElement = document.getElementById("awatingResults");
const awatingCameraElement = document.getElementById("awatingCamera");
const resultsDiv = document.getElementById("facial_results");
const WEIGHTS_URL = "/static/Registration/weights";
const csrfmiddlewaretoken = document.getElementsByName("csrfmiddlewaretoken")[0].defaultValue;
const _url = resultsDiv.getAttribute("url");
const clockElement = document.getElementById("clock");
var ready = null;
var capture = null;

document.addEventListener("DOMContentLoaded", load_faceapi_models, false);
document.addEventListener("DOMContentLoaded", toggle_capture, false);
document.addEventListener("DOMContentLoaded", showTime, false);
window.addEventListener("resize", resizeCanvas, false);
videoElement.addEventListener("play", resizeCanvas, false);


function toggle_capture() {
    // begin capture of frames with visitors face
    awatingCameraElement.style.display = "inline";
    start_capture();
    resizeCanvas();
}

function start_capture() {
    if (navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(function (stream) {
                videoElement.srcObject = stream;
                capture = true;
                resultsDiv.innerHTML = "&nbsp;";
            })
            .catch(function (err0r) {
                console.log("Something went wrong! " + err0r);
            });
    }
}

function prepare_data() {
    // send data to API for processing and saving to database
    var dataDict = {};
    dataDict['facial_features'] = JSON.stringify(savedFacialFeatures);
    dataDict['csrfmiddlewaretoken'] = csrfmiddlewaretoken;
    return dataDict;
}

function ajax_call(ajaxdict) {
    var timeout = 3000;
    $.ajax({
        url: _url,
        type: "POST",
        dataType: 'json',
        data: ajaxdict,
        success: function (data) {
            //data - response from server
            resultsDiv.innerHTML = data['message'];
            awatingResponseElement.style.display = "none";
            if (data['status'] == 'recognized') {
                timeout = 10000;
            }
            setTimeout(() => {
                resultsDiv.innerHTML = "&nbsp;";
                ready = null;
            }, timeout);
        },
        error: function (data) {
            // Error Message
            var status = data.status;
            var statusText = data.statusText;
            resultsDiv.innerHTML = `Error Code - ${status}: ${statusText}`;
            awatingResponseElement.style.display = "none";
            setTimeout(() => {
                resultsDiv.innerHTML = "&nbsp;";
                ready = null;
            }, 10000);
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
            if (mtcnnResults.length > 0) {
                if (ready == null) {
                    awatingResponseElement.style.display = "inline";
                    add_facial_feature(videoEl);
                }
            } else {
                awatingResponseElement.style.display = "none";
            }
        }
    }
    setTimeout(() => {
        _autoplay(videoEl)
    });
}

function add_facial_feature(video) {
    var type = "image/png"
    var frame = develop_frame(video);
    var data = frame.toDataURL(type);
    facialFeatures.push(data);
    if (facialFeatures.length > 2) {
        savedFacialFeatures = facialFeatures;
        ready = true;
        var features = prepare_data();
        ajax_call(features);
        facialFeatures = Array();
    }
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

function resizeCanvas(e) {
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