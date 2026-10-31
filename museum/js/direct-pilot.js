import {ENTRANCE, areaAt, move} from './direct-pilot-model.mjs';
import {humanVS, humanFS, buildHumans} from './direct-pilot-humans.mjs';

const canvas = document.querySelector('#gallery');
const loading = document.querySelector('#loading');
const errorBox = document.querySelector('#error');
const help = document.querySelector('#help');
const pose = {...ENTRANCE};
const keys = new Set();
const touchMoves = new Map();
let figureMode = 2;
let rendererState = 'loading';
let humanVertices = 0;
let frames = 0;
let activeArea = '';

// Read-only diagnostic state makes it possible to verify real input and rendering.
window.crittDirectPilot = Object.freeze({
  getState: () => ({...pose, area: areaAt(pose), renderer: rendererState, figureMode, humanVertices, frames})
});

function clearInput() {
  keys.clear();
  touchMoves.clear();
  document.querySelectorAll('.movement button').forEach(button => button.classList.remove('held'));
}

function fail(message, cause) {
  rendererState = 'error';
  clearInput();
  loading.hidden = true;
  errorBox.hidden = false;
  errorBox.textContent = `3D展示を表示できません。\n${message}${cause ? `\n診断: ${String(cause.message || cause)}` : ''}`;
  console.error('Direct pilot rendering error:', message, cause || '');
}

const labels = {
  entrance: ['ENTRANCE HALL / ROOM 01', '静止と時間', '球の先、右手の開口部から投球の軌跡へ。'],
  work01: ['001 / A BALL SUSPENDED IN TIME', '空中で止まった一球', '球の右側にある開口部から、作品002へ。'],
  work02: ['002 / THE 22 YARDS OF ETERNITY', '22ヤードの永遠', '歩きながら、投球の身体と時間をたどる。']
};
function updateLocation() {
  const next = areaAt(pose);
  if (next === activeArea) return;
  activeArea = next;
  const [kicker, title, note] = labels[next];
  document.querySelector('#location-kicker').textContent = kicker;
  document.querySelector('#location-title').textContent = title;
  document.querySelector('#location-note').textContent = note;
}
updateLocation();

document.querySelector('#help-button').addEventListener('click', () => { clearInput(); help.showModal(); });
document.querySelector('#close-help').addEventListener('click', () => help.close());
help.addEventListener('close', () => canvas.focus({preventScroll:true}));
document.querySelector('#reset-button').addEventListener('click', () => {
  clearInput(); Object.assign(pose, ENTRANCE); updateLocation(); canvas.focus({preventScroll:true});
});
document.querySelectorAll('[data-figure]').forEach(button => {
  button.addEventListener('click', () => {
    figureMode = Number(button.dataset.figure);
    document.querySelectorAll('[data-figure]').forEach(choice => choice.setAttribute('aria-pressed', String(choice === button)));
  });
});

window.addEventListener('keydown', event => {
  if (help.open || /^(BUTTON|INPUT|TEXTAREA|SELECT|SUMMARY)$/.test(event.target.tagName)) return;
  const key = event.key.toLowerCase();
  if (['w','a','s','d','q','e','r','f','arrowup','arrowdown','arrowleft','arrowright','shift'].includes(key)) {
    event.preventDefault(); keys.add(key);
  }
});
window.addEventListener('keyup', event => keys.delete(event.key.toLowerCase()));
window.addEventListener('blur', clearInput);
document.addEventListener('visibilitychange', () => { if (document.hidden) clearInput(); });

let pointer = null;
canvas.addEventListener('pointerdown', event => {
  if (pointer || help.open) return;
  event.preventDefault();
  canvas.focus({preventScroll:true});
  pointer = {id:event.pointerId, x:event.clientX, y:event.clientY};
  canvas.setPointerCapture(event.pointerId);
});
canvas.addEventListener('pointermove', event => {
  if (!pointer || pointer.id !== event.pointerId) return;
  pose.yaw += (event.clientX - pointer.x) * 0.0045;
  pose.pitch = Math.max(-1.32, Math.min(1.32, pose.pitch - (event.clientY - pointer.y) * 0.0045));
  pointer.x = event.clientX; pointer.y = event.clientY;
});
for (const eventName of ['pointerup','pointercancel','lostpointercapture']) {
  canvas.addEventListener(eventName, event => { if (pointer?.id === event.pointerId) pointer = null; });
}
document.querySelectorAll('[data-move]').forEach(button => {
  button.addEventListener('pointerdown', event => {
    event.preventDefault();
    touchMoves.set(event.pointerId, button.dataset.move);
    button.classList.add('held');
    button.setPointerCapture(event.pointerId);
  });
  const release = event => {
    touchMoves.delete(event.pointerId);
    if (![...touchMoves.values()].includes(button.dataset.move)) button.classList.remove('held');
  };
  for (const eventName of ['pointerup','pointercancel','lostpointercapture']) button.addEventListener(eventName, release);
});

