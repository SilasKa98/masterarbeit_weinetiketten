function process_search(){
    search_text = document.getElementById("search_text").value
    $.ajax({
        type: "POST",
        url: "http://127.0.0.1:5000/semantic_search",
        contentType: 'application/json',
        data: JSON.stringify({
            search_text: search_text
        }),
        success: function(response){ 
            console.log(response)
            const test = status_polling()
            console.log("test")
            console.log(test)
        }
    });
}