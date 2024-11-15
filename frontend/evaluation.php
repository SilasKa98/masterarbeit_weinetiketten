<?php
  $env = parse_ini_file('.env');
  $tables = explode(",",$env["TABLES"]);
  $error_rates = explode(",",$env["ERROR_RATES"]);

?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Evaluation</title>
    <script src="scripts/status_polling.js"></script>
    <script src="scripts/conent_filling_handler.js"></script>
    <script src="scripts/evaluation_page_calls_handler.js"></script>
    <script src="scripts/admin_page_calls_handler.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.2.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-GLhlTQ8iRABdZLl6O3oVMWSktQOp6b7In1Zl3/Jr59b6EGGoI1aFkw7cmDA6j6gD" crossorigin="anonymous">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js" integrity="sha384-w76AqPfDkMBDXo30jS1Sgez6pr3x5MlQ1ZAGC+nuZB+EYdgRZgiwxhTBTkF7CXvN" crossorigin="anonymous"></script>
    <link href="styles/admin.css" rel="stylesheet">
</head>
<body  onload="statusPolling(); startPolling(); getImageDirectories('eval');">
<?php include_once "components/navbar.php"?>
    <h1 style="text-align:center"> Evaluationen </h1>

    <div class="position-relative overflow-hidden p-3 p-md-5 m-md-3 bg-body-tertiary outer_card_wrapper">
        <div class="card">
            <div class="card-header">
                <span style="color: #d7a900;">eval_search_time</span>()
            </div>
            <div class="card-body">
                <h5 class="card-title">Evaluieren der Suchzeit</h5>
                <p class="card-text">
                    Mit diesem Modul kann die benötigte Zeit für eine Suchanfrage berechnet werden.<br>
                    Der Silder dient dazu, die Anzahl der Weinetiketten zu begrenzen die für die Suchanfrage genutzt werden.<br>
                    Durch diese Funktionalität kann evaluiert werden, wie die Anwendung skaliert. 
                </p>
                <div>
                    <input type="text" style="width: 30%" placeholder="Suchtext" id="search_text_eval">
                    <div class="form-check form-switch input_option_admin text-start">
                        <input class="form-check-input" type="checkbox" role="switch" id="search_logic_combined_eval">
                        <label class="form-check-label" for="search_logic_combined">Suchtext zusammenhängend betrachten</label>
                    </div><br>
                    <div id="range_input_wrapper" style="float:left;">
                        <label>Prozentanzahl der berücksichtigten Weinetiketten</label>
                        <input type="range" min="5" max="100" step="5" value="100" id="number_of_db_entries" onchange="update_range_diplay(this)">
                    </div>
                    <div id="range_display_wrapper" style="float:left; margin-left: 1%">
                        <p id="range_display">100%</p>
                    </div><br><br>
                    <button class="btn btn-success" onclick="run_eval_search_time()">Evaluation ausführen</button>
                </div>
            </div>
            <div class="card-footer text-body-secondary" id="footer_eval_search_time">
                Die Anwendung cached bereits getätigte Anfragen und kann somit bekannte Suchanfragen schneller verarbeiten.
                <div class="spinner-border" id="spinner_eval_search_time" role="status" style="float: right; display:none;">
                    <span class="sr-only"></span>
                </div>
                <div id="success_eval_search_time" role="status" style="float: right;display:none;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" class="bi bi-check" viewBox="0 0 16 16" style="border: 1px solid #5aa940; border-radius: 22px; background-color: #b5dfb5;">
                        <path style="color: #07c507;" d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425z"/>
                    </svg>
                </div>
                <div class="d-flex justify-content-end" style="margin-top: 20px;">
                    <button class="btn btn-info text-right" style="display: none;" id="result_eval_search_time_btn" type="button" data-bs-toggle="collapse" data-bs-target="#result_eval_search_time_wrp" aria-expanded="false" aria-controls="result_eval_search_time">
                       Ergebnisse anzeigen
                    </button>
                </div>
            </div>
            <div class="collapse" id="result_eval_search_time_wrp">
                <button type="button" class="btn btn-danger" style="padding:3px; margin-left:1px; margin-top:2px;" onclick="clear_SearchTimeEvalResult(this)">Ergebnissanzeige leeren</button>
                <div class="card card-body" id="result_eval_search_time">
                </div>
            </div>
        </div>
    </div>


    <div class="position-relative overflow-hidden p-3 p-md-5 m-md-3 bg-body-tertiary outer_card_wrapper">
        <div class="card">
            <div class="card-header">
                <span style="color: #d7a900;">do_ocr_eval</span>()
            </div>
            <div class="card-body">
                <h5 class="card-title">Evaluieren der OCR Genauigkeit</h5>
                <p class="card-text">
                    Mit diesem Modul kann die Genauigkeit der Weinetikettentexte bestimmt werden die mit OCR eingelesen wurden.<br>
                    Zur Bestimmung der Genauigkeit kann die "Word Error Rate (WER)", die "Character Error Rate (CER)" oder "Relevant Words Missing Rate (RWMR)" ausgewählt werden.<br>
                    Sowohl die WER als auch die CER folgen dabei den gängigen Formeln für die Bestimmung dieser Werte. <br> Die RWMR ist eine selbst erstelle Evaluationsmethode und überprüft, 
                    alle relavanten Wörter der Evaluationstexte auf Existenz in den OCR-Texten.<br>
                    Außerdem kann das verwendete OCR-Modell sowie die Datenbankspalte, welche zur OCR-Text Überprüfung genutzt werden soll, ausgewählt werden.
                </p>
                <div>
                    <select  class="form-select input_option_admin" id="ocr_modell_select" onchange="fetchColumns(value, 'do_ocr_eval')">
                        <option>OCR-Tool auswählen</option>
                        <?php foreach ($tables as &$val){?>
                            <option value="<?php print $val; ?>"><?php print $val; ?></option>
                        <?php }?>
                    </select>
                    <select class="form-select input_option_admin"  id="do_ocr_eval_column_input_select">
                        <option>Spalte für Evaluation auswählen</option>
                    </select>
                    <select class="form-select input_option_admin" id="do_ocr_eval_path_select">
                        <option>Pfad mit Evaluationstexten auswählen</option>
                    </select>
                    <select  class="form-select input_option_admin" id="error_rate_select">
                            <option>Methode zur Bewertung der OCR-Genauigkeit</option>
                        <?php foreach ($error_rates as &$val){?>
                            <option value="<?php print $val; ?>"><?php print $val; ?></option>
                        <?php }?>
                    </select>
                    <button class="btn btn-success" onclick="run_do_ocr_eval()">Evaluation ausführen</button>
                </div>
            </div>
            <div class="card-footer text-body-secondary" id="footer_do_ocr_eval">
                
                <div class="spinner-border" id="spinner_do_ocr_eval" role="status" style="float: right; display:none;">
                    <span class="sr-only"></span>
                </div>
                <div id="success_do_ocr_eval" role="status" style="float: right;display:none;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" class="bi bi-check" viewBox="0 0 16 16" style="border: 1px solid #5aa940; border-radius: 22px; background-color: #b5dfb5;">
                        <path style="color: #07c507;" d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425z"/>
                    </svg>
                </div>
                <div class="d-flex justify-content-end" style="margin-top: 20px;">
                    <button class="btn btn-info text-right" style="display: none;" id="result_do_ocr_eval_btn" type="button" data-bs-toggle="collapse" data-bs-target="#result_do_ocr_eval_wrp" aria-expanded="false" aria-controls="result_do_ocr_eval">
                       Ergebnisse anzeigen
                    </button>
                </div>
            </div>
            <div class="collapse" id="result_do_ocr_eval_wrp">
                <button type="button" class="btn btn-danger" style="padding:3px; margin-left:1px; margin-top:2px;" onclick="clear_SearchTimeEvalResult(this)">Ergebnissanzeige leeren</button>
                <div class="card card-body" id="result_do_ocr_eval">
                </div>
            </div>
        </div>
    </div>
</body>
</html>