
function inputGeometry({pivot,bob,pivotTolerancePx=0,bobTolerancePx=0,width=832,height=480}) {
  const finitePair=a=>Array.isArray(a)&&a.length===2&&a.every(Number.isFinite);
  if(!finitePair(pivot)||!finitePair(bob)) throw Error("two finite point pairs required");
  if(![width,height].every(x=>Number.isInteger(x)&&x>0)) throw Error("image dimensions");
  if(![pivotTolerancePx,bobTolerancePx].every(x=>Number.isFinite(x)&&x>=0)) throw Error("nonnegative location tolerances");
  for(const p of [pivot,bob]) if(p[0]<0||p[0]>width-1||p[1]<0||p[1]>height-1) throw Error("point outside image");
  const dx=bob[0]-pivot[0],dy=bob[1]-pivot[1],r=Math.hypot(dx,dy);
  if(r===0) throw Error("undefined direction/radius");
  const e=pivotTolerancePx+bobTolerancePx;
  const xs=[dx-e,dx+e],ys=[dy-e,dy+e];
  // Bounded location error is a square in each point's image coordinates.
  // Restrict this audit to observed pendulum bobs strictly below the pivot;
  // it avoids angle wrapping without relabeling projected geometry.
  if(ys[0]<=0) throw Error("uncertainty reaches pivot height; explicit geometry review required");
  const corners=xs.flatMap(x=>ys.map(y=>[x,y]));
  const thetaRange=corners.map(([x,y])=>Math.atan2(x,y));
  const minAbs=([lo,hi])=>lo>0?lo:hi<0?-hi:0;
  const radiusMin=Math.hypot(minAbs(xs),minAbs(ys));
  const radiusMax=Math.max(...corners.map(p=>Math.hypot(...p)));
  return {theta0:Math.atan2(dx,dy),radiusPx:r,
    thetaRange:[Math.min(...thetaRange),Math.max(...thetaRange)],
    radiusRangePx:[radiusMin,radiusMax],
    inwardVelocitySign:xs[0]>0?-1:xs[1]<0?1:null,
    uncertaintyModel:"independent per-coordinate hard bounds; not statistical CI"};
}
function harmonicStart(g,{amplitudeDeg=85,periodS,direction="inward",releaseFromRest=false,velocitySign=null}){
  if(!g||!Number.isFinite(g.theta0)) throw Error("geometry");
  if(typeof releaseFromRest!=="boolean") throw Error("boolean rest");
  if(!Number.isFinite(periodS)||periodS<=0) throw Error("positive period");
  const theta0=g.theta0,A=releaseFromRest?Math.abs(theta0):amplitudeDeg*Math.PI/180;
  if(!Number.isFinite(A)||A<Math.abs(theta0)||A>=Math.PI) throw Error("initial angle outside libration amplitude");
  if(!releaseFromRest && A<Math.max(...g.thetaRange.map(Math.abs))) throw Error("amplitude not compatible with entire geometry bound");
  const w=2*Math.PI/periodS;
  if(releaseFromRest) return {theta0,amplitudeRad:A,angularVelocity0:0,periodS,mode:"harmonic prescribed rest",temporalLaw:"small-angle harmonic, not exact nonlinear dynamics"};
  let sign=velocitySign;
  if(sign===null) {
    if(direction!=="inward"&&direction!=="outward") throw Error("direction");
    if(g.inwardVelocitySign===null) throw Error("inward/outward ambiguous within location bounds; supply absolute +/- velocitySign");
    sign=g.inwardVelocitySign*(direction==="inward"?1:-1);
  }
  if(sign!==-1&&sign!==1) throw Error("explicit angular velocity sign +/-1");
  const v0=sign*w*Math.sqrt(Math.max(0,(A-theta0)*(A+theta0)));
  return {theta0,amplitudeRad:A,angularVelocity0:v0,periodS,
    mode:"harmonic prescribed non-rest",temporalLaw:"small-angle harmonic, not exact nonlinear dynamics"};
}
function angularPosition(s,t){
  const w=2*Math.PI/s.periodS;
  return s.theta0*Math.cos(w*t)+(s.angularVelocity0/w)*Math.sin(w*t);
}
function imagePoint(pivot,r,theta){return [pivot[0]+r*Math.sin(theta),pivot[1]+r*Math.cos(theta)];}
function cvRotatePoint(point,pivot,alpha){
  const dx=point[0]-pivot[0],dy=point[1]-pivot[1],c=Math.cos(alpha),s=Math.sin(alpha);
  return [pivot[0]+c*dx+s*dy,pivot[1]-s*dx+c*dy];
}
function sweepBounds(pivot,r,amplitudeRad,{width=832,height=480,objectRadiusPx=0}={}){
  if(![...pivot,r,amplitudeRad,objectRadiusPx].every(Number.isFinite)||r<=0||amplitudeRad<0||amplitudeRad>=Math.PI||objectRadiusPx<0) throw Error("sweep parameters");
  const angles=[-amplitudeRad,amplitudeRad,0];
  for(let k=-2;k<=2;k++) if(Math.abs(k*Math.PI/2)<=amplitudeRad) angles.push(k*Math.PI/2);
  const pts=angles.map(a=>imagePoint(pivot,r,a));
  const x=[Math.min(...pts.map(p=>p[0]))-objectRadiusPx,Math.max(...pts.map(p=>p[0]))+objectRadiusPx];
  const y=[Math.min(...pts.map(p=>p[1]))-objectRadiusPx,Math.max(...pts.map(p=>p[1]))+objectRadiusPx];
  return {x,y,inside:x[0]>=0&&x[1]<=width-1&&y[0]>=0&&y[1]<=height-1,
    scope:objectRadiusPx===0?"bob center only; mask/crop extent untested":"bob disk only; rod/mask extent untested"};
}