function makeShader(gl, type, source) {
  const shader = gl.createShader(type);
  gl.shaderSource(shader, source);
  gl.compileShader(shader);
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(shader) || 'Shader compilation failed');
  return shader;
}
function makeProgram(gl, vertex, fragment) {
  const program = gl.createProgram();
  gl.attachShader(program, makeShader(gl, gl.VERTEX_SHADER, vertex));
  gl.attachShader(program, makeShader(gl, gl.FRAGMENT_SHADER, fragment));
  gl.linkProgram(program);
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(program) || 'Program link failed');
  return program;
}
function loadImage(url) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error(`素材を読み込めません: ${url}`));
    image.src = url;
  });
}
function cameraBasis() {
  const forward = [Math.sin(pose.yaw)*Math.cos(pose.pitch), Math.sin(pose.pitch), -Math.cos(pose.yaw)*Math.cos(pose.pitch)];
  let right = [-forward[2], 0, forward[0]];
  const length = Math.hypot(...right);
  right = right.map(value => value / length);
  const up = [right[1]*forward[2]-right[2]*forward[1], right[2]*forward[0]-right[0]*forward[2], right[0]*forward[1]-right[1]*forward[0]];
  return {forward, right, up};
}

async function start() {
  const gl = canvas.getContext('webgl2', {antialias:true, powerPreference:'high-performance', alpha:false});
  if (!gl) throw new Error('WebGL 2 が利用できません。対応するブラウザと GPU でお試しください。');
  canvas.addEventListener('webglcontextlost', event => { event.preventDefault(); fail('WebGL の描画コンテキストが失われました。再読み込みしてください。'); });
  const shaderURL = new URL('./direct-pilot-fragment.glsl', import.meta.url);
  const [response, photo, micro] = await Promise.all([
    fetch(shaderURL), loadImage('direct-pilot-assets/ball-front.jpg'), loadImage('direct-pilot-assets/leather-normal.jpg')
  ]);
  if (!response.ok) throw new Error(`シェーダーを読み込めません: HTTP ${response.status}`);
  const fragment = (await response.text()).trimStart();
  const vertex = `#version 300 es\nin vec2 aPos;void main(){gl_Position=vec4(aPos,0.,1.);}`;
  const sceneProgram = makeProgram(gl, vertex, fragment);
  const figureProgram = makeProgram(gl, humanVS, humanFS);

  const sceneVAO = gl.createVertexArray();
  gl.bindVertexArray(sceneVAO);
  const sceneBuffer = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, sceneBuffer);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1,1,-1,-1,1,-1,1,1,-1,1,1]), gl.STATIC_DRAW);
  const positionAttribute = gl.getAttribLocation(sceneProgram, 'aPos');
  gl.enableVertexAttribArray(positionAttribute);
  gl.vertexAttribPointer(positionAttribute, 2, gl.FLOAT, false, 0, 0);

  const figureVAO = gl.createVertexArray();
  gl.bindVertexArray(figureVAO);
  const figureBuffer = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, figureBuffer);
  const geometry = buildHumans();
  humanVertices = geometry.length / 8;
  gl.bufferData(gl.ARRAY_BUFFER, geometry, gl.STATIC_DRAW);
  for (const [name, size, offset] of [['aHumanPos',3,0],['aHumanNormal',3,12],['aHumanUV',2,24]]) {
    const attribute = gl.getAttribLocation(figureProgram, name);
    if (attribute >= 0) { gl.enableVertexAttribArray(attribute); gl.vertexAttribPointer(attribute, size, gl.FLOAT, false, 32, offset); }
  }
  gl.bindVertexArray(null);
  function texture(image, unit) {
    const tex = gl.createTexture();
    gl.activeTexture(gl.TEXTURE0 + unit); gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB, gl.RGB, gl.UNSIGNED_BYTE, image);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  }
  texture(photo, 0); texture(micro, 6);
  const scene = Object.fromEntries(['uRes','uTime','uCam','uRot','uFocal','uQuality','uMaterialMode','uBallPhoto','uPhotoReady','uBallMicro','uMicroReady','uGhostReady','uWalkProgress','uFigureMode'].map(name => [name, gl.getUniformLocation(sceneProgram, name)]));
  const figure = Object.fromEntries(['uEye','uRight','uUp','uForward','uProj','uFigureLook','uProgress','uSeconds'].map(name => [name, gl.getUniformLocation(figureProgram, name)]));
  gl.useProgram(sceneProgram);
  gl.uniform1i(scene.uBallPhoto, 0); gl.uniform1i(scene.uBallMicro, 6);
  gl.uniform1f(scene.uPhotoReady, 1); gl.uniform1f(scene.uMicroReady, 1);
  gl.uniform1f(scene.uGhostReady, 0); gl.uniform1i(scene.uMaterialMode, 3);
  if (gl.getError() !== gl.NO_ERROR) throw new Error('WebGL リソースの初期化に失敗しました。');
  rendererState = 'webgl2';
  loading.hidden = true;
  let last = 0;
  let lastCheck = 0;
  function render(now) {
    if (rendererState !== 'webgl2') return;
    try {
      if (now - last < 30) { requestAnimationFrame(render); return; }
      const dt = Math.min(.08, (now - last) / 1000 || .033); last = now;
      if (!help.open) {
        pose.yaw += (Number(keys.has('e')) - Number(keys.has('q'))) * dt * 1.65;
        pose.pitch = Math.max(-1.32, Math.min(1.32, pose.pitch + (Number(keys.has('r')) - Number(keys.has('f'))) * dt * 1.28));
        const held = direction => [...touchMoves.values()].includes(direction);
        let forward = Number(keys.has('w') || keys.has('arrowup') || held('forward')) - Number(keys.has('s') || keys.has('arrowdown') || held('back'));
        let side = Number(keys.has('d') || keys.has('arrowright') || held('right')) - Number(keys.has('a') || keys.has('arrowleft') || held('left'));
        const magnitude = Math.hypot(forward, side) || 1;
        const speed = dt * (keys.has('shift') ? 6.1 : 2.75) / magnitude;
        forward *= speed; side *= speed;
        move(pose, forward*Math.sin(pose.yaw)+side*Math.cos(pose.yaw), -forward*Math.cos(pose.yaw)+side*Math.sin(pose.yaw));
        updateLocation();
      }
      const mobile = matchMedia('(pointer:coarse)').matches || innerWidth <= 700;
      const scale = Math.min(devicePixelRatio || 1, mobile ? .8 : .94, 1350 / canvas.clientWidth, 840 / canvas.clientHeight);
      const width = Math.max(1, Math.round(canvas.clientWidth * scale));
      const height = Math.max(1, Math.round(canvas.clientHeight * scale));
      if (canvas.width !== width || canvas.height !== height) { canvas.width = width; canvas.height = height; gl.viewport(0, 0, width, height); }
      const focal = mobile ? 1.2 : 1.65;
      const {forward, right, up} = cameraBasis();
      const eye = [pose.x, 1.65, pose.z];
      const rotation = new Float32Array([...right, ...up, ...forward.map(value => -value)]);

      gl.useProgram(sceneProgram); gl.bindVertexArray(sceneVAO);
      gl.uniform2f(scene.uRes, width, height); gl.uniform1f(scene.uTime, now*.001);
      gl.uniform3fv(scene.uCam, eye); gl.uniformMatrix3fv(scene.uRot, false, rotation);
      gl.uniform1f(scene.uFocal, focal); gl.uniform1f(scene.uQuality, 1);
      gl.uniform1f(scene.uWalkProgress, Math.max(0, Math.min(1, (pose.x-14)/27)));
      gl.uniform1i(scene.uFigureMode, figureMode); gl.drawArrays(gl.TRIANGLES, 0, 6);

      gl.useProgram(figureProgram); gl.bindVertexArray(figureVAO);
      gl.uniform3fv(figure.uEye, eye); gl.uniform3fv(figure.uRight, right); gl.uniform3fv(figure.uUp, up); gl.uniform3fv(figure.uForward, forward);
      gl.uniform2f(figure.uProj, 2*focal*Math.min(width,height)/width, 2*focal*Math.min(width,height)/height);
      gl.uniform1f(figure.uFigureLook, figureMode); gl.uniform1f(figure.uProgress, Math.max(0, Math.min(1, (pose.x-14)/27)));
      gl.uniform1f(figure.uSeconds, now*.001);
      gl.enable(gl.BLEND); gl.blendEquation(gl.FUNC_ADD); gl.blendFunc(gl.SRC_ALPHA, gl.ONE);
      gl.disable(gl.DEPTH_TEST); gl.drawArrays(gl.TRIANGLES, 0, humanVertices); gl.disable(gl.BLEND);
      gl.bindVertexArray(null);
      frames++;
      canvas.dataset.diagnostic = JSON.stringify({x:pose.x, z:pose.z, yaw:pose.yaw, pitch:pose.pitch, area:activeArea, renderer:rendererState, figureMode, humanVertices, frames});
      if (now - lastCheck > 2000) { const code = gl.getError(); lastCheck = now; if (code !== gl.NO_ERROR) throw new Error(`WebGL error ${code}`); }
      requestAnimationFrame(render);
    } catch (cause) { fail('描画中にエラーが発生しました。', cause); }
  }
  requestAnimationFrame(render);
}

start().catch(cause => fail('展示の初期化に失敗しました。', cause));
