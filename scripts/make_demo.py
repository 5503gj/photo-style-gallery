"""Original procedural still life for the in-app demo (no external assets)."""
from pathlib import Path
from PIL import Image, ImageDraw

image = Image.new('RGB', (1000, 800), (243, 237, 224))
draw = ImageDraw.Draw(image)
draw.rectangle((0, 535, 1000, 800), fill=(211, 185, 153))
draw.polygon([(40,535),(345,535),(900,800),(620,800)],fill=(198,171,141))
draw.rounded_rectangle((70,90,360,520),radius=135,fill=(187,204,197))
draw.rectangle((70,320,360,520),fill=(187,204,197))
draw.line((215,90,215,520),fill=(236,231,217),width=10)
draw.line((70,300,360,300),fill=(236,231,217),width=10)
draw.ellipse((313,655,752,722),fill=(185,155,125))
draw.ellipse((405,375,701,700),fill=(167,91,63))
draw.rectangle((465,300,640,530),fill=(167,91,63))
draw.ellipse((465,278,640,325),fill=(193,119,83))
draw.ellipse((479,289,626,312),fill=(113,68,50))
draw.line((553,304,566,95),fill=(68,99,77),width=8)
draw.line((549,320,418,151),fill=(68,99,77),width=7)
draw.line((557,330,726,171),fill=(68,99,77),width=7)
for poly in [[(564,156),(491,104),(518,47),(570,115)],[(563,209),(633,117),(673,140),(602,219)],[(478,235),(390,203),(375,138),(438,164)],[(621,268),(698,211),(768,228),(700,269)],[(567,283),(493,247),(476,198),(542,218)]]:
 draw.polygon(poly,fill=(76,109,84))
draw.ellipse((135,587,392,731),fill=(224,216,196))
draw.ellipse((149,592,376,700),fill=(239,232,214))
draw.ellipse((256,594,354,674),fill=(214,149,67))
draw.ellipse((191,619,284,696),fill=(195,113,65))
draw.line((187,573,295,562),fill=(154,126,97),width=2)
out=Path(__file__).resolve().parents[1]/'assets/still-life.png'
image.save(out,optimize=True)
print(out.name)
