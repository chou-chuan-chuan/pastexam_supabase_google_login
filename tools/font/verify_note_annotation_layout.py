#!/usr/bin/env python3
"""Check inline annotation wrapping; optionally verify the production adapter."""
import sys
from pathlib import Path
from note_annotation_layout import annotation_lines

measure=lambda text:(len(text)*6,10,3)
math_measure=lambda text:(40,25,12)
lines=annotation_lines('Plain words with $a/b$, then $x_0$ and a tail.',100,measure,math_measure,6)
assert len(lines)>1
assert ''.join(content for line,*_ in lines for _,content,*_ in line)=='Plainwordswitha/b,thenx_0andatail.'
for line,width,ascent,descent in lines:
    assert width<=100
    assert all(x+w<=width+1e-9 and a<=ascent and d<=descent for _,_,x,w,a,d in line)
    if any(kind=='math' for kind,*_ in line):assert ascent==25 and descent==12
    assert line[0][1] not in (',','.')
try:annotation_lines('Unclosed $x',100,measure,math_measure,6)
except ValueError:pass
else:raise AssertionError('Unclosed math accepted')
try:annotation_lines('$wide$',20,measure,math_measure,6)
except ValueError:pass
else:raise AssertionError('Overwide math accepted')

if len(sys.argv)>1:
    import ast,re,json
    notes=Path(sys.argv[1]).resolve()
    sys.path.insert(0,str(notes))
    import vector_engine as v
    from fontTools.pens.boundsPen import BoundsPen
    from fontTools.pens.recordingPen import replayRecording
    tree=ast.parse((notes/'render_notes.py').read_text())
    annotations=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='annotation']
    assert len(annotations)==49
    samples=[(ast.literal_eval(n.args[0]),next(ast.literal_eval(k.value) for k in n.keywords if k.arg=='s'),665) for n in annotations]
    figure_notes=[k.value for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='fig' for k in n.keywords if k.arg=='note']
    assert len(figure_notes)==1
    from note_figure_layout import spectrum_note_frame
    samples.extend((ast.literal_eval(n),16,spectrum_note_frame(0,0,661)[2]) for n in figure_notes)
    bounds=[]
    def capture_text(x,y,value,size=21,ink='black',font='hand',record=True,relations=False):
        pads=v.note_layout.relation_spacing(value,size) if relations else [(0,0)]*len(value)
        for ch,(left,right) in zip(value,pads):
            x+=left
            box=v.text_hat_layouts[font].bounds(ch);scale=v.glyph_size(ch,size,font)/v.units[font]
            if box:
                if ch=='−' and relations:box=(45,306,292,354)
                a,b,c,d=box;bounds.append((x+a*scale,y-d*scale,x+c*scale,y-b*scale))
            x+=(v.note_layout.math_advance(ch,size) if relations else v.width(ch,size,font))+right
        return x
    def capture_outline(x,y,outline,ink,kind='radical'):
        pen=BoundsPen(None);replayRecording(outline,pen);a,b,c,d=pen.bounds;bounds.append((x+a,y+b,x+c,y+d))
    v.text=capture_text;v.filled_outline=capture_outline
    for source,size,max_width in samples:
        assert not re.search(r'[\u3400-\u9fff]',source)
        for prose in source.split('$')[::2]:
            assert not re.search(r'[_^αβδωΨΦℏ⟨⟩²⁻]',prose),(source,prose)
        bounds.clear();v.records.clear()
        block=v.Block(20,100,max_width,'',[]);block.annotation(source,size)
        assert bounds and v.records
        for a,b,c,d in bounds:
            assert any(a>=r['x']-1e-6 and c<=r['x']+r['w']+1e-6 and b>=r['y']-r['asc']-1e-6 and d<=r['y']+r['desc']+1e-6 for r in v.records),(source,(a,b,c,d),v.records)
        for previous,current in zip(v.records,v.records[1:]):
            assert current['y']-current['asc']>previous['y']+previous['desc']
        assert block.y>max(r['y']+r['desc'] for r in v.records)
    print('PASS: 50 English annotations (including the spectrum note); native math ink enclosed; lines separated')
print('PASS: inline annotation wrapping, math spans and attached punctuation')
