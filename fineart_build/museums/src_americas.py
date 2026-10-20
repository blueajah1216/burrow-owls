# Museum entries: slug, name, wiki (enwiki title), city, country, continent, aliases (gallery venue strings), founded, desc, history, highlights [(title, artist, year)]
M = []
def add(**k): M.append(k)

add(slug="met", name="The Metropolitan Museum of Art", wiki="Metropolitan Museum of Art", city="New York City", country="United States", continent="North America",
 aliases=["Metropolitan Museum of Art"], founded="1870",
 desc="The Met is the largest art museum in the Americas, with more than two million works, from ancient Egyptian temples to Van Gogh and modern design. It stands on the edge of Central Park on Fifth Avenue and welcomes millions of visitors every year.",
 history="A group of New York citizens, businessmen and artists founded the Met in 1870, after a speech in Paris in 1866 that argued America should have a great art museum of its own. It opened in a rented building in 1872 and moved to its current home in Central Park in 1880. The grand Fifth Avenue entrance was added in the early 1900s, and in 1965 the museum even rebuilt an Egyptian temple, the Temple of Dendur, inside a glass hall. Over time rich collectors donated whole collections, so today it is like several museums in one.",
 highlights=[("Washington Crossing the Delaware","Emanuel Leutze",1851),("Aristotle with a Bust of Homer","Rembrandt",1653),("Wheat Field with Cypresses","Vincent van Gogh",1889),("Madame X (Madame Pierre Gautreau)","John Singer Sargent",1884),("The Temple of Dendur","Ancient Egypt","about 15 BC")])
add(slug="moma", name="Museum of Modern Art (MoMA)", wiki="Museum of Modern Art", city="New York City", country="United States", continent="North America",
 aliases=["Museum of Modern Art"], founded="1929",
 desc="MoMA is the world's best-known museum of modern art, home to Van Gogh's Starry Night, Picasso's Les Demoiselles d'Avignon, Dalí's melting clocks and Warhol's soup cans. It covers painting, sculpture, photography, design and film from the 1880s to today.",
 history="MoMA was founded in 1929 by three women, Abby Aldrich Rockefeller, Lillie P. Bliss and Mary Quinn Sullivan, who wanted a museum for the new art that other museums ignored. It opened just nine days after the stock market crash of 1929, in a rented space in an office building. Its first director, Alfred H. Barr Jr., built a collection that included film and design as well as painting, which was new at the time. MoMA moved to its present site on West 53rd Street in 1939 and has been expanded several times since.",
 highlights=[("The Starry Night","Vincent van Gogh",1889),("Les Demoiselles d'Avignon","Pablo Picasso",1907),("The Persistence of Memory","Salvador Dalí",1931),("Water Lilies (triptych)","Claude Monet",1920),("Campbell's Soup Cans","Andy Warhol",1962)])
add(slug="guggenheim", name="Solomon R. Guggenheim Museum", wiki="Solomon R. Guggenheim Museum", city="New York City", country="United States", continent="North America",
 aliases=["Solomon R. Guggenheim Museum"], founded="1937",
 desc="A white spiral building by the architect Frank Lloyd Wright houses a world-famous collection of modern art, especially abstract painting by Kandinsky and his circle. Visitors walk up a gentle ramp that winds around a huge open space.",
 history="The collector Solomon R. Guggenheim began his foundation in 1937 to show 'non-objective' painting, art made of color and shape instead of recognizable things. His adviser, the artist Hilla Rebay, urged him to build a museum, and he hired Frank Lloyd Wright in 1943. The building took 16 years and opened in October 1959, shortly after both men had died. Its spiral shape was controversial at first and is now one of the most beloved buildings in New York.",
 highlights=[("Composition 8","Wassily Kandinsky",1923),("Woman Ironing","Pablo Picasso",1904),("Black Lines","Wassily Kandinsky",1913)])
