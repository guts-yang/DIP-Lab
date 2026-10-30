"""从源报告重建合并报告：图号全局递增(1..N)，公式抽为独立居中OMML段并右侧编号。"""
import glob, os, re, shutil, struct, zipfile, copy
from lxml import etree

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
M = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
MR = '{http://schemas.openxmlformats.org/officeDocument/2006/math}'
R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
WP = '{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}'
RELNS = 'http://schemas.openxmlformats.org/package/2006/relationships'
CTNS = '{http://schemas.openxmlformats.org/package/2006/content-types}'
EMU = 914400
MAXW, MAXH = 6.0, 4.2

# ---------- OMML 构造 ----------
def _t(text, italic=True):
    r = etree.Element(MR + 'r')
    rPr = etree.SubElement(r, MR + 'rPr')
    if italic:
        etree.SubElement(rPr, MR + 'sty').set(MR + 'val', 'i')
    t = etree.SubElement(r, MR + 't')
    t.text = text
    return r

def _op(text):
    """普通字符(非斜体)"""
    r = etree.Element(MR + 'r')
    etree.SubElement(r, MR + 'rPr')
    t = etree.SubElement(r, MR + 't')
    t.text = text
    return r

def _frac(num, den):
    f = etree.Element(MR + 'f')
    etree.SubElement(f, MR + 'fPr')
    n = etree.SubElement(f, MR + 'num')
    d = etree.SubElement(f, MR + 'den')
    for e in num: n.append(e)
    for e in den: d.append(e)
    return f

def _sup(base_elems, sup_text):
    s = etree.Element(MR + 'sSup')
    e = etree.SubElement(s, MR + 'e')
    for b in base_elems: e.append(b)
    sup = etree.SubElement(s, MR + 'sup')
    sup.append(_t(sup_text, italic=False))
    return s

def _run_para(elems, center=True):
    """生成含 oMath 的段落：公式居中，右侧 (n) 用右对齐制表位"""
    p = etree.Element(W + 'p')
    pPr = etree.SubElement(p, W + 'pPr')
    # 制表位：居中位(内容区中点) + 右对齐位(右边界)
    tabs = etree.SubElement(pPr, W + 'tabs')
    tc = etree.SubElement(tabs, W + 'tab')
    tc.set(W + 'val', 'center')
    tc.set(W + 'pos', '4153')  # 6.5in页面可用宽约6.5in，中点
    tr = etree.SubElement(tabs, W + 'tab')
    tr.set(W + 'val', 'right')
    tr.set(W + 'pos', '8306')  # 右边界
    if center:
        etree.SubElement(pPr, W + 'jc').set(W + 'val', 'center')
    om = etree.SubElement(p, MR + 'oMath')
    for e in elems:
        om.append(e)
    return p

