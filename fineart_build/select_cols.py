import json,re,collections
d=json.load(open("pool.json")); pool,meta=d["pool"],d["meta"]
auto=json.load(open("artist_cc_auto.json"))
OV={"Q104884":["de"],"Q122382":["ch","uk"],"Q134741":["fr"],"Q146691":["cz"],"Q155626":["us"],"Q160141":["fr"],"Q1133777":["ca"],"Q1390711":["al"],"Q175130":["fr","uk"],"Q214666":["ru"],"Q223725":["it"],"Q240526":["nl","uk"],"Q281812":["fr"],"Q334001":["us"],"Q3133062":["ca"],"Q452321":["us"],"Q365068":["dk","no"],"Q379150":["cz"],"Q466639":["pl"],"Q469063":["fr"],"Q4290523":["uk"],"Q4583808":["no"],"Q44007":["ch","de"],"Q61064":["ru"],"Q77132":["us"],"Q718020":["no"],"Q92539":["ca"],"Q922483":["ie","uk"],"Q958927":["pl"],"Q964608":["uk","fr"],"Q203643":["us"],"Q4583808":["no"],"Q173223":["us"],"Q120993":["it"],"Q724894":["fr"],"Q510723":["gr"],"Q112894782":["il"],"Q216018":["tr"],"Q124799132":["mx"]}
JEWISH={"Q134741","Q964608","Q120993","Q158062","Q512596","Q160141","Q443136","Q266415","Q214666","Q211356","Q528460","Q979534","Q213596","Q215073","Q469063","Q215572","Q213735","Q281812","Q379150","Q473771","Q1273537","Q594345","Q359506","Q1498652","Q69651","Q6505783","Q2839882","Q1674765","Q213726","Q9374535","Q2580416","Q4290523","Q215550","Q112894782"}
EXTRA_J={"Simeon Solomon","Solomon J. Solomon","Max Kurzweil","Isaak Brodsky"}  # names to flag if present
def cc(q):
    return OV.get(q) or auto.get(q,{}).get("cc",[])
def isjew(q): return q in JEWISH or auto.get(q,{}).get("jewish") or meta[q]["name"] in EXTRA_J
SKIP=re.compile(r"puberty|brothel|^ashes|caricature portrait|albertine|sick girl|death and the child|altarpiece in|^wrestlers|^arcadia|love locked out|^eva$|terror antiquus|samson and delilah|expulsion from the garden|prometheus bound|dead horse|carcass of beef|beef and calf|the wounded|massacre|slave|suicide|execution|hanging|corpse|crucif",re.I)
NUDE=re.compile(r"\b(nude|nu |bather|bathers|odalisque|venus|bath|toilette|baigneuse|naked|akt|harem|rape|slave market|origin of the world|susanna|leda|danaë|danae|bacchante|naiad|nymph)\b",re.I)
for p in pool.values():
    p["cc"]=sorted({c for a in p["artists"] for c in cc(a[0])})
    p["jew"]=any(isjew(a[0]) for a in p["artists"])
    p["nude"]=bool(NUDE.search(p["title"])) or bool(SKIP.search(p["title"]))
CAN_CAPS={"Tom Thomson":12,"Emily Carr":9,"Cornelius Krieghoff":9,"Paul Kane":8,"Paul Peel":5,"James Wilson Morrice":6,"Maurice Galbraith Cullen":5,"Homer Watson":5,"Lawren Harris":5,"J. E. H. MacDonald":5,"Franklin Carmichael":3,"Frank Johnston":3,"Arthur Lismer":3,"Horatio Walker":4,"Clarence Gagnon":4,"Marc-Aurèle de Foy Suzor-Coté":4,"Frederick Arthur Verner":3,"Frances Anne Hopkins":4,"Antoine Plamondon":3,"Théophile Hamel":3,"Joseph Légaré":3,"William Raphael":2,"William Brymner":3,"David Milne":3,"George Agnew Reid":3,"Henri Beau":1,"Charles Huot":2,"Robert Harris":2,"Aaron Allan Edson":2,"Henry Sandham":2,"Zacharie Vincent":1,"Eugène Hamel":1,"Florence Carlyle":1,"William Blair Bruce":1,"Thomas Davies":2,"William G. R. Hind":2,"Robert Clow Todd":1,"Laura Muntz Lyall":2,"Mary Riter Hamilton":2,"Peter Rindisbacher":2,"Arthur Heming":1,"Charles Alexander Smith":1}
def pick_canada(n=100):
    c=sorted([p for p in pool.values() if "ca" in p["cc"] and not p["nude"]],key=lambda p:(-p["sl"],p["title"]))
    cnt=collections.Counter(); out=[]
    for p in c:
        a=p["artists"][0][1]; cap=CAN_CAPS.get(a,0)
        if cnt[a]>=cap: continue
        cnt[a]+=1; out.append(p)
    return out[:n]
def pick(pred,n,cap,exist_cap=None):
    c=sorted([p for p in pool.values() if pred(p) and not (p["nude"] and not p["have"])],key=lambda p:(-p["sl"],p["title"]))
    cnt=collections.Counter(); out=[]
    for p in c:
        a=p["artists"][0][0]
        if cnt[a]>=cap: continue
        cnt[a]+=1; out.append(p)
        if len(out)>=n: break
    return out
COLS={
 "jewish":("jewish",100,12,lambda p:p["jew"]),
 "canada":("canada",100,12,lambda p:"ca" in p["cc"]),
 "norway":("norway",100,14,lambda p:"no" in p["cc"]),
 "usa":("usa",100,10,lambda p:"us" in p["cc"]),
 "japan":("japan",40,8,lambda p:"jp" in p["cc"]),
 "china":("china",25,6,lambda p:"cn" in p["cc"]),
 "middle-east":("middle-east",15,6,lambda p:bool({"tr","ir","eg","lb","il"}&set(p["cc"]))),
  "mexico":("mexico",15,6,lambda p:"mx" in p["cc"]),
}
for cc_,n in (("fr",40),("it",30),("es",30),("nl",25),("de",25),("uk",40),("ru",40),("pl",20),("se",20),("dk",20),("fi",15),("at",15),("be",12),("ch",10),("au",12),("br",10)):
    COLS[cc_]=(cc_,n,6,lambda p,cc_=cc_:cc_ in p["cc"])
sel={}
for k,(slug,n,cap,pred) in COLS.items():
    sel[k]=[p["qid"] for p in (pick_canada(n) if k=="canada" else pick(pred,n,cap))]
newq=set()
for k,v in sel.items():
    new=[q for q in v if not pool[q]["have"]]; newq|=set(new)
    print(f"{k:12} total {len(v):3} new {len(new):3}")
print("unique new paintings:",len(newq))
json.dump({"sel":sel,"pool":pool},open("sel.json","w"),ensure_ascii=False)
