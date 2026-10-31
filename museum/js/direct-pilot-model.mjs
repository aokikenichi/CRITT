// The same metre coordinates are used by the raycaster, human meshes and visitor.
export const ENTRANCE = Object.freeze({x: -8, z: 24, yaw: 0.57, pitch: 0.13});
const RADIUS = 0.32;

export function canStand(x, z, radius = RADIUS) {
  if (!Number.isFinite(x) || !Number.isFinite(z)) return false;
  const west = x >= -12.5 + radius && x <= 12.5 + radius &&
    z >= -14 + radius && z <= 28 - radius;
  const east = x >= 12.5 - radius && x <= 46 - radius &&
    z >= -8 + radius && z <= 14 - radius;
  if (!west && !east) return false;

  // Solid wall between entrance and the first gallery, except for its doorway.
  if (Math.abs(z - 17) < radius && Math.abs(x) > 8 - radius) return false;
  // Solid shared wall, except for the opening into the second installation.
  if (Math.abs(x - 12.5) < radius && !(z > 1 + radius && z < 13 - radius)) return false;
  // Keep a visitor from passing through the suspended ball.
  if (x < 12.5 && Math.hypot(x, z) < 2.18 + radius) return false;
  return true;
}

export function move(position, dx, dz) {
  // Small steps prevent crossing a wall in a long or delayed frame; separate axes slide along walls.
  const count = Math.max(1, Math.ceil(Math.hypot(dx, dz) / 0.1));
  for (let i = 0; i < count; i++) {
    const nx = position.x + dx / count;
    if (canStand(nx, position.z)) position.x = nx;
    const nz = position.z + dz / count;
    if (canStand(position.x, nz)) position.z = nz;
  }
  return position;
}

export function areaAt(position) {
  if (position.z > 17) return 'entrance';
  return position.x > 12.5 ? 'work02' : 'work01';
}
