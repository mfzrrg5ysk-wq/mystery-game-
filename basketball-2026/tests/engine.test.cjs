const test=require('node:test');
const assert=require('node:assert/strict');
const {Game,STARS,FLOOR,HOOPS}=require('../src/engine.js');
const dt=1/120;
function live(options={}){const g=new Game({mode:'versus',duration:90,seed:5,...options});g.state='playing';return g;}
function advance(g,seconds,controls=[{},{}]){for(let i=0;i<Math.ceil(seconds/dt);i++)g.update(dt,controls);}
function shot(g,side,x,charge=.73,special=false){const p=g.players[side];g.ball.owner=side;g.ball.scored=false;p.x=x;p.y=FLOOR-150;p.charge=charge;g.players[1-side].x=side?1020:180;g.release(p,special);return p;}

test('a timed three and a close two go through the attacked hoop',()=>{
 for(const [side,x,expected] of [[0,600,3],[0,900,2],[1,600,3],[1,300,2]]){
  const g=live(),p=shot(g,side,x);advance(g,1.8);
  assert.equal(p.score,expected);assert.equal(p.stats.made,1);assert.equal(g.players[1-side].score,0);
 }
});
test('early and late releases miss instead of receiving automatic points',()=>{
 for(const charge of [.15,1.08]){const g=live(),p=shot(g,0,600,charge);advance(g,3);assert.equal(p.score,0);assert.equal(p.stats.made,0);assert.equal(p.stats.attempts,1);}
});
test('the shooter cannot catch an unrebounced shot immediately after releasing',()=>{
 const g=live(),p=g.players[0];p.x=900;p.y=FLOOR-100;p.charge=.73;g.release(p);advance(g,.22);
 assert.equal(g.ball.owner,null);assert.equal(p.stats.attempts,1);
});
test('an airborne finish near the rim counts once as a dunk',()=>{
 const g=live(),p=shot(g,0,1010);assert.equal(p.score,2);assert.equal(p.stats.dunks,1);assert.equal(p.stats.attempts,1);advance(g,.6);assert.equal(p.score,2);
});
test('super shots spend heat and score three from inside the arc',()=>{
 const g=live(),p=g.players[0];p.heat=100;shot(g,0,920,.12,true);assert.equal(p.heat,0);advance(g,1.6);assert.equal(p.score,3);assert.equal(p.stats.threes,1);
});
test('a collision with a raised hand blocks a shot and grants defensive heat',()=>{
 const g=live(),p=g.players[1];p.x=820;p.y=FLOOR-130;p.block=.5;
 const b=g.ball;b.owner=null;b.shot=true;b.shooter=0;b.pickupDelay=1;b.x=p.x+p.facing*21;b.y=p.y-p.star.height-6;b.vx=0;b.vy=0;
 g.updateBall(dt);assert.equal(p.stats.blocks,1);assert.equal(b.shot,false);assert.ok(p.heat>0);
});
test('a super shot cannot be blocked by raised hands',()=>{
 const g=live(),p=g.players[1];p.x=820;p.y=FLOOR-130;p.block=.5;
 const b=g.ball;b.owner=null;b.shot=true;b.special=true;b.shooter=0;b.pickupDelay=1;b.x=p.x+p.facing*21;b.y=p.y-p.star.height-6;b.vx=0;b.vy=0;
 g.updateBall(dt);assert.equal(p.stats.blocks,0);assert.equal(b.shot,true);
});
test('a successful steal changes possession and cannot be repeated through cooldown',()=>{
 const g=live(),[a,b]=g.players;g.random=()=>0;a.x=600;b.x=661;a.shield=0;g.ball.owner=0;g.action(b);
 assert.equal(g.ball.owner,1);assert.equal(b.stats.steals,1);assert.equal(a.charge,null);
 g.ball.owner=0;a.shield=0;g.action(b);assert.equal(b.stats.steals,1);
});
test('steals require proximity, and pump fakes protect the ball briefly',()=>{
 const g=live(),[a,b]=g.players;g.random=()=>0;a.x=400;b.x=700;a.shield=0;g.action(b);assert.equal(g.ball.owner,0);
 b.stealCD=0;b.x=465;g.defend(a);g.action(b);assert.equal(g.ball.owner,0);assert.ok(a.shield>0);
});
test('the possession clock transfers the ball instead of freezing a match',()=>{
 const g=live();g.shotClock=.005;g.update(dt);assert.equal(g.ball.owner,1);assert.equal(g.state,'inbound');assert.equal(g.shotClock,12);
});
test('a shot released before the buzzer resolves before the winner is chosen',()=>{
 const g=live();g.players[1].score=2;shot(g,0,600);g.remaining=.005;g.update(dt);assert.equal(g.buzzer,true);assert.equal(g.state,'playing');advance(g,1.8);assert.equal(g.state,'ended');assert.equal(g.winner,0);assert.equal(g.players[0].score,3);
});
test('a missed buzzer shot ends the match, and a tie starts sudden-death overtime',()=>{
 const g=live();g.players[1].score=2;shot(g,0,600,.1);g.remaining=.005;advance(g,4);assert.equal(g.state,'ended');assert.equal(g.winner,1);
 const tie=live();tie.remaining=.005;tie.update(dt);assert.equal(tie.overtime,true);advance(tie,1);shot(tie,0,600);advance(tie,1.8);assert.equal(tie.state,'ended');assert.equal(tie.winner,0);
});
test('pause freezes players and both clocks, then resumes the previous state',()=>{
 const g=live(),before=g.snapshot();g.pause();advance(g,2,[{move:1},{}]);assert.equal(g.remaining,before.remaining);assert.equal(g.shotClock,before.shotClock);assert.equal(g.players[0].x,before.players[0].x);g.pause();assert.equal(g.state,'playing');
});
test('practice has no timer, restores loose balls and refills super-shot heat',()=>{
 const g=live({mode:'practice'});const remaining=g.remaining;g.ball.owner=null;g.ball.shot=false;g.ball.x=70;g.ball.y=FLOOR-11;g.ball.vx=0;g.ball.vy=0;g.players[0].heat=0;advance(g,4);assert.equal(g.remaining,remaining);assert.equal(g.ball.owner,0);assert.equal(g.players[0].heat,100);
});
test('all stars and difficulties complete a match with finite physics and working AI',()=>{
 for(const star of STARS)for(const difficulty of ['easy','normal','hard']){
  const g=new Game({star1:star.id,difficulty,duration:30,seed:101});
  for(let i=0;i<120*120&&g.state!=='ended';i++){
   g.update(dt,[{},{}]);
   assert.ok(Number.isFinite(g.ball.x)&&Number.isFinite(g.ball.y));
   for(const p of g.players)assert.ok(Number.isFinite(p.x)&&Number.isFinite(p.y)&&p.stamina>=0&&p.stamina<=100);
  }
  assert.equal(g.state,'ended',`${star.name} / ${difficulty}`);assert.ok(g.players[1].stats.attempts>0);
 }
});