add(slug="frick", name="The Frick Collection", wiki="Frick Collection", city="New York City", country="United States", continent="North America",
 aliases=["The Frick Collection","Frick Collection"], founded="1935",
 desc="A steel tycoon's elegant mansion on Fifth Avenue is now a small museum filled with Old Master paintings by Vermeer, Rembrandt, Holbein and Titian. Because the rooms look like a home, it feels far more personal than a big museum.",
 history="Henry Clay Frick, a Pittsburgh industrialist, built the mansion in 1913 to 1914 and filled it with art. When he died in 1919 he left it to the public, and after his widow Adelaide's death it opened as a museum in 1935. The rooms are still arranged much as the family lived in them, with paintings hung over fireplaces and among furniture. The result feels like a time capsule of Gilded Age taste.",
 highlights=[("Girl Interrupted at Her Music","Johannes Vermeer",1659),("Officer and Laughing Girl","Johannes Vermeer",1657),("Sir Thomas More","Hans Holbein the Younger",1527),("The Progress of Love","Jean-Honoré Fragonard",1771)])
add(slug="aic", name="Art Institute of Chicago", wiki="Art Institute of Chicago", city="Chicago", country="United States", continent="North America",
 aliases=["Art Institute of Chicago"], founded="1879",
 desc="Chicago's great museum, guarded by two bronze lions, holds some of the most famous paintings in America: Seurat's dotted Sunday on La Grande Jatte, Hopper's Nighthawks and Grant Wood's American Gothic. Its Impressionist collection is one of the best outside Paris.",
 history="The Art Institute started in 1879 as a school and exhibition space for artists, and its current Beaux-Arts building on Michigan Avenue opened in 1893 for the World's Columbian Exposition. Wealthy Chicagoans, like Bertha Palmer, bought French Impressionist paintings early, before they were famous, and gave them to the museum. The Modern Wing, designed by Renzo Piano, opened in 2009. The bronze lions out front have been there since 1894, and they are dressed up in team gear when Chicago teams make the playoffs.",
 highlights=[("A Sunday Afternoon on the Island of La Grande Jatte","Georges Seurat",1886),("Nighthawks","Edward Hopper",1942),("American Gothic","Grant Wood",1930),("Paris Street; Rainy Day","Gustave Caillebotte",1877),("The Bedroom","Vincent van Gogh",1889)])
add(slug="nga", name="National Gallery of Art", wiki="National Gallery of Art", city="Washington, D.C.", country="United States", continent="North America",
 aliases=["National Gallery of Art"], founded="1937",
 desc="Along the National Mall, this free museum holds the only painting by Leonardo da Vinci in the Americas, as well as great works by Vermeer, Rembrandt, Monet, Cole and many American artists. It is made up of an old marble building and a modern East Building joined by a tunnel with a moving walkway.",
 history="The National Gallery was founded by an act of Congress in 1937 after the banker and Treasury Secretary Andrew W. Mellon offered his great art collection and money for a building to the American people. The neoclassical West Building opened in 1941. Mellon wanted a national collection that was not controlled by the government of the day, and he asked that the museum not carry his name. The East Building, designed by I. M. Pei, opened in 1978. Entry is free.",
 highlights=[("Ginevra de' Benci","Leonardo da Vinci",1474),("Watson and the Shark","John Singleton Copley",1778),("The Voyage of Life","Thomas Cole",1842),("Girl with the Red Hat","Johannes Vermeer",1666),("Lucretia","Rembrandt",1664)])
add(slug="mfa-boston", name="Museum of Fine Arts, Boston", wiki="Museum of Fine Arts, Boston", city="Boston", country="United States", continent="North America",
 aliases=["Museum of Fine Arts Boston","Museum of Fine Arts, Boston"], founded="1870",
 desc="One of the largest art museums in the United States, with huge collections of Egyptian, Greek and Asian art and a famous collection of American paintings by Copley, Sargent and Homer. It also has one of the largest collections of Monet outside France.",
 history="The MFA was founded in 1870, the same year as the Met, by Boston citizens, and opened in 1876 in Copley Square. By the 1900s it had outgrown its building and moved to its current home on Huntington Avenue in 1909. It has long sent archaeologists abroad, so its Egyptian collection is one of the best outside Cairo.",
 highlights=[("The Daughters of Edward Darley Boit","John Singer Sargent",1882),("The Slave Ship","J. M. W. Turner",1840),("Paul Revere","John Singleton Copley",1768),("Where Do We Come From? What Are We? Where Are We Going?","Paul Gauguin",1897),("La Japonaise","Claude Monet",1876)])