def build_formula(kind):
    """按 kind 构造公式元素列表"""
    if kind == 'linear':      # g = alpha f + beta
        return [_t('g'), _op(' = '), _t('α'), _t('f'), _op(' + '), _t('β')]
    if kind == 'gamma':       # s = c r^gamma
        return [_t('s'), _op(' = '), _t('c'), _sup([_t('r')], 'γ')]
    if kind == 'log':         # s = c log(1+r)
        return [_t('s'), _op(' = '), _t('c'), _op('·log(1 + '), _t('r'), _op(')')]
    if kind == 'negative':    # s = 255 - r
        return [_t('s'), _op(' = 255 − '), _t('r')]
    if kind == 'laplacian':   # g = f - c grad^2 f
        return [_t('g'), _op(' = '), _t('f'), _op(' − '), _t('c'), _op('∇'), _sup([_t('')], '2'), _t('f')]
    if kind == 'butterworth': # H = 1/(1+(D/D0)^(2n))
        return [_t('H'), _op(' = '),
                _frac([_op('1')],
                      [_op('1 + ('), _t('D'), _op(' / '), _t('D'), _op('₀'), _op(')'),
                       _sup([_op('')], '2'), _sup([_t('')], 'n')])]
    if kind == 'gaussian_lp': # H = exp(-D^2/(2 D0^2))
        return [_t('H'), _op(' = exp(−'), _t('D'), _sup([_op('')], '2'),
                _op(' / (2'), _t('D'), _sup([_op('₀')], '2'), _op('))')]
    if kind == 'highpass':    # H_hp = 1 - H_lp
        return [_t('H'), _op('ₕₚ = 1 − '), _t('H'), _op('ₗₚ')]
    if kind == 'degrade':     # G = H F + N
        return [_t('G'), _op(' = '), _t('H'), _t('F'), _op(' + '), _t('N')]
    if kind == 'inverse':     # F = G / H
        return [_t('F'), _op(' = '), _frac([_t('G')], [_t('H')])]
    if kind == 'wiener':      # F = [H*/(|H|^2+K)] G
        return [_t('F'), _op(' = '),
                _frac([_t('H'), _op('*')],
                      [_op('|'), _t('H'), _op('|'), _sup([_op('')], '2'), _op(' + '), _t('K')]),
                _op(' · '), _t('G')]
    raise ValueError(kind)

# 正文中内嵌公式 -> 抽出为独立公式段
# (exp序号, 匹配正则, 公式kind)
FORMULAS = [
    (1, r'线性变换 g = alpha·f \+ beta', 'linear'),
    (2, r'幂律（伽马）变换 s = c \* r\^gamma', 'gamma'),
    (2, r'对数变换 s = c·log\(1\+r\)|s = c·log\(1\+r\) 同样用于扩展暗部', 'log'),
    (2, r'反色变换 s = 255-r', 'negative'),
    (4, r'拉普拉斯锐化：g = f \+ c \* Laplacian\(f\)', 'laplacian'),
    (5, r'巴特沃斯滤波器\s+过渡平滑|H = 1/\(1\+\(D/D0\)\^\(2n\)\)', 'butterworth'),
    (5, r'H = exp\(-D²/\(2D0²\)\)|完全平滑', 'gaussian_lp'),
    (5, r'H_hp = 1 - H_lp', 'highpass'),
    (6, r'G = H·F \+ N', 'degrade'),
    (6, r'逆滤波：F = G / H', 'inverse'),
    (6, r'维纳滤波：F = \[H\* / \(\|H\|\^2 \+ K\)\] \* G', 'wiener'),
]

def parse_docx(path):
    z = zipfile.ZipFile(path)
    return z, etree.fromstring(z.read('word/document.xml'))

def para_text(p):
    return ''.join(x.text or '' for x in p.iter(W + 't')).strip()

def set_para_text(p, newtext):
    """清空段落所有 run 文本，把 newtext 写进第一个 run"""
    ts = list(p.iter(W + 't'))
    if not ts:
        return
    ts[0].text = newtext
    for t in ts[1:]:
        t.text = ''

