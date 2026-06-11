# -*- coding: utf-8 -*-
# 解析 APELSO 2026 議程：官網 markdown（OP+SY 含講題）+ 大表轉錄（非 SY 場次層級）
# 為什麼這樣做：講題層級只有 SY 在官網抓得到；FC/HS/Seminar 只在 PDF 大表（場次層級）
import re, json, os

# 所有路徑相對於本腳本所在的 build/ 資料夾，重開機不會消失
HERE = os.path.dirname(os.path.abspath(__file__))
def P(name): return os.path.join(HERE, name)

# ---------- 1. 解析官網 markdown 的 OP + SY（含每筆講題） ----------
md = open(P('apelso_program.md'), encoding='utf-8').read()
lines = md.split('\n')

DAY_DATE = {
    '1': {'date': '6/11 (四)', 'iso': '2026-06-11'},
    '2': {'date': '6/12 (五)', 'iso': '2026-06-12'},
    '3': {'date': '6/13 (六)', 'iso': '2026-06-13'},
}

web_sessions = []  # 每個 = dict(day, room, roomDesc, start, end, code, title, talks)
day = room = roomDesc = start = end = None
cur = None  # 當前 session

def flush(cur):
    if cur and cur['code']:
        web_sessions.append(cur)

i = 0
re_day = re.compile(r'^### Day (\d):')
re_room = re.compile(r'^#### Room (\d+) \((.+)\)\s*$')
re_time = re.compile(r'^(\d{1,2}:\d{2})-(\d{1,2}:\d{2})\s*$')
re_talkcode = re.compile(r'^(OP|SY\d+)-(\d+)\s*$')
re_header = re.compile(r'^(OP|SY\d+)\s+(.*)$')

while i < len(lines):
    ln = lines[i].rstrip()
    m = re_day.match(ln)
    if m:
        flush(cur); cur = None
        day = m.group(1); room = roomDesc = start = end = None
        i += 1; continue
    m = re_room.match(ln)
    if m:
        flush(cur); cur = None
        room = m.group(1); roomDesc = m.group(2); start = end = None
        i += 1; continue
    m = re_time.match(ln)
    if m:
        flush(cur); cur = None
        start, end = m.group(1), m.group(2)
        i += 1; continue
    m = re_talkcode.match(ln)
    if m:
        # 收集後續非空行直到空行 = title / speaker / affiliation
        block = []
        j = i + 1
        while j < len(lines) and lines[j].strip() == '':
            j += 1
        while j < len(lines) and lines[j].strip() != '':
            block.append(lines[j].strip())
            j += 1
        title = block[0] if len(block) > 0 else 'T.B.A.'
        speaker = block[1] if len(block) > 1 else ''
        affil = ' '.join(block[2:]) if len(block) > 2 else ''
        if cur is not None:
            cur['talks'].append({'code': ln.strip(), 'title': title,
                                 'speaker': speaker, 'affiliation': affil})
        i = j; continue
    m = re_header.match(ln)
    if m:
        flush(cur)
        code = m.group(1); rest = m.group(2)
        bolds = re.findall(r'\*\*(.+?)\*\*', rest)
        if bolds:
            title = ' '.join(b.strip() for b in bolds)
        else:
            title = re.sub(r'^(Symposium|Joint Symposium|Opeing Ceremony)\s*', '', rest).strip()
            if not title:
                title = rest.strip()
        # 全形數字正規化
        title = title.replace('１', '1').replace('２', '2').replace('３', '3')
        cur = {'day': day, 'room': room, 'roomDesc': roomDesc,
               'start': start, 'end': end, 'code': code, 'title': title, 'talks': []}
        i += 1; continue
    i += 1
flush(cur)

# ---------- 1b. App 更新覆寫官網「T.B.A.」講題（來源：Conference Navi App 截圖） ----------
# 為什麼：官網 program.html 抓取時部分 SY 講題仍是 T.B.A.，大會 App 後續才公布實際題目/講者
SY_TALK_OVERRIDES = {
 'SY06-3': {'title': 'The role of physicians in IPW through training',
            'speaker': 'Gen Ouchi',
            'affiliation': 'University of the Ryukyus Hospital, Japan'},
}
for s in web_sessions:
    for t in s['talks']:
        ov = SY_TALK_OVERRIDES.get(t['code'])
        if ov:
            t.update(ov)

# ---------- 2. 非 SY 場次（從 PDF 大表轉錄，場次層級） ----------
# 欄位：day, code, type, title, room, roomDesc, start（end 後面用同時段 SY 推算）
ND = '5F Main Hall A;5F Main Hall B;5F Large Hall A;5F Large Hall B;6F Conference Room A;6F Conference Room B;6F Conference Room C;6F Meeting Room 1;6F Meeting Room 2;6F Meeting Room 3'.split(';')
ROOMDESC = {1:ND[0],2:ND[1],3:ND[2],4:ND[3],5:ND[4],6:ND[5],7:ND[6],8:ND[7],9:ND[8],10:ND[9]}