add(slug="philadelphia", name="Philadelphia Museum of Art", wiki="Philadelphia Museum of Art", city="Philadelphia", country="United States", continent="North America",
 aliases=["Philadelphia Museum of Art"], founded="1876",
 desc="A Greek-temple-style museum at the top of a famous flight of steps, which the movie hero Rocky runs up. Inside are Van Gogh's Sunflowers, Cézanne's huge Bathers, Duchamp's Nude Descending a Staircase and a whole collection of Klee's strange, playful paintings.",
 history="The museum began in 1876 when Philadelphia held the great Centennial Exhibition for the nation's 100th birthday. The city decided to make a permanent art museum from it. The Greek-revival building on a hill at the end of the Benjamin Franklin Parkway was begun in 1919 and opened in 1928. The museum's modern collections grew with the gifts of Louise and Walter Arensberg, who had known Marcel Duchamp personally.",
 highlights=[("Sunflowers","Vincent van Gogh",1889),("The Large Bathers","Paul Cézanne",1906),("Nude Descending a Staircase, No. 2","Marcel Duchamp",1912),("Fish Magic","Paul Klee",1925)])
add(slug="getty", name="J. Paul Getty Museum (Getty Center)", wiki="J. Paul Getty Museum", city="Los Angeles", country="United States", continent="North America",
 aliases=["Getty Center","J. Paul Getty Museum"], founded="1954",
 desc="A white hilltop campus above Los Angeles holds Van Gogh's Irises, Monet, Rembrandt and a superb collection of illuminated medieval manuscripts. The gardens and the views over the city are part of the visit, and entry is free.",
 history="Oil tycoon J. Paul Getty opened a small museum in his ranch house in Malibu in 1954, then built a Roman-villa-style museum there in 1974. When he died in 1976 he left it a fortune, and the Getty Trust became one of the richest art institutions in the world. The new Getty Center, by architect Richard Meier, opened on a hilltop in Brentwood in 1997. The Malibu villa reopened in 2006 as the Getty Villa for classical antiquities.",
 highlights=[("Irises","Vincent van Gogh",1889),("Wheatstacks, Snow Effect, Morning","Claude Monet",1891),("The Abduction of Europa","Rembrandt",1632),("Portrait of a Halberdier","Pontormo",1530)])
add(slug="lacma", name="Los Angeles County Museum of Art (LACMA)", wiki="Los Angeles County Museum of Art", city="Los Angeles", country="United States", continent="North America",
 aliases=["Los Angeles County Museum of Art","LACMA"], founded="1961",
 desc="The largest art museum in the western United States, with art from all over the world and from every era. Outside its entrance is Urban Light, a forest of 202 restored antique street lamps that has become a symbol of Los Angeles.",
 history="LACMA opened in 1965 on Wilshire Boulevard in an area called Miracle Mile, after it separated from the older Los Angeles County Museum of History, Science and Art, founded in 1910. Its first collections were helped by large gifts from wealthy collectors and Hollywood figures. The museum added the Pavilion for Japanese Art, the Broad Contemporary Art Museum and the glittering Urban Light in 2008. A new building is being constructed across the street.",
 highlights=[("The Treachery of Images (This is Not a Pipe)","René Magritte",1929),("Plague in an Ancient City","Michiel Sweerts",1652),("Urban Light","Chris Burden",2008)])
add(slug="cleveland", name="Cleveland Museum of Art", wiki="Cleveland Museum of Art", city="Cleveland", country="United States", continent="North America",
 aliases=["Cleveland Museum of Art"], founded="1913",
 desc="A free museum with one of the finest collections in the Midwest, from ancient Egypt to Monet, with a very strong collection of Asian art and Old Masters. Its marble building sits beside a lagoon in University Circle.",
 history="Cleveland's industrialists left money for the museum in their wills in 1913, and the Greek-style marble building on a hill above Wade Lagoon opened in 1916. Its early directors were determined to buy only top-quality works. Admission has been free since the museum opened. In 2008 the museum began a huge rebuilding and expansion that brought a new glass atrium.",
 highlights=[("The Large Plane Trees (Road Menders at Saint-Rémy)","Vincent van Gogh",1889),("The Crucifixion of Saint Andrew","Caravaggio",1607)])
