"""きんこうバスナビ（錦江町）の動作確認（Playwright）。

使い方（リポジトリの1つ上のフォルダで）:
  python3 -m http.server 8765 &
  APP_URL=http://localhost:8765/kinko-bus/ python3 kinko-bus/tools/test_app.py

地理院タイルは仮の画像で代わりに返す（作業環境から外へは出ない）。
時刻は日本時間の決まった日時に固定して確かめる。
"""
import datetime, os, re, struct, sys, zlib
from playwright.sync_api import sync_playwright

URL = os.environ.get('APP_URL', 'http://localhost:8765/kinko-bus/')
CHROME = '/usr/bin/google-chrome'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def png(rgba):
    raw = b''.join(b'\x00' + bytes(rgba) * 256 for _ in range(256))
    ch = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', 256, 256, 8, 6, 0, 0, 0)) + ch(b'IDAT', zlib.compress(raw)) + ch(b'IEND', b'')

TILE = png((236, 240, 236, 255))
fails = []
def check(cond, msg):
    print(('OK  ' if cond else 'NG  ') + msg)
    if not cond:
        fails.append(msg)

html = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
sw = open(os.path.join(ROOT, 'sw.js'), encoding='utf-8').read()
av = re.search(r"const APP_VER='([^']+)'", html).group(1)
check(av == re.search(r"const VER='([^']+)'", sw).group(1), f'版が一致（{av}）')

def ctx_with_tiles(br, log, **kw):
    ctx = br.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, **kw)
    def gsi(route):
        log.append(route.request.url)
        route.fulfill(status=200, body=TILE, headers={'Content-Type': 'image/png', 'Access-Control-Allow-Origin': '*'})
    ctx.route(re.compile(r'https://cyberjapandata\.gsi\.go\.jp/.*'), gsi)
    return ctx

