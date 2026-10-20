import json,re,collections
d=json.load(open("pool.json")); pool,meta=d["pool"],d["meta"]
MAP={"France":"fr","Kingdom of France":"fr","French Third Republic":"fr","French Empire":"fr","First French Empire":"fr","Second French Empire":"fr","July Monarchy":"fr","Bourbon Restoration":"fr","Italy":"it","Kingdom of Italy":"it","Spain":"es","Netherlands":"nl","Kingdom of the Netherlands":"nl","Dutch Republic":"nl","Germany":"de","German Empire":"de","Kingdom of Prussia":"de","Kingdom of Bavaria":"de","Weimar Republic":"de","Nazi Germany":"de","Prussia":"de","Kingdom of Saxony":"de","Grand Duchy of Baden":"de","Kingdom of Württemberg":"de","Confederation of the Rhine":"de","Free City of Frankfurt":"de","United Kingdom":"uk","United Kingdom of Great Britain and Ireland":"uk","Kingdom of Great Britain":"uk","England":"uk","Scotland":"uk","British Empire":"uk","Wales":"uk","Russia":"ru","Russian Empire":"ru","Soviet Union":"ru","Poland":"pl","Second Polish Republic":"pl","Congress Poland":"pl","Kingdom of Poland":"pl","Sweden":"se","Denmark":"dk","Kingdom of Denmark":"dk","Denmark-Norway":"no_x","Finland":"fi","Grand Duchy of Finland":"fi","Norway":"no","Kingdom of Norway":"no","Denmark–Norway":"no_x","Canada":"ca","United States":"us","United States of America":"us","Austria":"at","Cisleithania":"at","Austria-Hungary":"at","Austrian Empire":"at","Archduchy of Austria":"at","Belgium":"be","Switzerland":"ch","Japan":"jp","Empire of Japan":"jp","Tokugawa shogunate":"jp","Edo period":"jp","China":"cn","People's Republic of China":"cn","Qing dynasty":"cn","Republic of China (1912–1949)":"cn","Republic of China":"cn","Turkey":"tr","Ottoman Empire":"tr","Iran":"ir","Qajar dynasty":"ir","India":"in","British Raj":"in","Mexico":"mx","Ukraine":"ua","Czech Republic":"cz","Czechoslovakia":"cz","Kingdom of Bohemia":"cz","Hungary":"hu","Kingdom of Hungary":"hu","Ireland":"ie","Australia":"au","Philippines":"ph","Portugal":"pt","Greece":"gr","Romania":"ro","Lithuania":"lt","Latvia":"lv","Estonia":"ee","Belarus":"by","Argentina":"ar","Brazil":"br","Slovenia":"si","Croatia":"hr","Serbia":"rs","Bulgaria":"bg","Albania":"al","Iceland":"is","Egypt":"eg","Lebanon":"lb","South Africa":"za","Cuba":"cu","Chile":"cl","Peru":"pe","Venezuela":"ve","Colombia":"co","Indonesia":"id","Korea":"kr","Slovakia":"sk","Luxembourg":"lu","Israel":"il","Mandatory Palestine":"il","Puerto Rico":"pr","Taiwan":"tw","Republic of China (Taiwan)":"tw","Kingdom of Sardinia":"it","Kingdom of Naples":"it","Republic of Venice":"it","Papal States":"it","Kingdom of Two Sicilies":"it","Grand Duchy of Tuscany":"it","Duchy of Savoy":"it","Habsburg monarchy":"at","Kingdom of Spain":"es","Spanish Empire":"es","Habsburg Spain":"es","Kingdom of Portugal":"pt","Kingdom of Sweden":"se","Swedish Empire":"se","Kingdom of Belgium":"be","United Netherlands":"nl","Batavian Republic":"nl","Kingdom of Holland":"nl","Free State of Prussia":"de","German Reich":"de","German Confederation":"de","Hanover":"de","Kingdom of Hanover":"de","Duchy of Brunswick":"de","Grand Duchy of Hesse":"de","Free City of Hamburg":"de","Free Hanseatic City of Bremen":"de","Kingdom of Italy (Napoleonic)":"it","Duchy of Modena and Reggio":"it","Principality of Serbia":"rs","Kingdom of Yugoslavia":"rs","Yugoslavia":"rs","Latvia":"lv","Georgia":"ge","Armenia":"am","Azerbaijan":"az","Republic of Ireland":"ie","Kingdom of Ireland":"ie","Mexican Empire":"mx","Second Mexican Empire":"mx","Hawaii":"us","Confederate States of America":"us","Thirteen Colonies":"us","Colony of Virginia":"us","Province of Massachusetts Bay":"us"}
def codes(m):
    c=collections.Counter()
    for x in m["cit"]:
        if x in MAP: c[MAP[x]]+=2
    if not c:
        for x in m["born"]:
            if x in MAP: c[MAP[x]]+=1
    return [k for k,_ in c.most_common()]
res={}; unk=[]
for q,m in meta.items():
    cs=codes(m)
    res[q]={"name":m["name"],"cc":cs,"jewish":("Jewish people" in m["eth"] or any("Jew" in e for e in m["eth"]))}
    if not cs: unk.append((q,m["name"],m["cit"],m["born"]))
json.dump(res,open("artist_cc_auto.json","w"),ensure_ascii=False)
print(len(res),"artists;",len(unk),"without code")
for u in unk[:60]: print(u)
multi=[(q,r["name"],r["cc"]) for q,r in res.items() if len(r["cc"])>1]
print(len(multi),"multi"); 
for m in multi[:80]: print(m)
