"""Build the profile's static SVG artwork. Python 3 + fonttools; no raster assets.

Display alphabet: original cut-corner lettering on a 60 x 84 unit grid.
Small labels: bundled IBM Plex Mono (OFL), converted to paths for GitHub.
"""
from pathlib import Path
from html import escape
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

ROOT = Path(__file__).resolve().parents[1]
BG, FG, RED, LINE, GOLD = '#14201C', '#F2F0E6', '#F46B5B', '#65786B', '#D5B477'
FONT = TTFont(ROOT / 'tools/fonts/IBMPlexMono-Regular.ttf')
GLYPHS = FONT.getGlyphSet()
CMAP = FONT.getBestCmap()
UPM = FONT['head'].unitsPerEm

# Each counter is a second subpath, using evenodd fill. No font substitution.
ABC = {
'A': 'M0 84V16L16 0H44L60 16V84H42V54H18V84ZM18 18V38H42V18Z',
'B': 'M0 0H44L60 16V34L51 42L60 50V68L44 84H0ZM18 17V34H42V17ZM18 50V67H42V50Z',
'C': 'M60 0V18H18V66H60V84H16L0 68V16L16 0Z',
'D': 'M0 0H42L60 18V66L42 84H0ZM18 18V66H38L42 62V22L38 18Z',
'E': 'M0 0H60V18H18V33H50V51H18V66H60V84H0Z',
'G': 'M60 0V18H18V66H42V51H31V34H60V68L44 84H16L0 68V16L16 0Z',
'H': 'M0 0H18V32H42V0H60V84H42V51H18V84H0Z',
'I': 'M0 0H30V18H24V66H30V84H0V66H6V18H0Z',
'L': 'M0 0H18V66H60V84H0Z',
'N': 'M0 84V0H18L42 45V0H60V84H42L18 39V84Z',
'O': 'M16 0H44L60 16V68L44 84H16L0 68V16ZM18 18V66H42V18Z',
'P': 'M0 84V0H44L60 16V40L44 56H18V84ZM18 18V38H42V18Z',
'R': 'M0 84V0H44L60 16V40L46 54L63 84H42L27 56H18V84ZM18 18V38H42V18Z',
'S': 'M60 0V18H18V32H44L60 48V68L44 84H0V66H42V50H16L0 34V16L16 0Z',
'T': 'M0 0H60V18H39V84H21V18H0Z',
'W': 'M0 0H17V63L21 67L27 61V0H43V61L49 67L53 63V0H70V68L54 84H44L35 75L26 84H16L0 68Z',
'&': 'M15 0H43L55 12V29L43 41L47 47L55 38H72L58 60L76 84H54L46 74L35 84H14L0 70V53L15 38L4 25V11ZM22 15V23L29 30L38 22V15ZM20 53L16 57V65L21 69H29L36 63L27 52Z',
}
WIDTHS = {'I':30, 'W':70, '&':76, 'R':63}

def label(s, x, y, size=16, color=FG, tracking=0, anchor='start'):
    scale = size / UPM
    advances = [(FONT['hmtx'][CMAP[ord(c)]][0]*scale + tracking) for c in s]
    width = sum(advances) - (tracking if s else 0)
    if anchor == 'end': x -= width
    if anchor == 'middle': x -= width/2
    paths = []
    for c, advance in zip(s, advances):
        pen = SVGPathPen(GLYPHS)
        GLYPHS[CMAP[ord(c)]].draw(pen)
        if pen.getCommands():
            paths.append(f'<path transform="translate({x:.3f} {y}) scale({scale:.6f} {-scale:.6f})" d="{pen.getCommands()}"/>')
        x += advance
    return f'<g fill="{color}" aria-label="{escape(s)}">'+''.join(paths)+'</g>'

def display(s, x, y, width, height, accent=False):
    units = sum(32 if c == ' ' else WIDTHS.get(c,60)+6 for c in s)-6
    paths, offset = [], 0
    for i,c in enumerate(s):
        if c != ' ':
            color = RED if accent and c == '&' else FG
            paths.append(f'<path transform="translate({offset} 0)" fill="{color}" d="{ABC[c]}"/>')
        offset += 32 if c == ' ' else WIDTHS.get(c,60)+6
    return f'<g aria-label="{escape(s)}" fill-rule="evenodd" transform="translate({x} {y}) scale({width/units:.6f} {height/84:.6f})">'+''.join(paths)+'</g>'