with sync_playwright() as p:
    br = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox'])

    # ---- 1. 地図と時刻（平日の朝 7:30） ----
    log = []; errs = []
    ctx = ctx_with_tiles(br, log, service_workers='block', geolocation={'latitude': 31.2448, 'longitude': 130.7880}, permissions=['geolocation'])
    pg = ctx.new_page()
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.on('console', lambda m: m.type == 'error' and errs.append(m.text))
    pg.clock.install(time=datetime.datetime.fromisoformat('2026-11-19T07:30:00+09:00'))
    pg.goto(URL); pg.wait_for_timeout(1200)
    check(pg.inner_text('#vtag') == '試作 ' + av, '見出しに版が出ている')
    check(pg.inner_text('header h1').startswith('きんこうバスナビ') and '錦江町' in pg.title() and '錦江町' in pg.get_attribute('meta[name=description]','content'), '名前はきんこうバスナビ、題名と説明文に錦江町')
    check(pg.locator('#unoff').count()==0 and '試作中の非公式' in pg.inner_text('footer'), '上部の帯なし・非公式の注意は下部に表示')
    check(any('/xyz/pale/' in u for u in log), '淡色地図を読む')
    n_lines = pg.evaluate('Object.keys(lines).length')
    check(n_lines == 5, f'5路線の線を描く（{n_lines}）')
    n_mk = pg.evaluate('Object.keys(markers).length'); n_all = pg.evaluate('ALL.length')
    check(n_mk == n_all, f'時刻表のバス停すべてに印がある（{n_mk}/{n_all}）')
    check(pg.evaluate("ALL.filter(s=>!STOP_POS[s])") == [], 'すべてのバス停に位置がある')
    check(pg.input_value('#stop') == '大根占', '開いたとき、現在地から一番近いバス停（大根占）を出す')
    pg.select_option('#stop', '田代麓'); pg.wait_for_timeout(300)
    t = pg.inner_text('#v-next')
    check('7:36' in t and 'あと6分' in t, '田代麓の次のバス（7:36・あと6分）')
    pg.screenshot(path='/tmp/kb_bus_1.png', full_page=True)

    # 地図の下の端の「次のバス」の帯（田代麓）
    bar = pg.inner_text('#nextbar')
    check('田代麓' in bar and '7:36' in bar and 'あと6分' in bar, '地図の帯に次のバス（7:36・あと6分）')
    check('最終' in bar, '地図の帯に最終便が出る')
    check('最終' in t, '下の「次のバス」にも最終便が出る')
    # 地図のバス停を押す → 帯と下の画面が変わる（吹き出しは出さない）
    pg.evaluate("markers['神川'].fire('click')"); pg.wait_for_timeout(500)
    bar = pg.inner_text('#nextbar')
    check(pg.input_value('#stop') == '神川' and '神川' in bar and '海岸線' in bar, '地図のバス停を押すと選ばれ、帯が変わる')
    check('8:35' in bar, '神川の次の鹿屋方面は 8:35')
    check(pg.locator('.leaflet-popup').count() == 0, '吹き出しは出さない')
    # 凡例は2段に折り返して、すべて画面内に収まる
    w = pg.evaluate("Math.max(...[...document.querySelectorAll('.chip')].map(c=>c.getBoundingClientRect().right))")
    check(w <= 390, f'凡例が画面からはみ出さない（右端{w:.0f}px）')
    pg.screenshot(path='/tmp/kb_bus_pop.png')

    # 現在地から一番近いバス停（大根占のそばに置いた）
    pg.click('#locate'); pg.wait_for_timeout(1000)
    check(pg.input_value('#stop') == '大根占', '現在地から一番近いバス停（大根占）を選ぶ')

    # 根占〜佐多間（南大隅町）：大浜から根占方面・佐多方面（平日 7:30）
    pg.select_option('#stop', '大浜'); pg.wait_for_timeout(300)
    bar = pg.inner_text('#nextbar'); t2 = pg.inner_text('#v-next')
    check('根占・南大隅町役場方面' in bar and '8:05' in bar and '佐多方面' in bar and '8:22' in bar, '大浜の次は根占方面 8:05・佐多方面 8:22')
    check('根占で鹿児島交通の路線バスに接続' in t2, '根占での接続の印が出る')
    pg.select_option('#stop', '根占'); pg.wait_for_timeout(300)
    check('佐多方面' in pg.inner_text('#v-next'), '根占から佐多方面の便が出る')
    check(pg.get_attribute('#farepdf2','href').endswith('/b895630b63fe5da84e4bf8ef833be21b.pdf') and pg.get_attribute('#farepdf','href').endswith('/ac0da9f0815db155627cef3ed948a0e8.pdf'), '運賃表のリンク（海岸線・中央線）')
    check(pg.get_attribute('#satapdf','href').endswith('/kotsu/documents/nejimesaigo.pdf'), '根占〜佐多の出典に南大隅町のPDFへのリンク')
    # 大根占：詳しい画面は鹿屋方面が上
    pg.select_option('#stop', '大根占'); pg.wait_for_timeout(300)
    dn = pg.eval_on_selector_all('#v-next .grp-h .dn', 'e=>e.map(x=>x.textContent)')
    check(dn[0] == '鹿屋方面' and dn.count('鹿屋方面') == 1 and dn.count('根占方面') == 1, f'大根占：鹿屋方面が上で、海岸線・中央線を1つにまとめる（{dn}）')
    g = pg.inner_text('#v-next .grp >> nth=0')
    check('海岸線' in g and '中央線' in g, '鹿屋方面の便に路線の印が付く')
    tt = pg.eval_on_selector_all('#v-next .grp >> nth=0 >> .trip .tt', 'e=>e.map(x=>x.textContent)')
    m = [int(a)*60+int(b) for a,b in (x.split(':') for x in tt)]
    check(m == sorted(m), f'まとめた便は時刻順（{len(m)}便）')
    # 運賃：大根占から鹿屋まで 海岸線910円・中央線1,410円、コミュニティバスは無料
    pg.select_option('#stop', '大根占'); pg.wait_for_timeout(300)
    g = pg.inner_text('#v-next .grp >> nth=0')
    check('910円' in g and '1,410円' in g, '大根占→鹿屋の運賃（海岸線910円・中央線1,410円）')
    check('無料' in pg.inner_text('#v-next'), 'コミュニティバスは無料と出る')
    pg.click('#v-next .grp >> nth=0 >> .trip >> nth=2'); pg.wait_for_timeout(300)
    check('770円' not in pg.inner_text('#v-next .trip[aria-expanded=true]') and '910円' in pg.inner_text('#v-next .trip[aria-expanded=true]'), '便を開くと、先のバス停までの運賃が並ぶ（乗る前のバス停には出ない）')
    pg.click('#v-next .trip[aria-expanded=true]'); pg.wait_for_timeout(200)
    # セレクトで選ぶ（中央線の壱崎）・時刻表タブ
    pg.select_option('#stop', '壱崎'); pg.wait_for_timeout(400)
    check('中央線' in pg.inner_text('#v-next'), '壱崎で中央線が出る')
    pg.click('#tab-all'); pg.click('.rsel button[data-r="kaigan"]')
    check('通過' in pg.inner_text('#v-all'), '時刻表で海岸線の「通過」が出る')
    pg.click('.chip >> nth=4'); pg.wait_for_timeout(500)
    z = pg.evaluate('map.getZoom()')
    check(z <= 11, f'直行バスのボタンで鹿児島市内まで見える（拡大率{z}）')
    check(not errs, 'エラーが出ていない ' + ' / '.join(errs[:3]))
    ctx.close()

    # ---- 2. 土曜日（土日祝運休・土日祝のみの便） ----
    ctx = ctx_with_tiles(br, [], service_workers='block')
    pg = ctx.new_page()
    pg.clock.install(time=datetime.datetime.fromisoformat('2026-11-21T05:30:00+09:00'))
    pg.goto(URL); pg.wait_for_timeout(800)
    check(pg.input_value('#stop') == '田代麓', '位置情報が使えないときは田代麓のまま')
    pg.select_option('#stop', '根占'); pg.wait_for_timeout(300)
    t = pg.inner_text('#v-next')
    check('土日祝の時刻' in pg.inner_text('#daylbl'), '土曜は土日祝の時刻')
    check('6:12' not in t and '15:35' in t, '土日祝運休の便は出ず、土日祝のみの便は出る')
    check('中央線は、土日祝はこのバス停から鹿屋方面へ走りません' in t, '中央線は土日祝に走らないと出る')
    check('土日祝のみ' not in t and '土日祝運休' not in t, '「今日」の表示では曜日の印を出さない')
    pg.click('.seg button[data-mode="weekday"]'); t = pg.inner_text('#v-next')
    check('土日祝運休' in t, '「平日」を選ぶと「土日祝運休」の印が出る')
    order = pg.evaluate("[...document.querySelectorAll('#v-next .trip')].map(b=>[...b.querySelectorAll('.tags .b')].map(x=>x.textContent)).find(a=>a.length>=3)")
    check(order is not None and order[0] == '土日祝運休' and order[1] == '鹿屋工業経由' and order[2].startswith('押すと垂水'), f'印は決まった順で時刻の下に並ぶ {order}')
    ctx.close()

    # ---- 3. オフライン（サービスワーカー） ----
    log = []; errs = []
    ctx = ctx_with_tiles(br, log)
    pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(URL); pg.evaluate('navigator.serviceWorker.ready.then(()=>1)')
    pg.reload(); pg.wait_for_timeout(2000)
    info = pg.evaluate('''async()=>{const o={};for(const k of await caches.keys()){const c=await caches.open(k);const ks=await c.keys();let op=0;
        for(const r of ks){if((await c.match(r)).type==='opaque')op++}o[k]={n:ks.length,opaque:op}}return o}''')
    print('   保存の状態:', info)
    check(info.get(f'bus-shell-{av}', {}).get('n', 0) >= 5, '本体と時刻表データを保存している')
    check(info.get('bus-tiles-v1', {}).get('n', 0) > 0, '地図画像を保存している')
    check(all(v['opaque'] == 0 for v in info.values()), 'opaque で保存していない')
    check('gsi-saved-v1' not in info, '森林ナビの保存場所を空で作らない')
    ctx.set_offline(True); pg.reload(); pg.wait_for_timeout(1500)
    check(pg.evaluate('Object.keys(markers).length') == n_all and pg.is_visible('#map .leaflet-tile-loaded'), '圏外でも開いて地図とバス停が出る')
    ctx.set_offline(False)
    check(not errs, 'エラーが出ていない ' + ' / '.join(errs[:3]))
    ctx.close()
    br.close()

print('\n結果:', 'すべてOK' if not fails else f'{len(fails)}件NG')
sys.exit(1 if fails else 0)
