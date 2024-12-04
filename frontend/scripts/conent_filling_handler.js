function create_loading_placeholder(img_path){
    loading_placeholder_content = '<div class="card mb-3 offCanvasCard" id="placeholder_loading" aria-hidden="true">'+
                                    '<div class="img">'+
                                    '<img src="../'+img_path+'" style="filter: blur(5px);" class="card-img-top offCanvasCardImg" alt="placeholder image">'+
                                    '</div>'+
                                    '<div class="card-body">'+
                                    '<h5 class="card-title placeholder-glow"><span class="placeholder col-6"></span></h5>'+
                                    '<p class="card-text placeholder-glow">'+
                                    '<span class="placeholder col-7"></span>'+
                                    '<span class="placeholder col-4"></span>'+
                                    '<span class="placeholder col-8"></span>'+
                                    '<span class="placeholder col-4"></span>'+
                                    '<span class="placeholder col-6"></span>'+
                                    '</p></div></div>';
    
    if(document.getElementById("placeholder_loading") === null){
        document.getElementById("offcanvas_imgDetails_body").insertAdjacentHTML("afterbegin", loading_placeholder_content);
    }
}

function handel_offcanvas_content_filling(path){
    console.log("current_path")
    console.log(path)
    $.ajax({
        type: "POST",
        url: "http://127.0.0.1:5000/get_image_informations",
        contentType: 'application/json',
        data: JSON.stringify({
            path: path,
        }),
        success: function(response){
            console.log(response)
            for (const [category, item] of Object.entries(response)) {
                console.log(category)
                console.log(item)
                if(category == "name"){
                    var taskName = item
                }
            }
            specificTaskStatusPolling(taskName).then(response => {

                if (response.status === "processing") {
                    if(document.getElementById("placeholder_loading") === null){
                        create_loading_placeholder(path)
                    }
                    setTimeout(() => {
                        handel_offcanvas_content_filling(path);
                    }, 500);
                }else{

                    if(document.getElementById("placeholder_loading")){
                        document.getElementById("placeholder_loading").remove();
                    }

                    console.log(response);
                    console.log(response.status);
                    console.log(response.result);
                    var result = response.result

                    // pre processing and filtering
                    if(result.hasOwnProperty("image_anno")){
                        result["image_anno"] = result["image_anno"] || "";
                    }
                    const wineTypes = {
                        "white wine": "Weißwein",
                        "red wine": "Rotwein",
                        "unclear": ""
                    };

                    result["image_wine_type"] = wineTypes[result["image_wine_type"]] ?? result["image_wine_type"];
        
                    let labels = [
                        { key: "image_directory", label: "Etiketten-Verzeichnis" },
                        { key: "image_lang", label: "Etikettensprache" },
                        { key: "image_country", label: "Herkunftsland" },
                        { key: "image_provinces", label: "Region" },
                        { key: "image_anno", label: "Jahrgang" },
                        { key: "image_vol", label: "Alkoholgehalt" },
                        { key: "image_wine_type", label: "Weinsorte" },
                        { key: "wine_name", label: "Weinname/Rebsorte"},
                        { key: "google_query", label: "Google" }
                    ];

                    let content = '';

                    labels.forEach(item => {
                        if (result[item.key]) {
                            if(item.key == "google_query"){
                                let formattedQuery = result[item.key].replace(/ /g, '+')
                                let encodedQuery = encodeURIComponent(formattedQuery).replace(/%2B/g, '+')
                                content += `<br><span class="offCanvasCardLabel"></span><a href=https://www.google.com/search?q=${encodedQuery}&tbm=isch target='_blank'>Ähnliche Weine auf Google suchen</a><br>`;
                            }else{
                                content += `<span class="offCanvasCardLabel">${item.label}: </span><span>${result[item.key]}</span><br>`;
                            }
                            
                        }
                    });

                    let contentString = '<button type="button" onclick="removeElement(this)" class="btn btn-danger delDetailImgBtn"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-trash" viewBox="0 0 16 16"><path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0z"></path><path d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4zM2.5 3h11V2h-11z"></path></svg></button>'+
                                        '<div class="card mb-3 offCanvasCard">'+
                                            '<a href="../'+ path +'" target="_blank"><img src="../' + path + '" class="card-img-top offCanvasCardImg" alt="Etikettenbild"></a>'+
                                            '<div class="card-body">'+
                                                '<h5 class="card-title">'+result["image_name"]+'</h5>'+
                                                '<p class="card-text">'+
                                                    content + 
                                                '</p>'+
                                                '<p class="card-text"><small class="text-body-secondary">Gerade aktualisiert</small></p>'+
                                            '</div>'+
                                        '</div>';

                    document.getElementById("offcanvas_imgDetails_body").insertAdjacentHTML("afterbegin", contentString);
                }

            }).catch(error => {
                console.error("Error:", error);
                let errorString = "<p>Fehler beim laden der Etikettendetails. <br> Bitte versuchen Sie es erneut!</p>"
                document.getElementById("offcanvas_imgDetails_body").insertAdjacentHTML("afterbegin", errorString);
            });
        }
    });
}

function removeElement(elem){
    elem.nextElementSibling.remove();
    elem.remove();
}
                        



function handel_image_content_filling(path){

    const escapedPath = path.replace(/\\/g, "\\\\");

    let content_string = "<a data-bs-toggle='offcanvas' data-bs-target='#offcanvas_imgDetails' aria-controls='offcanvas_imgDetails' id='"+path+"' href='../" + path + "' onclick='handel_offcanvas_content_filling(\""+escapedPath+"\")'>" +
                            "<img class='wine_image' src='../" + path + "'>"+
                      "</a>"
    
    return content_string
}



function clear_SearchTimeEvalResult(e){
    e.nextElementSibling.innerHTML = ""
}

function update_range_diplay(e){
    let range = e.value
    let range_display = document.getElementById("range_display")
    range_display.innerHTML = range + "%"
}