def path(d, stroke=LINE, sw=1, fill='none', extra=''):
    return f'<path d="{d}" stroke="{stroke}" stroke-width="{sw}" fill="{fill}" {extra}/>'

def rect(x,y,w,h,fill,extra=''):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" {extra}/>'

def pixel(x,y,unit=6,seq=((0,0),(1,0),(0,1),(2,1)),color=RED):
    return ''.join(rect(x+a*unit,y+b*unit,unit-1,unit-1,color) for a,b in seq)

def dot(x,y,r=3):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{GOLD}"/>'

def mos(x,y,name):
    # N-channel enhancement MOSFET. D=(x,y), S=(x,y+72), gate left.
    # Broken channel, insulated gate, body tied to source, body arrow inward.
    # Explicit intrinsic diode: anode at S (bottom), cathode at D (top).
    p = path(f'M{x} {y}v16h-17 M{x} {y+56}h-17 M{x} {y+56}v16 '
             f'M{x-17} {y+12}v12 m0 6v12 m0 6v12 '
             f'M{x-25} {y+14}v44 M{x-43} {y+48}h18 '
             f'M{x-17} {y+36}h17v20 '
             f'M{x} {y+16}h22v15 M{x+22} {y+43}v13h-22 '
             f'M{x+14} {y+31}h16 M{x+14} {y+43}l8-12 8 12Z', GOLD, 1.7)
    p += path(f'M{x-8} {y+32}l-7 4 7 4Z',GOLD,1,GOLD)
    p += label(name,x-44,y+5,15)
    return p

def circuit(x,y,scale=1):
    # Diagram coordinates: two independent positive rails; common return only.
    s=path('M0 16L16 0H444L460 16V328L444 344H16L0 328Z',LINE,1.4)
    s+=rect(1,1,458,38,BG)+path('M1 39H459')
    s+=label('FIG.01 / FSBB',16,26,15)+label('BIDIR',441,26,13,GOLD,anchor='end')
    s+=rect(16,52,428,258,'url(#grid)')
    s+=label('VSC / PORT A',20,76,13,RED)+label('DC BUS / PORT B',440,76,13,RED,anchor='end')
    s+=path('M24 94H130V108 M330 108V94H436 M130 180V202 M330 180V202 M130 274V288 M330 274V288 M24 288H436',GOLD,2)
    s+=mos(130,108,'Q1')+mos(130,202,'Q2')+mos(330,108,'Q3')+mos(330,202,'Q4')
    # L between midpoint nodes at (130,191) and (330,191).
    s+=path('M130 191H188 M272 191H330',GOLD,2)
    s+=path('M188 191a10.5 10.5 0 0 1 21 0a10.5 10.5 0 0 1 21 0a10.5 10.5 0 0 1 21 0a10.5 10.5 0 0 1 21 0',GOLD,2.4)
    s+=label('L',230,169,18,RED,anchor='middle')
    # Port capacitors in parallel with each respective DC rail, never bridging rails.
    for cx in (44,416):
        s+=path(f'M{cx} 94V182 M{cx-10} 182h20 M{cx-10} 196h20 M{cx} 196V288',GOLD,1.8)
        s+=dot(cx,94,2.6)+dot(cx,288,2.6)
    s+=label('CA',28,221,12,GOLD,anchor='middle')+label('CB',433,221,12,GOLD,anchor='middle')
    s+=label('SW_A',166,219,11,LINE)+label('SW_B',254,219,11,LINE)
    for cx,cy in ((130,191),(330,191),(130,288),(330,288)):
        s+=dot(cx,cy)
    s+=path('M230 288v12 m-12 0h24 m-8 5h-8 m3 5h2',GOLD,1.5)
    s+=label('COMMON RETURN',20,326,11,LINE)+label('TOPOLOGY STUDY',440,326,11,LINE,anchor='end')
    return f'<g id="fsbb" transform="translate({x} {y}) scale({scale})">{s}</g>'

def svg(name,w,h,content,title,desc):
    defs=f'<defs><pattern id="grid" width="16" height="16" patternUnits="userSpaceOnUse"><path d="M16 0H0V16" fill="none" stroke="{LINE}" stroke-width="0.55" opacity="0.23"/></pattern></defs>'
    result=f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc"><title id="title">{escape(title)}</title><desc id="desc">{escape(desc)}</desc>{defs}{rect(0,0,w,h,BG)}{content}</svg>\n'
    (ROOT/'assets'/name).write_text(result,encoding='utf-8',newline='\n')

