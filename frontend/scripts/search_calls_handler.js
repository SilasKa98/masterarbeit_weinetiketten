function process_search(){
    let search_text = document.getElementById("search_text").value
    let search_logic_combined = document.getElementById("search_logic_combined")
    if(search_logic_combined.checked){
        search_logic_combined = true
    }else{
        search_logic_combined = false
    }
    $.ajax({
        type: "POST",
        url: "http://127.0.0.1:5000/search_algorithm",
        contentType: 'application/json',
        data: JSON.stringify({
            search_text: search_text,
            search_logic_combined: search_logic_combined
        }),
        success: function(response){ 
            console.log(response)
            tasksState["search_algorithm"] = "processing"
            delete pollingTasks["search_algorithm"]
            startPolling()
        }
    });
}