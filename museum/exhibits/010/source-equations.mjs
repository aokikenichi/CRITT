// Original Work10 boundary equations; renderer-independent.
export function equations(state){
const {artTime,crossCount}=state;
function boundaryRadius(a){return 7.55*(1+.018*Math.sin(5*a+artTime*.24)+(.025*crossCount)*Math.sin(3*a-artTime*.5));}
function boundaryPos(a,layer=0){const rr=boundaryRadius(a)+layer;return [Math.cos(a)*rr*1.04,.025+layer*.004,Math.sin(a)*rr*.94]}
function boundaryLevel(x,z){const a=Math.atan2(z,x);return Math.hypot(x/1.04,z/.94)-boundaryRadius(a)}
return {boundaryRadius,boundaryPos,boundaryLevel};}
