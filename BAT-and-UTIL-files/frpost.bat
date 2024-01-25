@Echo off

 REM we must pipe the output through cat to get ANSI rendered correctl

 frpost-helper.pl %*| cat_fast