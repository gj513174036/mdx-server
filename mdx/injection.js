// injections.js

const audio_type = {
    'mp3': 'audio/mpeg',
    'mp4': 'audio/mp4',
    'wav': 'audio/wav',
    'spx': 'audio/ogg',
    'ogg': 'audio/ogg'
};

function audio_content_type(ext) {
    return audio_type[ext] || 'audio/mpeg';
}

$(document).ready(function() {
    // Load dictionary list on page load
    $.ajax({
        url: '/mydict/list_dicts',
        type: 'GET',
        success: function(files) {
            const select = $("#dict_select");
            select.empty(); // Clear existing options
            if (files && files.length > 0) {
                files.forEach(function(file) {
                    select.append($('<option>', {
                        value: file,
                        text: file
                    }));
                });
            } else {
                select.append($('<option>', {
                    text: 'No dictionaries found in mdx/ folder'
                }));
                $('#set_dict_btn').prop('disabled', true);
            }
        },
        error: function() {
            const select = $("#dict_select");
            select.empty();
            select.append($('<option>', {
                text: 'Error loading dictionaries'
            }));
            $('#set_dict_btn').prop('disabled', true);
        }
    });

    // Handle setting the dictionary
    $("#set_dict_btn").click(function() {
        const dict_file = $("#dict_select").val();
        if (dict_file) {
            $("#setting_status").text("Setting dictionary...");
            $.ajax({
                url: '/mydict/set_dict',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ path: dict_file }),
                success: function(response) {
                    if (response.status === 'success') {
                        $("#setting_status").text(response.message + " Reloading...");
                        // reload page to reflect new dictionary
                        setTimeout(function() { location.reload(); }, 1000);
                    } else {
                        $("#setting_status").text("Error: " + response.message);
                    }
                },
                error: function(error) {
                    $("#setting_status").text("Error setting dictionary.");
                    console.log(error);
                }
            });
        }
    });

    // Handle sound links
    $("body a").click(function(event) {
        const tag = $(this).attr("href");
        if (!tag) {
            return;
        }
        if (tag.startsWith("sound://")) {
            event.preventDefault(); // Prevent default link behavior
            const soundFile = tag.substring("sound://".length);
            $("#audiotag").attr("src", "/mydict/" + soundFile);
            $("#audiotag").attr("type", audio_content_type(tag.slice(-3)));
            try {
                const audioElement = document.getElementById("audiotag");
                audioElement.play();
            } catch (err) {
                console.error("Audio playback error:", err);
            }
        }
    });
});