const fn={inputGeometry,harmonicStart,angularPosition,imagePoint,cvRotatePoint,sweepBounds};
let checks=0;const check=(x,m)=>{if(!x)throw Error(m);checks++;};
const throws=f=>{let yes=false;try{f();}catch{yes=true;}check(yes,"expected reject");};
let maxPointError=0,maxAngleError=0,scenes=0;
for(const thetaDeg of [-60,-10,-2,2,10,60]) for(const P of [.6,1.186,2.0162]) for(const direction of ["inward","outward"]){
  const pivot=[416,100],r=150,theta=thetaDeg*Math.PI/180,bob=fn.imagePoint(pivot,r,theta);
  const g=fn.inputGeometry({pivot,bob,pivotTolerancePx:.1,bobTolerancePx:.1});
  const s=fn.harmonicStart(g,{periodS:P,direction});
  const th=fn.angularPosition(s,0);maxAngleError=Math.max(maxAngleError,Math.abs(th-theta));
  const vNumerical=(fn.angularPosition(s,1e-7)-fn.angularPosition(s,-1e-7))/(2e-7);
  check(Math.abs(vNumerical-s.angularVelocity0)<1e-7,"derivative");
  check(Math.sign(s.angularVelocity0)*Math.sign(theta)===(direction==="inward"?-1:1),"inward sign");
  for(const targetDeg of [-85,-45,0,45,85]){
    const target=targetDeg*Math.PI/180,expected=fn.imagePoint(pivot,r,target),actual=fn.cvRotatePoint(bob,pivot,target-theta);
    maxPointError=Math.max(maxPointError,Math.hypot(actual[0]-expected[0],actual[1]-expected[1]));
  }
  const slow=fn.harmonicStart(g,{periodS:P*1.7,direction});
  check(Math.abs(s.angularVelocity0/slow.angularVelocity0-1.7)<1e-12,"matched x1.7 velocity");
  for(const t of [0,.1,.4])check(Math.abs(fn.angularPosition(s,t)-fn.angularPosition(slow,t*1.7))<1e-13,"time dilation");
  scenes++;
}
const base={pivot:[416,100],bob:[416,250],pivotTolerancePx:1,bobTolerancePx:2};
const vert=fn.inputGeometry(base);
check(vert.inwardVelocitySign===null,"vertical uncertainty");
throws(()=>fn.harmonicStart(vert,{periodS:1.186}));
const signed=fn.harmonicStart(vert,{periodS:1.186,velocitySign:1});
check(signed.angularVelocity0>0,"absolute velocity at vertical");
const rest=fn.harmonicStart(vert,{periodS:1.186,releaseFromRest:true});
check(rest.amplitudeRad===0&&rest.angularVelocity0===0,"static equilibrium no oscillation");
throws(()=>fn.inputGeometry({...base,bob:[416,100]}));
throws(()=>fn.inputGeometry({...base,bob:[416,102]}));
throws(()=>fn.inputGeometry({...base,bob:[900,250]}));
throws(()=>fn.harmonicStart(vert,{periodS:0}));
throws(()=>fn.harmonicStart(vert,{periodS:1,amplitudeDeg:0,velocitySign:1}));
check(fn.sweepBounds([416,100],150,85*Math.PI/180).inside,"center inside");
check(!fn.sweepBounds([10,100],150,85*Math.PI/180).inside,"clipped center");
check(!fn.sweepBounds([416,100],150,85*Math.PI/180,{objectRadiusPx:200}).inside,"clipped disk");
const g=fn.inputGeometry({pivot:[400,100],bob:[425,250],pivotTolerancePx:2,bobTolerancePx:3});
for(let a=-2;a<=2;a++)for(let b=-2;b<=2;b++)for(let c=-3;c<=3;c++)for(let d=-3;d<=3;d++){
  const dx=425+c-(400+a),dy=250+d-(100+b),theta=Math.atan2(dx,dy),r=Math.hypot(dx,dy);
  check(theta>=g.thetaRange[0]-1e-14&&theta<=g.thetaRange[1]+1e-14,"angle bounds");
  check(r>=g.radiusRangePx[0]-1e-12&&r<=g.radiusRangePx[1]+1e-12,"radius bounds");
}
const summary={checks,syntheticBoundaryStates:scenes,geometryPerturbations:1225,
  maxAngleErrorRad:maxAngleError,maxPointErrorPx:maxPointError};
