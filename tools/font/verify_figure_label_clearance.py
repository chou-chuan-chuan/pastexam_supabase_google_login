#!/usr/bin/env python3
"""Check selected native label ink boxes against vector strokes in note SVGs.

Cubic curves are sampled at 1/64 intervals; straight-segment intersections are
exact. Intended as a regression check alongside visual review, not general SVG.
"""
import argparse
import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET


def segments(path):
    tokens = re.findall(r'[MLCZ]|[-+]?(?:\d*\.)?\d+(?:[eE][-+]?\d+)?', path)
    cursor = 0
    point = start = None
    while cursor < len(tokens):
        op = tokens[cursor]; cursor += 1
        count = {'M': 2, 'L': 2, 'C': 6, 'Z': 0}[op]
        values = list(map(float, tokens[cursor:cursor+count])); cursor += count
        if op == 'M': point = start = tuple(values)
        elif op == 'L':
            end = tuple(values); yield point, end; point = end
        elif op == 'C':
            p0 = point; p1,p2,p3 = values[:2], values[2:4], values[4:]
            for step in range(1,65):
                t = step/64; u = 1-t
                end = tuple(u**3*p0[i]+3*u*u*t*p1[i]+3*u*t*t*p2[i]+t**3*p3[i] for i in (0,1))
                yield point,end; point=end
        elif op == 'Z': yield point,start; point=start


def intersects(a,b,rect):
    low,high = 0,1
    for i in (0,1):
        delta=b[i]-a[i]
        if abs(delta)<1e-12:
            if not rect[i] <= a[i] <= rect[i+2]: return False
        else:
            t0,t1=sorted(((rect[i]-a[i])/delta,(rect[i+2]-a[i])/delta))
            low,high=max(low,t0),min(high,t1)
            if low>high:return False
    return True


def verify(svg_dir, labels, page_map):
    pages={}
    for file in sorted(svg_dir.glob('page-*.svg')):
        lines=[]
        for element in ET.parse(file).getroot().iter():
            if element.tag.endswith('path') and element.get('fill')=='none':
                radius=float(element.get('stroke-width','1'))/2
                lines.extend((a,b,radius) for a,b in segments(element.attrib['d']))
        pages[int(file.stem.split('-')[-1])]=lines
    results=[]
    for label in labels:
        if not label['role']:continue
        page=page_map[label['figure']]
        dx,dy=[p-o for p,o in zip(label['position'],label['origin'])]
        def collisions(bounds):
            return sum(intersects(a,b,(bounds[0]-radius-2,bounds[1]-radius-2,bounds[2]+radius+2,bounds[3]+radius+2))
                       for a,b,radius in pages[page])
        box=label['bounds'];before=[box[0]-dx,box[1]-dy,box[2]-dx,box[3]-dy]
        results.append(dict(figure=label['figure'],role=label['role'],text=label['text'],
                            before_segments=collisions(before),after_segments=collisions(box)))
    return results


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('notes',type=Path,help='Full-lecture folder containing output/ and analysis/')
    parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    labels=json.loads((args.notes/'analysis/figure-labels.json').read_text())
    layout=json.loads((args.notes/'analysis/layout.json').read_text())
    result=verify(args.notes/'output',labels,{f['id']:f['page'] for f in layout['figures']})
    if args.report:args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    assert result, 'No adjusted labels found; did the renderer emit its label audit?'
    failures=[r for r in result if r['after_segments']]
    assert not failures,failures
    print(f'PASS: {len(result)} adjusted labels have 2 canvas units of clearance from diagram strokes')
