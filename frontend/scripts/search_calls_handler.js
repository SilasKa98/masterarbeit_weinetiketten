function process_search(){
    search_text = document.getElementById("search_text").value
    $.ajax({
        type: "POST",
        url: "http://127.0.0.1:5000/search_algorithm",
        contentType: 'application/json',
        data: JSON.stringify({
            search_text: search_text
        }),
        success: function(response){ 
            console.log(response)
            tasksState["search_algorithm"] = "processing";     
            status_polling()
        }
    });
}