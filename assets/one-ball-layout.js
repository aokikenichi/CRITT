/* Complete-path layout: d3-sankey places nodes; paired lane offsets retain identity. */
(function (root) {
  'use strict';
  const deliveryOrder = ['normal', 'noball', 'wide'];
  const runOrder = ['zero', 'one', 'two', 'three', 'four', 'four_non_boundary', 'six', 'six_non_boundary', 'other', 'extras'];
  const endOrder = ['none', 'out', 'out:bowled', 'out:caught', 'out:lbw', 'out:run_out', 'out:stumped', 'out:other', 'retirement', 'multiple'];
  const labels = {total:'全投球', normal:'通常投球', noball:'ノーボール', wide:'ワイド', zero:'無得点', one:'打者1点', two:'打者2点', three:'打者3点', four:'FOUR（4点）', four_non_boundary:'4ラン（非バウンダリー）', six:'SIX（6点）', six_non_boundary:'6ラン（非バウンダリー）', other:'その他の打者得点', extras:'エクストラのみ', none:'アウトなし', out:'アウトあり', 'out:bowled':'Bowled', 'out:caught':'Caught', 'out:lbw':'LBW', 'out:run_out':'Run out', 'out:stumped':'Stumped', 'out:other':'その他のアウト', retirement:'退場（アウトではない）', multiple:'複数イベント'};
  function endpoint(p, expanded) {
    return !expanded && p.dismissal_outcome.startsWith('out:') ? 'out' : p.dismissal_outcome;
  }
  function graphFor(paths, expanded) {
    const nodes = new Map(), links = new Map();
    for (const p of paths) {
      const keys = ['total', p.delivery_type, p.run_outcome, endpoint(p, expanded)];
      const ids = keys.map((key, col) => col + ':' + key);
      keys.forEach((key, col) => {
        if (!nodes.has(ids[col])) nodes.set(ids[col], {id:ids[col], key, col, label:labels[key], count:0,
          order:[['total'],deliveryOrder,runOrder,endOrder][col].indexOf(key)});
        nodes.get(ids[col]).count += p.count;
      });
      for (let segment = 0; segment < 3; segment++) {
        const key = ids[segment] + '>' + ids[segment + 1];
        if (!links.has(key)) links.set(key, {source:ids[segment], target:ids[segment+1], value:0});
        links.get(key).value += p.count;
      }
    }
    return {nodes:[...nodes.values()], links:[...links.values()]};
  }
  function labelsFor(nodes, top, bottom) {
    const labelGap = 38; // Name, then count + percentage. The single root uses three lines.
    for (let col = 0; col < 4; col++) {
      const column = nodes.filter(n => n.col === col).sort((a,b) => a.y0-b.y0);
      let last = top - labelGap;
      for (const n of column) {
        n.labelY = Math.max((n.y0+n.y1)/2, last+labelGap);
        last = n.labelY;
      }
      if (last > bottom) {
        last = bottom + labelGap;
        for (const n of column.slice().reverse()) {
          n.labelY = Math.min(n.labelY, last-labelGap);
          last = n.labelY;
        }
      }
    }
  }
  function layout(paths, {width=1180, height=660, expanded=false} = {}) {
    if (!paths.length) return {nodes:[], routes:[], width, height, ky:0, validation:{passed:true, routes:0}};
    const graph = graphFor(paths, expanded);
    const sankey = root.d3.sankey().nodeId(n=>n.id).nodeAlign(n=>n.col)
      .nodeWidth(16).nodePadding(28).nodeSort((a,b)=>a.order-b.order)
      .extent([[98,22],[width-176,height-28]]).iterations(32);
    sankey(graph);
    // Short introduction, then two generous spans for score and dismissal flows.
    const span=width-176-98;
    const columnX=[98,98+span*.20,98+span*.60,width-176];
    for (const n of graph.nodes) {n.x0=columnX[n.col];n.x1=n.x0+16;}
    const nodes = new Map(graph.nodes.map(n=>[n.id,n]));
    const ky = graph.links[0].width / graph.links[0].value;
    const routes = paths.map(p=>({path:p, id:p.path_id, count:p.count, width:p.count*ky,
      total:nodes.get('0:total'), left:nodes.get('1:'+p.delivery_type), middle:nodes.get('2:'+p.run_outcome), right:nodes.get('3:'+endpoint(p,expanded))}));
    const compare = (a,b) => deliveryOrder.indexOf(a.path.delivery_type)-deliveryOrder.indexOf(b.path.delivery_type)
      || endOrder.indexOf(a.path.dismissal_outcome)-endOrder.indexOf(b.path.dismissal_outcome) || a.id.localeCompare(b.id);
    for (const n of graph.nodes.filter(n=>n.col===2)) {
      let y=n.y0;
      for (const r of routes.filter(r=>r.middle===n).sort(compare)) {
        r.middleY=y+r.width/2;
        // Shared slot for BOTH links: never let automatic source/target sorting mix origins.
        r.middleIn=[y,y+r.width]; r.middleOut=[y,y+r.width];
        y+=r.width;
      }
    }
    for (const col of [1,3]) {
      for (const n of graph.nodes.filter(n=>n.col===col)) {
        let y=n.y0;
        for (const r of routes.filter(r=>(col===1?r.left:r.right)===n).sort((a,b)=>a.middleY-b.middleY || compare(a,b))) {
          r[col===1?'leftY':'rightY']=y+r.width/2; y+=r.width;
        }
      }
    }
    let totalY=nodes.get('0:total').y0;
    for (const r of routes.slice().sort((a,b)=>a.leftY-b.leftY || compare(a,b))) {
      r.totalY=totalY+r.width/2;
      totalY+=r.width;
    }
    const link = root.d3.sankeyLinkHorizontal();
    for (const r of routes) {
      r.segments = [
        {path_id:r.id, value:r.count, width:r.width, source:r.total, target:r.left, y0:r.totalY, y1:r.leftY},
        {path_id:r.id, value:r.count, width:r.width, source:r.left, target:r.middle, y0:r.leftY, y1:r.middleY},
        {path_id:r.id, value:r.count, width:r.width, source:r.middle, target:r.right, y0:r.middleY, y1:r.rightY}
      ];
      r.paths=r.segments.map(link);
      r.bridge=`M${r.middle.x0},${r.middleY}L${r.middle.x1},${r.middleY}`;
      r.bridges=[`M${r.left.x0},${r.leftY}L${r.left.x1},${r.leftY}`,r.bridge];
      r.paintPaths=r.paths.concat(r.bridges);
    }
    labelsFor(graph.nodes, 32, height-38);
    const result={nodes:graph.nodes,routes,width,height,ky,columnX};
    result.validation=assertLayout(result);
    return result;
  }
  function assertLayout(result) {
    const ids = new Set();
    const close=(a,b)=>Math.abs(a-b)<1e-6;
    for (const r of result.routes) {
      if (ids.has(r.id)) throw new Error('Duplicate complete path');
      ids.add(r.id);
      if (![r.width,r.totalY,r.leftY,r.middleY,r.rightY].every(Number.isFinite) || r.width<=0) throw new Error('Invalid path geometry');
      if (!close(r.middleIn[0],r.middleOut[0]) || !close(r.middleIn[1],r.middleOut[1])) throw new Error('Broken middle lane');
      if (r.segments.some(s=>s.path_id!==r.id || s.value!==r.count || !close(s.width,r.width))) throw new Error('Mixed path identity');
      if (r.segments.length!==3) throw new Error('Missing total-delivery segment');
      for (let i=0;i<2;i++) {
        if (!close(r.segments[i].y1,r.segments[i+1].y0)) throw new Error('Discontinuous through-node lane');
      }
    }
    for (const n of result.nodes) {
      const routes=result.routes.filter(r=>[r.total,r.left,r.middle,r.right].includes(n));
      if (routes.reduce((v,r)=>v+r.count,0)!==n.count) throw new Error('Node count mismatch');
      const key=['totalY','leftY','middleY','rightY'][n.col];
      const ordered=routes.slice().sort((a,b)=>a[key]-b[key]);
      let y=n.y0;
      for (const r of ordered) {
        if (!close(y,r[key]-r.width/2)) throw new Error('Lane gap or overlap');
        y+=r.width;
      }
      if (!close(y,n.y1)) throw new Error('Lane width mismatch');
    }
    return {passed:true,routes:result.routes.length};
  }
  // Used by rendering and tests: selection only returns the exact complete path.
  function selectedRoutes(routes, id) { return routes.filter(r=>r.id===id); }
  root.CrittSankey={layout,graphFor,assertLayout,selectedRoutes,labels,deliveryOrder,runOrder,endOrder};
})(typeof globalThis !== 'undefined' ? globalThis : window);
