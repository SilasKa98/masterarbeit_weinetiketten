function process_search(){
    let search_text = document.getElementById("search_text").value
    let search_logic_combined = document.getElementById("search_logic_combined")
    let custom_search_precision = document.getElementById("custom_search_precision")
    if(search_logic_combined.checked){
        search_logic_combined = true
    }else{
        search_logic_combined = false
    }

    if(custom_search_precision.checked){
        var percentage_matching_range = document.getElementById("percentage_matching_range").value
    }else{
        var percentage_matching_range = ""
    }

    $.ajax({
        type: "POST",
        url: "http://127.0.0.1:5000/search_algorithm",
        contentType: 'application/json',
        data: JSON.stringify({
            search_text: search_text,
            search_logic_combined: search_logic_combined,
            percentage_matching_range: percentage_matching_range
        }),
        success: function(response){ 
            console.log(response)
            tasksState["search_algorithm"] = "processing"
            delete pollingTasks["search_algorithm"]
            startPolling()
        }
    });
}


function toggle_precision_range_slider(){
    let custom_search_precision = document.getElementById("custom_search_precision")
    let percentage_matching_range_wrapper = document.getElementById("percentage_matching_range_wrapper")
    let range_display = document.getElementById("range_display")
    let percentage_matching_range = document.getElementById("percentage_matching_range")

    range_display.innerHTML = percentage_matching_range.value + "%"
    if (custom_search_precision.checked) {
        percentage_matching_range_wrapper.style.display = 'block';
    } else {
        percentage_matching_range_wrapper.style.display = 'none';
    }
}

function update_range_diplay(e){
    let range = e.value
    let range_display = document.getElementById("range_display")
    range_display.innerHTML = range + "%"
}