const sceneRecords=[
 {scene:"real06",pivot:[322,121],bob:[207,154],tolerance:6},
 {scene:"real14",pivot:[324,122],bob:[333,252],tolerance:5}
];
let envelopeSamples=0;
const sceneResults=sceneRecords.map(s=>{
  const g=inputGeometry({pivot:s.pivot,bob:s.bob,
      pivotTolerancePx:s.tolerance,bobTolerancePx:s.tolerance});
  const ext=g.radiusRangePx.map(r=>sweepBounds(s.pivot,r,85*Math.PI/180));
  const envelope={x:[Math.min(...ext.map(e=>e.x[0]))-s.tolerance,
                     Math.max(...ext.map(e=>e.x[1]))+s.tolerance],
                  y:[Math.min(...ext.map(e=>e.y[0]))-s.tolerance,
                     Math.max(...ext.map(e=>e.y[1]))+s.tolerance]};
  for(const r of g.radiusRangePx)for(let i=0;i<=1000;i++)
    for(const ox of [-s.tolerance,s.tolerance])for(const oy of [-s.tolerance,s.tolerance]){
      const p=imagePoint([s.pivot[0]+ox,s.pivot[1]+oy],r,(-85+170*i/1000)*Math.PI/180);
      if(p[0]<envelope.x[0]-1e-10||p[0]>envelope.x[1]+1e-10||
         p[1]<envelope.y[0]-1e-10||p[1]>envelope.y[1]+1e-10)throw Error("envelope");
      envelopeSamples++;
    }
  const starts=[1.186,2.0162].map(periodS=>{
    const state=harmonicStart(g,{periodS,velocitySign:-Math.sign(g.theta0)});
    const points=Array.from({length:93},(_,i)=>imagePoint(s.pivot,g.radiusPx,angularPosition(state,i/24)));
    const travels=points.slice(1).map((p,i)=>Math.hypot(p[0]-points[i][0],p[1]-points[i][1]));
    return {...state,bobFrame1:points[1],maxConsecutiveCenterDisplacementPx:Math.max(...travels)};
  });
  return {scene:s.scene,geometry:g,envelope,starts};
});
const result={summary,envelopeSamples,sceneResults,
 scope:"software and owner-pasted image geometry; no source/media/Nano/referee validation"};

console.log(JSON.stringify(result,null,2));
