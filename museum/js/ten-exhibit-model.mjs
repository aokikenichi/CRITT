// A single walkable floor shared by Manual and Auto. Each hall has two works;
// openings at x=18..27 join the five halls without changing the camera.
export const rooms=Array.from({length:5},(_,i)=>({index:i,center:-i*70,minZ:-i*70-32,maxZ:-i*70+32}));
export const limits={minX:-19,maxX:64,minZ:-320,maxZ:40};
export function makeNavigation(obstacles=[]){
 const walkable=(x,z,margin=.28)=>{
  if(x<limits.minX+margin||x>limits.maxX-margin||z<limits.minZ+margin||z>limits.maxZ-margin)return false;
  const hall=rooms.some(r=>z>=r.minZ+margin&&z<=r.maxZ-margin);
  if(!hall&&(x<18+margin||x>27-margin))return false;
  return !obstacles.some(o=>Math.hypot(x-o.x,z-o.z)<o.r+margin);
 };
 const clear=(a,b)=>{const n=Math.ceil(Math.hypot(b.x-a.x,b.z-a.z)/.22);for(let i=0;i<=n;i++){const t=i/(n||1);if(!walkable(a.x+(b.x-a.x)*t,a.z+(b.z-a.z)*t))return false}return true};
 function path(start,goal){
  if(!walkable(goal.x,goal.z))throw new Error('鑑賞地点が歩行領域の外です');if(clear(start,goal))return [goal];
  const width=84,height=361,idx=(x,z)=>(z+320)*width+x+19,point=i=>({x:i%width-19,z:Math.floor(i/width)-320});
  const nearest=p=>{let best=null,d=Infinity;for(let dx=-2;dx<=2;dx++)for(let dz=-2;dz<=2;dz++){const q={x:Math.round(p.x)+dx,z:Math.round(p.z)+dz},dist=Math.hypot(q.x-p.x,q.z-p.z);if(dist<d&&walkable(q.x,q.z)&&clear(p,q)){d=dist;best=q}}if(!best)throw new Error('歩行経路を取得できません');return best};
  const a=nearest(start),b=nearest(goal),from=idx(a.x,a.z),to=idx(b.x,b.z),parents=new Int32Array(width*height).fill(-2),queue=new Int32Array(width*height);let head=0,tail=0;parents[from]=-1;queue[tail++]=from;
  while(head<tail&&parents[to]===-2){const current=queue[head++],p=point(current);for(const [dx,dz] of [[1,0],[-1,0],[0,1],[0,-1]]){const q={x:p.x+dx,z:p.z+dz};if(q.x< -19||q.x>64||q.z< -320||q.z>40)continue;const n=idx(q.x,q.z);if(parents[n]!==-2||!walkable(q.x,q.z))continue;parents[n]=current;queue[tail++]=n}}
  if(parents[to]===-2)throw new Error('展示間の歩行経路がつながりません');const raw=[goal];for(let i=to;i!==-1;i=parents[i])raw.push(point(i));raw.reverse();const result=[];let cursor=start,j=0;
  while(j<raw.length){let k=j;while(k+1<raw.length&&clear(cursor,raw[k+1]))k++;result.push(raw[k]);cursor=raw[k];j=k+1}return result;
 }
 return {walkable,clear,path};
}
export function moveWithCollision(nav,position,dx,dz){const steps=Math.max(1,Math.ceil(Math.hypot(dx,dz)/.15));for(let i=0;i<steps;i++){const x=position.x+dx/steps,z=position.z+dz/steps;if(nav.walkable(x,z)){position.x=x;position.z=z}else if(nav.walkable(x,position.z))position.x=x;else if(nav.walkable(position.x,z))position.z=z}return position}
export const angleDelta=(a,b)=>Math.atan2(Math.sin(b-a),Math.cos(b-a));