TITLE='Power Electronics & Hardware Design'
DESC='LLS144 engineering journal. Original geometric lettering. Four-switch bidirectional Buck-Boost topology: Q1/Q2 and Q3/Q4 form two half bridges, L joins their switching nodes, independent positive ports share only the return. Conceptual topology, not an as-built schematic.'

def hero(mobile=False):
    if mobile:
        w,h=600,888
        s=path('M24 20H576 M24 870H576')+pixel(26,38,10)
        s+=label('LLS144 / HARDWARE FIELD NOTES',68,52,14,FG,0.7)
        s+=rect(400,78,176,293,'url(#grid)')
        s+=display('POWER',26,96,405,105)
        s+=display('ELECTRONICS &',26,217,548,79,True)
        s+=display('HARDWARE DESIGN',26,312,548,70)
        s+=label('circuits / control / bring-up',27,415,16,FG)
        s+=circuit(30,453,540/460)
        s+=pixel(490,104,10,((0,0),(1,0),(2,0),(2,1),(2,2),(3,2),(4,2),(4,3)))
        svg('hero-narrow.svg',w,h,s,TITLE,DESC)
    else:
        w,h=1280,600
        s=path('M32 24H1248 M32 574H1248')+pixel(36,44,10)
        s+=label('LLS144 / HARDWARE FIELD NOTES',82,61,16,FG,1.5)
        s+=path('M680 55H1248')
        s+=rect(804,96,426,430,'url(#grid)')
        s+=display('POWER',36,112,560,142)
        s+=display('ELECTRONICS &',36,272,730,106,True)
        s+=display('HARDWARE DESIGN',36,396,730,92)
        s+=circuit(810,169,0.9)
        s+=label('circuits / control / bring-up',38,540,20,FG)
        s+=label('POWER STAGE / 01',1224,133,14,LINE,anchor='end')
        s+=pixel(666,126,10,((0,0),(1,0),(2,0),(2,1),(2,2),(3,2),(4,2),(4,3),(4,4),(5,4)))
        s+=path('M615 224H756 M750 218v12')
        s+=label('DESIGN. TEST. ITERATE.',1224,540,14,LINE,anchor='end')
        svg('hero.svg',w,h,s,TITLE,DESC)

def coil(x,y,n=4,r=7,vertical=False):
    d=f'M{x} {y}'
    for _ in range(n): d+=f'a{r} {r} 0 0 1 {0 if vertical else 2*r} {2*r if vertical else 0}'
    return path(d,GOLD,1.5)

def port(x,y):
    return f'<circle cx="{x}" cy="{y}" r="3" stroke="{GOLD}" stroke-width="1.4" fill="{BG}"/>'

def corner_arrow(x,y):
    return path(f'M{x} {y+10}l10-10 m-10 0h10v10',RED,1.5)

def menu_title():
    s=pixel(16,18,8,((0,0),(1,0),(1,1),(2,1),(1,2),(0,2)))
    s+=label('PROJECT SELECT',52,37,23,FG,1)
    svg('project-select.svg',300,58,s,'Project Select','Four projects. Open any cover to explore its notes.')

def supercap():
    w,h=470,274
    s=path('M18 1H469V256 M1 18V273H452',LINE,0.8)
    s+=label('01',24,65,55,RED)
    s+=label('POWER BUFFER',109,37,13,LINE,1)
    s+=label('FSBB / STM32F334',109,59,12,FG)
    s+=corner_arrow(432,25)
    s+=label('Supercapacitor',25,117,31,FG)
    s+=label('Controller',25,153,31,FG)
    s+=rect(280,174,170,82,'url(#grid)')
    # Local FSBB fragment: one inductor joins the two switching nodes.
    s+=path('M285 218H323 M379 218H433',GOLD,1.5)+coil(323,218)
    s+=port(285,218)+port(433,218)
    s+=label('SW_A',281,246,10,LINE)+label('SW_B',407,246,10,LINE)
    s+=label('L',351,193,13,GOLD,anchor='middle')
    s+=label('Charge / discharge',25,208,14,FG)
    s+=label('Board bring-up',25,230,14,LINE)
    svg('select-supercap.svg',w,h,s,'01 / Supercapacitor Controller','FSBB, STM32F334, board bring-up. Partial topology: L joins switching nodes SW_A and SW_B.')