add(slug="dia", name="Detroit Institute of Arts", wiki="Detroit Institute of Arts", city="Detroit", country="United States", continent="North America",
 aliases=["Detroit Institute of Arts"], founded="1885",
 desc="The DIA is famous for Diego Rivera's huge murals about Detroit's factories, painted straight on the walls of its central court, and for a fine collection that includes Van Gogh and Bruegel.",
 history="The museum started in 1885 when Detroit citizens founded the Detroit Museum of Art, and its current Beaux-Arts building opened in 1927. In 1932 and 1933 the Mexican artist Diego Rivera spent months painting the Detroit Industry murals, a salute to the city's car workers. When the city of Detroit went bankrupt in 2013, there was a danger that the art might be sold, but donors raised money to protect it in the 'Grand Bargain'.",
 highlights=[("Detroit Industry Murals","Diego Rivera",1933),("Self-Portrait","Vincent van Gogh",1887),("The Wedding Dance","Pieter Bruegel the Elder",1566)])
add(slug="barnes", name="Barnes Foundation", wiki="Barnes Foundation", city="Philadelphia", country="United States", continent="North America",
 aliases=["Barnes Foundation"], founded="1922",
 desc="One of the world's finest collections of Impressionist and early Modern art, including nearly 180 works by Renoir, 69 by Cézanne and Matisse's big mural, hung salon-style on the walls, just as the founder arranged them.",
 history="The chemist and businessman Albert C. Barnes, who made a fortune with a medicine called Argyrol, began collecting in 1912 and founded the Barnes Foundation in 1922 as a school, not just a museum. He hung his pictures in groups with African art, furniture and metalwork to teach how to see. After his death in 1951 the collection stayed in Merion, Pennsylvania, until 2012, when it was moved to a new building in Philadelphia, which copied the arrangement of the rooms exactly.",
 highlights=[("The Joy of Life (Le bonheur de vivre)","Henri Matisse",1906),("The Card Players","Paul Cézanne",1892),("Models","Georges Seurat",1888)])

add(slug="ngc", name="National Gallery of Canada", wiki="National Gallery of Canada", city="Ottawa", country="Canada", continent="North America",
 aliases=["National Gallery of Canada"], founded="1880",
 desc="Canada's national art museum, in a glass-towered building overlooking the Ottawa River, holds the country's finest collection of Canadian art, including Tom Thomson's Jack Pine and many works by the Group of Seven, as well as European and Indigenous art. A giant spider sculpture called Maman stands outside.",
 history="The Marquess of Lorne, Canada's Governor General, started the National Gallery in 1880 as part of the founding of the Royal Canadian Academy of Arts. The collection moved many times in its first century. Its present building, by the architect Moshe Safdie, opened in 1988. In 1913 the government gave the gallery its own law, and its great purchases of the 1910s and 1920s were of early Canadian painters such as Tom Thomson and the Group of Seven.",
 highlights=[("The Jack Pine","Tom Thomson",1917),("The Death of General Wolfe","Benjamin West",1770),("Maman","Louise Bourgeois",1999)])
add(slug="ago", name="Art Gallery of Ontario", wiki="Art Gallery of Ontario", city="Toronto", country="Canada", continent="North America",
 aliases=["Art Gallery of Ontario"], founded="1900",
 desc="Toronto's art gallery has a spiral staircase and a glass front designed by Frank Gehry, a big Canadian collection including Tom Thomson's West Wind, and the world's largest public collection of Henry Moore sculptures.",
 history="It began in 1900 as the Art Museum of Toronto and became the Art Gallery of Toronto in 1919 and, in 1966, the Art Gallery of Ontario. Its first building was the Grange, an old mansion, and the gallery grew around it. In 2008 the architect Frank Gehry, who was born in Toronto, completed a big redesign. Its famous Canadian paintings came in part from Group of Seven supporters like J. S. McLean.",
 highlights=[("The West Wind","Tom Thomson",1917),("Henry Moore Sculpture Centre","Henry Moore",1974)])
