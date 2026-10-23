#!/bin/bash
S=/private/tmp/claude-501/-Users-whitetower-dev-burrow-owls/717d435b-0809-4761-bc97-df7352efb381/scratchpad
cd /Users/whitetower/dev/burrow-owls/fineart_build/old
python3 sheet2.py $1 $2
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu --hide-scrollbars --window-size=1500,1250 --virtual-time-budget=25000 --screenshot=$S/o_$1.png file://$S/sheet_o.html >/dev/null 2>&1
