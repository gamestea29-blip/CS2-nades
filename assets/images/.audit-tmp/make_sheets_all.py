import json, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
root = Path(r'C:\Users\svato\Documents\Codex\2026-10-27\1-2-3-css-4-5\outputs\mirage-lineups')
manifest = json.loads((root / 'assets/images/audit-image-manifest.tmp.json').read_text(encoding='utf-8'))
audit_dir = root / 'assets/images/.audit-tmp'
outdir = audit_dir / 'sheets-all'
outdir.mkdir(parents=True, exist_ok=True)
font_path = Path(r'C:\Windows\Fonts\arial.ttf')
font = ImageFont.truetype(str(font_path), 13) if font_path.exists() else ImageFont.load_default()
thumb_w, thumb_h, label_h, cols, rows_per = 320, 180, 42, 4, 4
summary, bad, hashes = [], [], {}
for map_name in sorted(set(x['map'] for x in manifest['images'])):
    items = [x for x in manifest['images'] if x['map'] == map_name]
    pages = math.ceil(len(items)/(cols*rows_per))
    for page in range(pages):
        batch = items[page*cols*rows_per:(page+1)*cols*rows_per]
        sheet = Image.new('RGB', (cols*thumb_w, rows_per*(thumb_h+label_h)), '#0b1422')
        draw = ImageDraw.Draw(sheet)
        for i, item in enumerate(batch):
            x0 = (i % cols)*thumb_w
            y0 = (i // cols)*(thumb_h+label_h)
            source = Path(item['localPath']) if item.get('localPath') else audit_dir / item['remoteFile']
            try:
                im = Image.open(source).convert('RGB')
                fingerprint = __import__('hashlib').sha256(im.tobytes()).hexdigest()
                hashes.setdefault(fingerprint, []).append({'map':map_name,'card':item['card'],'source':item['src']})
                im = ImageOps.contain(im, (thumb_w, thumb_h))
                px = x0+(thumb_w-im.width)//2
                py = y0+(thumb_h-im.height)//2
                sheet.paste(im, (px, py))
                title = item.get('card','')
                alt = item.get('alt','')
                draw.text((x0+4,y0+thumb_h+2), f"{i+1+page*cols*rows_per}. {title[:43]}", fill='#e5f1ff', font=font)
                draw.text((x0+4,y0+thumb_h+21), alt[:45], fill='#82caff', font=font)
            except Exception as exc:
                draw.rectangle((x0,y0,x0+thumb_w-1,y0+thumb_h+label_h-1),fill='#531f2a')
                draw.text((x0+8,y0+10), f"BAD IMAGE: {source.name}",fill='white',font=font)
                bad.append({'map':map_name,'file':str(source),'error':str(exc)})
        sheet.save(outdir/f'review-{map_name}-{page+1:02d}.jpg', quality=90)
    summary.append({'map':map_name,'images':len(items),'sheets':pages})
duplicates=[v for v in hashes.values() if len(v)>1]
print(json.dumps({'outdir':str(outdir),'summary':summary,'decodeFailures':bad,'exactPixelDuplicateGroups':duplicates},ensure_ascii=False,indent=2))
