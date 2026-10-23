from src_world import M, add

# extra aliases for venue strings used by the newer paintings
for m in M:
    if m["slug"] == "thyssen": m["aliases"] += ["Thyssen-Bornemisza Museum"]
    if m["slug"] == "vatican-museums": m["aliases"] += ["Sistine Chapel", "Pinacoteca Vaticana"]

add(slug="palatina", name="Palatine Gallery (Palazzo Pitti)", wiki="Palatine Gallery", city="Florence", country="Italy", continent="Europe",
 aliases=["Galleria Palatina"], founded="1828",
 desc="Rooms in the huge Pitti Palace in Florence are hung floor to ceiling with paintings in golden frames, as they were when the Medici family and later Grand Dukes of Tuscany lived there. It has the largest collection of Raphael's work outside the Vatican.",
 history="The Pitti Palace was begun in the 1400s for a Florentine banker and was bought by the Medici in 1549. Over the next centuries the family and their successors, the Habsburg-Lorraine grand dukes, hung their favorite paintings in the state rooms. The collection was opened to the public in 1828, and the rooms were kept much as they were, with paintings arranged by their look rather than by date or artist.",
 highlights=[("Madonna della Seggiola","Raphael",1513),("La Velata","Raphael",1513),("Portrait of Leo X","Raphael",1518)])
add(slug="budapest-mfa", name="Museum of Fine Arts, Budapest", wiki="Museum of Fine Arts, Budapest", city="Budapest", country="Hungary", continent="Europe",
 aliases=["Museum of Fine Arts, Budapest"], founded="1906",
 desc="Hungary's biggest museum of foreign art stands on Heroes' Square in Budapest and holds Old Masters from Spain, Italy and the Netherlands, such as El Greco, Raphael and Goya, along with later European art.",
 history="The museum opened in 1906 in a grand neoclassical building. Its collection began with the Esterházy family's paintings, which the Hungarian state bought in 1871. It was damaged in the Second World War and reopened, and it was renovated in the 2010s.",
 highlights=[("The Penitent Mary Magdalene","El Greco",1570)])
add(slug="conde-museum", name="Musée Condé", wiki="Musée Condé", city="Chantilly", country="France", continent="Europe",
 aliases=["Condé Museum"], founded="1898",
 desc="A museum in a fairy-tale castle by a lake near Paris, with one of the best collections of old master paintings in France, rare illuminated manuscripts and Raphael's Three Graces.",
 history="The Duke of Aumale, a son of the last French king, collected art and books during his exile in England and, when he returned, put them in the Château de Chantilly. He gave the castle and collection to the Institut de France in 1886, with the condition that nothing be changed. It opened to the public in 1898, and the paintings still hang as he arranged them.",
 highlights=[("Three Graces","Raphael",1500),("Portrait of Simonetta Vespucci","Piero di Cosimo",1480)])
add(slug="wallraf-richartz", name="Wallraf-Richartz-Museum", wiki="Wallraf-Richartz Museum", city="Cologne", country="Germany", continent="Europe",
 aliases=["Wallraf–Richartz Museum"], founded="1861",
 desc="Cologne's museum of European painting from the Middle Ages to the 1800s shows the medieval masters of the city, such as Stefan Lochner, and also Rubens, Rembrandt and the Impressionists.",
 history="A Cologne priest and professor, Ferdinand Franz Wallraf, left his collection to the city in 1824. A merchant, Johann Heinrich Richartz, paid for the first museum building, which opened in 1861. It was badly damaged in the Second World War, and the museum has been housed in a modern building since 2001.",
 highlights=[("Madonna of the Rose Bower","Stefan Lochner",1440)])
add(slug="gardner", name="Isabella Stewart Gardner Museum", wiki="Isabella Stewart Gardner Museum", city="Boston", country="United States", continent="North America",
 aliases=["Isabella Stewart Gardner Museum"], founded="1903",
 desc="A Venetian-style palace in Boston with a sunny courtyard garden was built to hold one woman's art collection, from Titian and Botticelli to Sargent. Her will says nothing may be changed, so empty frames still hang where paintings were stolen.",
 history="Isabella Stewart Gardner, a rich Bostonian, collected art on her travels and built the palace to show it. It opened in 1903. When she died in 1924, her will required that the arrangement be kept as it was. In 1990 thieves disguised as police officers stole 13 works, including a Vermeer and a Rembrandt, and they have never been found, so the empty frames are still on the walls.",
 highlights=[("The Concert","Johannes Vermeer",1663),("The Rape of Europa","Titian",1560),("The Story of Lucretia","Sandro Botticelli",1500)])
