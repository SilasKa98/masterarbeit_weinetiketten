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
    <script src="scripts/status_polling.js"></script>
    <script src="scripts/admin_page_calls_handler.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.2.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-GLhlTQ8iRABdZLl6O3oVMWSktQOp6b7In1Zl3/Jr59b6EGGoI1aFkw7cmDA6j6gD" crossorigin="anonymous">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js" integrity="sha384-w76AqPfDkMBDXo30jS1Sgez6pr3x5MlQ1ZAGC+nuZB+EYdgRZgiwxhTBTkF7CXvN" crossorigin="anonymous"></script>
    <link href="styles/admin.css" rel="stylesheet">
</head>
<body onload="statusPolling(); startPolling(); getImageDirectories('admin')">
<?php include_once "components/navbar.php"?>
    <h1 style="text-align:center"> Admin </h1>

    <div class="position-relative overflow-hidden p-3 p-md-5 m-md-3 bg-body-tertiary outer_card_wrapper">
        <div class="card">
            <div class="card-header">
                <span style="color: #d7a900;">read_and_save_ocr</span>()
            </div>
            <div class="card-body">
                <h5 class="card-title">Weinetiketten einlesen und speichern</h5>
                <p class="card-text">
                    Mit diesem Modul können Weinetiketten mittels OCR eingelesen werden. <br>
                    Dabei können verschiedene Hilfsparameter aktiviert werden, die ein besseres und gezielteres einlesen ermöglichen.
                    Außerdem kann ausgewählt werden, welches OCR-Modell genutzt werden soll.
                </p>
                <div>

                    <select class="form-select input_option_admin" onchange="fetchColumns(value, 'read_and_save_ocr')" id="read_and_save_ocr_table_select">
                        <option>OCR-Modell auswählen</option>
                        <?php foreach ($tables as &$val){?>
                                <option value="<?php print $val; ?>"><?php print $val; ?></option>
                        <?php }?>
                    </select>

                    <select class="form-select input_option_admin" id="read_and_save_ocr_column_input_select">
                        <option>Spalte für Persistierung auswählen</option>
                    </select>

                    <select class="form-select input_option_admin" id="read_and_save_ocr_path_select">
                        <option>Pfad mit Bildern auswählen</option>
                    </select>

                    <div class="form-check form-switch input_option_admin">
                        <input class="form-check-input" type="checkbox" role="switch" id="read_and_save_ocr_use_translation">
                        <label class="form-check-label" for="read_and_save_ocr_use_translation">Etikettensprache erkennen, nutzen und speichern</label>
                    </div>

                    <div class="form-check form-switch input_option_admin">
                        <input class="form-check-input" type="checkbox" role="switch" id="read_and_save_ocr_only_new_entries" onclick="toggleOnlyNewImgs_readSaveOcr(this)">
                        <label class="form-check-label" for="read_and_save_ocr_only_new_entries">Nur nach neuen Bildern suchen</label>
                    </div>

                    <button class="btn btn-success" onclick="run_read_and_save_ocr()">Weinetiketten einlesen</button>
                </div>
            </div>
            <div class="card-footer text-body-secondary" id="footer_read_and_save_ocr">
                Vorsicht! Dieser Prozess kann einige Zeit in Anspruch nehmen!
                <div class="spinner-border" id="spinner_read_and_save_ocr" role="status" style="float: right; display:none;">
                    <span class="sr-only"></span>
                </div>
                <div id="success_read_and_save_ocr" role="status" style="float: right;display:none;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" class="bi bi-check" viewBox="0 0 16 16" style="border: 1px solid #5aa940; border-radius: 22px; background-color: #b5dfb5;">
                        <path style="color: #07c507;" d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425z"/>
                    </svg>
                </div>
            </div>
        </div>
    </div>




    <div class="position-relative overflow-hidden p-3 p-md-5 m-md-3 bg-body-tertiary outer_card_wrapper">
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
                    <select class="form-select input_option_admin" onchange="fetchColumns(value, 'spelling_correction')" id="spell_correction_table_select">
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
                        <input class="form-check-input" type="checkbox" role="switch" id="spelling_correction_only_new">
                        <label class="form-check-label" for="spelling_correction_only_new">Bereits geprüfte Labels ignorieren</label>
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

                    <button class="btn btn-success" onclick="run_spelling_correction()">Fehlerkorrektur ausführen</button>
                </div>
            </div>
            <div class="card-footer text-body-secondary" id="footer_spelling_correction">
                Vorsicht! Dieser Prozess kann einige Zeit in Anspruch nehmen!
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


    <div class="position-relative overflow-hidden p-3 p-md-5 m-md-3 bg-body-tertiary outer_card_wrapper">
        <div class="card">
            <div class="card-header">
                <span style="color: #d7a900;">update_label_detail_infos</span>()
            </div>
            <div class="card-body">
                <h5 class="card-title">Etiketten nach Details durchsuchen</h5>
                <p class="card-text">
                    Mit diesem Modul können die persistierten Details der Weinetiketten aktualisiert werden. 
                    Hierrunter zählen Das <b>Land</b>, die <b>Region</b>, der <b>Jahrgang</b>, der <b>Alkohlgehalt</b> und der <b>Weintyp (Rotwein/Weißwein)</b> des jeweiligen Weines.<br>
                    Jeder erkannte Weinetikettentext wird hierbei nach all diesen Informationen durchsucht. 
                </p>
                <div>
                    <button class="btn btn-success" onclick="run_update_label_detail_infos()">Detailsuche ausführen</button>
                </div>
            </div>
            <div class="card-footer text-body-secondary" id="footer_update_label_detail_infos">
                Vorsicht! Dieser Prozess kann einige Zeit in Anspruch nehmen!
                <div class="spinner-border" id="spinner_update_label_detail_infos" role="status" style="float: right; display:none;">
                    <span class="sr-only"></span>
                </div>
                <div id="success_update_label_detail_infos" role="status" style="float: right;display:none;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" class="bi bi-check" viewBox="0 0 16 16" style="border: 1px solid #5aa940; border-radius: 22px; background-color: #b5dfb5;">
                        <path style="color: #07c507;" d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425z"/>
                    </svg>
                </div>
            </div>
        </div>
    </div>


    <div class="position-relative overflow-hidden p-3 p-md-5 m-md-3 bg-body-tertiary outer_card_wrapper">
        <div class="card">
            <div class="card-header">
                <span style="color: #d7a900;">update_entities_for_labels</span>()
            </div>
            <div class="card-body">
                <h5 class="card-title">Etiketten-Entitäten finden und aktuallisieren</h5>
                <p class="card-text">
                    Mit diesem Modul können für jedes Etikett in der Datenbank Entitäten erstellt werden. <br>
                    Die Entitäten werden durch Natural Language Processing aus dem Etikettentext extrahiert und kategorisiert.<br>
                    Die gewonnenen Informationen werden im JSON Format in der Datenbank abgelegt um sie so später optimal weiter verarbeiten zu können.
                </p>
                <div>
                    <div class="form-check form-switch input_option_admin">
                        <input class="form-check-input" type="checkbox" role="switch" id="update_entities_for_labels_only_missings">
                        <label class="form-check-label" for="update_entities_for_labels_only_missings">Nur fehlende Werte</label>
                    </div>
                    <button class="btn btn-success" onclick="run_update_entities_for_labels()">Entitäten finden und aktuallisieren</button>
                </div>
            </div>
            <div class="card-footer text-body-secondary" id="footer_update_entities_for_labels">
                Vorsicht! Dieser Prozess kann einige Zeit in Anspruch nehmen!
                <div class="spinner-border" id="spinner_update_entities_for_labels" role="status" style="float: right; display:none;">
                    <span class="sr-only"></span>
                </div>
                <div id="success_update_entities_for_labels" role="status" style="float: right;display:none;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" class="bi bi-check" viewBox="0 0 16 16" style="border: 1px solid #5aa940; border-radius: 22px; background-color: #b5dfb5;">
                        <path style="color: #07c507;" d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425z"/>
                    </svg>
                </div>
            </div>
        </div>
    </div>


    <div class="position-relative overflow-hidden p-3 p-md-5 m-md-3 bg-body-tertiary outer_card_wrapper">
        <div class="card">
            <div class="card-header">
                <span style="color: #d7a900;">search_for_duplicate_entrys</span>()
            </div>
            <div class="card-body">
                <h5 class="card-title">Etiketten nach Duplikaten durchsuchen</h5>
                <p class="card-text">
                    Mit diesem Modul können die Etiketten nach möglichen Duplikaten durchsucht werden. <br>
                    Die Duplikatsuche beschränkt sich hierbei auf die Texte der Etiketten. Es werden keine Formen oder sonstiges beachtet. 
                </p>
                <div>
                    <select class="form-select input_option_admin" onchange="fetchColumns(value, 'search_for_duplicate_entrys')" id="search_for_duplicate_entrys_table_select">
                        <option>Tabelle auswählen</option>
                        <?php foreach ($tables as &$val){?>
                                <option value="<?php print $val; ?>"><?php print $val; ?></option>
                        <?php }?>
                    </select>

                    <select class="form-select input_option_admin" id="dup_search_column_input_select">
                        <option>Spalte auswählen</option>
                    </select>

                    <div class="form-check form-switch input_option_admin">
                        <input class="form-check-input" type="checkbox" role="switch" id="search_for_duplicate_entrys_save">
                        <label class="form-check-label" for="search_for_duplicate_entrys_save">Ergebnisse in Datenbank speichern</label>
                    </div>

                    <button class="btn btn-success" onclick="run_search_for_duplicate_entrys()">Duplikatsuche ausführen</button>
                </div>
            </div>
            <div class="card-footer text-body-secondary" id="footer_search_for_duplicate_entrys">
                Dieser Prozess sollte weniger als eine Minute dauern!

                <div class="spinner-border" id="spinner_search_for_duplicate_entrys" role="status" style="float: right; display:none;">
                    <span class="sr-only"></span>
                </div>
                <div id="success_search_for_duplicate_entrys" role="status" style="float: right;display:none;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" class="bi bi-check" viewBox="0 0 16 16" style="border: 1px solid #5aa940; border-radius: 22px; background-color: #b5dfb5;">
                        <path style="color: #07c507;" d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425z"/>
                    </svg>
                </div>

                <div class="d-flex justify-content-end" style="margin-top: 20px;">
                    <button class="btn btn-info text-right" style="display: none;" id="result_search_for_duplicate_entrys_btn" type="button" data-bs-toggle="collapse" data-bs-target="#result_search_for_duplicate_entrys_wrp" aria-expanded="false" aria-controls="result_search_for_duplicate_entrys">
                       Ergebnisse anzeigen
                    </button>
                </div>
            </div>
            <div class="collapse" id="result_search_for_duplicate_entrys_wrp">
                <div class="card card-body" id="result_search_for_duplicate_entrys">
                </div>
            </div>
        </div>
    </div>



    <div class="position-relative overflow-hidden p-3 p-md-5 m-md-3 bg-body-tertiary outer_card_wrapper">
        <div class="card">
            <div class="card-header">
                <span style="color: #d7a900;">check_directory_for_duplicates</span>()
            </div>
            <div class="card-body">
                <h5 class="card-title">Duplikate erkennen</h5>
                <p class="card-text">
                   Dieses Modul kann zum finden von Duplikaten vor dem eigentlichen Hochladen der neuen Etiketten genutzt werden.<br>
                   So soll sichergestellt werden, dass keine Etiketten hochgeladen werden, die sich bereits in der Sammlung befinden.                          
                </p>
                <div>
                    <input type="file"  name="images" id="duplicate_directory_file" webkitdirectory directory multiple><br><br>
                    <button class="btn btn-success" onclick="run_check_directory_for_duplicates()">Nach Duplikaten suchen</button>
                </div>
            </div>
            <div class="card-footer text-body-secondary" id="footer_check_directory_for_duplicates">
                Vorsicht! Eine große Anzahl an Etiketten kann eine lange Verarbeitungszeit bedeuten.
                <div class="spinner-border" id="spinner_check_directory_for_duplicates" role="status" style="float: right; display:none;">
                    <span class="sr-only"></span>
                </div>
                <div id="success_check_directory_for_duplicates" role="status" style="float: right;display:none;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" class="bi bi-check" viewBox="0 0 16 16" style="border: 1px solid #5aa940; border-radius: 22px; background-color: #b5dfb5;">
                        <path style="color: #07c507;" d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425z"/>
                    </svg>
                </div>
                <div class="d-flex justify-content-end" style="margin-top: 20px;">
                    <button class="btn btn-info text-right" style="display: none;" id="result_check_directory_for_duplicates_btn" type="button" data-bs-toggle="collapse" data-bs-target="#result_check_directory_for_duplicates_wrp" aria-expanded="false" aria-controls="result_check_directory_for_duplicates">
                       Ergebnisse anzeigen
                    </button>
                </div>
            </div>
            <div class="collapse" id="result_check_directory_for_duplicates_wrp">
                <div class="card card-body" id="result_check_directory_for_duplicates">
                </div>
            </div>
        </div>
    </div>




    <div class="position-relative overflow-hidden p-3 p-md-5 m-md-3 bg-body-tertiary outer_card_wrapper">
        <div class="card">
            <div class="card-header">
                <span style="color: #d7a900;">read_db_and_detect_lang</span>()
            </div>
            <div class="card-body">
                <h5 class="card-title">Etikettensprache erkennen</h5>
                <p class="card-text">
                   Dieses Modul dient zur erkennung der Sprache auf Weinetiketten. Unter Umständen, wurde dies bereits beim initialen Einlesen der Etiketten durchgeführt. <br>
                   Allerdings gibt es hiermit die Möglichkeit manuell nochmals für alle Etiketten die Sprache zu erkennen.<br>
                   Sollte der Schalter für "Alles erneut erkennen" auf "aus" gesetzt sein, werden nur neue bzw. noch nicht erkannte Etiketten analysiert.<br>
                   Anderenfalls werden alle Etiketten erneut analysiert und überprüft, dies kann zu längeren Bearbeitungszeit führen.
                </p>
                <div>
                    <div class="form-check form-switch input_option_admin">
                        <input class="form-check-input" type="checkbox" role="switch" id="read_db_and_detect_lang_force_update">
                        <label class="form-check-label" for="read_db_and_detect_lang_force_update">Alles erneut erkennen</label>
                    </div>

                    <button class="btn btn-success" onclick="run_read_db_and_detect_lang()">Sprachen erkennen</button>
                </div>
            </div>
            <div class="card-footer text-body-secondary" id="footer_read_db_and_detect_lang">
                Vorsicht! Dieser Prozess kann einige Zeit in Anspruch nehmen!
                <div class="spinner-border" id="spinner_read_db_and_detect_lang" role="status" style="float: right; display:none;">
                    <span class="sr-only"></span>
                </div>
                <div id="success_read_db_and_detect_lang" role="status" style="float: right;display:none;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" class="bi bi-check" viewBox="0 0 16 16" style="border: 1px solid #5aa940; border-radius: 22px; background-color: #b5dfb5;">
                        <path style="color: #07c507;" d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425z"/>
                    </svg>
                </div>
            </div>
        </div>
    </div>


    <div class="position-relative overflow-hidden p-3 p-md-5 m-md-3 bg-body-tertiary outer_card_wrapper">
        <div class="card">
            <div class="card-header">
                <span style="color: #d7a900;">modify_images</span>()
            </div>
            <div class="card-body">
                <h5 class="card-title">Etikettenbilder modifizieren</h5>
                <p class="card-text">
                    Mit diesem Modul können die Etikettenbilder visuell modifiziert werden. Durch die Modifizierung kann das Einlesen mittels OCR verbessert werden.<br>
                    Zur Modifikation werden folgende Schritte durchgeführt: <b>"Grayscaling", "Sharpening", "Contrast bumping", "Noise removing", "Blur applying"</b> <br>
                    und alternativ auch <b>"Image rescaling"</b>, wenn die Bildauflösung kleiner als 300 dpi ist.<br>
                    Die modifizierten Bilder werden in <b>"wine_images/edited_wine_imgages"</b> gespeichert.
                </p>
                <div>
                    
                    <select class="form-select input_option_admin" id="modify_images_path_select">
                        <option>Pfad mit Bildern auswählen</option>
                    </select>

                    <button class="btn btn-success" onclick="run_modify_images()">Bildmodifikationen ausführen</button>
                </div>
            </div>
            <div class="card-footer text-body-secondary" id="footer_modify_images">
                Vorsicht! Dieser Prozess kann einige Zeit in Anspruch nehmen!
                <div class="spinner-border" id="spinner_modify_images" role="status" style="float: right; display:none;">
                    <span class="sr-only"></span>
                </div>
                <div id="success_modify_images" role="status" style="float: right;display:none;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" class="bi bi-check" viewBox="0 0 16 16" style="border: 1px solid #5aa940; border-radius: 22px; background-color: #b5dfb5;">
                        <path style="color: #07c507;" d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425z"/>
                    </svg>
                </div>
            </div>
        </div>
    </div>


</body>
</html>