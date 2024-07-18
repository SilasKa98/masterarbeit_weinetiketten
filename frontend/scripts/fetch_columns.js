function fetchColumns(table, module_name){
    console.log(module_name)
    $.ajax({
        type: "POST",
        url: "sql_requests/fetch_table_columns.php",
        data: {
            table: table
        },
        success: function(response){ 
            const json_response = JSON.parse(response)
            let columnNames = [];
            json_response.forEach(colName => {
                columnNames.push(colName.COLUMN_NAME)
                
            });

            if(module_name == "spelling_correction"){
                let col_sel_id = document.getElementById("spell_correction_column_input_select")
                let col_sel_id_2 = document.getElementById("spell_correction_column_output_select")
                
                // remove all options except the first one ("Spalte auswählen"), so its not stacking up by switching tables
                while (col_sel_id.options.length > 1) {
                    selectElement.remove(1);
                }
                columnNames = columnNames.filter(columnName => columnName !== 'path');
                columnNames.forEach(columnName => {
                    const option = document.createElement('option');
                    option.value = columnName;
                    option.text = columnName;
                    col_sel_id.appendChild(option);
                });
                columnNames.forEach(columnName => {
                    const option = document.createElement('option');
                    option.value = columnName;
                    option.text = columnName;
                    col_sel_id_2.appendChild(option);
                });

            }else if(module_name == "search_for_duplicate_entrys"){
                let col_sel_id = document.getElementById("dup_search_column_input_select")

                // remove all options except the first one ("Spalte auswählen"), so its not stacking up by switching tables
                while (col_sel_id.options.length > 1) {
                    selectElement.remove(1);
                }

                columnNames.forEach(columnName => {
                    const option = document.createElement('option');
                    option.value = columnName;
                    option.text = columnName;
                    col_sel_id.appendChild(option);
                });
            }

        },
    });
}


function showLangFilter(e){
    const lang_dropdown = document.getElementById("spell_correction_select_langFilter")
    if (e.checked == true) {
        lang_dropdown.style.display = "block";
    }else{
        lang_dropdown.style.display = "none";
    }
}

function run_spelling_correction(){
    const spell_correction_table_select = document.getElementById("spell_correction_table_select").value
    const spell_correction_column_input_select = document.getElementById("spell_correction_column_input_select").value
    const spell_correction_column_output_select = document.getElementById("spell_correction_column_output_select").value
    const spelling_correction_useML = document.getElementById("spelling_correction_useML")
    const spelling_correction_langFilter = document.getElementById("spelling_correction_langFilter")
    const spell_correction_select_langFilter = document.getElementById("spell_correction_select_langFilter").value


    if(spelling_correction_useML.checked){
        use_ml = true
    }else{
        use_ml = false
    }

    if(spelling_correction_langFilter.checked){
        lang_filter = spell_correction_select_langFilter
    }else{
        lang_filter = "None"
    }

    $.ajax({
        type: "POST",
        url: "http://127.0.0.1:5000/spelling_correction",
        contentType: 'application/json',
        data: JSON.stringify({
            table: spell_correction_table_select,
            sel_columns: spell_correction_column_input_select,
            insert_column: spell_correction_column_output_select,
            use_ml: use_ml,
            lang_filter: lang_filter
        }),
        success: function(response){ 
            console.log(response)
            status_polling()
        }
    });
}

function run_update_label_detail_infos(){
    $.ajax({
        type: "POST",
        url: "http://127.0.0.1:5000/update_label_detail_infos",
        contentType: 'application/json',
        success: function(response){ 
            console.log(response)
            status_polling()
        }
    });
}


function run_search_for_duplicate_entrys(){
    const search_for_duplicate_entrys_table_select = document.getElementById("search_for_duplicate_entrys_table_select").value
    const dup_search_column_input_select = document.getElementById("dup_search_column_input_select").value
    const search_for_duplicate_entrys_save = document.getElementById("search_for_duplicate_entrys_save")

    if(search_for_duplicate_entrys_save.checked){
        save = true
    }else{
        save = false
    }

    $.ajax({
        type: "POST",
        url: "http://127.0.0.1:5000/search_for_duplicate_entrys",
        contentType: 'application/json',
        data: JSON.stringify({
            table: search_for_duplicate_entrys_table_select,
            column: dup_search_column_input_select,
            save: save
        }),
        success: function(response){ 
            console.log(response)
            status_polling()
        }
    });
}

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
                    }
                }
            });
        }
    });


    setTimeout(status_polling, 10000);
}