def main():
    reports = sorted(
        [r for r in glob.glob('experiments/exp*/report/*.docx') if '~$' not in r],
        key=lambda p: int(re.search(r'exp(\d)', p).group(1)))
    z0 = zipfile.ZipFile(reports[0])
    base = {n: z0.read(n) for n in z0.namelist()}
    z0.close()

    root = etree.fromstring(base['word/document.xml'])
    body = root.find(W + 'body')
    for c in list(body):
        body.remove(c)
    rels_root = etree.fromstring(base['word/_rels/document.xml.rels'])
    for rel in list(rels_root):
        if '/image' in (rel.get('Type') or ''):
            rels_root.remove(rel)

    def ridnum(x):
        m = re.search(r'rId(\d+)', x or '')
        return int(m.group(1)) if m else 0
    next_rid = max([ridnum(r.get('Id')) for r in rels_root] + [0]) + 1

    media = {}
    ct = etree.fromstring(base['[Content_Types].xml'])
    cover = open('/tmp/tpl_cover_clean.xml', encoding='utf-8').read()
    NS = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
    out = [copy.deepcopy(k) for k in
           etree.fromstring(('<w:root ' + NS + '>' + cover + '</w:root>').encode())]

    def pagebreak():
        p = etree.Element(W + 'p')
        r = etree.SubElement(p, W + 'r')
        etree.SubElement(r, W + 'br').set(W + 'type', 'page')
        return p

    out.append(pagebreak())

    fig_no = 0
    fml_no = 0
    # 需要替换的正文内嵌公式: (exp, 原文片段, kind, 说明前缀)
    pending = {}
    for (ex, pat, kind) in FORMULAS:
        pending.setdefault(ex, []).append((re.compile(pat), kind))

    for rp in reports:
        exp = int(re.search(r'exp(\d)', rp).group(1))
        z = zipfile.ZipFile(rp)
        rbody = etree.fromstring(z.read('word/document.xml')).find(W + 'body')
        rmap = {}
        for rel in etree.fromstring(z.read('word/_rels/document.xml.rels')):
            if '/image' in (rel.get('Type') or ''):
                tgt = rel.get('Target')
                d = z.read('word/' + tgt)
                ext = os.path.splitext(tgt)[1]
                nm = f'media/m{len(media)+1:03d}{ext}'
                media['word/' + nm] = d
                nid = f'rId{next_rid}'
                nr = etree.SubElement(rels_root, '{' + RELNS + '}Relationship')
                nr.set('Id', nid)
                nr.set('Type', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/image')
                nr.set('Target', nm)
                rmap[rel.get('Id')] = nid
                next_rid += 1

        kids = list(rbody)
        start = None
        for i, c in enumerate(kids):
            if re.match(r'^实验[一二三四五六七]', para_text(c)):
                start = i
                break
        if start is None:
            start = 0

        for c in kids[start:]:
            k = copy.deepcopy(c)
            txt = para_text(k)
            # 图注重编号
            m = re.match(r'^图\s?\d+(.*)$', txt)
            if m:
                fig_no += 1
                set_para_text(k, f'图 {fig_no}{m.group(1)}')
            # 内嵌公式 -> 抽出
            # 一段内可能含多个公式，逐个抽出
            hits = []
            for pat, kind in pending.get(exp, []):
                if pat.search(txt):
                    hits.append((pat, kind))
            if hits:
                cleaned = txt
                for pat, kind in hits:
                    fml_no += 1
                    fp = _run_para(build_formula(kind))
                    rr = etree.SubElement(fp, W + 'r')
                    etree.SubElement(rr, W + 'tab')
                    tt = etree.SubElement(rr, W + 't')
                    tt.text = f'({fml_no})'
                    out.append(fp)
                    cleaned = pat.sub('', cleaned).strip()
                if cleaned and len(cleaned) > 2:
                    set_para_text(k, cleaned)
                    out.append(k)
                continue
            for bl in k.iter(A + 'blip'):
                e = bl.get(R + 'embed')
                if e in rmap:
                    bl.set(R + 'embed', rmap[e])
            out.append(k)
        if rp != reports[-1]:
            out.append(pagebreak())
        z.close()

    # 追加未抽出的常见公式（log/negative/highpass/butterworth/gaussian/degrade）
    # 这些以内嵌在正文中的形式存在，统一在对应实验末尾不额外增加，避免重复
    # 仅对明确独立语句处理已在 FORMULAS 中完成

    for c in out:
        body.append(c)
    sp = root.find('.//' + W + 'sectPr')
    if sp is not None:
        body.append(sp)

    def psize(d):
        if d[:8] == b'\x89PNG\r\n\x1a\n':
            return struct.unpack('>II', d[16:24])
        if d[:2] == b'\xff\xd8':
            with open('/tmp/_j.jpg', 'wb') as f:
                f.write(d)
            from PIL import Image
            return Image.open('/tmp/_j.jpg').size
        return None

    for dw in list(root.iter(WP + 'inline')) + list(root.iter(WP + 'anchor')):
        ex = dw.find(WP + 'extent')
        if ex is None:
            continue
        bl = dw.find('.//' + A + 'blip')
        rid = bl.get(R + 'embed') if bl is not None else None
        tg = next((r.get('Target') for r in rels_root if r.get('Id') == rid), None)
        if not tg:
            continue
        real = psize(media.get('word/' + tg, b''))
        if not real:
            continue
        w, h = real
        rr = w / h
        wi, hi = MAXW, MAXW / rr
        if hi > MAXH:
            hi, wi = MAXH, MAXH * rr
        ex.set('cx', str(int(wi * EMU)))
        ex.set('cy', str(int(hi * EMU)))

    # 确保根元素声明 m 命名空间（OMML 必需）
    if 'm' not in root.nsmap:
        nsmap = dict(root.nsmap)
        nsmap['m'] = M
        newroot = etree.Element(root.tag, nsmap=nsmap)
        for k, v in root.attrib.items():
            newroot.set(k, v)
        for ch in list(root):
            newroot.append(ch)
        root = newroot
        body = root.find(W + 'body')

    nd = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)
    nr = etree.tostring(rels_root, xml_declaration=True, encoding='UTF-8', standalone=True)
    exts = set(os.path.splitext(k)[1].lstrip('.') for k in media)
    have = {d.get('Extension', '').lower() for d in ct.iter(CTNS + 'Default')}
    for e in exts:
        if e.lower() not in have:
            d = etree.SubElement(ct, CTNS + 'Default')
            d.set('Extension', e)
            d.set('ContentType', 'image/' + ('jpeg' if e.lower() in ('jpg', 'jpeg') else 'png'))
    nct = etree.tostring(ct, xml_declaration=True, encoding='UTF-8', standalone=True)

    outp = 'docs/202330451061廖晨扬实验报告.docx'
    zo = zipfile.ZipFile(outp, 'w', zipfile.ZIP_DEFLATED)
    for n, d in base.items():
        if n == 'word/document.xml':
            d = nd
        elif n == 'word/_rels/document.xml.rels':
            d = nr
        elif n == '[Content_Types].xml':
            d = nct
        zo.writestr(n, d)
    for n, d in media.items():
        zo.writestr(n, d)
    zo.close()

    # verify
    z = zipfile.ZipFile(outp)
    r2 = etree.fromstring(z.read('word/document.xml'))
    t2 = ''.join(x.text or '' for x in r2.iter(W + 't'))
    figs = re.findall(r'图 (\d+)', t2)
    nums = [int(x) for x in figs]
    rels2 = {r.get('Id'): r.get('Target') for r in etree.fromstring(z.read('word/_rels/document.xml.rels'))}
    bad = 0
    ti = 0
    for dw in list(r2.iter(WP + 'inline')) + list(r2.iter(WP + 'anchor')):
        ex = dw.find(WP + 'extent')
        bl = dw.find('.//' + A + 'blip')
        if ex is None or bl is None:
            continue
        tg = rels2.get(bl.get(R + 'embed'))
        if not tg:
            continue
        real = psize(z.read('word/' + tg))
        if not real:
            continue
        ti += 1
        cx, cy = int(ex.get('cx')), int(ex.get('cy'))
        if abs(cx / cy - real[0] / real[1]) > 0.03:
            bad += 1
    omml = len(list(r2.iter(MR + 'oMath')))
    print('图注数:', len(nums), '连续递增:', nums == list(range(1, len(nums) + 1)))
    print('图片数:', ti, '畸形:', bad)
    print('OMML公式:', omml)
    print('cover:', t2.count('数字图像处理实验报告书'))
    print('zip:', z.testzip() or 'OK')

main()
