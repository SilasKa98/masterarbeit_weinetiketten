<!doctype html>
<html lang="en" data-bs-theme="auto">
  <head>

    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="author" content="Silas Kammerer">
    <title>Weinetiketten App</title>

    <script src="https://code.jquery.com/jquery-3.6.2.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-GLhlTQ8iRABdZLl6O3oVMWSktQOp6b7In1Zl3/Jr59b6EGGoI1aFkw7cmDA6j6gD" crossorigin="anonymous">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js" integrity="sha384-w76AqPfDkMBDXo30jS1Sgez6pr3x5MlQ1ZAGC+nuZB+EYdgRZgiwxhTBTkF7CXvN" crossorigin="anonymous"></script>
    <link href="styles/index.css" rel="stylesheet">

  </head>
  <body>
    <?php include_once "components/navbar.php"?>

    <main>
      <div class="position-relative overflow-hidden p-3 p-md-5 m-md-3 text-center bg-body-tertiary">
        <div class="col-md-6 p-lg-5 mx-auto my-5">
          <h1 class="display-3 fw-bold">Weinetiketten Suche</h1>
          <h3 class="fw-normal text-muted mb-3">Build anything you want with Aperture</h3>
          <div class="input-group mb-3">
            <input type="text" class="form-control" placeholder="..." aria-label="..." aria-describedby="basic-addon2">
            <span class="input-group-text" id="index_search_btn_wrapper">
              <button id="index_search_btn">Suchen</button>
            </span>
          </div>

        </div>
      </div>

      <div class="flex-md-equal my-md-3 ps-md-3">
        <div class="text-bg-dark me-md-3 pt-3 px-3 pt-md-5 px-md-5 text-center overflow-hidden">
          <div class="my-3 py-3">
            <h2 class="display-5">Another headline</h2>
            <p class="lead">And an even wittier subheading.</p>
          </div>
          <div class="mx-auto" style="width: 80%; height: 300px; border-radius: 21px 21px 0 0;">
            <p>test</p>
          </div>
        </div>
      </div>

      <div class="flex-md-equal my-md-3 ps-md-3">
        <div class="text-bg-dark me-md-3 pt-3 px-3 pt-md-5 px-md-5 text-center overflow-hidden">
          <div class="my-3 py-3">
            <h2 class="display-5">Another headline</h2>
            <p class="lead">And an even wittier subheading.</p>
          </div>
          <div class="mx-auto" style="width: 80%; height: 300px; border-radius: 21px 21px 0 0;">
            <p>test2</p>
          </div>
        </div>
      </div>

    </main>

<?php include_once "components/footer.php"?>
<script src="../assets/dist/js/bootstrap.bundle.min.js"></script>

    </body>
</html>
