from pathlib import Path

p=Path('guide/wicket.html')
s=p.read_text(encoding='utf-8')
for old,new in [
('>MCC Laws: The Wickets</a>','>情報ソース：MCC Laws: The Wickets</a>'),
('>FORTRESS Rubber Base Stump</a>','>情報ソース：FORTRESS Rubber Base Stump</a>'),
('>Gray-Nicolls Spring Return Stumps</a>','>情報ソース：Gray-Nicolls Spring Return Stumps</a>'),
('>Gray-Nicolls Power Play Plastic Set</a>','>情報ソース：Gray-Nicolls Power Play Plastic Set</a>'),
('>Zings official site</a>','>情報ソース：Zings official site</a>'),
('>Science Museum Group: CCD cricket stump camera</a>','>情報ソース：Science Museum Group: CCD cricket stump camera</a>')]: s=s.replace(old,new)
p.write_text(s,encoding='utf-8')

p=Path('index.html');s=p.read_text(encoding='utf-8')
s=s.replace('<div><a class="button" href="guide/wicket.html">ウィケットを知る →</a> <a class="button" href="guide/">ガイド一覧 →</a></div>','<div><a class="button" href="guide/">ガイド一覧 →</a></div>',1)
p.write_text(s,encoding='utf-8')

p=Path('history.html');s=p.read_text(encoding='utf-8')
a='        <li class="event"><time class="date" datetime="2026-07-14">7.14</time><div class="event-copy"><p>日本のクリケットに関するファンサイト、ブログ、ポッドキャスト、体験活動を紹介する「<a href="links.html"><strong>日本のクリケットとつながる。</strong></a>」リンク集を公開</p></div></li>'
b=a+'\n        <li class="event"><time class="date" datetime="2026-07-20">7.20</time><div class="event-copy"><p>「<a href="guide/"><strong>クリケットガイド</strong></a>」ページを開設し、第一弾として「<a href="guide/wicket.html"><strong>三本のStumps、二本のBails</strong></a>」を公開</p></div></li>'
s=s.replace(a,b,1)
p.write_text(s,encoding='utf-8')
