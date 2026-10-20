import json, requests, warnings, time
warnings.filterwarnings("ignore")
H={"User-Agent":"BurrowOwlsFineArt/1.0 (blueajah@pm.me)"}
JEWISH=["Camille Pissarro","Lucien Pissarro","Amedeo Modigliani","Max Liebermann","Lesser Ury","Chaim Soutine","Maurycy Gottlieb","Isidor Kaufmann","Léon Bakst","Isaac Levitan","Jozef Israëls","Isaac Israëls","Leonid Pasternak","Moritz Daniel Oppenheim","Jules Pascin","Felix Nussbaum","Charlotte Salomon","Moïse Kisling","Emil Orlik","Hermann Struck","Ephraim Moses Lilien","Samuel Hirszenberg","Mark Gertler","Solomon Alexander Hart","Eduard Bendemann","Julius Rolshoven","Lazar Krestin","Abel Pann","Jakob Steinhardt","Josef Israels","Alphonse Lévy","Edmund Blair Leighton","Boris Schatz","Marc Chagall","Mané-Katz","Issachar Ber Ryback","Alexander Bogomazov","Jankel Adler","Lasar Segall","Eugen Spiro","Jozef Mehoffer","Alfred Stevens","Leopold Gottlieb","Marcel Janco","Josef Sudek","Henryk Gotlib","Wilhelm Wachtel","Leo Kahn","William Rothenstein","Philip de László","Jacob Kramer","Bernard Meninsky","Lilian Westcott Hale","Maurice Sterne","William Zorach","Max Weber","Abraham Walkowitz","Louis Lozowick","Marsden Hartley","Man Ray","Rudolf Levy","Ludwig Meidner","Lotte Laserstein","Gabriele Münter"]
CANADA=["Tom Thomson","Emily Carr","Cornelius Krieghoff","Paul Kane","Paul Peel","Homer Watson","Ozias Leduc","James Wilson Morrice","Maurice Cullen","Horatio Walker","J. E. H. MacDonald","William Brymner","Clarence Gagnon","Marc-Aurèle de Foy Suzor-Coté","Lucius O'Brien","Napoléon Bourassa","Théophile Hamel","Antoine Plamondon","Robert Harris","Frederick Arthur Verner","Charles Huot","Joseph Légaré","William Raphael","Robert Pilot","Frances Anne Hopkins","Thomas Davies","George Agnew Reid","Franklin Carmichael","Arthur Lismer","Frank Johnston","Lawren Harris","A. Y. Jackson","Marc-Aurele Fortin","Edwin Holgate","David Milne","John Lyman","Blair Bruce","Wyatt Eaton","Henri Julien","Adolphe Rho","Eugène Hamel","Allan Edson","John A. Fraser","Otto Jacobi","Arthur Heming","William G. R. Hind","Henry Sandham","Mary Riter Hamilton","Florence Carlyle","Laura Muntz Lyall","William Blair Bruce","Ernest Lawson","Tom Roberts","Peter Rindisbacher","Robert Clow Todd","Cornelius Kreighoff","Berthe Des Clayes","Jean-Paul Riopelle"]
def find(name):
    r=requests.get("https://www.wikidata.org/w/api.php",params={"action":"wbsearchentities","search":name,"language":"en","type":"item","limit":3,"format":"json"},headers=H,timeout=30).json()
    return [(x["id"],x.get("description","")) for x in r.get("search",[])]
out={}
for grp,names in (("jewish",JEWISH),("canada",CANADA)):
    for n in names:
        try: out[(grp,n)]=find(n)
        except Exception as e: out[(grp,n)]=[]
        time.sleep(0.15)
res={f"{g}|{n}":v for (g,n),v in out.items()}
json.dump(res,open("artist_search.json","w"),ensure_ascii=False,indent=0)
for k,v in res.items(): print(k,v[:2])
