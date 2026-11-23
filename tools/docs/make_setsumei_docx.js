const fs=require('fs');
const {Document,Packer,Paragraph,TextRun,Table,TableRow,TableCell,WidthType,ShadingType,AlignmentType,LevelFormat,HeadingLevel,BorderStyle,ExternalHyperlink,Footer,PageNumber}=require('docx');
const F='Yu Gothic';
const p=(t,o={})=>new Paragraph({spacing:{after:100,line:300},...o,children:Array.isArray(t)?t:[new TextRun(t)]});
const b=t=>new TextRun({text:t,bold:true});
const r=t=>new TextRun(t);
const bul=(c)=>new Paragraph({numbering:{reference:'bul',level:0},spacing:{after:60,line:290},children:Array.isArray(c)?c:[r(c)]});
const num=(c,ref)=>new Paragraph({numbering:{reference:ref,level:0},spacing:{after:60,line:290},children:Array.isArray(c)?c:[r(c)]});
const h1=t=>new Paragraph({heading:HeadingLevel.HEADING_1,children:[r(t)]});
const h2=t=>new Paragraph({heading:HeadingLevel.HEADING_2,children:[r(t)]});
const W=9026;
const brd={style:BorderStyle.SINGLE,size:4,color:'BFC7D1'};
const borders={top:brd,bottom:brd,left:brd,right:brd};
function table(widths,rows){
  return new Table({width:{size:W,type:WidthType.DXA},columnWidths:widths,rows:rows.map((row,i)=>new TableRow({tableHeader:i===0,cantSplit:true,children:row.map((c,j)=>new TableCell({borders,width:{size:widths[j],type:WidthType.DXA},margins:{top:60,bottom:60,left:100,right:100},shading:i===0?{type:ShadingType.CLEAR,fill:'E7EEF8',color:'auto'}:undefined,children:[new Paragraph({spacing:{line:270},children:[i===0?b(c):r(c)]})]}))}))});
}
const sp=()=>new Paragraph({spacing:{after:60},children:[]});
const URL='https://tockyocky12-droid.github.io/kinko-bus/';
const body=[
  new Paragraph({heading:HeadingLevel.TITLE,children:[r('きんこうバスナビ 説明資料')]}),
  p([r('2026年11月23日　産業振興課 林務担当 時吉')],{alignment:AlignmentType.RIGHT}),

  h1('1. 概要'),
  p('きんこうバスナビは、錦江町に関係するバス6路線の「次のバス」と時刻・運賃を、スマホの地図で見られる無料のアプリ（試作版）です。産業振興課 林務担当の時吉が、時刻案内を見やすくする提案として作りました。'),
  bul([b('公開先：'),new ExternalHyperlink({link:URL,children:[new TextRun({text:URL,style:'Hyperlink'})]}),r('（2026年11月23日時点で v49）')]),
  bul([b('費用：'),r('0円。無料の公開先（GitHub Pages）を使い、外部委託もしていません。ダウンロードや登録も不要です。')]),
  bul([b('位置づけ：'),r('町の「錦江町関連バスの運行時刻表」をもとに、スマホで調べやすくしたものです。時刻表PDFの代わりではなく、入口を増やす役割です。')]),
  bul([b('注意点：'),r('今は非公式の試作です。ダイヤ改定のたびに手作業で直す必要があり、その担い手がまだ決まっていません。')]),

  h1('2. できること'),
  table([2300,6726],[
    ['機能','内容'],
    ['次のバス','開くといちばん近いバス停を選び、「次のバスは何時何分、あと何分」と最終便を表示。今日の便が終わったら「明日の始発」を同じ大きな枠で表示'],
    ['行き先から','行き先を先に選ぶと、鹿屋・鹿児島空港・鹿児島中央駅への行き方と帰り方を、乗り継ぎ（2回まで）込みの到着時刻と運賃の合計で一覧表示'],
    ['行き方を送る','調べた行き方を、LINEなどでそのまま家族に送れる'],
    ['時刻表','路線ごとの時刻表。平日・土日祝・祝日を自動で判定。年末年始の運休は確かめられたものだけ反映'],
    ['地図','路線のボタンで、その路線だけを地図で濃く表示。主なバス停だけ載せている路線は「主なバス停○か所」と表示'],
    ['使いやすさ','「文字 大」ボタンで文字を大きくできる。よく使うバス停を3つまで登録。一度開けば圏外でも表示'],
    ['遅れ・運休','鹿児島交通のお知らせへのリンクと、垂水フェリーの電話番号を表示'],
  ]),
  sp(),

  h1('3. 載っている路線'),
  table([3600,5426],[
    ['路線','備考'],
    ['コミュニティバス（田代地区）','無料'],
    ['路線バス 海岸線（神川・坂元経由）','鹿児島交通。主なバス停のみ掲載'],
    ['路線バス 中央線（田代・吾平経由）','鹿児島交通。主なバス停のみ掲載'],
    ['根占〜佐多間コミュニティバス','南大隅町。平日のみ・無料・フリー乗降'],
    ['鹿屋〜鹿児島空港線','鹿児島交通。鹿屋で乗り継ぎ'],
    ['鹿屋〜鹿児島中央駅 直行バス','鹿児島交通。垂水港からフェリー経由'],
  ]),
  sp(),

  h1('4. 住民と町にとってのよさ'),
  bul('紙の時刻表を読み解かなくても、自分の乗るバスがすぐわかります。'),
  bul('通院や買い物に出る高齢者にも使いやすいよう、文字を大きくできます。'),
  bul('帰省や出張で空港・鹿児島市へ行き来する人と、その家族に役立ちます。鹿児島空港・鹿児島中央駅から大根占などへの帰り方も調べられ、LINEで送れます。'),
  bul('町の時刻表にない情報（運賃、鹿屋での空港バス・直行バスへの乗り継ぎ、遅れ・運休の確かめ先）も足しています。'),
  bul('地図で路線が見えるので、町外から来た人や新しく住む人にも伝えやすいです。'),

  h1('5. 費用と仕組み'),
  bul('費用は0円。無料の公開先（GitHub Pages）で、サーバーも契約も不要です。'),
  bul('一度開けば圏外でも使えます。通信量は初回およそ75KBで、地図画像は端末に保存します。'),
  bul('森林ナビ・防災ナビと同じ仕組みです。'),
  bul('機能を入れすぎないよう、最初の画面は地図・1行の「次のバス」・路線のボタンだけに絞っています。今後は利用者の声を聞いてから足します。'),

  h1('6. リスクと対策'),
  table([3800,5226],[
    ['リスク','対策'],
    ['ダイヤ改定に直しが遅れて、古い時刻が出る','改定のたびに直す人を決める。直し方は1枚にまとめる'],
    ['非公式の情報を公式と取り違えられる','画面に「試作・非公式。正式な時刻は町の時刻表で」と表示済み'],
    ['年末年始などの臨時運行','確かめられた運休だけ反映。未確認の路線は「乗る前に確かめて」と表示'],
    ['乗り継ぎの案内どおりにいかず、乗り遅れる','乗り継ぎは5分以上の便だけ。画面と送る文に「時刻表の上の計算です。遅れることがあります」と表示済み'],
    ['個人情報','位置情報は近くのバス停を探すためだけに端末の中で使い、どこにも送らない'],
    ['公開先（GitHub Pages）の管理が時吉個人のアカウントのため、異動などで更新が止まる','町（課）の共用アカウントを作るか、管理者をもう1人加える。アプリはファイルの集まりなので、町のホームページのサーバーなどへいつでも移せる'],
    ['公開先のサービス（GitHub、マイクロソフト社）の条件が変わる','通信量の上限（月100GB）に対しアプリは1回約75KBで余裕がある。お金のやり取りがない公共の案内で、禁止された用途にも当たらない。変わったときは上と同じく移せる'],
  ]),
  sp(),

  h1('7. ご判断いただきたいこと'),
  num('町の案内（町ホームページ・広報・チラシ）で紹介するか。紹介するなら「試作」の表示をどうするか。','dec'),
  num('時刻更新の担当：政策企画課で時刻表を直すときに、アプリの直しもあわせて時吉に連絡する形を提案します。','dec'),
  num('鹿児島交通と南大隅町（企画観光課）への一声かけを、どの課から行うか。','dec'),
  num('時刻のまちがいを利用者が知らせる先（課のメール・電話・フォームのどれか）。決まればアプリの画面下に出します。','dec'),

  h1('8. 政策企画課に確認をお願いしたいこと'),
  num('田代地区コミュニティバスの年末年始の運行（運休日があれば反映します。12月中旬までに）','chk'),
  num('アプリの時刻が町の時刻表（令和8年10月1日改定）と合っているか、主なバス停での抜き取り確認','chk'),
  num('田代地区コミュニティバスはフリー乗降（バス停以外でも乗り降りできる）か。そうなら画面で案内します','chk'),

  h1('9. ダイヤ改定のときの流れ'),
  num('政策企画課で新しい時刻表ができたら、PDF（元のExcelがあればそれも）を時吉に送る。','flow'),
  num('時吉がアプリの時刻データを直し、自動の動作確認を通す。','flow'),
  num('切り替え日に公開し、担当者が主なバス停を抜き取りで確認する。','flow'),
  num('年末年始など臨時の運休は、わかった時点で日付と路線を連絡する（1行足すだけで反映できます）。','flow'),

  h1('10. データの出典'),
  table([2800,6226],[
    ['内容','出典'],
    ['時刻（町の路線）','錦江町「錦江町関連バスの運行時刻表」（令和8年10月1日改定）'],
    ['工業高校前の時刻','鹿児島交通 海岸線・中央線の時刻表（2026年10月1日）'],
    ['根占〜佐多間','南大隅町「南大隅町コミュニティバス交通利用案内」（令和8年10月1日〜）'],
    ['空港バス','鹿児島交通「鹿屋～空港線」時刻表（令和8年4月1日改正）'],
    ['直行バス（時刻・運賃）','鹿児島交通「鹿屋～鹿児島直行バス 運行時刻のお知らせ」（2026年7月18日改正、鹿屋市のページに掲載）'],
    ['運賃','鹿児島交通の運賃表（海岸線・中央線）'],
    ['バス停の位置・路線の道すじ','国土数値情報（バス停留所・バスルート・高速道路時系列、国土交通省）'],
    ['背景の地図','地理院タイル（国土地理院）'],
  ]),
  sp(),

  h1('11. 問い合わせ先'),
  bul('アプリについて：産業振興課 林務担当 時吉'),
  bul('路線バス・直行バス・空港バス：鹿児島交通 鹿屋営業所 0994-65-2258'),
  bul('直行バス：鹿屋市 交通政策係 0994-31-1147、垂水フェリー 垂水営業所 0994-32-0001'),
  bul('根占〜佐多間：南大隅町役場 企画観光課 0994-24-3113'),
  bul('田代地区コミュニティバス：政策企画課 0994-22-3032'),
];
const numCfg=ref=>({reference:ref,levels:[{level:0,format:LevelFormat.DECIMAL,text:'%1.',alignment:AlignmentType.LEFT,style:{paragraph:{indent:{left:440,hanging:360}}}}]});
const doc=new Document({
  styles:{default:{document:{run:{font:F,size:22}},
    title:{run:{font:F,size:40,bold:true,color:'1E4F9C'},paragraph:{spacing:{before:0,after:120},keepNext:true}},
    heading1:{run:{font:F,size:28,bold:true,color:'1E4F9C'},paragraph:{spacing:{before:280,after:120},keepNext:true,border:{bottom:{style:BorderStyle.SINGLE,size:6,color:'1E4F9C',space:2}}}},
    heading2:{run:{font:F,size:24,bold:true},paragraph:{spacing:{before:200,after:80},keepNext:true}}},
    characterStyles:[{id:'Hyperlink',name:'Hyperlink',run:{color:'1E4F9C',underline:{}}}]},
  numbering:{config:[{reference:'bul',levels:[{level:0,format:LevelFormat.BULLET,text:'・',alignment:AlignmentType.LEFT,style:{paragraph:{indent:{left:440,hanging:300}}}}]},numCfg('dec'),numCfg('chk'),numCfg('flow')]},
  sections:[{properties:{page:{margin:{top:1300,bottom:1300,left:1440,right:1440}}},
    footers:{default:new Footer({children:[new Paragraph({alignment:AlignmentType.CENTER,children:[new TextRun({children:[PageNumber.CURRENT],size:18})]})]})},
    children:body}]});
Packer.toBuffer(doc).then(buf=>fs.writeFileSync('きんこうバスナビ_説明資料_一本版.docx',buf));
