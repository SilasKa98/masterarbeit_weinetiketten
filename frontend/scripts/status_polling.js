function status_polling(){
    $.ajax({
        type: "GET",
        url: "http://127.0.0.1:5000/status",
        contentType: 'application/json',
        success: function(response){ 
            console.log(response)
            Object.keys(response).forEach(function(key) {
                console.log(response[key]["name"])
                let task_name = response[key]["name"]
                var task_status = response[key]["status"]
                var spinner_elem = document.getElementById("spinner_"+task_name)
                var success_elem = document.getElementById("success_"+task_name)
                if(task_status == "processing"){
                    success_elem.style.display = "none";
                    spinner_elem.style.display = "block";
                }else if(task_status == "success"){
                    spinner_elem.style.display = "none";
                    success_elem.style.display = "block";
                }else{
                    spinner_elem.style.display = "none";
                    success_elem.style.display = "none";
                }

                if(response[key]["result"]){
                    console.log(response[key]["result"])
                    var result_elem = document.getElementById("result_"+task_name)

                    if(task_name == "search_for_duplicate_entrys"){
                        document.getElementById("result_"+task_name+"_btn").style.display = "block"
                        result_elem.innerHTML = ""
                        response[key]["result"].forEach(resElem => {
                            result_elem.innerHTML += resElem+"<br>"
                        });
                    }else if(task_name == "semantic_search"){
                        const image_result_holder = document.getElementById("image_result_holder");
                        image_result_holder.innerHTML = ""
                        data = response[key]["result"]
                        for (const [category, paths] of Object.entries(data)) {
                            const newDiv = document.createElement("div");
                            newDiv.classList.add("result_category_wrap");
                            image_result_holder.append(newDiv)
                            newDiv.innerHTML += "<h2>"+category+"</h2>"
                            paths.forEach(path => {
                                console.log(`  Image: ${path}`);
                                newDiv.innerHTML += "<a href='../"+path+"' target='_blank'><img src='../"+path+"' width='150px' height='150px' style='margin-right:10px;margin-bottom:10px;'></a>"
                            });
                            
                        }
                        
                    }
                    
                }
            });
        }
    });

    setTimeout(status_polling, 15000);
}

