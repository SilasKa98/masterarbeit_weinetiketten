function status_polling(){
    $.ajax({
        type: "GET",
        url: "http://127.0.0.1:5000/status",
        contentType: 'application/json',
        success: function(response){ 
            Object.keys(response).forEach(function(key) {
                console.log(response)
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
                    var result_elem = document.getElementById("result_"+task_name)
                    if(task_name == "search_for_duplicate_entrys"){
                        document.getElementById("result_"+task_name+"_btn").style.display = "block"
                        result_elem.innerHTML = ""
                        sortedResponse.forEach(resElem => {
                            result_elem.innerHTML += resElem+"<br>"
                        });
                    }else if(task_name == "search_algorithm"){
                        
                        // order the results in the correct Order and rename the categroys to display names
                        const desiredOrder = [
                            { oldKey: 'top_hits', newKey: 'Beste Treffer' },
                            { oldKey: 'text_based_hits', newKey: 'Weitere Treffer' },
                            { oldKey: 'second_choice_hits', newKey: 'Etiketten die Sie auch interessieren könnten' }
                        ];
                        const sortedResponse = {};
                        desiredOrder.forEach(({ oldKey, newKey }) => {
                            if (response[key]["result"][oldKey]) {
                                sortedResponse[newKey] = response[key]["result"][oldKey];
                            }
                        });

                        const image_result_holder = document.getElementById("image_result_holder");
                        image_result_holder.innerHTML = ""
                        for (const [category, item] of Object.entries(sortedResponse)) {
                            const newDiv = document.createElement("div");
                            newDiv.classList.add("result_category_wrap");
                            image_result_holder.append(newDiv)
                            newDiv.innerHTML += "<h2>"+category+"</h2>"
                            console.log(item)
                            if (typeof item === 'object' && !Array.isArray(item) && item !== null){
                                for (const [category_inner, item_inner] of Object.entries(item)) {
                                    const newDiv_inner = document.createElement("div");
                                    newDiv_inner.classList.add("result_category_wrap");
                                    newDiv.append(newDiv_inner)
                                    newDiv_inner.innerHTML += "<h3>Gefunden durch: "+category_inner+"</h3>"
                                    item_inner.forEach(path => {
                                        newDiv_inner.innerHTML += "<a href='../"+path+"' target='_blank'><img src='../"+path+"' width='150px' height='150px' style='margin-right:10px;margin-bottom:10px;'></a>"
                                    });
                                }
                            }else{
                                item.forEach(path => {
                                    newDiv.innerHTML += "<a href='../"+path+"' target='_blank'><img src='../"+path+"' width='150px' height='150px' style='margin-right:10px;margin-bottom:10px;'></a>"
                                });
                            }  
                        }
                        
                    }
                    
                }
            });
        }
    });

    setTimeout(status_polling, 15000);
}

