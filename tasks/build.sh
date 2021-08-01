#!/usr/bin/env bash

PROJECT="NukeServerSocket"
(
    cd ..
    zip -r "$PROJECT/dist/$PROJECT.zip" \
        $PROJECT/src \
        $PROJECT/__init__.py \
        $PROJECT/CHANGELOG.md \
        $PROJECT/README.md \
        $PROJECT/LICENSE
)

build=$(git branch --show-current)
zip_file="dist/${PROJECT}_$build.zip"

if [[ -f $zip_file ]]; then
    rm "$zip_file"
fi

# rename file so when unzipped has only the name with no build
mv dist/$PROJECT.zip "$zip_file"
