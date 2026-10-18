(function () {
  'use strict';
  const S=window.CrittSankey, fmt=new Intl.NumberFormat('ja-JP');
  const colors={normal:'#0e6b69',noball:'#b18b38',wide:'#a92b2c'};
  const phaseNames={all:'全体',early:'序盤 Powerplay（1–6）',middle:'中盤 Middle（7–15）',late:'終盤 Death（16–20）'};
  const titles={all:'一球を、たどる。',early:'試合の始まり、その一球。',middle:'流れをつくる、その一球。',late:'勝負を決める、その一球。'};
  const eventNames={'bowled':'Bowled','caught':'Caught','caught and bowled':'Caught and bowled','lbw':'LBW','run out':'Run out','stumped':'Stumped','retired hurt':'retired hurt（非アウト退場）','retired not out':'retired not out（非アウト退場）','retired out':'retired out（アウト）','hit wicket':'Hit wicket','obstructing the field':'Obstructing the field','hit the ball twice':'Hit the ball twice'};
  const extraNames={wides:'ワイド',noballs:'ノーボール',byes:'バイ',legbyes:'レッグバイ',penalty:'ペナルティ'};
  let data, phase='all', expanded=false, selected=null, geometry=null, waitForPointerMove=false;
  const $=s=>document.querySelector(s), number=x=>fmt.format(x), percent=(n,d)=>d?(100*n/d).toFixed(n>0&&100*n/d<.01?4:2)+'%':'—';
  const escape=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const pathName=p=>['全投球',S.labels[p.delivery_type],S.labels[p.run_outcome],S.labels[p.dismissal_outcome]].join(' → ');
  function metrics() {
    const ph=data.phases[phase];
    const rows=[['対象試合数',number(ph.match_count),'試合'],['記録投球件数',number(ph.delivery_count),'球'],['無得点率',percent(ph.metrics.zero.numerator,ph.delivery_count),''],['FOUR＋SIX率',percent(ph.metrics.boundary.numerator,ph.delivery_count),''],['アウトを伴った投球率',percent(ph.metrics.out.numerator,ph.delivery_count),'']];
    $('#metrics').innerHTML=rows.map(([label,value,unit])=>`<div class="metric"><span class="metric-label">${label}</span><span class="metric-value">${value}<span class="metric-unit">${unit}</span></span></div>`).join('');
    $('#phase-title').textContent=titles[phase];
    $('#phase-panel').setAttribute('aria-labelledby','tab-'+phase);
    document.querySelectorAll('#phase-tabs [role=tab]').forEach(b=>{const yes=b.dataset.phase===phase;b.setAttribute('aria-selected',yes);b.tabIndex=yes?0:-1;});
  }
  function details(p) {
    if (!p) {
      $('#detail-content').innerHTML='<h3 id="detail-title">気になる帯を、ひとつ。</h3><p>ホバー、タップ、または一覧から選ぶと、得点の内訳とアウトの種類が分かります。</p><p>例えば、点が入りながらアウトになる球。ノーボールに重なるFOUR。どれも、一球の道です。</p>';
      return;
    }
    const totals=Object.fromEntries(Object.keys(extraNames).map(k=>[k,0]));
    const distributions={bat:{},extras:{},team_total:{}};
    p.score_variants.forEach(v=>{
      Object.keys(extraNames).forEach(k=>totals[k]+=v.extras_breakdown[k]*v.count);
      Object.keys(distributions).forEach(k=>distributions[k][v[k]]=(distributions[k][v[k]]||0)+v.count);
    });
    const distribution=k=>Object.entries(distributions[k]).map(([runs,count])=>`${runs}点：${number(count)}球`).join(' ／ ');
    const extras=Object.entries(totals).filter(([,n])=>n).map(([k,n])=>`${extraNames[k]} ${number(n)}点`).join(' ／ ')||'なし';
    const events=Object.entries(p.event_counts).map(([k,n])=>`${eventNames[k]||k} ${number(n)}件`).join(' ／ ')||'なし';
    const nonBoundary=p.score_variants.filter(v=>v.non_boundary).reduce((n,v)=>n+v.count,0);
    $('#detail-content').innerHTML=`<h3 id="detail-title">${escape(pathName(p))}</h3>
      <p><strong class="path-count">${number(p.count)}</strong>球 ／ ${escape(phaseNames[phase])} ${number(data.phases[phase].delivery_count)}球中 <b>${percent(p.count,data.phases[phase].delivery_count)}</b></p>
      <div class="score-totals"><div><span>打者得点の累積</span><b>${number(p.bat_runs)}</b> 点</div><div><span>エクストラの累積</span><b>${number(p.extra_runs)}</b> 点</div><div><span>チーム合計得点の累積</span><b>${number(p.team_runs)}</b> 点</div></div>
      <p>一球ごとの打者得点：${distribution('bat')}<br>一球ごとのエクストラ：${distribution('extras')}<br>一球ごとのチーム合計：${distribution('team_total')}</p>
      <p>エクストラ内訳（累積）：${extras}</p><p class="event-note">アウト・退場：${escape(events)}<br>アウトを伴った球 ${number(p.out_deliveries)}球 ／ アウトイベント ${number(p.out_events)}件</p>
      <p>非バウンダリー指定：${number(nonBoundary)}球${nonBoundary?'（打者4点・6点などの元の点数を下表に保持）':''}</p>
      <details><summary>得点とイベントの組合せを見る（${number(p.score_variants.length)}種類）</summary><div class="table-scroll"><table><thead><tr><th>打者</th><th>extras</th><th>チーム合計</th><th>非バウンダリー</th><th>イベント</th><th>球数</th></tr></thead><tbody>${p.score_variants.map(v=>`<tr><td>${v.bat}点</td><td>${v.extras}点</td><td>${v.team_total}点</td><td>${v.non_boundary?'指定あり':'指定なし'}</td><td>${escape(v.events.map(e=>eventNames[e]||e).join(' ＋ ')||'なし')}</td><td>${number(v.count)}</td></tr>`).join('')}</tbody></table></div></details>`;
  }
  function select(id) {
    selected=id||null;
    const chosen=S.selectedRoutes(geometry.routes,selected);
    if (selected && chosen.length!==1) throw new Error('Selection must resolve to exactly one complete path');
    d3.selectAll('.route').classed('is-selected',d=>d.id===selected).classed('is-muted',d=>!!selected&&d.id!==selected);
    // Point markers locate subpixel paths without exaggerating their count-scaled width.
    const markers=chosen.flatMap(r=>[{x:r.total.x1,y:r.totalY},{x:(r.left.x0+r.left.x1)/2,y:r.leftY},{x:(r.middle.x0+r.middle.x1)/2,y:r.middleY},{x:r.right.x0,y:r.rightY}]);
    d3.select('#selection-markers').selectAll('circle').data(markers).join('circle').attr('cx',d=>d.x).attr('cy',d=>d.y).attr('r',3);
    d3.selectAll('.route-hit').attr('aria-pressed',d=>d.id===selected?'true':'false');
    $('#path-picker').value=selected||'';
    details(chosen[0]?.path);
    window.oneBallState.selectedPathId=selected;
  }
  function render() {
    const ph=data.phases[phase];
    const width=Math.max(1120,$('.chart-inner').clientWidth);
    geometry=S.layout(ph.paths,{width,height:660,expanded});
    const svg=d3.select('#sankey').attr('viewBox',`0 0 ${width} 660`);
    document.querySelectorAll('.column-heads>div').forEach((el,i)=>{el.style.left=(geometry.columnX?.[i]??0)+8+'px';});
    svg.selectAll('*').remove();
    svg.append('title').text(`${phaseNames[phase]}：${number(ph.delivery_count)}球のゆくえ`);
    svg.append('desc').text('全投球から投球種類、得点、アウトまでをたどる4列の図。帯は投球種類ごとに色分けされ、両中間ノードで同じ幅と高さを保ちます。FOURと4ラン、SIXと6ランは非バウンダリー指定で区別しています。一覧からも選択できます。');
    svg.append('g').selectAll('rect').data(geometry.nodes).join('rect').attr('class',n=>'node-rect'+([1,2].includes(n.col)?' middle':''))
      .attr('x',n=>n.x0).attr('y',n=>n.y0).attr('width',n=>n.x1-n.x0).attr('height',n=>n.y1-n.y0);
    const routes=geometry.routes.slice().sort((a,b)=>b.count-a.count);
    const painted=svg.append('g').attr('class','painted-routes');
    for (const segment of [0,1,2,3,4]) {
      painted.selectAll(`.segment-${segment}`).data(routes).join('path').attr('class',`route segment-${segment}`)
        .attr('data-path-id',r=>r.id).attr('data-segment',segment)
        .attr('d',r=>r.paintPaths[segment]).attr('stroke',r=>colors[r.path.delivery_type])
        .attr('stroke-width',r=>r.width).style('pointer-events','none');
    }
    const hits=svg.append('g');
    for (const segment of [0,1,2,3,4]) {
      hits.selectAll(`.hit-${segment}`).data(routes).join('path').attr('class',`route-hit hit-${segment}`)
        .attr('data-path-id',r=>r.id).attr('d',r=>r.paintPaths[segment])
        .style('stroke-width',r=>Math.max(9,r.width)).attr('tabindex',segment===0?0:null).attr('role','button')
        .attr('aria-label',r=>`${pathName(r.path)}、${number(r.count)}球、${percent(r.count,ph.delivery_count)}`)
        .on('pointerenter',(_,r)=>{if(!waitForPointerMove)select(r.id);})
        .on('pointermove',(_,r)=>{if(waitForPointerMove){waitForPointerMove=false;select(r.id);}})
        .on('click',(_,r)=>{waitForPointerMove=false;select(r.id);window.OneBallModes.rememberExplorer();}).on('focus',(_,r)=>select(r.id))
        .on('keydown',(e,r)=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();select(r.id);window.OneBallModes.rememberExplorer();}if(e.key==='Escape'){select(null);window.OneBallModes.rememberExplorer();}});
    }
    const labels=svg.append('g').style('pointer-events','none').selectAll('g').data(geometry.nodes).join('g')
      .attr('class','node-annotation').attr('data-node-id',n=>n.id)
      .attr('aria-label',n=>`${n.label}、${number(n.count)}球、${phaseNames[phase]}の全${number(ph.delivery_count)}球に対して${percent(n.count,ph.delivery_count)}`);
    labels.append('path').attr('class','leader').attr('d',n=>{
      const x=n.col<2?n.x0-8:n.x1+8, x2=n.col<2?n.x0:n.x1;
      return `M${x2},${(n.y0+n.y1)/2}L${x},${n.labelY}`;
    });
    labels.append('text').attr('class','node-label').attr('x',n=>n.col<2?n.x0-13:n.x1+13)
      .attr('y',n=>n.labelY-(n.col===0?12:4)).attr('text-anchor',n=>n.col<2?'end':'start').text(n=>n.label);
    const countLabels=labels.append('text').attr('class','node-count').attr('x',n=>n.col<2?n.x0-13:n.x1+13)
      .attr('y',n=>n.labelY+(n.col===0?4:12)).attr('text-anchor',n=>n.col<2?'end':'start').text(n=>number(n.count)+' 球');
    countLabels.filter(n=>n.col!==0).append('tspan').attr('class','node-percentage').text(n=>' · '+percent(n.count,ph.delivery_count));
    labels.filter(n=>n.col===0).append('text').attr('class','node-percentage').attr('x',n=>n.x0-13)
      .attr('y',n=>n.labelY+20).attr('text-anchor','end').text(n=>percent(n.count,ph.delivery_count));
    svg.append('g').attr('id','selection-markers').attr('aria-hidden','true').style('pointer-events','none');
    const ordered=ph.paths.slice().sort((a,b)=>S.deliveryOrder.indexOf(a.delivery_type)-S.deliveryOrder.indexOf(b.delivery_type)||S.runOrder.indexOf(a.run_outcome)-S.runOrder.indexOf(b.run_outcome)||b.count-a.count);
    $('#path-picker').innerHTML='<option value="">経路を選択…</option>'+ordered.map(p=>`<option value="${escape(p.path_id)}">${escape(pathName(p))} · ${number(p.count)}球</option>`).join('');
    window.oneBallState={phase,expanded,selectedPathId:selected,geometry,data,validation:geometry.validation};
    select(selected&&ph.paths.some(p=>p.path_id===selected)?selected:null);
  }
  document.querySelectorAll('#phase-tabs [role=tab]').forEach(b=>{
    b.addEventListener('click',()=>{phase=b.dataset.phase;selected=null;metrics();render();window.OneBallModes.rememberExplorer({push:true});});
    b.addEventListener('keydown',e=>{
      const keys=['ArrowLeft','ArrowRight','Home','End'];if(!keys.includes(e.key))return;
      e.preventDefault();const tabs=[...document.querySelectorAll('#phase-tabs [role=tab]')],i=tabs.indexOf(b);
      const next=e.key==='Home'?0:e.key==='End'?3:(i+(e.key==='ArrowRight'?1:3))%4;
      tabs[next].focus();tabs[next].click();
    });
  });
  $('#expand-outs').addEventListener('change',e=>{expanded=e.target.checked;render();window.OneBallModes.rememberExplorer();});
  $('#path-picker').addEventListener('change',e=>{select(e.target.value);window.OneBallModes.rememberExplorer();});
  $('#reset-selection').addEventListener('click',()=>{select(null);window.OneBallModes.rememberExplorer();});
  let timer;window.addEventListener('resize',()=>{clearTimeout(timer);timer=setTimeout(()=>{if(data&&!$('#explore').hidden)render();},100);});

  window.OneBallExplorer={
    isReady:()=>Boolean(data),getData:()=>data,
    snapshot:()=>({phase,path:selected,expanded}),
    open(options={}) {
      if(!data)return;
      // Revealing/scrolling the panel can place a different band beneath a stationary
      // pointer. Keep the requested path until the reader actually moves or selects.
      waitForPointerMove=true;
      phase=Object.hasOwn(data.phases,options.phase)?options.phase:'all';
      selected=options.path&&data.phases[phase].paths.some(p=>p.path_id===options.path)?options.path:null;
      expanded=options.expanded===undefined?Boolean(selected?.includes('|out:')):Boolean(options.expanded);
      $('#expand-outs').checked=expanded;
      metrics();
      if(!$('#explore').hidden)render();
    }
  };
  fetch('data/one-ball-sankey.json').then(r=>{if(!r.ok)throw new Error('HTTP '+r.status);return r.json();}).then(value=>{
    if(value.schema_version!==2)throw new Error('Unsupported data schema');data=value;
    $('#load-status').hidden=true;$('#explore').hidden=false;
    $('#provenance').innerHTML=`<p>対象：男子T20国際試合 ${number(data.match_count)}試合 ／ ${data.scope.date_from}〜${data.scope.date_to}<br>採用：${number(data.delivery_count)}記録投球 ／ 除外：${number(data.excluded_delivery_count)}記録投球（スーパーオーバー等）<br>集計生成日時：${escape(data.generated_at)}<br>警告：${data.warnings.length}件 ／ 試合単位の除外：${data.excluded_matches.length}件</p><p>添付ZIPのinfoファイルに記録されたバージョン申告値：${escape(Object.entries(data.format.declared_info_versions).map(([v,n])=>v+' / '+number(n)+'ファイル').join('、'))}。参照した公式仕様は${data.format.reference_spec_version}です。申告値と公式仕様の版は区別しています。</p>`;
    metrics();render();document.body.dataset.ready='true';document.dispatchEvent(new CustomEvent('oneball-ready'));
  }).catch(err=>{$('#load-status').hidden=false;$('#load-status').classList.add('error');$('#load-status').textContent='データを読み込めませんでした。ローカルHTTPサーバー経由で開き、集計JSONとライブラリを確認してください。';console.error(err);});
})();
