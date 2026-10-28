/* Reversible presentation/accessibility adapters. Recovered source bytes,
   shaders, artwork meshes and guide trajectories remain untouched. */
export function adaptRecoveredWork(doc, item, canvas) {
  const replace = text => text.replace(/原画/g, '参考画像（採用未承認）');
  function label(node) {
    if (node.nodeType === 3) {
      if (!node.parentElement?.closest('script,style') && node.data.includes('原画')) node.data = replace(node.data);
      return;
    }
    if (node.nodeType !== 1 || node.matches('script,style')) return;
    for (const attribute of ['alt', 'title', 'aria-label']) {
      if (node.hasAttribute(attribute) && node.getAttribute(attribute).includes('原画')) node.setAttribute(attribute, replace(node.getAttribute(attribute)));
    }
    for (const child of node.childNodes) label(child);
  }
  label(doc.body);
  new MutationObserver(records => {
    for (const record of records) {
      if (record.type === 'characterData') label(record.target);
      else if (record.type === 'attributes') label(record.target);
      else for (const node of record.addedNodes) label(node);
    }
  }).observe(doc.body, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ['alt', 'title', 'aria-label'] });

  canvas.tabIndex = 0;
  canvas.addEventListener('pointerdown', () => canvas.focus({ preventScroll: true }));

  function bindOverlay(overlayId, closeId, openClass) {
    const overlay = doc.getElementById(overlayId);
    const close = doc.getElementById(closeId);
    if (!overlay || !close) return;
    let wasOpen = false;
    let opener = null;
    let background = [];
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-label', '作品内の参考画像・作品情報');
    const update = () => {
      const open = overlay.classList.contains(openClass);
      if (open === wasOpen) return;
      wasOpen = open;
      if (open) {
        opener = doc.activeElement;
        background = [];
        let current = overlay;
        while (current.parentElement) {
          for (const sibling of current.parentElement.children) {
            if (sibling !== current && !sibling.matches('script,style')) {
              background.push([sibling, sibling.inert]);
              sibling.inert = true;
            }
          }
          current = current.parentElement;
          if (current === doc.body) break;
        }
        close.focus({ preventScroll: true });
      } else {
        for (const [sibling, inert] of background) sibling.inert = inert;
        background = [];
        (opener?.isConnected ? opener : canvas).focus({ preventScroll: true });
      }
    };
    new MutationObserver(update).observe(overlay, { attributes: true, attributeFilter: ['class'] });
    overlay.addEventListener('keydown', event => {
      if (event.key !== 'Tab') return;
      const controls = [...overlay.querySelectorAll('button,a[href],input,select,[tabindex="0"]')].filter(node => !node.disabled && node.getBoundingClientRect().width > 0);
      const first = controls[0] || close;
      const last = controls.at(-1) || close;
      if (event.shiftKey && doc.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && doc.activeElement === last) { event.preventDefault(); first.focus(); }
    });
    doc.addEventListener('keydown', event => {
      if (event.key === 'Escape' && overlay.classList.contains(openClass)) {
        event.crittInternalModal = true;
        close.click();
      }
    }, true);
  }

  if (item.id === '001' || (item.id === '002' && item.key === '3d_lab_v1.2')) {
    bindOverlay('reference', 'closeReference', 'open');
    bindOverlay('info', 'closeInfo', 'open');
    // This file opens at work 001; use its existing validation waypoint for 002.
    if (item.id === '002') doc.getElementById('jumpWork02')?.click();
  } else if (item.id === '003') bindOverlay('compare', 'closeCompare', 'show');
  else if (item.id === '004') bindOverlay('modal', 'closeModal', 'open');
  else if (['005', '006', '007', '008'].includes(item.id)) bindOverlay('modal', 'close', 'open');
  else if (item.id === '009') bindOverlay('reference', 'closeRef', 'open');
  else if (item.id === '010') bindOverlay('ref', 'closeRef', 'open');

  const restoreConfig = {
    '004': ['uiToggle', 'hiddenUi'], '005': ['ui', 'hiddenUI'],
    '006': ['hide', 'no-ui'], '007': ['hide', 'no-ui'], '008': ['hide', 'no-ui'],
    '009': ['quiet', 'hidden-ui'], '010': ['quiet', 'minimal']
  }[item.id];
  if (restoreConfig && doc.getElementById(restoreConfig[0])) {
    const button = doc.createElement('button');
    button.id = 'critt-restore-work-ui';
    button.type = 'button';
    button.textContent = '作品UIを表示';
    button.setAttribute('style', 'position:fixed;right:12px;top:70px;z-index:100;min-height:44px;padding:10px 14px;border:1px solid #eee;background:#102126;color:white;font:13px system-ui;cursor:pointer');
    button.addEventListener('click', () => doc.getElementById(restoreConfig[0]).click());
    doc.body.append(button);
    const sync = () => { button.hidden = !doc.body.classList.contains(restoreConfig[1]); };
    new MutationObserver(sync).observe(doc.body, { attributes: true, attributeFilter: ['class'] });
    sync();
  }
  // Inform the host that this is a recovered comparison, never a mode API.
  doc.documentElement.dataset.crittRecoveryAdapter = 'labels-focus-ui-restore';
}