add(slug="mmfa", name="Montreal Museum of Fine Arts", wiki="Montreal Museum of Fine Arts", city="Montreal", country="Canada", continent="North America",
 aliases=["Montreal Museum of Fine Arts"], founded="1860",
 desc="Canada's oldest art museum is made of several linked buildings on Sherbrooke Street in Montreal, with Canadian, European, Indigenous and decorative art, including some of the best Quebec paintings.",
 history="The Art Association of Montreal was founded in 1860, making it the oldest art museum in Canada, and it opened its first gallery building on Phillips Square in 1879. The marble Beaux-Arts building on Sherbrooke Street opened in 1912, and several pavilions have been added since. It became known for large exhibitions, and its education programs for children and for people who are ill are well known.",
 highlights=[])
add(slug="mcmichael", name="McMichael Canadian Art Collection", wiki="McMichael Canadian Art Collection", city="Kleinburg", country="Canada", continent="North America",
 aliases=["McMichael Canadian Art Collection"], founded="1966",
 desc="A log-and-stone gallery in the woods north of Toronto devoted to the Group of Seven and their circle, including a cabin shack that belonged to Tom Thomson and the graves of several of the painters.",
 history="Robert and Signe McMichael began collecting Group of Seven paintings in the 1950s and in 1966 gave their log-and-stone house and 194 paintings to the province of Ontario, so that everyone could see the art in the setting that had inspired it. The collection now holds thousands of works, including Indigenous and Inuit art. Tom Thomson's own shack was moved to the grounds in 1962.",
 highlights=[])
add(slug="vag", name="Vancouver Art Gallery", wiki="Vancouver Art Gallery", city="Vancouver", country="Canada", continent="North America",
 aliases=["Vancouver Art Gallery"], founded="1931",
 desc="British Columbia's main art museum, in a grand former courthouse in the middle of downtown Vancouver, holds the world's largest collection of work by the painter Emily Carr.",
 history="The Vancouver Art Gallery opened in 1931 in a small building and moved to the old provincial courthouse, a neoclassical building redone by the architect Arthur Erickson, in 1983. Its collection of Emily Carr's paintings of Indigenous villages and wild forests came largely through gifts. A new building has been planned for decades.",
 highlights=[("Emily Carr collection","Emily Carr",1930)])
add(slug="cwm", name="Canadian War Museum", wiki="Canadian War Museum", city="Ottawa", country="Canada", continent="North America",
 aliases=["Canadian War Museum","Beaverbrook Collection of War Art"], founded="1880",
 desc="Canada's national museum of military history holds the country's war art, including large paintings by official war artists of both World Wars. Its building by the Ottawa River is shaped like a grass-roofed bunker.",
 history="The roots of the museum go back to 1880, when a small collection of war trophies began to be gathered in Ottawa. In 1916 the newspaper owner Lord Beaverbrook started the Canadian War Memorials Fund, hiring painters including A. Y. Jackson and Frederick Varley to record the First World War, and this is the core of the art collection. The museum moved to a dramatic new building designed by Raymond Moriyama in 2005.",
 highlights=[("Gas Attack, Liévin","A. Y. Jackson",1918),("Canadian Gunners in the Mud","Alfred Bastien",1917)])
add(slug="mnbaq", name="Musée national des beaux-arts du Québec", wiki="Musée national des beaux-arts du Québec", city="Quebec City", country="Canada", continent="North America",
 aliases=["Musée national des beaux-arts du Québec"], founded="1933",
 desc="Quebec's national fine arts museum, set on the Plains of Abraham, tells the story of Quebec's art from the colonial period to today, with the largest collection of Quebec art in the world.",
 history="The museum opened in 1933 as the Musée du Québec, in a neoclassical building on the Plains of Abraham, the very battlefield of 1759. It has been expanded several times, with new pavilions in 2002 and 2016. It is known for paintings by Cornelius Krieghoff, Jean Paul Lemieux and Jean Paul Riopelle.",
 highlights=[])

add(slug="munal", name="Museo Nacional de Arte (MUNAL)", wiki="Museo Nacional de Arte", city="Mexico City", country="Mexico", continent="North America",
 aliases=["Museo Nacional de Arte"], founded="1982",
 desc="Mexico's national art museum, in a lavish palace in the old center of Mexico City, shows five centuries of Mexican art, including the glowing volcano landscapes of José María Velasco.",
 history="The museum was founded in 1982 and moved into the Palacio de Comunicaciones, a grand marble building finished in 1911 for the Mexican postal and telegraph service. The collection includes paintings from the colonial period to the early twentieth century. It's best known for landscapes of the Valley of Mexico by José María Velasco and works by Saturnino Herrán.",
 highlights=[("The Valley of Mexico","José María Velasco",1875)])
