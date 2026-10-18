(function () {
  'use strict';
  const $=s=>document.querySelector(s),number=n=>new Intl.NumberFormat('ja-JP').format(n);
  const escape=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const value=m=>m.denominator?m.numerator/m.denominator:null;
  const percent=(m,digits=2)=>value(m)===null?'—':(100*value(m)).toFixed(digits)+'%';
  const decimal=(m,digits=3)=>value(m)===null?'—':value(m).toFixed(digits);
  const phases=['early','middle','late'];
  const short={early:'序盤',middle:'中盤',late:'終盤'};
  const names={early:'序盤 Powerplay（1–6）',middle:'中盤 Middle（7–15）',late:'終盤 Death（16–20）'};
  const colors={teal:'#0e6b69',gold:'#b18b38',red:'#a92b2c',paper:'#ddd7c9',ink:'#17201e',muted:'#666b66'};
  let content,loading;
  function check(data,sankey) {
    if(data.schema_version!==1||data.sankey_schema_version!==sankey.schema_version||data.source_sha256!==sankey.source_sha256)throw new Error('集計データの版が一致しません。');
    for(const ph of ['all',...phases]){
      for(const key of ['delivery_count','match_count'])if(data.sankey_totals[ph][key]!==sankey.phases[ph][key])throw new Error('集計対象が一致しません。');
    }
    if(data.stories.length!==4||data.overs.length!==20)throw new Error('記事データが不足しています。');
    for(const story of data.stories)for(const link of story.links){
      if(!sankey.phases[link.phase]?.paths.some(p=>p.path_id===link.path))throw new Error('参照する経路がありません。');
    }
  }
  function links(id) {
    return content.stories.find(s=>s.id===id).links.map(link=>{
      const q=new URLSearchParams({mode:'explore',phase:link.phase,path:link.path,story:id});
      const path=['total',...link.path.split('|').slice(1)].map(key=>window.CrittSankey.labels[key]).join(' → ');
      return `<a class="story-to-flow" data-oneball-link href="#${q}">完全経路の例：${escape(path)} <span aria-hidden="true">↗</span></a>`;
    }).join('');
  }
  function table(headers,rows,caption) {
    return `<details class="story-data-table"><summary>数値を表で読む</summary><div class="story-table-scroll"><table><caption>${escape(caption)}</caption><thead><tr>${headers.map(x=>`<th scope="col">${escape(x)}</th>`).join('')}</tr></thead><tbody>${rows.map(row=>`<tr>${row.map((cell,i)=>i?`<td>${escape(cell)}</td>`:`<th scope="row">${escape(cell)}</th>`).join('')}</tr>`).join('')}</tbody></table></div></details>`;
  }
  function article(id,index,title,lead,figureId,caption,body,method,dataTable) {
    return `<article id="story-${id}" class="data-story"><header class="story-heading"><p class="story-number">${String(index).padStart(2,'0')} <span>ONE BALL / DATA STORY</span></p><h2 tabindex="-1">${title}</h2><p class="story-lead">${lead}</p></header><figure class="story-figure"><div id="${figureId}" class="story-plot" data-chart="${id}"></div><figcaption>${caption}</figcaption><p class="chart-insight" role="status">グラフに触れると、件数と分母を確認できます。</p></figure><div class="story-prose">${body}</div><div class="story-flow-links">${links(id)}</div>${dataTable}<details class="story-method"><summary>対象・計算方法・解釈について</summary><div>${method}</div></details></article>`;
  }
  function renderContent() {
    const d=content,h=d.highlights,ps=d.phases,a=ps.all;
    const boundaryTitle=`約${Math.round(100*value(h.boundary_deliveries))}%の球が、得点の${value(h.boundary_points)>=.45&&value(h.boundary_points)<=.55?'半分':percent(h.boundary_points)}を生む`;
    const titles=[boundaryTitle,'中盤は、1点でつなぐ','終盤は、得点もアウトも増える','得点したのに、アウトになる'];
    const ids=['boundaries','middle','death','score-out'];
    const intro=`<header id="stories-intro" class="stories-intro"><p class="eyebrow">READ BETWEEN THE DELIVERIES</p><h2 tabindex="-1">数字の向こうに、<br>クリケットが見えてくる。</h2><p>${number(a.match_count)}試合、${number(a.delivery_count)}回の記録投球。<br>一球の記録から、四つの発見をたどります。</p><p class="stories-scope">${d.scope.date_from}〜${d.scope.date_to} ／ 男子T20国際試合 ／ スーパーオーバーを除外</p></header><nav class="story-contents" aria-label="データストーリーの目次">${ids.map((id,i)=>`<a data-oneball-link href="#mode=stories&story=${id}"><span>${String(i+1).padStart(2,'0')}</span>${titles[i]}<b aria-hidden="true">↓</b></a>`).join('')}</nav>`;
    const common=`<p>対象は収録データの男子T20I。ワイド・ノーボールを含む記録投球を使い、有効球数とは区別しています。球単位の集計であり、試合ごとの平均ではありません。</p>`;
    const stories=[];
    const boundaryHeading=boundaryTitle.split('、').map((part,i)=>`<span class="title-clause">${escape(part)}${i===0?'、':''}</span>`).join('');
    stories.push(article('boundaries',1,boundaryHeading,
      `FOURとSIXが生まれたのは、全投球の<strong>${percent(h.boundary_deliveries)}</strong>。その打者得点だけで、チーム合計得点の<strong>${percent(h.boundary_points)}</strong>に達します。`,
      'chart-boundaries','上段の分母は球数、下段の分母は得点。二つの棒は異なるものの構成を示しています。',
      `<p>クリケットでは、地面に触れてから境界に届く一打はFOUR、地面に触れずに境界を越える一打はSIXになります。4点・6点を一度に得られるため、少ない球数でも得点への寄与は大きくなります。</p><p>このデータでは、バウンダリー（FOUR・SIX）は<strong>${number(h.boundary_deliveries.numerator)}球</strong>。そこから生まれた打者得点は<strong>${number(h.boundary_points.numerator)}点</strong>です。一方、走って重ねる1点や2点、追加点も、残りの得点を支えています。</p>`,
      `${common}<p>球の割合＝(FOUR球数＋SIX球数)÷全記録投球。得点の割合＝(4×FOUR球数＋6×SIX球数)÷(打者得点＋extras)。バウンダリー（FOUR・SIX）と同時に生じたextrasは、得点側の分子へ加えていません。非バウンダリーの打者4点・6点も分子に含めません。</p>`,
      table(['構成','バウンダリー（FOUR・SIX）の分子','分母','割合'],[['記録投球',number(h.boundary_deliveries.numerator)+'球',number(h.boundary_deliveries.denominator)+'球',percent(h.boundary_deliveries)],['チーム得点',number(h.boundary_points.numerator)+'点',number(h.boundary_points.denominator)+'点',percent(h.boundary_points)]],'バウンダリー（FOUR・SIX）の球数と得点の寄与')));
    stories.push(article('middle',2,titles[1],
      `打者1点の球は、序盤の<strong>${percent(ps.early.metrics.single)}</strong>から中盤の<strong>${percent(ps.middle.metrics.single)}</strong>へ。試合の途中では、得点の重ね方が変わって見えます。`,
      'chart-middle','それぞれの局面の記録投球に対する割合。打者1点・FOUR・SIXは同じ分母で比較しています。',
      `<p>派手な一打だけが得点の取り方ではありません。打者が1点を得る球を積み重ねることも、攻撃を支えます。ここでの「打者1点」は追加点の有無を問いません。</p><p>中盤は、序盤よりFOUR率が<strong>${percent(ps.early.metrics.four)}から${percent(ps.middle.metrics.four)}</strong>へ下がります。一方、SIX率は<strong>${percent(ps.early.metrics.six)}から${percent(ps.middle.metrics.six)}</strong>へ。FOURとSIXをまとめるだけでは見えにくい違いです。</p><p>無得点の球も、序盤${percent(ps.early.metrics.zero)}、中盤${percent(ps.middle.metrics.zero)}、終盤${percent(ps.late.metrics.zero)}。打者2点の球は${percent(ps.early.metrics.double)}、${percent(ps.middle.metrics.double)}、${percent(ps.late.metrics.double)}と変わります。</p><aside class="story-rule"><b>守備配置も、試合の風景を変える。</b><p>標準20オーバー試合では、最初の6オーバーにPowerplayの守備制限があります。Middle・Deathはこのページの分析区分です。守備制限は背景の一つですが、この図だけで変化の原因を特定することはできません。</p><a href="${d.sources.rules.url}">ICC競技条件 28.7（2025年7月版） ↗</a></aside>`,
      `${common}<p>打者1点率＝runs_off_batが1の球数÷局面の全記録投球。FOUR・SIXはnon_boundary=trueを除きます。無得点は打者得点＋extras=0です。短縮試合も固定の1–6／7–15／16–20オーバーで分類しているため、実際のPowerplay期間と一致しない場合があります。球種、打球内容、選手の意図を測定した結果ではありません。</p>`,
      table(['局面','試合数','記録投球','打者1点','FOUR','SIX','無得点'],phases.map(ph=>[names[ph],number(ps[ph].match_count),number(ps[ph].delivery_count),percent(ps[ph].metrics.single),percent(ps[ph].metrics.four),percent(ps[ph].metrics.six),percent(ps[ph].metrics.zero)]),'局面別の得点結果')));
    stories.push(article('death',3,titles[2],
      `終盤のチーム得点は<strong>${decimal(ps.late.metrics.mean_runs)}点／記録投球</strong>。アウトを伴う球の割合は<strong>${percent(ps.late.metrics.out)}</strong>で、中盤の約<strong>${(value(ps.late.metrics.out)/value(ps.middle.metrics.out)).toFixed(2)}倍</strong>です。`,
      'chart-death','1〜20オーバーを同じ横軸で比較。上段は得点、下段はアウト率で、縦軸は分けています。各点の分母はそのオーバーの記録投球です。',
      `<p>残りの投球が少なくなると、得点を伸ばすことと、アウトで攻撃の機会を失うことの両方が気になります。終盤の記録には、得点とアウトがともに増える様子が表れています。</p><p>中盤から終盤にかけて、チーム得点は<strong>${decimal(ps.middle.metrics.mean_runs)}から${decimal(ps.late.metrics.mean_runs)}点／記録投球</strong>、アウト率は<strong>${percent(ps.middle.metrics.out)}から${percent(ps.late.metrics.out)}</strong>へ変化します。ただし、「積極的に打ったからアウトが増えた」と、この集計だけで断定することはできません。</p><p>後のオーバーまで進んだ試合だけが、後半の点を構成します。追走の早い終了、全員アウト、短縮・中断などによって、比較する母集団は変わります。</p>`,
      `${common}<p>平均得点＝そのオーバーのチーム合計得点÷そのオーバーの記録投球。アウト率＝少なくとも1件のアウトを伴う球数÷同じ分母。アウトイベント件数ではありません。後半まで進んだ試合の選択、先攻・後攻、年代、会場、チーム力などの影響は取り除いていません。</p>`,
      table(['オーバー','試合数','記録投球','チーム得点','点／記録投球','アウト球数','アウト率'],d.overs.map(r=>[r.over,number(r.match_count),number(r.delivery_count),number(r.team_runs),decimal(r.metrics.mean_runs),number(r.out_deliveries),percent(r.metrics.out)]),'オーバー別の得点とアウト')));
    const other=h.runout_among_score_out.denominator-h.runout_among_score_out.numerator;
    stories.push(article('score-out',4,titles[3],
      `得点とアウトが同時に記録されたのは<strong>${number(h.score_out.numerator)}球</strong>、全体の<strong>${percent(h.score_out,4)}</strong>。そのうち<strong>${percent(h.runout_among_score_out)}</strong>がRun outを含む球でした。`,
      'chart-score-out','この棒の分母は「得点とアウトが同時に起きた球」。全投球を分母とする上の割合とは区別しています。',
      `<p>1点を取り、その後でもう1点を狙っている途中にアウトになる。クリケットでは、得点とアウトは一球の中で重なることがあります。Run outでは、ウィケットが倒される前に完了した得点が認められる場合があります。</p><p>実際に「通常投球 → 打者1点 → Run out」という経路は<strong>${number(d.runout_single_example_count)}球</strong>ありました。ただしCSVだけから、そのすべてで「2点目を狙った」とまでは分かりません。</p><p>同時発生の${number(h.score_out.numerator)}球のうち、Run outを含む球は${number(h.runout_among_score_out.numerator)}球。それ以外も<strong>${number(other)}球</strong>あり、追加点とStumpedなどの組合せが含まれます。</p><aside class="story-rule"><b>「得点した」と「アウトになった」は両立する。</b><p>得点とアウトを排他的な結果にすると、この競技の一面が消えてしまいます。サンキーでは、その両方を同じ一球の経路としてたどれます。</p><a href="${d.sources.rules.url}">ICC競技条件 18.8.2（2025年7月版） ↗</a></aside>`,
      `${common}<p>同時発生＝チーム合計得点が正、かつアウトイベントが1件以上ある記録投球。retired hurt／retired not outはアウトに含めません。構成比は「Run outを含む球」と「それ以外の球」に分け、複数イベントも一球として計上します。参照する競技条件は背景説明であり、過去の全投球を現在の規則で再判定したものではありません。</p>`,
      table(['区分','球数','分母','割合'],[['得点＋アウト',number(h.score_out.numerator),number(h.score_out.denominator),percent(h.score_out,4)],['うちRun outを含む',number(h.runout_among_score_out.numerator),number(h.runout_among_score_out.denominator),percent(h.runout_among_score_out)],['うちその他',number(other),number(h.runout_among_score_out.denominator),percent({numerator:other,denominator:h.runout_among_score_out.denominator})]],'得点とアウトの同時発生')));
    const control=d.cohorts.both_innings_reach_over20;
    const sensitivity=`<section class="story-quality"><p class="eyebrow">READING THE EVIDENCE</p><h2>比べるときに、覚えておきたいこと。</h2><p>各局面に同じ試合が同じ数だけ含まれているわけではありません。終盤に記録があるのは、先攻${number(d.cohorts.innings_1.late.match_count)}試合、後攻${number(d.cohorts.innings_2.late.match_count)}試合。後攻の追走が早く終わることなども、後半の母集団に影響します。</p><details class="story-method"><summary>比較条件を変えた確認と、データの制約</summary><div><p>target_oversが20未満の試合は${number(d.quality.reduced_target_overs_matches)}、D/Lは${number(d.quality.method_counts['D/L']||0)}、Awardedは${number(d.quality.method_counts.Awarded||0)}。条件は重なります。第2イニングの記録がない試合は${number(d.quality.no_second_innings)}あります。</p><p>短縮・特殊決着の記録を除き、両イニングが第20オーバーまで進んだ${number(control.all.match_count)}試合に絞った結果です。「20オーバーを完投した」と同じ意味ではありません。</p><div class="story-table-scroll"><table><thead><tr><th>局面</th><th>対象球数</th><th>アウト率</th><th>打者1点率</th></tr></thead><tbody>${phases.map(ph=>`<tr><th scope="row">${short[ph]}</th><td>${number(control[ph].delivery_count)}</td><td>${percent(control[ph].metrics.out)}</td><td>${percent(control[ph].metrics.single)}</td></tr>`).join('')}</tbody></table></div><p>主要な傾向はこの条件でも残りますが、この絞り込み自体にも選択の偏りがあります。年代、会場、チーム力、当時の規則差などをすべて調整した分析ではありません。観測された関係から因果関係を断定せず、収録データの発見として読んでください。</p></div></details></section>`;
    $('#stories-content').innerHTML=intro+stories.join('')+sensitivity;
    renderCharts();
  }
  function canvas(id,title,height) {
    const host=document.getElementById(id);host.replaceChildren();
    const width=Math.max(270,Math.floor(host.clientWidth));
    const svg=d3.select(host).append('svg').attr('viewBox',`0 0 ${width} ${height}`).attr('role','group').attr('aria-label',title);
    svg.append('title').text(title);
    return {svg,width,host};
  }
  function inspect(selection,describe,host) {
    const show=(_,datum)=>{host.closest('figure').querySelector('.chart-insight').textContent=describe(datum);};
    selection.attr('tabindex',0).attr('role','button').attr('aria-label',describe)
      .on('pointerenter',show).on('focus',show).on('click',show)
      .on('keydown',(event,datum)=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();show(event,datum);}});
  }
  function composition(id,rows,title) {
    const {svg,width,host}=canvas(id,title,rows.length*112+10),barWidth=width-4;
    rows.forEach((row,i)=>{
      const y=i*112;
      svg.append('text').attr('class','plot-label').attr('x',0).attr('y',y+20).text(row.label);
      svg.append('text').attr('class','plot-value').attr('x',width).attr('y',y+20).attr('text-anchor','end').text(percent(row.metric));
      svg.append('rect').attr('x',0).attr('y',y+34).attr('width',barWidth).attr('height',24).attr('fill',colors.paper);
      const mark=svg.append('rect').datum(row).attr('x',0).attr('y',y+34).attr('width',barWidth*(value(row.metric)||0)).attr('height',24).attr('fill',colors.teal).attr('data-numerator',row.metric.numerator).attr('data-denominator',row.metric.denominator);
      inspect(mark,r=>`${r.label}：${number(r.metric.numerator)}${r.unit} ／ ${number(r.metric.denominator)}${r.unit}、${percent(r.metric)}`,host);
      svg.append('text').attr('class','plot-note').attr('x',0).attr('y',y+82).text(`分母 ${number(row.metric.denominator)}${row.unit} ／ 青緑：${row.highlight}`);
    });
  }
  function middleChart() {
    const {svg,width,host}=canvas('chart-middle','局面別の打者1点・FOUR・SIX率',414);
    const types=[['single','打者1点',colors.teal],['four','FOUR',colors.gold],['six','SIX',colors.red]];
    const x=d3.scaleLinear().domain([0,.5]).range([62,width-58]);
    svg.append('g').attr('class','plot-grid').attr('transform','translate(0,380)').call(d3.axisBottom(x).tickValues([0,.1,.2,.3,.4,.5]).tickFormat(n=>Math.round(n*100)+'%').tickSize(-355));
    phases.forEach((ph,i)=>{
      const y=22+i*122;
      svg.append('text').attr('class','plot-phase').attr('x',0).attr('y',y).text(names[ph]);
      types.forEach(([key,label,color],j)=>{
        const metric=content.phases[ph].metrics[key],row=y+17+j*26;
        svg.append('text').attr('class','plot-label').attr('x',0).attr('y',row+11).text(label);
        const mark=svg.append('rect').datum({ph,label,metric}).attr('x',x(0)).attr('y',row).attr('width',x(value(metric)||0)-x(0)).attr('height',15).attr('fill',color).attr('data-numerator',metric.numerator).attr('data-denominator',metric.denominator);
        inspect(mark,d=>`${names[d.ph]}・${d.label}：${number(d.metric.numerator)}球 ／ ${number(d.metric.denominator)}球、${percent(d.metric)}`,host);
        svg.append('text').attr('class','plot-note').attr('x',x(value(metric)||0)+6).attr('y',row+12).text(percent(metric));
      });
    });
  }
  function deathChart() {
    const {svg,width,host}=canvas('chart-death','オーバー別の平均得点とアウト率',410);
    const x=d3.scaleLinear().domain([1,20]).range([44,width-20]);
    for(const [index,key,label,color] of [[0,'mean_runs','チーム得点（点／記録投球）',colors.teal],[1,'out','アウトを伴った球（%）',colors.red]]){
      const top=36+index*205,bottom=top+132;
      const topValue=d3.max(content.overs,r=>value(r.metrics[key]))||1;
      const y=d3.scaleLinear().domain([0,topValue*1.16]).nice().range([bottom,top]);
      for(const [a,b] of [[1,6.5],[6.5,15.5],[15.5,20]])svg.append('rect').attr('x',x(a)).attr('y',top).attr('width',x(b)-x(a)).attr('height',bottom-top).attr('fill',a===6.5?'#e5ded0':'#eee8dc');
      if(index===0)for(const [over,label] of [[3.75,'序盤'],[11,'中盤'],[17.75,'終盤']])svg.append('text').attr('class','plot-note').attr('x',x(over)).attr('y',top+15).attr('text-anchor','middle').text(label);
      svg.append('text').attr('class','plot-phase').attr('x',0).attr('y',top-14).text(label);
      svg.append('g').attr('class','plot-grid').attr('transform',`translate(44,0)`).call(d3.axisLeft(y).ticks(3).tickFormat(n=>key==='out'?Math.round(n*100)+'%':n.toFixed(1)).tickSize(-(width-64)));
      svg.append('g').attr('class','plot-axis').attr('transform',`translate(0,${bottom})`).call(d3.axisBottom(x).tickValues([1,5,10,15,20]).tickFormat(n=>n));
      svg.append('path').datum(content.overs).attr('class','story-trend-line').attr('fill','none').attr('stroke',color).attr('stroke-width',2).attr('d',d3.line().x(r=>x(r.over)).y(r=>y(value(r.metrics[key])||0)));
      const marks=svg.append('g').selectAll('circle').data(content.overs).join('circle').attr('cx',r=>x(r.over)).attr('cy',r=>y(value(r.metrics[key])||0)).attr('r',3.5).attr('fill',color).attr('stroke','transparent').attr('stroke-width',16).style('pointer-events','all').attr('data-numerator',r=>r.metrics[key].numerator).attr('data-denominator',r=>r.metrics[key].denominator);
      inspect(marks,r=>`第${r.over}オーバー・${label}：${key==='out'?percent(r.metrics[key]):decimal(r.metrics[key])+'点／記録投球'}。分子 ${number(r.metrics[key].numerator)}${key==='out'?'球':'点'}、分母 ${number(r.delivery_count)}記録投球、${number(r.match_count)}試合。`,host);
      svg.append('text').attr('class','plot-note').attr('x',width-20).attr('y',bottom+35).attr('text-anchor','end').text('オーバー');
    }
  }
  function scoreOutChart() {
    const h=content.highlights.runout_among_score_out;
    const {svg,width,host}=canvas('chart-score-out','得点とアウトが同時に起きた球の内訳',175);
    const split=(width-4)*(value(h)||0);
    const rows=[{label:'Run outを含む',n:h.numerator,x:0,w:split,color:colors.teal},{label:'それ以外',n:h.denominator-h.numerator,x:split,w:width-4-split,color:colors.gold}];
    svg.append('text').attr('class','plot-label').attr('x',0).attr('y',22).text('得点＋アウトの球の内訳');
    const marks=svg.append('g').selectAll('rect').data(rows).join('rect').attr('x',r=>r.x).attr('y',40).attr('width',r=>r.w).attr('height',27).attr('fill',r=>r.color).attr('data-numerator',r=>r.n).attr('data-denominator',h.denominator);
    inspect(marks,r=>`${r.label}：${number(r.n)}球 ／ ${number(h.denominator)}球、${percent({numerator:r.n,denominator:h.denominator})}`,host);
    rows.forEach((r,i)=>{
      svg.append('rect').attr('x',0).attr('y',91+i*33).attr('width',8).attr('height',8).attr('fill',r.color);
      svg.append('text').attr('class','plot-label').attr('x',16).attr('y',100+i*33).text(`${r.label}　${number(r.n)}球`);
      svg.append('text').attr('class','plot-value').attr('x',width).attr('y',100+i*33).attr('text-anchor','end').text(percent({numerator:r.n,denominator:h.denominator}));
    });
  }
  function renderCharts() {
    if(!content||$('#stories').hidden)return;
    composition('chart-boundaries',[
      {label:'記録投球のうちバウンダリー（FOUR・SIX）',metric:content.highlights.boundary_deliveries,unit:'球',highlight:'FOUR・SIXの球'},
      {label:'チーム得点のうちバウンダリーによる打者点',metric:content.highlights.boundary_points,unit:'点',highlight:'バウンダリーの打者点'}
    ],'バウンダリー（FOUR・SIX）の球数と得点への寄与');
    middleChart();deathChart();scoreOutChart();
  }
  function ensure() {
    if(content){renderCharts();return Promise.resolve(true);}
    if(loading)return loading;
    loading=fetch('data/one-ball-stories.json').then(r=>{if(!r.ok)throw new Error('記事データを取得できませんでした。');return r.json();}).then(data=>{
      check(data,window.OneBallExplorer.getData());content=data;renderContent();
      $('#stories-status').hidden=true;document.body.dataset.storiesReady='true';
      window.oneBallStoriesData=content;
      return true;
    }).catch(error=>{
      $('#stories-status').hidden=false;$('#stories-status').classList.add('error');
      $('#stories-status').textContent=error.message+' 「図を見る」は引き続き利用できます。';
      return false;
    });
    return loading;
  }
  let timer;
  window.addEventListener('resize',()=>{clearTimeout(timer);timer=setTimeout(renderCharts,120);});
  window.OneBallStories={ensure,check};
})();