add(slug="groeninge", name="Groeningemuseum", wiki="Groeningemuseum", city="Bruges", country="Belgium", continent="Europe",
 aliases=["Groeningemuseum"], founded="1930",
 desc="The art museum of the old Belgian city of Bruges is the best place to see Flemish Primitives, with Jan van Eyck, Hans Memling and Gerard David, who all worked in Bruges.",
 history="Bruges was one of the richest cities in Europe in the 1400s, with painters supported by rich merchants and bankers. The city's art collection, started in the 1700s, moved into its present building in 1930. It holds about 800 years of art, with the Flemish masters at its center.",
 highlights=[("Madonna with Canon Joris van der Paele","Jan van Eyck",1436),("Portrait of Margareta van Eyck","Jan van Eyck",1439),("Judgement of Cambyses","Gerard David",1498),("Moreel Triptych","Hans Memling",1484)])
add(slug="boijmans", name="Museum Boijmans Van Beuningen", wiki="Museum Boijmans Van Beuningen", city="Rotterdam", country="Netherlands", continent="Europe",
 aliases=["Museum Boijmans Van Beuningen"], founded="1849",
 desc="Rotterdam's great art museum holds paintings from the Middle Ages to modern art, including Bosch, Bruegel, Rembrandt, Van Gogh and Dalí, as well as design.",
 history="The museum began in 1849 with a collection that Frans Boijmans, a lawyer, left to the city. Another collector, Daniël van Beuningen, donated more in the 1950s. A new building called the Depot, shaped like a huge mirrored bowl and holding the stored artworks, opened in 2021 so that visitors can see behind the scenes.",
 highlights=[("The Wayfarer","Hieronymus Bosch",1500),("Saint Christopher Carrying the Christ Child","Hieronymus Bosch",1500)])
add(slug="musee-fabre", name="Musée Fabre", wiki="Musée Fabre", city="Montpellier", country="France", continent="Europe",
 aliases=["Musée Fabre"], founded="1828",
 desc="One of the best art museums in the south of France has a big collection of 17th-century European paintings, plus works by Courbet, Delacroix and Soulages.",
 history="The painter François-Xavier Fabre, who had lived in Florence for many years, gave his collection to his home town of Montpellier in 1825. The museum opened in 1828 in an old mansion. A big renovation and extension ended in 2007.",
 highlights=[("Saint Agatha","Francisco de Zurbarán",1630)])
add(slug="lyon-mba", name="Museum of Fine Arts of Lyon", wiki="Museum of Fine Arts of Lyon", city="Lyon", country="France", continent="Europe",
 aliases=["Museum of Fine Arts of Lyon"], founded="1801",
 desc="France's second-biggest museum of fine arts sits in an old abbey in Lyon, with a courtyard garden, and holds European paintings from the Renaissance to Picasso, as well as antiquities.",
 history="The museum was created in 1801 when the French government, after the Revolution, sent a collection of paintings to Lyon. It moved into the former Saint-Pierre Abbey, which had been built in the 1600s. Its garden courtyard is a quiet green spot in the middle of the city.",
 highlights=[("Danaë","Jacopo Tintoretto",1570)])
add(slug="walters", name="The Walters Art Museum", wiki="Walters Art Museum", city="Baltimore", country="United States", continent="North America",
 aliases=["Walters Art Museum"], founded="1934",
 desc="A free art museum in Baltimore with 36,000 objects covering 55 centuries, from ancient Egypt and Greece to medieval manuscripts and Impressionist paintings.",
 history="Henry Walters inherited a collection from his father, a railroad and banking tycoon, and added to it. When he died in 1931 he left it to the city of Baltimore, and the museum opened in 1934. It is free to enter.",
 highlights=[])