non_sy = [
 # Day1
 ('1','OP-RELAY','Opening Ceremony','Opening Ceremony (relayed 轉播)',2,'8:15'),
 ('1','L1','Luncheon Seminar 1（Getinge 贊助）','Right Patient. Right Center. Right Time – Optimizing Transport and Triage for Advanced ECLS cases',1,'11:50'),
 ('1','L2','Luncheon Seminar 2（Senko Medical Instrument 贊助）','Beyond Access: Cannulation Strategy for Safer and More Effective ECMO from Prehospital to the ICU',2,'11:50'),
 ('1','L3','Luncheon Seminar 3（Paramount Bed 贊助）','Prioritization of Mobilization while on ECMO',3,'11:50'),
 ('1','L4','Luncheon Seminar 4（NIPRO 贊助）','Multicenter Collaboration in Mechanical Circulatory Support ～ How We Save the Cardiogenic Shock Patients ～',4,'11:50'),
 ('1','FC-D01','Free Communications','Doctors 1',6,'10:00'),
 ('1','FC-D03','Free Communications','Doctors 3',8,'10:00'),
 ('1','FC-D06','Free Communications','Doctors 6',10,'10:00'),
 ('1','HS-A1(E)','Hands-on','Adult Session 1（English）',6,'13:00'),
 ('1','FC-D02','Free Communications','Doctors 2',7,'13:00'),
 ('1','FC-D04','Free Communications','Doctors 4',9,'13:00'),
 ('1','FC-D07','Free Communications','Doctors 7',10,'13:00'),
 ('1','HS-A2(J)','Hands-on','Adult Session 2（Japanese）',6,'14:45'),
 ('1','FC-D05','Free Communications','Doctors 5',9,'14:45'),
 ('1','FC-D08','Free Communications','Doctors 8',10,'14:45'),
 ('1','EV1','Evening Seminar','Evening Seminar 1（sponsored by Terumo）',2,'16:30'),
 ('1','EV2','Evening Seminar','Evening Seminar 2（sponsored by Getinge）',4,'16:30'),
 ('1','GT','Get-together','Get-together 交流會',1,'17:40'),
 # Day2
 ('2','OA1','Outstanding Abstracts','Outstanding Abstracts 1',4,'8:00'),
 ('2','HS-P1(J)','Hands-on','Pediatrics Session 1（Japanese）',5,'8:00'),
 ('2','HS-A3(E)','Hands-on','Adult Session 3 for Nurses（English）',6,'8:00'),
 ('2','FC-NP1','Free Communications','Nurses / Physical Therapists 1',9,'8:00'),
 ('2','OA2','Outstanding Abstracts','Outstanding Abstracts 2',4,'9:45'),
 ('2','HS-P2(E)','Hands-on','Pediatrics Session 2（English）',5,'9:45'),
 ('2','HS-A4(J)','Hands-on','Adult Session 4 for Nurses（Japanese）',6,'9:45'),
 ('2','IMPELLA','Hands-on','Impella Hands-on Workshop（sponsored by J&J MedTech）',7,'9:45'),
 ('2','FC-NP2','Free Communications','Nurses / Physical Therapists 2',9,'9:45'),
 ('2','L5','Luncheon Seminar 5（Getinge 贊助）','eCPR Pathways: Integrating In-Hospital and Out-of-Hospital Care',1,'11:35'),
 ('2','L6','Luncheon Seminar 6（J&J MedTech 贊助）','Impella as a Treatment Strategy for Improved Outcome',2,'11:35'),
 ('2','L7','Luncheon Seminar 7（Mallinckrodt Pharmaceuticals 贊助）','Inhaled Nitric Oxide',3,'11:35'),
 ('2','HS-P3(J)','Hands-on','Pediatrics Session 3（Japanese）',5,'12:45'),
 ('2','HS-A5(E)','Hands-on','Adult Session 5（English）',6,'12:45'),
 ('2','FC-NP3','Free Communications','Nurses / Physical Therapists 3',9,'12:45'),
 ('2','HS-P4(E)','Hands-on','Pediatrics Session 4（English）',5,'14:30'),
 ('2','HS-A6(J)','Hands-on','Adult Session 6（Japanese）',6,'14:30'),
 ('2','FC-D09','Free Communications','Doctors 9',9,'14:30'),
 ('2','EV3','Evening Seminar','Evening Seminar 3（sponsored by Resuscitec GmbH）',4,'16:15'),
 # Day3
 ('3','FC-PC1','Free Communications','Perfusionists / Clinical Engineers / Others 1',9,'8:00'),
 ('3','FC-D10','Free Communications','Doctors 10',10,'8:00'),
 ('3','FC-PC2','Free Communications','Perfusionists / Clinical Engineers / Others 2',9,'9:45'),
 ('3','FC-D11','Free Communications','Doctors 11',10,'9:45'),
 ('3','UD','Up-to-date','Up-to-date APELSO Nations and Regions',1,'11:30'),
]