add(slug="bellas-artes-mx", name="Palacio de Bellas Artes", wiki="Palacio de Bellas Artes", city="Mexico City", country="Mexico", continent="North America",
 aliases=["Palacio de Bellas Artes"], founded="1934",
 desc="A white marble and stained glass palace in Mexico City, famous as an opera and concert hall and for huge murals by Diego Rivera, José Clemente Orozco and David Alfaro Siqueiros on its walls.",
 history="Mexico began the Palace of Fine Arts under President Porfirio Díaz in 1904, but the revolution interrupted construction and it was not opened until 1934. The building mixes Art Nouveau and Art Deco, and after the revolution the government invited the Mexican muralists to paint the walls. Rivera's Man at the Crossroads was painted for Rockefeller Center in New York, destroyed there, and repainted here in 1934.",
 highlights=[("Man, Controller of the Universe","Diego Rivera",1934)])

add(slug="mnba-argentina", name="Museo Nacional de Bellas Artes", wiki="Museo Nacional de Bellas Artes (Argentina)", city="Buenos Aires", country="Argentina", continent="South America",
 aliases=["National Museum of Fine Arts, Argentina","Museo Nacional de Bellas Artes"], founded="1895",
 desc="Argentina's national art museum, in the elegant Recoleta district of Buenos Aires, has the best collection of European art in South America as well as Argentine masters.",
 history="Founded in 1895 by the art critic Eduardo Schiaffino, it was first housed in a department store building. Its present building, once a water pumping station, was remodeled in 1933 for the museum. It holds works by Goya, Monet, Rodin and Van Gogh next to the best of Argentine painters.",
 highlights=[])
add(slug="masp", name="São Paulo Museum of Art (MASP)", wiki="São Paulo Museum of Art", city="São Paulo", country="Brazil", continent="South America",
 aliases=["São Paulo Museum of Art"], founded="1947",
 desc="MASP is the most important art museum in Brazil's biggest city, in a famous red concrete building lifted on two giant beams over an open public square. It holds the best collection of European art in the southern hemisphere.",
 history="The newspaper owner Assis Chateaubriand and the Italian art dealer Pietro Maria Bardi founded MASP in 1947 and gathered masterpieces by pressing wealthy Brazilians to donate. Its dramatic building on Paulista Avenue, designed by Lina Bo Bardi, opened in 1968. Its glass easels, which let visitors see paintings floating in the air without walls, became famous.",
 highlights=[("Van Gogh, Renoir, Rembrandt","European masters",1900)])
add(slug="mnba-brazil", name="Museu Nacional de Belas Artes", wiki="Museu Nacional de Belas Artes", city="Rio de Janeiro", country="Brazil", continent="South America",
 aliases=["Museu Nacional de Belas Artes"], founded="1937",
 desc="Brazil's national fine arts museum, in a classical building downtown, holds the best Brazilian painting of the 1800s, including big history paintings by Pedro Américo and Victor Meirelles.",
 history="The museum was formally created in 1937 from the old National School of Fine Arts, which had been set up by French artists who came to Rio in 1816, after the Portuguese court had moved to Brazil. Its home, built in 1908, is a copy of a Parisian beaux-arts palace. It is known for its Brazilian academic painting of the 1800s.",
 highlights=[("The Battle of Avaí","Pedro Américo",1877)])
add(slug="mali", name="Museo de Arte de Lima (MALI)", wiki="Museo de Arte de Lima", city="Lima", country="Peru", continent="South America",
 aliases=["Museo de Arte de Lima"], founded="1961",
 desc="Peru's main art museum shows 3,000 years of Peruvian art, from pre-Inca ceramics to colonial paintings, in a palace built for the 1872 Lima Exhibition.",
 history="The museum opened in 1961 in the Palacio de la Exposición, a stately building from the 1870s in Lima's Parque de la Exposición. Its collection runs from ancient Paracas and Nazca textiles to Peruvian modern painters. It has a famous collection of colonial religious painting from the Cusco school.",
 highlights=[])
