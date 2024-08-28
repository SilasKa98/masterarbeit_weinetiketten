function run_eval_search_time(){
    let search_text_eval = document.getElementById("search_text_eval").value
    let search_logic_combined_eval = document.getElementById("search_logic_combined_eval")
    let number_of_db_entries = document.getElementById("number_of_db_entries").value

    if(search_logic_combined_eval.checked){
        search_logic_combined_eval = true
    }else{
        search_logic_combined_eval = false
    }

    $.ajax({
        type: "POST",
        url: "http://127.0.0.1:5000/eval_search_time",
        contentType: 'application/json',
        data: JSON.stringify({
            search_text_eval: search_text_eval,
            search_logic_combined_eval: search_logic_combined_eval,
            number_of_db_entries: number_of_db_entries
        }),
        success: function(response){ 
            console.log(response)
            tasksState["eval_search_time"] = "processing";
            statusPolling()    
            startPolling()
        }
    });
}