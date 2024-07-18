function fetchColumns(table){
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
        }
    });
}