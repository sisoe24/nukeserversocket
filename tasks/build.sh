#!/usr/bin/env bash
#
# Internal script that should be launched from vscode task ZipProject.
#
# Build zip project with only essential files. needs git to append the build version
#

PROJECT=$(basename "$(pwd)")

(
    cd ..
    zip -r "$PROJECT/dist/$PROJECT.zip" \
        "$PROJECT"/src \
        "$PROJECT"/__init__.py \
        "$PROJECT"/CHANGELOG.md \
        "$PROJECT"/README.md \
        "$PROJECT"/LICENSE \
        "$PROJECT"/VERSION
)

# only works for git > 2.22
# build=$(git branch --show-current)

build=$(git rev-parse --abbrev-ref HEAD)
version=$(cat VERSION)

zip_file="dist/${PROJECT}_${build}_${version}.zip"

if [[ -f $zip_file ]]; then
    rm "$zip_file"
fi

# rename file so when unzipped has only the name with no build
mv dist/"$PROJECT".zip "$zip_file"
