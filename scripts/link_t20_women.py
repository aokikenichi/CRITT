from pathlib import Path

p=Path('data-analytics.html')
s=p.read_text(encoding='utf-8')
if 'href="t20-women.html"' not in s:
    marker='<a class="analysis-card lab-card" href="t20-men.html">'
    start=s.index(marker)
    end=s.index('</a>',start)+4
    card='''\n<a class="analysis-card lab-card" href="t20-women.html" style="margin-top:24px"><div class="analysis-image"><img src="assets/data-cricket.png" alt="女子T20I選手のデータ比較を表すイメージ"></div><div class="analysis-copy"><span class="experiment-status">実験中・検証改善中</span><small>EXPERIMENT 02 / WOMEN'S T20I</small><h3>120球で見る、日本の現在地。— 女子版</h3><p>Cricsheetの女子T20I収録データから、打者の得点速度とアウトされにくさ、投手の失点抑制とウィケット獲得頻度を二軸で比較。男子版と同じ資格条件・指標・相手／局面の部分補正で、日本女子代表選手の特徴を探索します。</p><span class="more">女子版の実験を見る →</span></div></a>'''
    s=s[:end]+card+s[end:]
    p.write_text(s,encoding='utf-8')
