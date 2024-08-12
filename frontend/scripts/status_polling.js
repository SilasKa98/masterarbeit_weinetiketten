let tasksState = {};
let pollingTasks = {};
let pollingRates = {
    "default": 15000, 
    "search_algorithm": 2000 
};


function handleTask(task_name, task_status, task_result) {
    var spinner_elem = document.getElementById("spinner_" + task_name);
    var success_elem = document.getElementById("success_" + task_name);

    if (spinner_elem && success_elem) {
        if (task_status == "processing") {
            success_elem.style.display = "none";
            spinner_elem.style.display = "block";
        } else if (task_status == "success") {
            spinner_elem.style.display = "none";
            success_elem.style.display = "block";
        } else {
            spinner_elem.style.display = "none";
            success_elem.style.display = "none";
        }
    }

    // get current fileName to determine if polling for search is needed or not
    let path = window.location.pathname;
    const fileName = path.substring(path.lastIndexOf('/') + 1);

    if (task_name == "search_for_duplicate_entrys" && task_status == "success" && fileName == "admin_page.php") {
        handleDuplicateEntries(task_result);
    } else if (task_name == "search_algorithm" && task_status == "success" && fileName != "admin_page.php") {
        handleSearchAlgorithm(task_result, task_name);
    }
}


function handleDuplicateEntries(result) {

    if (tasksState["search_for_duplicate_entrys"] === "success") return;

    var result_elem = document.getElementById("result_search_for_duplicate_entrys");
    document.getElementById("result_search_for_duplicate_entrys_btn").style.display = "block";
    result_elem.innerHTML = "";
    result.forEach(resElem => {
        result_elem.innerHTML += resElem + "<br>";
    });

    tasksState["search_for_duplicate_entrys"] = "success";
}


function handleSearchAlgorithm(result, task_name) {
    
    if (tasksState["search_algorithm"] === "success"){
        clearInterval(pollingTasks["search_algorithm"])
        return;
    }

    const image_result_holder = document.getElementById("image_result_holder");
    if (image_result_holder) {
        const desiredOrder = [
            { oldKey: 'top_hits', newKey: 'Beste Treffer' },
            { oldKey: 'text_based_hits', newKey: 'Weitere Treffer' },
            { oldKey: 'second_choice_hits', newKey: 'Etiketten die Sie auch interessieren könnten' }
        ];
        const sortedResponse = {};
        desiredOrder.forEach(({ oldKey, newKey }) => {
            if (result[oldKey]) {
                sortedResponse[newKey] = result[oldKey];
            }
        });
        console.log(sortedResponse)
        image_result_holder.innerHTML = "";
        for (const [category, item] of Object.entries(sortedResponse)) {
            const newDiv = document.createElement("div");
            newDiv.classList.add("result_category_wrap");
            image_result_holder.append(newDiv)
            newDiv.innerHTML += "<h2>" + category + "</h2>";
            if (typeof item === 'object' && !Array.isArray(item) && item !== null) {
                for (const [category_inner, item_inner] of Object.entries(item)) {
                    const newDiv_inner = document.createElement("div");
                    newDiv_inner.classList.add("result_category_wrap");
                    newDiv.append(newDiv_inner)
                    newDiv_inner.innerHTML += "<h3>Gefunden durch: " + category_inner + "</h3>";
                    item_inner.forEach(path => {
                        let content_string = handel_image_content_filling(path)
                        newDiv_inner.innerHTML += content_string;
                    });
                }
            } else {
                item.forEach(path => {
                    let content_string = handel_image_content_filling(path)
                    newDiv.innerHTML += content_string ;
                });
            }
        }
        let search_background = document.getElementById("search_background")
        if(!search_background.classList.contains('show')){
            search_background.classList.toggle("show")
        }
        //let search_background = document.getElementById('search_background');
        //search_background.classList.toggle('show');
    }

    tasksState["search_algorithm"] = "success";
}


function statusPolling(){
    console.log("polling current status...")
    $.ajax({
        type: "GET",
        url: "http://127.0.0.1:5000/status",
        contentType: 'application/json',
        success: function(response){ 
            let objKeys = Object.keys(response)
            for (let obj_name of objKeys){
                Object.keys(response[obj_name]).forEach(function(key) {
                    let task_name = response[obj_name].name
                    let task_status = response[obj_name].status
                    if(task_status == "success" && response[obj_name].result){
                        var task_result = response[obj_name].result;
                    }else{
                        var task_result = undefined
                    }
                    handleTask(task_name, task_status, task_result);
                });

            }
        }
    });
}

function specificTaskStatusPolling(name) {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: "GET",
            url: "http://127.0.0.1:5000/status/" + name,
            contentType: 'application/json',
            success: function(response) { 
                resolve(response);
            },
            error: function(error) {
                reject(error);
            }
        });
    });
}


function startPolling() {
    let path = window.location.pathname;
    var tasks = [];
    const fileName = path.substring(path.lastIndexOf('/') + 1);
    if(fileName == "admin_page.php"){
        tasks.push("default")
    }else{
        tasks.push("search_algorithm")
    }
    tasks.forEach(task => {
        console.log(pollingTasks[task])
        if (!pollingTasks[task]) {
            pollingTasks[task] = setInterval(() => {
                statusPolling();
            }, pollingRates[task] || pollingRates["default"]); 
        }
    });
}
