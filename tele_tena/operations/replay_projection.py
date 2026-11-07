"""Strict rrweb projection. No arbitrary attributes, CSS, URL or displayed text.
Owned static CSS is injected separately after validation. Never serialize a raw event.
"""
import re
TAGS = set('html head body div span section article main header footer nav h1 h2 h3 h4 h5 h6 p a button label input textarea select option ul ol li table thead tbody tr th td strong em small br hr dialog title form fieldset legend details summary dl dt dd aside output progress meter'.split())
NUMBERS = {'width','height','rows','cols','rr_width','rr_height'}
STYLE = {'width','height','min-width','max-width','min-height','max-height','padding','margin','gap','top','left','right','bottom','display','position','flex','flex-direction','grid-template-columns','grid-template-rows','overflow','transform','opacity','border-radius','background-color','color'}
STYLE_WORDS=set('none auto block inline inline-block contents flex grid absolute relative fixed sticky row column wrap hidden visible scroll inherit initial unset transparent currentcolor black white center px rem em vh vw vmin vmax svh dvh fr deg translate translateX translateY translate3d scale rotate calc minmax repeat min max clamp rgb rgba hsl hsla'.split())
def style_value(value):
    stripped=re.sub(r'#[0-9a-fA-F]{3,8}', '', value)
    return all(word in STYLE_WORDS for word in re.findall('[A-Za-z-]+',stripped))
class ProjectionError(ValueError): pass

def mask(value):
    return re.sub(r'\S','*',str(value or ''))[:500]

def attributes(raw, classes):
    out = {}
    if not isinstance(raw, dict): return out
    for name, value in raw.items():
        if name == 'class' and isinstance(value,str):
            out['class'] = ' '.join(x for x in value.split()[:60] if x in classes)
        elif name in NUMBERS and re.fullmatch(r'\d{1,5}(?:px)?',str(value)):
            out[name] = str(value)
        elif name == 'open': out['open'] = ''
        elif name == 'type' and value in ('button','checkbox','radio','range','text','email','tel','password','number','date'):
            out[name] = value
        elif name == 'style' and isinstance(value,str):
            parts=[]
            for item in value.split(';')[:40]:
                key,_,v=item.partition(':');key=key.strip();v=v.strip()
                if key in STYLE and len(v)<150 and re.fullmatch(r'[a-zA-Z0-9#.%(), +\-]*',v) and not re.search(r'url|image|expression|var|attr',v,re.I) and style_value(v):parts.append(key+':'+v)
            if parts: out[name]=';'.join(parts)
    return out

def node(raw, classes, budget, depth=0):
    budget[0]+=1
    if depth>100 or budget[0]>12000 or not isinstance(raw,dict) or type(raw.get('id')) is not int:raise ProjectionError('node_limit_or_format')
    out={'id':raw['id'],'type':raw.get('type')}
    if out['type'] in (3,4):out['textContent']=mask(raw.get('textContent'))
    elif out['type'] in (1,5):pass
    elif out['type'] in (0,2):
        if out['type']==2:
            tag=str(raw.get('tagName','')).lower()
            if tag not in TAGS:
                out.update(tagName='div',attributes={},childNodes=[])
                return out
            out.update(tagName=tag,attributes=attributes(raw.get('attributes'),classes))
        children=raw.get('childNodes',[])
        if not isinstance(children,list):raise ProjectionError('node_children_invalid')
        out['childNodes']=[node(x,classes,budget,depth+1) for x in children]
    else:raise ProjectionError('node_version_unsupported')
    return out

def project(event, classes, route='/unknown'):
    if not isinstance(event,dict) or type(event.get('timestamp')) not in (int,float):raise ProjectionError('event_format_invalid')
    out={'type':event.get('type'),'timestamp':event['timestamp']};d=event.get('data') or {};budget=[0]
    if not isinstance(d,dict):raise ProjectionError('event_data_invalid')
    def num(value):
        if type(value) not in (int,float) or not -100000<=value<=100000:raise ProjectionError('layout_value_invalid')
        return value
    if out['type'] in (0,1):out['data']={}
    elif out['type']==5:out['data']={'tag':'teletena-checkpoint','payload':{}}
    elif out['type']==4:out['data']={'href':'https://replay.invalid'+route,'width':num(d.get('width',0)),'height':num(d.get('height',0))}
    elif out['type']==2:out['data']={'node':node(d.get('node'),classes,budget),'initialOffset':{'left':0,'top':0}}
    elif out['type']==3:
        source=d.get('source');data={'source':source}
        if source==0:
            for key in ('adds','removes','texts','attributes'):
                values=d.get(key,[])
                if not isinstance(values,list) or len(values)>12000:raise ProjectionError('mutation_limit')
                result=[]
                for x in values:
                    if not isinstance(x,dict):raise ProjectionError('mutation_invalid')
                    item={k:num(x[k]) for k in ('id','parentId','nextId','previousId') if k in x and x[k] is not None}
                    if key=='adds':item['node']=node(x.get('node'),classes,budget)
                    elif key=='texts':item['value']=mask(x.get('value'))
                    elif key=='attributes':item['attributes']=attributes(x.get('attributes'),classes)
                    result.append(item)
                data[key]=result
        elif source in (1,6):
            positions=d.get('positions',[])
            if not isinstance(positions,list) or len(positions)>500:raise ProjectionError('positions_limit')
            data['positions']=[{k:num(x[k]) for k in ('x','y','id','timeOffset') if k in x} for x in positions]
        elif source in (2,3,4):data.update({k:num(d[k]) for k in ('id','type','x','y','width','height') if k in d})
        elif source==5:data.update(id=num(d.get('id',0)),text=mask(d.get('text')),isChecked=False)
        else:raise ProjectionError('interaction_unverified')
        out['data']=data
    else:raise ProjectionError('event_unverified')
    return out
