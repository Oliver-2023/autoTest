var USBLoaded = '<span class="goofy-label-en">LOADED</span>' +
    '<span class="goofy-label-zh">已载入</span>';
var USBUnloaded = '<span class="goofy-label-en">UNLOADED</span>' +
    '<span class="goofy-label-zh">未载入</span>';
var fxtAvailable = '<span class="goofy-label-en">OK</span>' +
    '<span class="goofy-label-zh">已连接</span>';
var fxtUnavailable = '<span class="goofy-label-en">UNAVAILABLE</span>' +
    '<span class="goofy-label-zh">未连接</span>';
var fxtDetecting = '<span class="goofy-label-en">DETECTING</span>' +
    '<span class="goofy-label-zh">侦测中</span>';
var statIdle = '<span class="color_idle goofy-label-en">IDLE</span>' +
    '<span class="color_idle goofy-label-zh">閒置中</span>';

var useFixture = true;
var useUSBDisk = true;
var useShopfloor = false;
var disableEnterKey = false;

window.onkeydown = function(event) {
    if ((!disableEnterKey && event.keyCode == 13) || event.keyCode == 32) {
        var testButton = document.getElementById("btn_run_test");
        if (!testButton.disabled)
            ButtonRunTestClick();
    }
}

function InitLayout(talkToFixture, talkToShopfloor,
                    inputSerialNumber, ignoreEnterKey) {
    if (inputSerialNumber) {
        var snInputBox = document.getElementById("serial_number");
        snInputBox.disabled = false;
        snInputBox.autofocus = true;
    } else {
        document.getElementById("test_sn_label").hidden = true;
        document.getElementById("test_sn").hidden = true;
        document.getElementById("menu_placeholder").style.height = "30%";
    }

    useFixture = talkToFixture;
    if (!talkToFixture) {
        document.getElementById("fixture_label").hidden = true;
        document.getElementById("test_fixture").hidden = true;
        document.getElementById("fixture_status").hidden = true;
    }

    if (talkToShopfloor) {
        useShopfloor = true;
        useUSBDisk = false;
        document.getElementById("prompt_usb").hidden = true;
        document.getElementById("usb_status_panel").hidden = true;
        document.getElementById("prompt_ethernet").hidden = false;
    } else {
        useShopfloor = false;
        useUSBDisk = true;
        document.getElementById("prompt_usb").hidden = false;
        document.getElementById("usb_status_panel").hidden = false;
        document.getElementById("prompt_ethernet").hidden = true;
    }

    disableEnterKey = ignoreEnterKey;
}

function UpdateTestBottonStatus() {
    var testButton = document.getElementById("btn_run_test");
    var isSnReady = (document.getElementById("test_sn").hidden ||
                     document.getElementById("serial_number").value !== "");
    var isUSBReady = (!useUSBDisk ||
               document.getElementById('usb_status').innerHTML == USBLoaded)
    var isFixtureReady = (!useFixture ||
        document.getElementById('fixture_status').innerHTML == fxtAvailable);

    testButton.disabled =
        !(isSnReady &&
        document.getElementById('serial_number').validity.valid &&
        isUSBReady &&
        isFixtureReady);
}

function RestartSnInputBox() {
    var snInputBox = document.getElementById("serial_number");
    snInputBox.focus();
    snInputBox.value="";
    UpdateTestBottonStatus();
}

function OnSnInputBoxClick() {
    var snInputBox = document.getElementById("serial_number");
    snInputBox.value="";
    UpdateTestBottonStatus();
}

function OnShopfloorInit(pattern) {
    document.getElementById("prompt_ethernet").hidden = true;
    document.getElementById("container").hidden = false;
    ConfigureSNInputbox(pattern);
    if (useFixture)
        test.sendTestEvent('sync_fixture', {});
    else
        UpdateTestBottonStatus();
}

function OnUSBInsertion() {
    document.getElementById("usb_status").innerHTML = USBLoaded;
    document.getElementById("test_param").className = "panel_good";
    UpdateTestBottonStatus();
}

function OnUSBInit(pattern) {
    document.getElementById("prompt_usb").hidden = true;
    document.getElementById("container").hidden = false;
    document.getElementById("usb_status").innerHTML = USBLoaded;
    document.getElementById("test_param").className = "panel_good";
    ConfigureSNInputbox(pattern);
    if (useFixture)
        test.sendTestEvent('sync_fixture', {});
    else
        UpdateTestBottonStatus();
}

function OnUSBRemoval() {
    document.getElementById("usb_status").innerHTML = USBUnloaded;
    document.getElementById("test_param").className = "panel_bad";
    UpdateTestBottonStatus();
}

function ConfigureSNInputbox(pattern) {
    var snInputBox = document.getElementById("serial_number");
    if (!snInputBox.disabled) {
        snInputBox.pattern = pattern;
        snInputBox.focus();
    }
}

function OnAddFixtureConnection() {
    document.getElementById("fixture_status").innerHTML = fxtAvailable;
    document.getElementById("test_fixture").className = "panel_good";
    UpdateTestBottonStatus();
}

function OnRemoveFixtureConnection() {
    document.getElementById("fixture_status").innerHTML = fxtUnavailable;
    document.getElementById("test_fixture").className = "panel_bad";
    UpdateTestBottonStatus();
}

function OnDetectFixtureConnection() {
    document.getElementById("fixture_status").innerHTML = fxtDetecting;
    document.getElementById("test_fixture").className = "panel_bad";
    UpdateTestBottonStatus();
}

function ButtonRunTestClick() {
    var testButton = document.getElementById("btn_run_test");
    testButton.disabled = true;
    test.sendTestEvent("run_test",
        {"sn": document.getElementById("serial_number").value});
    testButton.disabled = false;
    UpdateTestBottonStatus();
}

function ButtonExitTestClick() {
    test.sendTestEvent("exit_test", {});
}

function ResetUiData() {
    document.getElementById("camera_image").hidden = true;
    document.getElementById("camera_image").src = "";
    document.getElementById("analyzed_image").hidden = true;
    document.getElementById("analyzed_image").src = "";
    UpdateTestStatus(statIdle);
    UpdatePrograssBar("0%");
}

function ClearBuffer() {
    buf = ""
}

function AddBuffer(value) {
    buf += value
}

function UpdateImage(container_id) {
    var img = document.getElementById(container_id);
    img.src = "data:image/jpeg;base64," + buf;
    img.hidden = false;
}

function UpdateTestStatus(msg) {
    var statusText = document.getElementById("test_status");
    statusText.innerHTML = msg;
}

function UpdatePrograssBar(progress) {
    var pBar = document.getElementById("progress_bar");
    pBar.style.width = progress;
}
