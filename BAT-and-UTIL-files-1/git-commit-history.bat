@on break cancel
@Echo OFF

call validate-environment-variable GITHUB_USERNAME

https://github.com/search?o=desc&s=author-date&type=Commits&q=author%%3A%GITHUB_USERNAME%
