#!/usr/bin/env bash
#
# Internal script that should be launched from vscode task ZipProject.
#
# Build zip project with only essential files. needs git to append the build version
#

find . -type f \( -name '*.pyc' -o -name '.DS_Store' \) -exec rm {} \;

PROJECT=$(basename "$(pwd)")

(
    cd ..
    zip -r "$PROJECT/dist/$PROJECT.zip" \
        "$PROJECT"/src \
        "$PROJECT"/__init__.py \
        "$PROJECT"/CHANGELOG.md \
        "$PROJECT"/README.md \
        "$PROJECT"/LICENSE \
)

# only works for git > 2.22
# build=$(git branch --show-current)

build=$(git rev-parse --abbrev-ref HEAD)
version=$( < pyproject.toml grep version | grep -Eo '".+"' | sed 's/"//g')

zip_file="dist/${PROJECT}_${build}_${version}.zip"

if [[ -f $zip_file ]]; then
    rm "$zip_file"
fi

# rename file so when unzipped has only the name with no build
mv dist/"$PROJECT".zip "$zip_file"
