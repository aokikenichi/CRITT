(function () {
  'use strict';
  const modes=[...document.querySelectorAll('.mode-switch [role=tab]')];
  let active='explore', story='', lastExplorer={phase:'all',path:null,expanded:false};
  const explorer=()=>window.OneBallExplorer;
  function href(state) {
    const query=new URLSearchParams({mode:state.mode||active,phase:state.phase||lastExplorer.phase});
    if(state.path)query.set('path',state.path);
    if(state.story)query.set('story',state.story);
    return '#'+query.toString();
  }
  function parse() {
    const q=new URLSearchParams(location.hash.slice(1));
    return {mode:q.get('mode')==='stories'?'stories':'explore',phase:q.get('phase')||'all',path:q.get('path')||null,story:q.get('story')||''};
  }
  async function apply({scroll=false}={}) {
    if(!explorer()?.isReady())return;
    const state=parse();active=state.mode;story=state.story;
    document.querySelector('#explore').hidden=active!=='explore';
    document.querySelector('#stories').hidden=active!=='stories';
    document.querySelector('.reading').hidden=active==='stories';
    modes.forEach(button=>{const selected=button.dataset.mode===active;button.setAttribute('aria-selected',selected);button.tabIndex=selected?0:-1;});
    // A visible panel must be measured before the original Sankey renderer runs.
    const revealOut=state.path!==lastExplorer.path&&state.path?.includes('|out:');
    explorer().open({phase:state.phase,path:state.path,expanded:revealOut||lastExplorer.expanded});
    lastExplorer=explorer().snapshot();
    if(active==='stories') {
      await window.OneBallStories.ensure();
      if(active!=='stories')return;
      const target=story?document.getElementById('story-'+story):document.getElementById('stories-intro');
      if(target&&scroll){target.scrollIntoView({block:'start'});target.querySelector('h2')?.focus({preventScroll:true});}
    } else if(scroll) {
      document.getElementById('explore').scrollIntoView({block:'start'});
      document.getElementById('phase-title').focus({preventScroll:true});
    }
    document.body.dataset.mode=active;
  }
  function navigate(state,{replace=false,scroll=true}={}) {
    if(explorer()?.isReady()&&active==='explore')lastExplorer=explorer().snapshot();
    const next={mode:active,story,...lastExplorer,...state};
    history[replace?'replaceState':'pushState'](null,'',href(next));
    return apply({scroll});
  }
  function rememberExplorer({push=false}={}) {
    if(active!=='explore'||!explorer()?.isReady())return;
    lastExplorer=explorer().snapshot();
    history[push?'pushState':'replaceState'](null,'',href({mode:active,story,...lastExplorer}));
  }
  modes.forEach((button,index)=>{
    button.addEventListener('click',()=>navigate({mode:button.dataset.mode},{scroll:false}));
    button.addEventListener('keydown',event=>{
      if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
      event.preventDefault();const next=event.key==='Home'?0:event.key==='End'?1:1-index;
      modes[next].focus();modes[next].click();
    });
  });
  document.addEventListener('click',event=>{
    const link=event.target.closest('a[data-oneball-link]');
    if(!link||event.ctrlKey||event.metaKey||event.shiftKey||event.altKey||event.button)return;
    event.preventDefault();
    const q=new URLSearchParams(link.hash.slice(1));
    const next={mode:q.get('mode'),phase:q.get('phase')||lastExplorer.phase,story:q.get('story')||story};
    if(q.has('path'))next.path=q.get('path');
    navigate(next);
  });
  window.addEventListener('hashchange',()=>apply({scroll:true}));
  window.addEventListener('popstate',()=>apply({scroll:true}));
  document.addEventListener('oneball-ready',()=>apply({scroll:Boolean(location.hash)}));
  window.OneBallModes={navigate,rememberExplorer,href,getMode:()=>active};
})();
