/* Shared UI for Step03 and the explicit Step04 recovery review catalog.
   Only approved local paths enter the iframe; no postMessage API. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const element = (tag, text, className) => {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (className) node.className = className;
    return node;
  };
  const trustedWorks = new Set(['009', '010']);
  const reviewMode = document.body.dataset.review === 'true';
  const listPage = reviewMode ? 'review.html' : 'index.html';
  const workPage = reviewMode ? 'review-work.html' : 'work.html';
  let uiHidden = false;
  let frameDocument = null;

  function canDisplay(item) {
    if (trustedWorks.has(item.id) && item.work_url === `works/${item.id}/index.html`) return true;
    return reviewMode && item.connection_allowed === true && item.representation === 'library_extracted_utf8_text_to_html'
      && new RegExp(`^recovered/sources/${item.id}/[A-Za-z0-9_.-]+\\.html$`).test(item.work_url);
  }

  function waitForCanvas(doc) {
    return new Promise((resolve, reject) => {
      const find = () => [...doc.querySelectorAll('canvas')].find(canvas => canvas.getBoundingClientRect().width > 0 && canvas.getBoundingClientRect().height > 0);
      const existing = find();
      if (existing) return resolve(existing);
      const observer = new MutationObserver(() => {
        const canvas = find();
        if (canvas) { observer.disconnect(); clearTimeout(timeout); resolve(canvas); }
      });
      const timeout = setTimeout(() => { observer.disconnect(); reject(new Error('Work canvas missing')); }, 14000);
      observer.observe(doc.body, { childList: true, subtree: true, attributes: true });
    });
  }

  function setUIHidden(hidden) {
    uiHidden = hidden;
    document.body.classList.toggle('ui-hidden', hidden);
    $('shell-header').hidden = hidden;
    $('shell-footer').hidden = hidden;
    $('show-ui').hidden = !hidden;
    (hidden ? $('show-ui') : $('hide-ui')).focus({ preventScroll: true });
    frameDocument?.defaultView.dispatchEvent(new Event('resize'));
  }

  function list(items) {
    for (const item of items) {
      const available = canDisplay(item);
      const card = element('article', undefined, `work-card ${available ? 'is-available' : 'is-missing'}`);
      card.dataset.workId = item.id;
      const heading = element('h3', item.title_ja);
      heading.id = `title-${item.id}`;
      card.setAttribute('aria-labelledby', heading.id);
      card.append(element('span', item.id, 'work-number'), element('span', item.status_label, 'work-status'),
        heading, element('p', item.title_note, 'work-note'));
      const actions = element('div', undefined, 'card-actions');
      const detail = element('a', available ? (reviewMode ? '候補を比較 →' : '鑑賞する →') : '詳細・収録状況 →');
      detail.href = `${workPage}?id=${item.id}`;
      detail.setAttribute('aria-label', `${item.id} ${item.title_ja} ${available ? (reviewMode ? 'の候補を比較する' : 'を鑑賞する') : 'の収録状況を見る'}`);
      actions.append(detail);
      if (!available) {
        const disabled = element('button', '鑑賞する');
        disabled.type = 'button';
        disabled.disabled = true;
        actions.prepend(disabled);
      }
      card.append(actions);
      $('artwork-list').append(card);
    }
    $('catalog-status').textContent = reviewMode ? '10作品の比較台帳 ／ 回収14候補＋現行009・010 ／ 正式採用は未承認' : '10作品の台帳 ／ 接続済み試作 2作品 ／ 原本未取得 8作品';
  }

  function openInfo(item, kind, opener) {
    const content = $('info-content');
    content.replaceChildren();
    $('info-title').textContent = kind === 'about' ? '作品について' : '操作方法';
    content.append(element('p', `${item.id}　${item.title_ja}（${item.title_note}）`, 'dialog-work-title'));
    if (kind === 'about') {
      const rows = [
        ['鑑賞文', item.statement || '原本を取得してから内容を照合します。'],
        ['作品の問い', item.question || '原本未取得のため未確認です。'],
        ['問いの来歴', item.question_note],
        ['技法・表示方法', item.technique || '原本未取得のため未確認です。'],
        ['架空作品について', item.fiction_notice],
        ['試作状況', item.alpha_notes],
        ['原画', item.originals_note]
      ];
      const description = element('dl');
      for (const [label, text] of rows) {
        if (text) description.append(element('dt', label), element('dd', text));
      }
      content.append(description);
    } else {
      const instructions = element('ul');
      for (const text of item.controls || ['原本未取得／現在収録準備中です。操作方法は原本接続後に確認します。']) {
        instructions.append(element('li', text));
      }
      content.append(instructions, element('p', '共通UI：Tabで選択、Enter／Spaceで決定。ダイアログはEscまたは「閉じる」で閉じます。UIを隠した場合は「UIを表示」、またはEscで復帰します。作品のキー操作は作品画面を選んでから行ってください。'));
    }
    const dialog = $('info-dialog');
    dialog.addEventListener('close', () => opener.focus({ preventScroll: true }), { once: true });
    dialog.showModal();
  }

  /* The source calls unapproved image candidates "originals". Correct only
     their displayed provenance, retaining the source bytes and artwork logic. */
  function adaptReferenceLabels(doc) {
    doc.getElementById('openOriginals').textContent = '制作途中の参考画像';
    doc.querySelector('#originals h2').textContent = '制作途中の参考画像 — 未承認の候補素材3点';
    doc.querySelector('#originals .note').textContent = 'この3枚は試作に使われた未承認の候補素材です。正式採用原画ではありません。高精細画像・写真調素材・透視投影を重ねた仮想インスタレーションであり、実在のクリケット史料ではありません。';
    for (const node of doc.querySelectorAll('#originals img')) {
      node.alt = node.alt.replace('原画', '未承認の参考画像');
    }
    const hint = doc.getElementById('hint');
    hint.textContent = hint.textContent.replace('原画を見る', '制作途中の参考画像');

    const overlay = doc.getElementById('originals');
    const trigger = doc.getElementById('openOriginals');
    const close = doc.getElementById('closeOriginals');
    const heading = doc.querySelector('#originals h2');
    heading.id = 'reference-images-title';
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-labelledby', heading.id);
    overlay.setAttribute('aria-hidden', 'true');
    new MutationObserver(() => {
      const open = overlay.classList.contains('open');
      overlay.setAttribute('aria-hidden', String(!open));
      doc.querySelector('header').inert = open;
      for (const sibling of overlay.parentElement.children) {
        if (sibling !== overlay) sibling.inert = open;
      }
      (open ? close : trigger).focus({ preventScroll: true });
    }).observe(overlay, { attributes: true, attributeFilter: ['class'] });
    overlay.addEventListener('keydown', event => {
      if (event.key === 'Tab') {
        event.preventDefault();
        close.focus();
      }
    });
  }

  function adaptContributionFocus(doc) {
    const overlay = doc.getElementById('contrib');
    const trigger = doc.getElementById('leave');
    const app = doc.getElementById('app');
    new MutationObserver(() => {
      const open = overlay.classList.contains('show');
      for (const sibling of app.children) {
        if (sibling !== overlay) sibling.inert = open;
      }
      for (const sibling of doc.body.children) {
        if (sibling !== app) sibling.inert = open;
      }
      (open ? doc.getElementById('phrase') : trigger).focus({ preventScroll: true });
    }).observe(overlay, { attributes: true, attributeFilter: ['class'] });
    overlay.addEventListener('keydown', event => {
      if (event.key !== 'Tab') return;
      const first = doc.getElementById('phrase');
      const last = doc.getElementById('send');
      if (event.shiftKey && doc.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && doc.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    });
  }

  function bindFrame(item) {
    const frame = $('artwork-frame');
    const loadStatus = $('load-status');
    let connected = false;
    const timeout = setTimeout(() => {
      if (!connected) loadStatus.textContent = '作品の読み込みを確認できませんでした。一覧へ戻るか、ページを再読み込みしてください。';
    }, 15000);
    frame.addEventListener('load', async () => {
      clearTimeout(timeout);
      try {
        if (frame.contentWindow.location.origin !== location.origin) throw new Error('Untrusted work origin');
        const doc = frame.contentDocument;
        if (!doc) throw new Error('Work document missing');
        const canvas = await waitForCanvas(doc);
        canvas.tabIndex = 0;
        if (item.work_url === 'works/009/index.html') adaptReferenceLabels(doc);
        if (item.work_url === 'works/010/index.html') adaptContributionFocus(doc);
        if (reviewMode && item.representation === 'library_extracted_utf8_text_to_html') {
          const { adaptRecoveredWork } = await import('./recovery-adapter.js');
          adaptRecoveredWork(doc, item, canvas);
        }
        frameDocument = doc;
        connected = true;
        loadStatus.hidden = true;
        $('hide-ui').disabled = false;

        const ids = ['manual', 'auto', 'pause'];
        const bridgeSupported = item.common_mode_bridge_supported !== false && item.manual_supported === true && item.auto_supported === true && ids.every(id => doc.getElementById(id));
        if (bridgeSupported) {
          $('mode-controls').hidden = false;
          $('mode-hint').textContent = '作品画面内でも操作できます。移動キーは作品画面を選んでから。';
          const sync = () => {
            const isAuto = doc.getElementById('auto').getAttribute('aria-pressed') === 'true';
            document.querySelector('[data-mode="manual"]').setAttribute('aria-pressed', String(!isAuto));
            document.querySelector('[data-mode="auto"]').setAttribute('aria-pressed', String(isAuto));
            const pause = document.querySelector('[data-mode="pause"]');
            pause.disabled = !isAuto;
            pause.textContent = /再開/.test(doc.getElementById('pause').textContent) ? '再開' : '一時停止';
          };
          const observer = new MutationObserver(sync);
          for (const id of ids) observer.observe(doc.getElementById(id), { attributes: true, childList: true, subtree: true });
          for (const control of document.querySelectorAll('[data-mode]')) {
            control.addEventListener('click', () => {
              doc.getElementById(control.dataset.mode).click();
              sync();
              frame.contentWindow.focus();
              canvas.focus({ preventScroll: true });
            });
          }
          sync();
        }
        doc.addEventListener('keydown', event => {
          const internalModal = doc.getElementById('originals')?.classList.contains('open') || doc.getElementById('contrib')?.classList.contains('show');
          if (event.key === 'Escape' && uiHidden && !internalModal && !event.crittInternalModal && !/INPUT|TEXTAREA/.test(event.target.tagName)) setUIHidden(false);
        }, true);
      } catch (error) {
        frame.hidden = true;
        loadStatus.hidden = false;
        loadStatus.textContent = '作品を表示できませんでした。一覧へ戻るか、ページを再読み込みしてください。';
      }
    });
    frame.title = `${item.id} ${item.title_ja}：${item.status_label}`;
    frame.hidden = false;
    frame.src = item.work_url;
  }

  async function work(items) {
    const params = new URLSearchParams(location.search);
    const id = params.get('id');
    let item = items.find(entry => entry.id === id);
    if (params.getAll('id').length !== 1 || !/^00[1-9]$|^010$/.test(id || '') || !item) {
      location.replace(listPage);
      return;
    }
    if (reviewMode) {
      const key = params.get('variant') || item.default_variant;
      const selected = item.variants.find(variant => variant.key === key);
      if (params.getAll('variant').length > 1 || !selected) { location.replace(listPage); return; }
      item = { ...item, ...selected, originals: [] };
      $('review-note').textContent = `${item.label} ／ ${item.qa_status} ／ 元原本とのバイト一致未検証`;
      for (const variant of item.variants) {
        const link = element('a', `${variant.label} — ${variant.qa_status}`);
        link.href = `${workPage}?id=${item.id}&variant=${encodeURIComponent(variant.key)}`;
        if (variant.key === key) link.setAttribute('aria-current', 'page');
        $('variant-panel').append(link);
      }
    }
    document.title = `${item.id} ${item.title_ja}｜CRITT Museum α試作`;
    $('work-id').textContent = item.id;
    $('work-title').textContent = item.title_ja;
    $('work-status').textContent = `${item.title_note} ／ ${item.status_label}`;
    const index = items.findIndex(entry => entry.id === item.id);
    for (const [target, next] of [['previous-work', items[index - 1]], ['next-work', items[index + 1]]]) {
      const link = $(target);
      if (next) {
        link.href = `${workPage}?id=${next.id}`;
        link.removeAttribute('aria-disabled');
        link.setAttribute('aria-label', `${target === 'previous-work' ? '前の作品' : '次の作品'} ${next.id} ${next.title_ja}`);
      } else {
        link.removeAttribute('href');
        link.setAttribute('aria-disabled', 'true');
      }
    }
    $('about-button').addEventListener('click', event => openInfo(item, 'about', event.currentTarget));
    $('help-button').addEventListener('click', event => openInfo(item, 'help', event.currentTarget));
    $('info-dialog').querySelector('[data-close-dialog]').addEventListener('click', () => $('info-dialog').close());
    $('info-dialog').addEventListener('click', event => {
      if (event.target === $('info-dialog')) {
        const rect = event.target.getBoundingClientRect();
        if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) event.target.close();
      }
    });
    $('hide-ui').addEventListener('click', () => setUIHidden(true));
    $('show-ui').addEventListener('click', () => setUIHidden(false));
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && uiHidden && !$('info-dialog').open && !document.querySelector('.original-viewer-dialog[open]')) setUIHidden(false);
    });
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) {
      $('reduced-motion-note').hidden = false;
      $('reduced-motion-note').textContent = reviewMode ? '動きを減らす設定を検出しました。回収作品内部の粒子・光・ガイドはこの設定に未対応の場合があります。' : '動きを減らす設定を検出しました。作品はManualで開始します。Autoは選択すると動きます。010の静止モードもカメラ移動全体は止めません。';
    }
    const originals = (item.originals || []).filter(image => {
      if (image.approval_status !== 'approved' || typeof image.src !== 'string' || !image.src.trim()) return false;
      try {
        const url = new URL(image.src, location.href);
        return url.origin === location.origin && ['http:', 'https:'].includes(url.protocol) && !url.username && !url.password;
      } catch { return false; }
    });
    if (originals.length) {
      const { createOriginalViewer } = await import('./original-viewer.js');
      const viewer = createOriginalViewer();
      $('originals-button').disabled = false;
      $('originals-status').textContent = `正式採用原画 ${originals.length}点`;
      $('originals-button').addEventListener('click', event => viewer.open(originals, event.currentTarget));
    }
    if (canDisplay(item)) {
      bindFrame(item);
    } else {
      $('load-status').hidden = true;
      $('missing-work').hidden = false;
      $('missing-work').replaceChildren(element('p', `WORK ${item.id}`, 'work-number'), element('h2', '原本未取得／現在収録準備中'), element('p', 'この作品は未収録です。個別作品HTMLと依存素材、採用版の確認が必要です。原本を取得してから鑑賞を接続します。'), element('p', '作品名は暫定です。鑑賞用の代替作品は作成していません。'));
      $('mode-hint').textContent = '未収録のため、鑑賞操作は利用できません。';
      if (reviewMode) {
        $('missing-work').replaceChildren(element('h2', 'この候補の共通接続は保留中です'), element('p', item.qa_status), element('p', '原本の再制作や不具合の自動修正は行っていません。比較候補メニューで別の版を選択できます。'));
        $('mode-hint').textContent = '不具合・条件はSTEP04_BROWSER_QA.mdとSTEP04_PENDING.mdに記録しています。';
      }
    }
  }

  async function start() {
    if (!['index', 'work'].includes(document.body.dataset.page)) return;
    try {
      const response = await fetch(reviewMode ? 'review-artworks.json' : 'artworks.json');
      if (!response.ok) throw new Error('Catalog unavailable');
      const data = await response.json();
      if (!Array.isArray(data.items) || data.items.length !== 10 || new Set(data.items.map(item => item.id)).size !== 10) throw new Error('Invalid catalog');
      const items = data.items.slice().sort((a, b) => a.id.localeCompare(b.id));
      if (document.body.dataset.page === 'index') list(items);
      else await work(items);
    } catch (error) {
      const status = $('catalog-status') || $('load-status');
      status.hidden = false;
      status.textContent = '作品台帳を読み込めませんでした。HTTPで開いていることを確認し、ページを再読み込みしてください。';
    }
  }
  start();
})();
