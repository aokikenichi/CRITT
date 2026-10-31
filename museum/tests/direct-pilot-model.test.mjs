import test from 'node:test';
import assert from 'node:assert/strict';
import {ENTRANCE, areaAt, canStand, move} from '../js/direct-pilot-model.mjs';

test('one continuous walk connects the entrance, ball and human installation in both directions', () => {
  const p = {...ENTRANCE};
  const path = [[-4, 18], [-4, 11], [-4, 4], [5, 7], [14, 7], [19, 7], [23, 3]];
  const walk = ([x, z]) => {
    let frames = 0;
    while (Math.hypot(x - p.x, z - p.z) > 0.02) {
      const distance = Math.hypot(x - p.x, z - p.z);
      const step = Math.min(0.08, distance);
      move(p, (x - p.x) / distance * step, (z - p.z) / distance * step);
      assert.ok(canStand(p.x, p.z));
      assert.ok(++frames < 3000, `blocked before ${x}, ${z}`);
    }
  };
  path.forEach(walk);
  assert.equal(areaAt(p), 'work02');
  [...path].reverse().concat([[ENTRANCE.x, ENTRANCE.z]]).forEach(walk);
  assert.equal(areaAt(p), 'entrance');
});

test('door openings pass, solid walls and the ball stop even a long step', () => {
  const blockedLobby = {x: 10, z: 21};
  move(blockedLobby, 0, -10);
  assert.ok(blockedLobby.z > 17);
  const throughLobby = {x: 0, z: 21};
  move(throughLobby, 0, -6);
  assert.ok(throughLobby.z < 17);
  const blockedGallery = {x: 10, z: -3};
  move(blockedGallery, 10, 0);
  assert.ok(blockedGallery.x < 12.5);
  const throughGallery = {x: 10, z: 7};
  move(throughGallery, 6, 0);
  assert.ok(throughGallery.x > 12.5);
  const ball = {x: 0, z: 5};
  move(ball, 0, -10);
  assert.ok(ball.z >= 2.5 - 0.001);
});