def wireless():
    w,h=320,304
    s=rect(208,0,112,137,'url(#grid)')
    s+=label('02',22,47,30,RED)+corner_arrow(282,27)
    # A coupled-inductor fragment. Four terminals; no galvanic connection.
    s+=path('M175 29V43 M175 99V113 M229 29V43 M229 99V113',GOLD,1.5)
    s+=coil(175,43,4,7,True)+coil(229,43,4,7,True)
    s+=label('M',202,78,11,GOLD,anchor='middle')
    s+=dot(165,39,2)+dot(219,39,2)
    for x in (175,229):
        s+=port(x,29)+port(x,113)
    s+=label('TX',154,134,11,LINE)+label('RX',228,134,11,LINE)
    s+=label('Wireless',22,174,30,FG)+label('Power Transfer',22,208,29,FG)
    s+=path('M22 228H108')
    s+=label('LCC-S / S-S',22,255,15,GOLD)
    s+=label('Coils / compensation / PCB',22,281,12,LINE)
    svg('select-wireless.svg',w,h,s,'02 / Wireless Power Transfer','LCC-S and S-S resonant compensation; Tx and Rx PCB. Drawing shows a coupled-inductor fragment, not a complete compensation circuit.')

def dcdc():
    w,h=320,252
    s=label('03',22,44,29,RED)+corner_arrow(282,24)
    s+=label('Bidirectional',22,88,28,FG)+label('DC/DC',22,120,28,FG)
    s+=label('Control + sensing',22,168,14,FG)
    s+=label('STM32G474',22,192,13,LINE)
    s+=label('Initial design',22,225,11,LINE)
    # Generic ADC voltage divider fragment, without project component values.
    s+=path('M248 135v9 M248 164v16 M248 180v9 M248 209v13 M248 180h43 M238 222h20 m-16 5h12 m-8 5h4',GOLD,1.3)
    s+=rect(243,144,10,20,BG,f'stroke="{GOLD}" stroke-width="1.3"')
    s+=rect(243,189,10,20,BG,f'stroke="{GOLD}" stroke-width="1.3"')
    s+=dot(248,180,2)+port(248,135)+port(291,180)
    s+=label('ADC',278,165,10,GOLD)
    svg('select-dcdc.svg',w,h,s,'03 / Bidirectional DC/DC','STM32G474. Control and sensing circuit design. Generic ADC voltage-divider fragment, not a claimed as-built circuit.')

def solar():
    w,h=470,282
    s=rect(0,0,160,282,'url(#grid)')
    s+=label('04',26,54,39,RED)+corner_arrow(432,26)
    # PV panel pictogram, not a circuit or measured curve.
    s+=path('M26 92H142L130 176H14Z',GOLD,1.4)
    s+=path('M23 113H139 M20 134H136 M17 155H133 M55 92L43 176 M84 92L72 176 M113 92L101 176 M72 176v23 m-25 0h50',GOLD,1)
    s+=label('PV',76,224,13,LINE,anchor='middle')
    s+=label('Solar MPPT',181,107,31,FG)
    s+=label('LT8705 / CVT',182,143,16,GOLD)
    s+=path('M182 168H439')
    s+=label('From sunlight',182,200,17,FG)+label('to storage.',182,225,17,FG)
    svg('select-solar.svg',w,h,s,'04 / Solar MPPT','LT8705 four-switch Buck-Boost with CVT. Storage and output tests. PV panel is a pictogram, not a waveform or schematic.')

def savepoint():
    s=path('M12 13H348',LINE,0.7)
    s+=pixel(21,36,8,((0,0),(1,0),(2,0),(2,1),(2,2),(3,2),(4,2),(5,2),(5,1),(5,0),(6,0),(7,0)))
    s+=rect(102,36,7,7,FG)
    s+=label('SAVE POINT',150,49,21,FG)
    s+=label('OFF DUTY / CONTINUE LATER',150,73,11,LINE)
    svg('save-point.svg',360,96,s,'Save point / Off duty','A small original pixel trail. Space reserved for future personal easter eggs.')

if __name__ == '__main__':
    hero(); hero(True)
    svg('fsbb.svg',920,688,circuit(0,0,2),'FIG.01 / FSBB',DESC)
    menu_title(); supercap(); wireless(); dcdc(); solar(); savepoint()
    print('Built 9 SVG assets. Original title alphabet and FSBB geometry retained.')
