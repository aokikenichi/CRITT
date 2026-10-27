// Only formally approved, same-origin images enter this viewer. Candidate
// materials and previews belong to their own, explicitly labelled interfaces.
const workPage = new URL('../work.html', import.meta.url);
let viewerCount = 0;

function element(tag, className, text) {
  const node = document.createElement(tag);
  node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function approvedImages(originals) {
  if (!Array.isArray(originals)) return [];
  return originals.flatMap((original) => {
    if (!original || original.approval_status !== 'approved' || typeof original.src !== 'string' || !original.src.trim()) return [];
    try {
      const url = new URL(original.src, workPage);
      if (url.origin !== workPage.origin || !['http:', 'https:'].includes(url.protocol) || url.username || url.password) return [];
      return [{ ...original, src: url.href }];
    } catch {
      return [];
    }
  });
}

/**
 * Build a reusable native-dialog viewer. No artwork or test image is registered
 * by this module; callers must supply explicitly approved metadata.
 */
export function createOriginalViewer() {
  const titleId = `original-viewer-title-${++viewerCount}`;
  const dialog = element('dialog', 'original-viewer-dialog');
  dialog.setAttribute('aria-labelledby', titleId);
  const header = element('header', 'original-viewer-header');
  const heading = element('h2', 'original-viewer-heading', '原画を見る');
  heading.id = titleId;
  const closeButton = element('button', 'original-viewer-button original-viewer-close', '閉じる');
  closeButton.type = 'button';
  closeButton.setAttribute('aria-label', '原画ビューアを閉じる');
  header.append(heading, closeButton);

  const toolbar = element('div', 'original-viewer-toolbar');
  toolbar.setAttribute('role', 'group');
  toolbar.setAttribute('aria-label', '画像の切替と拡大縮小');
  const button = (text, label, action) => {
    const node = element('button', 'original-viewer-button', text);
    node.type = 'button';
    node.setAttribute('aria-label', label);
    node.addEventListener('click', action);
    toolbar.append(node);
    return node;
  };
  const previous = button('← 前へ', '前の原画', () => showImage(index - 1));
  const counter = element('span', 'original-viewer-counter');
  counter.setAttribute('aria-live', 'polite');
  toolbar.append(counter);
  const next = button('次へ →', '次の原画', () => showImage(index + 1));
  button('フィット', '画面に合わせる', fit);
  button('100%', '原寸の100パーセントで表示', () => zoom(1));
  button('−', '原画を縮小', () => zoom(scale / 1.25));
  button('＋', '原画を拡大', () => zoom(scale * 1.25));
  const zoomLabel = element('output', 'original-viewer-zoom', '—');
  zoomLabel.setAttribute('aria-label', '表示倍率');
  toolbar.append(zoomLabel);

  const viewport = element('div', 'original-viewer-viewport');
  viewport.setAttribute('aria-label', '原画表示領域。拡大後はスクロールまたは指で移動できます');
  viewport.tabIndex = 0;
  const imageArea = element('div', 'original-viewer-image-area');
  viewport.append(imageArea);
  const status = element('p', 'original-viewer-status');
  status.setAttribute('role', 'status');
  const caption = element('section', 'original-viewer-caption');
  const imageTitle = element('h3', 'original-viewer-image-title');
  const description = element('p', 'original-viewer-description');
  const provenance = element('p', 'original-viewer-provenance');
  const hint = element('p', 'original-viewer-hint', '← →：画像切替 / ＋ −：拡大縮小 / 0：フィット / Esc：閉じる。スマートフォンでは2本指で拡大縮小できます。');
  caption.append(imageTitle, description, provenance, hint);
  dialog.append(header, toolbar, status, viewport, caption);
  document.body.append(dialog);

  let images = [];
  let index = 0;
  let image = null;
  let scale = 1;
  let fitted = true;
  let returnFocus = null;
  let loadSequence = 0;
  const pointers = new Map();
  let pinch = null;

  function updateZoom() {
    zoomLabel.textContent = image?.naturalWidth ? `${Math.round(scale * 1000) / 10}%` : '—';
  }

  function setScale(value, anchor) {
    if (!image?.naturalWidth || !image.naturalHeight || image.hidden) return;
    const viewportRect = viewport.getBoundingClientRect();
    const point = anchor || { x: viewport.clientWidth / 2, y: viewport.clientHeight / 2 };
    const before = image.getBoundingClientRect();
    const ratioX = before.width ? (viewportRect.left + point.x - before.left) / before.width : 0.5;
    const ratioY = before.height ? (viewportRect.top + point.y - before.top) / before.height : 0.5;
    scale = Math.min(8, Math.max(0.001, value));
    image.style.width = `${Math.max(1, Math.round(image.naturalWidth * scale))}px`;
    image.style.height = `${Math.max(1, Math.round(image.naturalHeight * scale))}px`;
    const after = image.getBoundingClientRect();
    viewport.scrollLeft += after.left + ratioX * after.width - viewportRect.left - point.x;
    viewport.scrollTop += after.top + ratioY * after.height - viewportRect.top - point.y;
    updateZoom();
  }

  function zoom(value, anchor) {
    fitted = false;
    setScale(value, anchor);
  }

  function fit() {
    fitted = true;
    if (!image?.naturalWidth || !image.naturalHeight) return;
    setScale(Math.min(1, Math.max(1, viewport.clientWidth - 32) / image.naturalWidth, Math.max(1, viewport.clientHeight - 32) / image.naturalHeight));
    viewport.scrollLeft = 0;
    viewport.scrollTop = 0;
  }

  function showImage(nextIndex) {
    if (nextIndex < 0 || nextIndex >= images.length) return;
    index = nextIndex;
    pointers.clear();
    pinch = null;
    const original = images[index];
    const sequence = ++loadSequence;
    previous.disabled = index === 0;
    next.disabled = index === images.length - 1;
    counter.textContent = `${index + 1} / ${images.length}`;
    imageTitle.textContent = typeof original.title === 'string' ? original.title : '登録済みの原画';
    description.textContent = typeof original.description === 'string' ? original.description : '画像の説明は未登録です。';
    provenance.textContent = `来歴：${typeof original.provenance === 'string' && original.provenance ? original.provenance : '情報は未登録です。'}`;
    status.textContent = '画像を読み込んでいます…';
    status.hidden = false;
    viewport.setAttribute('aria-busy', 'true');
    image = element('img', 'original-viewer-image');
    image.alt = typeof original.alt === 'string' ? original.alt : imageTitle.textContent;
    image.hidden = true;
    image.draggable = false;
    const loadingImage = image;
    image.addEventListener('load', () => {
      if (sequence !== loadSequence) return;
      loadingImage.hidden = false;
      status.textContent = '';
      status.hidden = true;
      viewport.setAttribute('aria-busy', 'false');
      fit();
    });
    image.addEventListener('error', () => {
      if (sequence !== loadSequence) return;
      status.textContent = '画像を読み込めませんでした。別の画像へ切り替えるか、ビューアを閉じてください。';
      status.hidden = false;
      viewport.setAttribute('aria-busy', 'false');
      updateZoom();
    });
    imageArea.replaceChildren(image);
    scale = 1;
    updateZoom();
    image.src = original.src;
  }

  function close() {
    if (dialog.open) dialog.close();
  }

  closeButton.addEventListener('click', close);
  dialog.addEventListener('close', () => {
    pointers.clear();
    pinch = null;
    if (returnFocus?.isConnected && typeof returnFocus.focus === 'function') returnFocus.focus({ preventScroll: true });
  });
  dialog.addEventListener('click', (event) => {
    if (event.target !== dialog) return;
    const bounds = dialog.getBoundingClientRect();
    if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) close();
  });
  dialog.addEventListener('keydown', (event) => {
    if (event.altKey || event.ctrlKey || event.metaKey) return;
    const actions = {
      ArrowLeft: () => showImage(index - 1),
      ArrowRight: () => showImage(index + 1),
      '+': () => zoom(scale * 1.25),
      '=': () => zoom(scale * 1.25),
      '-': () => zoom(scale / 1.25),
      '0': fit,
    };
    if (actions[event.key]) {
      event.preventDefault();
      actions[event.key]();
    }
    // Escape and focus containment are supplied by the native modal dialog.
  });

  function touchPair() {
    const [a, b] = [...pointers.values()];
    if (!a || !b) return null;
    const bounds = viewport.getBoundingClientRect();
    return {
      distance: Math.hypot(b.x - a.x, b.y - a.y),
      center: { x: (a.x + b.x) / 2 - bounds.left, y: (a.y + b.y) / 2 - bounds.top },
    };
  }

  viewport.addEventListener('pointerdown', (event) => {
    if (event.pointerType !== 'touch') return;
    pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
    viewport.setPointerCapture(event.pointerId);
    const pair = touchPair();
    if (pair) pinch = { distance: Math.max(1, pair.distance), scale };
  });
  viewport.addEventListener('pointermove', (event) => {
    const old = pointers.get(event.pointerId);
    if (!old) return;
    pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
    const pair = touchPair();
    if (pair && pinch) {
      zoom(pinch.scale * pair.distance / pinch.distance, pair.center);
    } else {
      viewport.scrollLeft -= event.clientX - old.x;
      viewport.scrollTop -= event.clientY - old.y;
    }
  });
  for (const eventName of ['pointerup', 'pointercancel', 'lostpointercapture']) {
    viewport.addEventListener(eventName, (event) => {
      pointers.delete(event.pointerId);
      if (pointers.size < 2) pinch = null;
    });
  }
  const observer = new ResizeObserver(() => {
    if (dialog.open && fitted) fit();
  });
  observer.observe(viewport);

  return {
    open(originals, opener = document.activeElement) {
      const approved = approvedImages(originals);
      if (approved.length === 0) return false;
      images = approved;
      returnFocus = opener;
      if (!dialog.open) dialog.showModal();
      showImage(0);
      closeButton.focus({ preventScroll: true });
      return true;
    },
    close,
  };
}
