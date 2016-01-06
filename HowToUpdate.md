# How to Update

This site is based on the twitter theme with some slight modifications.  Themes can be installed using `rake`:

    rake theme:install name="name or path"

Similarly, if you need to modify the theme (further), change the files under `_theme_packages/twitter`.  Then run the rake task again using `twitter` as the name.  It will ask you if you want to overwrite the files (in `_includes`) -- simply say yes to each.  The next time you rebuild the site, those theme changes will get applied.

# Running the site locally

Jekyll needs to run with an empty base path from the root directory in order to visit the site.  Easy enough, just run`jekyll serve -b ''` and then visit the [site](http://localhost:4000/).