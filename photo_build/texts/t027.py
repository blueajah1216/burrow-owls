import json
R = [
[1312,6,0,2016,"A Bee Hummingbird","The bee hummingbird, which lives only in Cuba, is the smallest bird in the world, about 5 centimeters long and weighing around two grams. Its wings beat so fast they blur.","How do you think such a tiny bird finds enough food?"],
[1315,7,0,2016,"Farewell Rosetta","This image of a comet shows the rubbery-looking nucleus of Comet 67P, which the European Space Agency's Rosetta spacecraft studied for two years. On September 30, 2016, Rosetta landed softly on the comet to end its mission.","What does a comet look like up close compared with the pictures of faraway ones?"],
[1320,7,0,2017,"Total Solar Eclipse, 2017","On August 21, 2017, the Moon covered the Sun across the United States. Just as totality ends, a bright spot of sunlight peeks through valleys on the Moon's edge, called the diamond ring effect. NASA photographer Carla Thomas captured it.","Why are special glasses needed to look at a partial eclipse?"],
[1323,7,0,2017,"A Major Solar Flare","NASA's Solar Dynamics Observatory watches the Sun all day and night in many colors of ultraviolet light. Here it shows a big solar flare, a sudden burst of energy that can affect satellites and power grids.","How is the Sun different from what we see in the sky?"],
[1324,7,0,2018,"Hurricane Florence from the Space Station","Astronauts aboard the International Space Station photographed Hurricane Florence in September 2018 as it grew over the Atlantic. The huge storm has an open eye in the middle, with towering clouds spiraling around.","How big do you think a hurricane is compared with a country?"],
[1335,7,0,1871,"Mental Distress","Oscar Rejlander photographed a crying child for Charles Darwin's book about emotions. Darwin wanted to show that people everywhere show feelings in the same ways, and photographs helped him prove it.","What does your face do when you feel sad?"],
[1336,1,0,2019,"The Bamboo Forest at Arashiyama","Tall green bamboo stalks fill a path in the Arashiyama forest, near Kyoto in Japan. Some bamboo can grow up to a meter in a single day.","What sound do you think the stalks make in the wind?"],
[1341,6,0,2021,"A Golden Eagle in the Alps","A golden eagle soars in front of the snowy Alps. Golden eagles are among the largest birds of prey, with a wingspan of up to about two meters, and they can spot small animals from far away.","How far do you think an eagle can see?"],
[1343,6,0,2021,"A Marmot in the Swiss Alps","A wild alpine marmot sits in the grass in the mountains, watching. Marmots whistle to warn each other of danger and sleep through the winter in deep burrows.","What would you whistle to warn a friend?"],
]
json.dump({"rows": R, "range": [1296, 1344]}, open("t027.json", "w"), ensure_ascii=False)
print(len(R))
