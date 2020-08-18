$(document).ready(function () {
    var counter = 0;

    $("form#formConvert").submit(function (e) {
        e.preventDefault();

        div = $('<div class="progress"><div></div></div><hr>');
        $('#progress').append(div);

        var formData = new FormData(this);
        // Send POST to convert video
        $.ajax({
            url: window.location.pathname,
            type: 'POST',
            data: formData,
            success: function (data, status, request) {
                status_url = request.getResponseHeader('Location');
                progressCount = count();
                update_progress(status_url, div[0], progressCount);
                // console.log(status_url);
            },
            error: function (response) {
                alert(response);
            },
            cache: false,
            contentType: false,
            processData: false
        });
    });

    function update_progress(status_url, status_div, progressCount) {
        // Send GET request to status URL
        $.getJSON(status_url, function (data) {
            if (data['state'] != 'PENDING') {
                if (data['info'] == false) {
                    $(status_div.childNodes[0]).text('[' + progressCount + '] [' + formatDate(new Date()) + '] STATE: FAILED');
                } else {
                    $(status_div.childNodes[0]).text('[' + progressCount + '] [' + formatDate(new Date()) + '] STATE: ' + data['state']);
                    a = $('<a href="' + data['result_url'] + '">' + data['info'] + '</a>');
                    $(status_div).append(a);
                }
            }
            else {
                $(status_div.childNodes[0]).text('[' + progressCount + '] [' + formatDate(new Date()) + '] STATE: CONVERTING...');

                // re-run in 2 seconds
                setTimeout(function () {
                    update_progress(status_url, status_div, progressCount);
                }, 2000);
            }
        });
    }
    // Get Time
    function formatDate(date) {
        const h = "0" + date.getHours();
        const m = "0" + date.getMinutes();
        const s = "0" + date.getSeconds();

        return `${h.slice(-2)}:${m.slice(-2)}:${s.slice(-2)}`;
    }

    // Get Count
    function count() {
        return counter = counter + 1;
    }
});