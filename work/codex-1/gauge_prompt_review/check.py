"""Compare pinned GAUGE slope and turntable prompts; no video access."""
import hashlib, json, urllib.parse, urllib.request
REV = '9e0acb70fecc0d4161660264d9a4b08d8f56d45a'
base = f'https://huggingface.co/datasets/InternRobotics/GAUGE-Dataset/resolve/{REV}/'
files = {}
for scene in ('slope slider', 'turntable'):
    for material in ('plastic', 'wood', 'metal'):
        path = f'input/text prompts/{scene}/prompt({material}).txt'
        url = base + urllib.parse.quote(path, safe='/')
        with urllib.request.urlopen(url, timeout=30) as f:
            data = f.read()
        files[f'{scene}/{material}'] = {'url':url,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'contains_turntable':b'turntable' in data.lower(),'contains_plank':b'plank' in data.lower()}
pairs = {m:files[f'slope slider/{m}']['sha256']==files[f'turntable/{m}']['sha256'] for m in ('plastic','wood','metal')}
# The paper embeds prompt text inside SVG foreignObject; inspect only the labeled block.
with urllib.request.urlopen('https://arxiv.org/html/2608.05948v1', timeout=30) as f:
    paper = f.read().decode('utf-8')
start = paper.index('Slope Slider (plastic)')
end = paper.index('</foreignObject>', start)
block = paper[start:end].lower()
paper_checks = {'plank': 'plank' in block, 'turntable': 'turntable' in block,
                'friction_0_28': '0.28' in block, 'incline_30_degree': '30 degree' in block}
print(json.dumps({'revision': REV, 'same_material_equal': pairs, 'paper_slope_plastic_checks':paper_checks, 'files': files},indent=2))
