import json,sys
for f in sys.argv[1:]:
    for r in json.load(open(f)):
        print(f'{r["id"]}|{r["title"]}|{r["artist"]}|{r["year"]}|{",".join(r["genre_hint"][:2])}')
