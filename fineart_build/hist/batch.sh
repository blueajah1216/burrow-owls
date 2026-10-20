#!/bin/bash
S=/private/tmp/claude-501/-Users-whitetower-dev-burrow-owls/717d435b-0809-4761-bc97-df7352efb381/scratchpad
cd /Users/whitetower/dev/burrow-owls/fineart_build/hist
python3 sheet.py $1 48 >/dev/null
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --screenshot=$S/sheet_h$1.png --window-size=1300,1720 --virtual-time-budget=25000 file://$S/sheet_h.html 2>/dev/null
python3 todo.py $1 48