# 手動補入的 FC 講題（來源：大會 Conference Navi App 截圖）。key = 場次代碼
MANUAL_TALKS = {
 'FC-D09': [
   {'code':'FC-D9-08',
    'title':'Sudden Hemodynamic Collapse Post-ROSC on ECPR: Unmasking a Fatal CPR-Related Cardiac Trauma',
    'speaker':'Chang Chih Tsai',
    'affiliation':'Department of Emergency Medicine, Chi-Mei Medical Center, Tainan, Taiwan / Department of Health and Nutrition, Chia Nan University of Pharmacy and Science'},
 ],
}

# 用同一天同 start 的 SY/OP 推算 end
end_lookup = {}
for s in web_sessions:
    end_lookup[(s['day'], s['start'])] = s['end']
EXPLICIT_END = {('1','8:15'):'9:45', ('1','17:40'):'19:00'}

def classify(code, title):
    t = (code + ' ' + title).lower()
    if 'nurse' in t: return 'nurse'
    if 'pediatric' in t or 'hs-p' in t: return 'pediatric'
    if 'perfusion' in t or 'fc-pc' in t: return 'perfusionist'
    if 'ecpr' in t: return 'ecpr'
    if 'cardiac' in t or 'vad' in t or 'va ecmo' in t or 'post cardiotomy' in t: return 'cardiac'
    if 'respiratory' in t: return 'respiratory'
    if 'doctors' in t or code.startswith('FC-D'): return 'doctors'
    if 'hands-on' in t or code.startswith('HS'): return 'handson'
    if 'seminar' in t: return 'seminar'
    if 'outstanding' in t: return 'oral'
    return 'other'

unified = []
for s in web_sessions:
    s2 = {'day': s['day'], 'code': s['code'], 'type': 'Symposium' if s['code'].startswith('SY') else 'Opening',
          'title': s['title'], 'room': int(s['room']), 'roomDesc': s['roomDesc'],
          'start': s['start'], 'end': s['end'], 'talks': s['talks'],
          'cat': classify(s['code'], s['title']), 'mine': False}
    unified.append(s2)

for (d, code, typ, title, room, start) in non_sy:
    end = EXPLICIT_END.get((d, start)) or end_lookup.get((d, start)) or ''
    cat = 'seminar' if (code.startswith('L') or code.startswith('EV')) else classify(code, title)
    unified.append({'day': d, 'code': code, 'type': typ, 'title': title,
                    'room': room, 'roomDesc': ROOMDESC[room], 'start': start, 'end': end,
                    'talks': MANUAL_TALKS.get(code, []), 'cat': cat,
                    'partial': bool(MANUAL_TALKS.get(code)),
                    'mine': (code == 'FC-D08')})

# 排序：day, start, room
def tmin(t):
    if not t: return 9999
    h, m = t.split(':'); return int(h)*60 + int(m)
unified.sort(key=lambda s: (s['day'], tmin(s['start']), s['room']))

out = {'meta': {'title': 'APELSO 2026 我的議程', 'dates': DAY_DATE,
                'venue': 'Hamamatsucho Convention Hall, Tokyo'},
       'sessions': unified}
json.dump(out, open(P('apelso_data.json'),'w',encoding='utf-8'), ensure_ascii=False, indent=1)

# ---------- 3. 把資料注入 HTML 模板，產出 ../index.html（成品） ----------
# 一鍵到底：跑這個腳本就同時更新中繼 JSON 與最終 index.html
_tpl = open(P('template.html'), encoding='utf-8').read()
_html = _tpl.replace('/*__DATA__*/{}', json.dumps(out, ensure_ascii=False, indent=1))
open(os.path.join(HERE, '..', 'index.html'),'w',encoding='utf-8').write(_html)
print('已寫出 index.html：', len(_html), 'bytes')

# ---------- 樣本輸出 ----------
sy_with_talks = sum(1 for s in unified if s['talks'])
total_talks = sum(len(s['talks']) for s in unified)
print('總場次：', len(unified))
print('含講題的場次（SY+OP）：', sy_with_talks, '｜講題總數：', total_talks)
print('非 SY 場次卡片：', len(non_sy))
for d in ('1','2','3'):
    print(f"  Day{d}: {sum(1 for s in unified if s['day']==d)} 場")
print('\n===== 你的場次 FC-D08 =====')
mine = [s for s in unified if s['mine']][0]
print(json.dumps(mine, ensure_ascii=False, indent=1))
print('\n===== SY 範例（含講題）=====')
sample = [s for s in unified if s['code']=='SY02'][0]
print('code:', sample['code'], '|', sample['title'], '|', f"Day{sample['day']} {sample['start']}-{sample['end']} Room{sample['room']}")
for t in sample['talks']:
    print(' -', t['code'], t['title'], '/', t['speaker'])
