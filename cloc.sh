#!/usr/bin/env bash
#cloc --exclude-dir=doc,texts,LL1Table,.idea,resources_gen,ui --exclude-list-file=.cloc_exclude_file --exclude-lang=SQL ./
cloc --exclude-list-file=.cloc_exclude_file --exclude-lang=SQL --exclude-ext=txt ./
