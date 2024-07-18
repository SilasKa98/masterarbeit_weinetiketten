<?php
  $env = parse_ini_file('.env');
  $tables = explode(",",$env["TABLES"]);
  $languages = explode(",",$env["LANGUAGES_FILTER"]);

?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin</title>
    <script src="scripts/fetch_columns.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.2.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-GLhlTQ8iRABdZLl6O3oVMWSktQOp6b7In1Zl3/Jr59b6EGGoI1aFkw7cmDA6j6gD" crossorigin="anonymous">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js" integrity="sha384-w76AqPfDkMBDXo30jS1Sgez6pr3x5MlQ1ZAGC+nuZB+EYdgRZgiwxhTBTkF7CXvN" crossorigin="anonymous"></script>
    <link href="styles/admin.css" rel="stylesheet">
</head>
<body onload="status_polling()">
    <h1 style="text-align:center"> Admin </h1>
    <div class="position-relative overflow-hidden p-3 p-md-5 m-md-3 bg-body-tertiary">
        <div class="card">
            <div class="card-header">
                <span style="color: #d7a900;">spelling_correction</span>()
            </div>
            <div class="card-body">
                <h5 class="card-title">OCR-Fehler korrigieren</h5>
                <p class="card-text">
                    Dieses Modul erlaubt es alle Bildertexte auf falsch erkannte Buchstaben bzw. falsche Wörter zu untersuchen.<br>
                    Mögliche Fehler werden direkt korrigiert.<br>
                    Zur Fehleranalyse werden Wörterbücher und alternativ ein Machine-Learning Modell eingesetzt.
                </p>
                <div>
                    <select class="form-select input_option_admin" onchange="fetchColumns(value)" id="spell_correction_table_select">
                        <option>Tabelle auswählen</option>
                        <?php foreach ($tables as &$val){?>
                                <option value="<?php print $val; ?>"><?php print $val; ?></option>
                        <?php }?>
                    </select>

                    <select class="form-select input_option_admin" id="spell_correction_column_input_select">
                        <option>Spalte auswählen (Input)</option>
                    </select>

                    <select class="form-select input_option_admin" id="spell_correction_column_output_select">
                        <option>Spalte auswählen (Output)</option>
                    </select>

                    <div class="form-check form-switch input_option_admin">
                        <input class="form-check-input" type="checkbox" role="switch" id="spelling_correction_useML">
                        <label class="form-check-label" for="spelling_correction_useML">Machine-Learning Modell benutzen</label>
                    </div>
                    
                    <div class="form-check form-switch input_option_admin">
                        <input class="form-check-input" type="checkbox" role="switch" id="spelling_correction_langFilter" onclick="showLangFilter(this)">
                        <label class="form-check-label" for="spelling_correction_langFilter">Nur gezielte Sprache überprüfen</label>
                    </div>

                    <select class="form-select input_option_admin" id="spell_correction_select_langFilter" style="display:none;">
                        <option>Sprache auswählen</option>
                        <?php foreach ($languages as &$val){?>
                                <option value="<?php print $val; ?>"><?php print $val; ?></option>
                        <?php }?>
                    </select>

                    <br>

                    <a href="#" class="btn btn-success" onclick="run_spelling_correction()">Fehlerkorrektur ausführen</a>
                </div>
            </div>
            <div class="card-footer text-body-secondary" id="footer_spelling_correction">
                Vorsicht! Dieser Prozess kann einige Zeit in anspruch nehmen!
                <div class="spinner-border" id="spinner_spelling_correction" role="status" style="float: right; display:none;">
                    <span class="sr-only"></span>
                </div>
                <div id="success_spelling_correction" role="status" style="float: right;display:none;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" class="bi bi-check" viewBox="0 0 16 16" style="border: 1px solid #5aa940; border-radius: 22px; background-color: #b5dfb5;">
                        <path style="color: #07c507;" d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425z"/>
                    </svg>
                </div>
            </div>
        </div>
    </div>
</body>
</html>