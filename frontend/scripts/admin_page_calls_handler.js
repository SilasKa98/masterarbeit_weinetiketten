function fetchColumns(table, module_name){
    console.log(module_name)
    $.ajax({
        type: "POST",
        url: "backend_handling/fetch_table_columns.php",
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
                    col_sel_id.remove(1);
                    col_sel_id_2.remove(1);
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
                    col_sel_id.remove(1);
                }

                columnNames.forEach(columnName => {
                    const option = document.createElement('option');
                    option.value = columnName;
                    option.text = columnName;
                    col_sel_id.appendChild(option);
                });
            }else if(module_name == "read_and_save_ocr" || module_name == "do_ocr_eval"){
                if(module_name == "read_and_save_ocr"){
                    var col_sel_id = document.getElementById("read_and_save_ocr_column_input_select")
                }else{
                    var col_sel_id = document.getElementById("do_ocr_eval_column_input_select")
                }

                // remove all options except the first one ("Spalte auswählen"), so its not stacking up by switching tables
                while (col_sel_id.options.length > 1) {
                    col_sel_id.remove(1);
                }

                columnNames = columnNames.filter(columnName => columnName !== 'path');
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


function getImageDirectories(called_from){
    $.ajax({
        type: "POST",
        url: "backend_handling/fetch_image_directories.php",
        data: {
            called_from: called_from
        },
        success: function(response){ 
            const json_response =  JSON.parse(response);
            if(called_from == "admin"){
                const read_and_save_ocr_path_select = document.getElementById("read_and_save_ocr_path_select");
                const modify_images_path_select = document.getElementById("modify_images_path_select");
            }else if(called_from == "eval"){
                const do_ocr_eval_path_select = document.getElementById("do_ocr_eval_path_select");
            }
            
            json_response.forEach(path => {
                if(called_from == "admin"){
                    const option = document.createElement('option');
                    option.value = path;
                    option.text = path;
                    read_and_save_ocr_path_select.appendChild(option);

                    const option2 = document.createElement('option');
                    option2.value = path;
                    option2.text = path;
                    modify_images_path_select.appendChild(option2);
                }else if(called_from == "eval"){
                    const option3 = document.createElement('option');
                    option3.value = path;
                    option3.text = path;
                    do_ocr_eval_path_select.appendChild(option3);
                }
            });
        }
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
    const spelling_correction_only_new = document.getElementById("spelling_correction_only_new")


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

    if(spelling_correction_only_new.checked){
        only_new = true
    }else{
        only_new = false
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
            lang_filter: lang_filter,
            only_new: only_new
        }),
        success: function(response){ 
            console.log(response)
            tasksState["spelling_correction"] = "processing";
            statusPolling()  
            startPolling()
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
            tasksState["update_label_detail_infos"] = "processing";
            statusPolling()   
            startPolling()
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
            tasksState["search_for_duplicate_entrys"] = "processing";
            statusPolling()   
            startPolling()
        }
    });
}


function run_read_and_save_ocr(){
    const read_and_save_ocr_table_select = document.getElementById("read_and_save_ocr_table_select").value
    const read_and_save_ocr_column_input_select = document.getElementById("read_and_save_ocr_column_input_select").value
    const read_and_save_ocr_path_select = document.getElementById("read_and_save_ocr_path_select").value
    const read_and_save_ocr_use_translation = document.getElementById("read_and_save_ocr_use_translation")
    const read_and_save_ocr_only_new_entries = document.getElementById("read_and_save_ocr_only_new_entries")


    if(read_and_save_ocr_use_translation.checked){
        use_translation = true
    }else{
        use_translation = false
    }

    if(read_and_save_ocr_only_new_entries.checked){
        only_new_entries = true
    }else{
        only_new_entries = false
    }

    $.ajax({
        type: "POST",
        url: "http://127.0.0.1:5000/read_and_save_ocr",
        contentType: 'application/json',
        data: JSON.stringify({
            table: read_and_save_ocr_table_select,
            column: read_and_save_ocr_column_input_select,
            path: read_and_save_ocr_path_select,
            use_translation: use_translation,
            only_new_entries: only_new_entries
        }),
        success: function(response){ 
            console.log(response)
            tasksState["read_and_save_ocr"] = "processing";
            statusPolling()   
            startPolling()
        }
    });
}


function run_read_db_and_detect_lang(){
    const read_db_and_detect_lang_force_update = document.getElementById("read_db_and_detect_lang_force_update")


    if(read_db_and_detect_lang_force_update.checked){
        force_update = true
    }else{
        force_update = false
    }

    $.ajax({
        type: "POST",
        url: "http://127.0.0.1:5000/read_db_and_detect_lang",
        contentType: 'application/json',
        data: JSON.stringify({
            force_update: force_update
        }),
        success: function(response){ 
            console.log(response)
            tasksState["read_db_and_detect_lang"] = "processing";
            statusPolling()    
            startPolling()
        }
    });
}


function run_modify_images(){
    const modify_images_path_select = document.getElementById("modify_images_path_select").value
    $.ajax({
        type: "POST",
        url: "http://127.0.0.1:5000/modify_images",
        contentType: 'application/json',
        data: JSON.stringify({
            directory: modify_images_path_select
        }),
        success: function(response){ 
            console.log(response)
            tasksState["modify_images"] = "processing";
            statusPolling()    
            startPolling()
        }
    });
}


function run_check_directory_for_duplicates(){
    const directoryInput = document.getElementById("duplicate_directory_file")
    const files = directoryInput.files;
    const formData = new FormData();

    for (let i = 0; i < files.length; i++) {
        formData.append('images', files[i]);
    }

    $.ajax({
        type: "POST",
        url: "http://127.0.0.1:5000/check_directory_for_duplicates",
        data: formData,
        processData: false,
        contentType: false,
        success: function(response){ 
            console.log(response)
            tasksState["check_directory_for_duplicates"] = "processing";
            statusPolling()   
            startPolling()
        }
    });

}


function run_update_entities_for_labels(){

    let update_entities_for_labels_only_missings = document.getElementById("update_entities_for_labels_only_missings")

    if(update_entities_for_labels_only_missings.checked){
        update_entities_for_labels_only_missings = true
    }else{
        update_entities_for_labels_only_missings = false
    }

    $.ajax({
        type: "POST",
        url: "http://127.0.0.1:5000/update_entities_for_labels",
        contentType: 'application/json',
        data: JSON.stringify({
            only_update_missings: update_entities_for_labels_only_missings
        }),
        success: function(response){ 
            console.log(response)
            tasksState["update_entities_for_labels"] = "processing";
            statusPolling()   
            startPolling()
        }
    });
}


function toggleOnlyNewImgs_readSaveOcr(switch_elem){
    let ocr_sel = document.getElementById("read_and_save_ocr_table_select")
    let col_sel = document.getElementById("read_and_save_ocr_column_input_select")
    let path_sel = document.getElementById("read_and_save_ocr_path_select")
    let translation_switch = document.getElementById("read_and_save_ocr_use_translation")

    ocr_sel.disabled = !ocr_sel.disabled;
    translation_switch.disabled = !translation_switch.disabled

    if(switch_elem.checked){
        ocr_sel.innerHTML = '<option>tesseract, easyocr, doctr, kerasocr, mmocr</option>'
        col_sel.innerHTML = '<option value="text_pure">text_pure</option><option value="text_pure_modified_images">text_pure_modified_images</option>'
        path_sel.innerHTML = '<option value="/wine_images">/wine_images</option>'+
                             '<option value="/wine_images/edited_wine_images">/wine_images/edited_wine_images</option>'
    }else{
        location.reload()
    }
}

