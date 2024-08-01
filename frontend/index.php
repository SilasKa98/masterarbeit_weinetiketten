<!doctype html>
<html lang="en" data-bs-theme="auto">
  <head>

    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="author" content="Silas Kammerer">
    <title>Weinetiketten App</title>
    <script src="scripts/status_polling.js"></script>
    <script src="scripts/search_calls_handler.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.2.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-GLhlTQ8iRABdZLl6O3oVMWSktQOp6b7In1Zl3/Jr59b6EGGoI1aFkw7cmDA6j6gD" crossorigin="anonymous">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js" integrity="sha384-w76AqPfDkMBDXo30jS1Sgez6pr3x5MlQ1ZAGC+nuZB+EYdgRZgiwxhTBTkF7CXvN" crossorigin="anonymous"></script>
    <link href="styles/index.css" rel="stylesheet">

  </head>
  <body>
    <?php include_once "components/navbar.php"?>
  	<div class="content_container">
      <main>
        <div class="position-relative overflow-hidden p-3 p-md-5 m-md-3 text-center h-100">
          <div class="col-md-6 p-lg-5 mx-auto my-5">
            <h1 class="display-3 fw-bold">Weinetiketten</h1>
            <h3 class="fw-normal text-muted mb-3">Die intelligente Suche nach Weinetiketten</h3>
            <div class="input-group mb-3">
              <input type="text" class="form-control" id="search_text" placeholder="" aria-label="..." aria-describedby="basic-addon2">
              <span class="input-group-text" id="index_search_btn_wrapper">
                <button id="index_search_btn" onclick="process_search()">Suchen</button>
              </span>
            </div>
            <div class="form-check form-switch input_option_admin text-start">
              <input class="form-check-input" type="checkbox" role="switch" id="search_logic_combined">
              <label class="form-check-label" for="read_and_save_ocr_only_new_entries">Suchtext zusammenhängend betrachten</label>
            </div>
            <div class="spinner-border" id="spinner_search_algorithm" role="status" style="float: right; display:none;">
                <span class="sr-only"></span>
              </div>
              <div id="success_search_algorithm" role="status" style="float: right;display:none;">
                <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" fill="currentColor" class="bi bi-check" viewBox="0 0 16 16" style="border: 1px solid #5aa940; border-radius: 22px; background-color: #b5dfb5;">
                    <path style="color: #07c507;" d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425z"/>
                </svg>
            </div>

          </div>
        </div>

        <div class="flex-md-equal my-md-3 ps-md-3" id="search_background">
          <div class="text-bg-dark me-md-3 pt-3 px-3 pt-md-5 px-md-5 text-center">
            <div class="my-3 py-3">
              <h2 class="display-5">Suchergebnisse</h2>
            </div>
            <div class="mx-auto" id="image_result_holder" style="width: 80%; min-height: 300px; border-radius: 21px 21px 0 0;">

            </div>
          </div>
        </div>
      </main>
      <footer>
        <?php include_once "components/footer.php"?>
      </footer>
    </div>
  </body>
</html>
