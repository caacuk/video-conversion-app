document.addEventListener("DOMContentLoaded", () => {
    // Get Time
    function formatDate(date) {
        const h = "0" + date.getHours();
        const m = "0" + date.getMinutes();

        return `${h.slice(-2)}:${m.slice(-2)}`;
    }

    // Insert Message to Display Message
    function appendMessage(name, img, side, text) {
        const msgHTML = `
        <div class="msg ${side}-msg">
        <div class="msg-img" style="background-image: url(${img})"></div>
        
        <div class="msg-bubble">
        <div class="msg-info">
        <div class="msg-info-name">${name}</div>
        <div class="msg-info-time">${formatDate(new Date())}</div>
        </div>
        
        <div class="msg-text">${text}</div>
        </div>
        </div>
        `;

        document
            .querySelector(".msger-chat")
            .insertAdjacentHTML("beforeend", msgHTML);
        document.querySelector(".msger-chat").scrollTop += 500;
    }

    // onclick Handler
    document.querySelector("#btnConvert").onclick = (e) => {
        const form = new FormData(document.querySelector("#form"))

        e.preventDefault();
        // collect the form data while iterating over the inputs
        var data = {};
        for (var i = 0, ii = form.length; i < ii; ++i) {
            var input = form[i];
            if (input.name) {
                data[input.name] = input.value;
            }
        }

        // construct an HTTP request
        var xhr = new XMLHttpRequest();
        xhr.open(form.method, form.action, true);
        xhr.setRequestHeader('Content-Type', "multipart/form-data");
        xhr.onreadystatechange = function () {
            if (xhr.readyState == XMLHttpRequest.DONE) {
                alert(xhr.responseText);
            }
        }

        // send the collected data as JSON
        xhr.send(form);

        xhr.onloadend = function () {
            // done
        };

        console.log('btnConvert clicked')
    };
});
