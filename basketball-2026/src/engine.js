/* Court Kings '26. Original arcade basketball engine, no dependencies. */
(function (root) {
  'use strict';
  const W = 1200, H = 650, FLOOR = 503, GRAVITY = 1230;
  const HOOPS = [{ x: 145, y: 266 }, { x: 1055, y: 266 }];
  const clamp = (n, lo, hi) => Math.max(lo, Math.min(hi, n));
  const STARS = [
    { id:'curry', name:'Stephen Curry', short:'CURRY', num:30, role:'Deep-range shooter', special:'Logo range', shoot:99, speed:90, defense:78, power:75, skin:'#b97950', hair:'#251b19', beard:true, style:'crop', color:'#427aff', accent:'#f8cf52', height:131 },
    { id:'luka', name:'Luka Dončić', short:'DONČIĆ', num:77, role:'Shot creator', special:'Wide release window', shoot:96, speed:79, defense:80, power:88, skin:'#e7b792', hair:'#49342d', beard:true, style:'sweep', color:'#aa7bf3', accent:'#f4d566', height:139 },
    { id:'shai', name:'Shai Gilgeous-Alexander', short:'SGA', num:2, role:'Slashing guard', special:'Quick first step', shoot:94, speed:97, defense:92, power:82, skin:'#825139', hair:'#1e1615', style:'braids', color:'#1dd6c4', accent:'#f27840', height:136 },
    { id:'wemby', name:'Victor Wembanyama', short:'WEMBY', num:1, role:'Rim protector', special:'Extended block reach', shoot:87, speed:85, defense:99, power:91, skin:'#b87d59', hair:'#272019', style:'curl', color:'#c3c8d3', accent:'#3a424e', height:155 },
    { id:'jokic', name:'Nikola Jokić', short:'JOKIĆ', num:15, role:'Post technician', special:'Protected post game', shoot:94, speed:73, defense:87, power:98, skin:'#e8b99a', hair:'#655046', style:'crop', color:'#3e76bc', accent:'#f4c052', height:147 },
    { id:'giannis', name:'Giannis Antetokounmpo', short:'GIANNIS', num:34, role:'Downhill finisher', special:'Long-distance dunks', shoot:78, speed:93, defense:96, power:99, skin:'#805035', hair:'#221c17', style:'curl', color:'#47bb84', accent:'#e2e9c8', height:146 },
    { id:'lebron', name:'LeBron James', short:'LEBRON', num:23, role:'Power wing', special:'Powerful takeoff', shoot:89, speed:86, defense:90, power:99, skin:'#805238', hair:'#261b17', beard:true, style:'crop', color:'#e0b74e', accent:'#8962d7', height:142 },
    { id:'kd', name:'Kevin Durant', short:'DURANT', num:35, role:'Tall shot-maker', special:'High release point', shoot:98, speed:83, defense:90, power:82, skin:'#895438', hair:'#201713', beard:true, style:'crop', color:'#ea6650', accent:'#ededeb', height:148 },
    { id:'ant', name:'Anthony Edwards', short:'ANT', num:5, role:'Explosive guard', special:'Fast heat charge', shoot:90, speed:96, defense:91, power:94, skin:'#875335', hair:'#231b16', style:'curl', color:'#4c81b6', accent:'#b8ee61', height:136 },
    { id:'brunson', name:'Jalen Brunson', short:'BRUNSON', num:11, role:'Crafty guard', special:'Quick shot gather', shoot:95, speed:88, defense:83, power:83, skin:'#b88158', hair:'#292019', beard:true, style:'braids', color:'#eb803c', accent:'#5393f1', height:129 },
    { id:'booker', name:'Devin Booker', short:'BOOKER', num:1, role:'Midrange scorer', special:'Smooth release', shoot:97, speed:88, defense:82, power:84, skin:'#d3a27b', hair:'#34251e', beard:true, style:'crop', color:'#bb74d8', accent:'#f3a748', height:136 },
    { id:'mitchell', name:'Donovan Mitchell', short:'MITCHELL', num:45, role:'Attacking guard', special:'Quick first step', shoot:93, speed:96, defense:86, power:87, skin:'#815138', hair:'#231c16', style:'curl', color:'#b8455b', accent:'#ecc881', height:132 }
  ];
  function rng(seed) { return () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  function player(star, side) {
    return { star, side, x: side ? 770 : 430, y:FLOOR, vx:0, vy:0, facing:side ? -1 : 1,
      charge:null, heat:0, stamina:100, dash:0, dashCD:0, stealCD:0, block:0, fake:0, stun:0, shield:0,
      score:0, stats:{ attempts:0, made:0, threes:0, dunks:0, steals:0, blocks:0 }, aiWait:0.6, aiCharging:false, aiTarget:0.73 };
  }
  class Game {
    constructor(options={}) {
      this.random = rng(options.seed || 26); this.events=[]; this.time=0; this.particles=[];
      this.start({ mode:'solo', duration:90, difficulty:'normal', star0:'curry', star1:'wemby', ...options });
      if (options.idle) this.state='idle';
    }
    start(options={}) {
      this.options={ mode:'solo', duration:90, difficulty:'normal', star0:'curry', star1:'wemby', ...options };
      this.mode=this.options.mode;
      this.players=[player(STARS.find(s=>s.id===this.options.star0)||STARS[0],0), player(STARS.find(s=>s.id===this.options.star1)||STARS[3],1)];
      this.remaining=Number(this.options.duration); this.shotClock=12; this.overtime=false; this.buzzer=false;
      this.state='countdown'; this.stateTimer=2.8; this.winner=null; this.notice=''; this.noticeTimer=0; this.result=null; this.time=0;
      this.ball={ x:430, y:FLOOR-66, vx:0, vy:0, owner:0, shooter:null, shot:false, special:false, value:2, trail:[], age:0, scored:false, rebound:false, pickupDelay:0.4 };
      if(this.mode==='practice') { this.players[0].x=720; this.players[0].heat=100; }
      this.events=[]; this.emit('start');
    }
    emit(type, data={}) { this.events.push({type,...data}); }
    setNotice(s,t=1.0) { this.notice=s; this.noticeTimer=t; }
    target(p) { return HOOPS[p.side===0?1:0]; }
    jump(p) { if(p.y>=FLOOR-1 && p.stun<=0) { p.vy=-(652+(p.star.power-80)*2.0); this.emit('jump'); return true; } return false; }
    dash(p,dir) { if(p.dashCD<=0 && p.stamina>=28 && p.stun<=0) { p.dash=0.17; p.dashCD=0.8; p.stamina-=28; p.facing=dir||p.facing; p.vx=p.facing*805; this.emit('dash'); } }
    beginShot(p) { if(this.ball.owner===p.side && p.charge===null && p.stun<=0) { p.charge=0; if(p.y>=FLOOR-1) this.jump(p); } }
    release(p,special=false) {
      if(this.ball.owner!==p.side || (p.charge===null&&!special)) {p.charge=null;return;}
      const target=this.target(p), distance=Math.abs(target.x-p.x);
      if(p.y<FLOOR-105 && distance<(p.star.id==='giannis'?139:93) && !special) { this.dunk(p); return; }
      const charge=p.charge===null?0.73:p.charge; p.charge=null;
      const opp=this.players[1-p.side];
      const contest=this.mode==='practice'?0:clamp(1-Math.abs(p.x-opp.x)/126,0,1)*clamp((FLOOR-opp.y+45)/140,0,1);
      const window=this.greenWindow(p);
      const green=Math.abs(charge-0.73)<=window;
      const error=special?0:(green?((this.random()-0.5)*9):(charge-0.73)*240+(this.random()-0.5)*26)+((this.random()-0.5)*contest*56);
      const ball=this.ball;
      ball.x=p.x+p.facing*18; ball.y=p.y-(p.star.id==='kd'?132:p.star.height-28);
      const travel=0.76+distance/1350;
      ball.vx=(target.x+error-ball.x)/travel; ball.vy=(target.y-ball.y-0.5*GRAVITY*travel*travel)/travel;
      ball.owner=null; ball.shooter=p.side; ball.shot=true; ball.special=special; ball.value=special?3:distance>=345?3:2;
      ball.age=0; ball.scored=false; ball.rebound=false; ball.pickupDelay=.16; ball.trail=[];
      p.stats.attempts++; p.shield=0.25;
      if(special) {p.heat=0;this.setNotice('SUPER SHOT',0.8);this.emit('super');}
      else {this.setNotice(green?(contest>.45?'GREEN · CONTESTED':'GREEN RELEASE'):charge<.73-window?'EARLY RELEASE':'LATE RELEASE',.85);this.emit(green?'green':'shoot');}
      this.emit('shot',{side:p.side,green,special,value:ball.value});
    }
    greenWindow(p) { return .035+(p.star.shoot-75)*.00125+(p.star.id==='luka'?.02:0)+(p.star.id==='booker'?.008:0); }
    heat(p,n) {p.heat=clamp(p.heat+n*(p.star.id==='ant'?1.3:1),0,100);}
    dunk(p) {
      p.charge=null; p.stats.attempts++; p.stats.dunks++;
      this.ball.owner=null; this.ball.shooter=p.side; this.ball.shot=true; this.ball.special=false; this.ball.value=2;
      this.ball.x=this.target(p).x; this.ball.y=this.target(p).y; this.ball.vx=0; this.ball.vy=160;
      this.score(p.side,2,'DUNK'); this.emit('dunk',{side:p.side});
    }
    action(p) {
      if(this.ball.owner===p.side) {this.beginShot(p);return;}
      if(p.stealCD>0 || p.stun>0) return;
      p.stealCD=.8; p.fake=.23;
      const opp=this.players[1-p.side], b=this.ball;
      if(b.owner===opp.side && Math.abs(p.x-opp.x)<83 && Math.abs(p.y-opp.y)<60 && opp.shield<=0) {
        const chance=clamp(.64+(p.star.defense-85)*.008-(opp.star.power-85)*.004,.35,.83);
        if(this.random()<chance) {this.takeBall(p);opp.stun=.24;opp.charge=null;p.stats.steals++;this.heat(p,18);this.setNotice('STEAL',.75);this.emit('steal',{side:p.side});}
        else {p.stun=.16; this.emit('swipe');}
      } else this.emit('swipe');
    }
    defend(p) {
      if(this.ball.owner===p.side) {p.charge=null;p.fake=.38;p.shield=.22;this.emit('fake');}
      else if(p.block<=0&&p.stun<=0) {p.block=.65;this.jump(p);this.emit('swipe');}
    }
    takeBall(p) {
      const b=this.ball;b.owner=p.side;b.shooter=null;b.shot=false;b.special=false;b.scored=false;b.rebound=false;b.vx=0;b.vy=0;b.trail=[];
      p.shield=.36; p.charge=null;this.shotClock=12;
      if(this.mode==='practice') p.heat=100;
      if(this.buzzer) this.end();
    }
    turnOver(side,label) {
      const p=this.players[side];this.ball.owner=side;this.ball.shot=false;this.ball.special=false;this.ball.shooter=null;this.ball.trail=[];
      for(const q of this.players) {q.charge=null;q.vx=0;q.vy=0;q.y=FLOOR;}
      p.x=side?865:335;this.players[1-side].x=side?635:565;p.shield=.85;this.shotClock=12;
      this.state='inbound';this.stateTimer=.7;this.setNotice(label,1);this.emit('whistle');
    }
    score(side,value,label) {
      if(this.ball.scored) return;
      const p=this.players[side];p.score+=value;p.stats.made++;if(value===3)p.stats.threes++;this.heat(p,value===3?30:24);
      this.ball.scored=true;this.ball.shot=false;this.ball.special=false;this.ball.trail=[];this.ball.vx=0;this.ball.vy=160;
      this.setNotice(label|| (value===3?'THREE POINTER':'BUCKET'),1.0);this.emit('score',{side,value});
      if(this.overtime || this.buzzer) {this.end();return;}
      this.state='scored';this.stateTimer=1.05;
    }
    end() {
      if(this.mode==='practice') return;
      if(this.players[0].score===this.players[1].score) {this.overtime=true;this.buzzer=false;this.state='inbound';this.stateTimer=.8;this.shotClock=12;this.ball.owner=Math.floor(this.random()*2);this.ball.shot=false;this.setNotice('OVERTIME · NEXT BASKET WINS',2.0);this.emit('whistle');return;}
      this.state='ended';this.winner=this.players[0].score>this.players[1].score?0:1;
      this.result={winner:this.winner,score:this.players.map(p=>p.score),stats:this.players.map(p=>({...p.stats})),overtime:this.overtime};this.emit('end',this.result);
    }
    update(dt, inputs=[{},{}]) {
      dt=clamp(dt,0,.035);this.time+=dt;this.noticeTimer=Math.max(0,this.noticeTimer-dt);
      if(['paused','ended','idle'].includes(this.state)) return;
      if(['countdown','inbound'].includes(this.state)) {this.stateTimer-=dt;this.followBall();if(this.stateTimer<=0) {this.state='playing';this.emit('whistle');}return;}
      if(this.state==='scored') {
        this.stateTimer-=dt;this.ball.y+=this.ball.vy*dt;this.ball.vy+=GRAVITY*dt;
        if(this.stateTimer<=0) { const side=this.mode==='practice'?0:1-this.ball.shooter;this.turnOver(side,'');if(this.mode==='practice'){this.players[0].x=720;this.players[0].heat=100;} } return;
      }
      if(!this.overtime && !this.buzzer && this.mode!=='practice') {
        this.remaining=Math.max(0,this.remaining-dt);
        if(this.remaining===0) {this.buzzer=true;this.emit('buzzer');if(!this.ball.shot){this.end();return;}}
      }
      if(this.ball.owner!==null && this.mode!=='practice'&&!this.buzzer) {
        this.shotClock-=dt;if(this.shotClock<=0) {this.turnOver(1-this.ball.owner,'SHOT CLOCK');return;}
      }
      if(this.mode==='solo'||this.mode==='tournament') inputs=[inputs[0]||{},this.bot(dt)];
      for(let i=0;i<2;i++) {
        const p=this.players[i], input=inputs[i]||{};if(this.mode==='practice'&&i===1)continue;
        for(const key of ['dash','dashCD','stealCD','block','fake','stun','shield','aiWait']) p[key]=Math.max(0,p[key]-dt);
        p.stamina=clamp(p.stamina+(p.dash>0?0:23)*dt,0,100);
        if(p.stun<=0) {
          if(input.jump)this.jump(p);if(input.dash)this.dash(p,input.move||p.facing);
          if(input.defend)this.defend(p);if(input.action)this.action(p);
          if(input.super && this.ball.owner===i&&p.heat>=99.9)this.release(p,true);
          if(input.release)this.release(p);
        }
        let move=p.stun>0?0:clamp(input.move||0,-1,1);
        if(move)p.facing=move;
        if(p.dash<=0) {let target=move*(285+(p.star.speed-75)*3.2)*(p.charge!==null?.45:1);const amount=2400*dt;p.vx+=clamp(target-p.vx,-amount,amount);}
        p.x=clamp(p.x+p.vx*dt,77,W-77);p.vy+=GRAVITY*dt;p.y+=p.vy*dt;
        if(p.y>=FLOOR){p.y=FLOOR;p.vy=0;}
        if(p.charge!==null) {p.charge+=dt/(p.star.id==='brunson'?.86:1.0);if(p.charge>=1.13)this.release(p);}
      }
      this.resolvePlayers();this.updateBall(dt);
      if(this.buzzer&&this.state==='playing'&&(!this.ball.shot||this.ball.age>4))this.end();
    }
    resolvePlayers() {
      if(this.mode==='practice')return;
      const [a,b]=this.players,delta=b.x-a.x;
      if(Math.abs(delta)<45 && Math.abs(a.y-b.y)<75) {const push=(45-Math.abs(delta))*.5*(delta>=0?1:-1);a.x=clamp(a.x-push,77,W-77);b.x=clamp(b.x+push,77,W-77);}
    }
    followBall() {
      const b=this.ball;if(b.owner===null)return;const p=this.players[b.owner];
      b.x=p.x+p.facing*30;
      b.y=p.y-(p.charge!==null?p.star.height-30:p.fake>0?100:35+Math.abs(Math.sin(this.time*10))*32);
    }
    updateBall(dt) {
      const b=this.ball; if(b.owner!==null){this.followBall();return;}
      b.age+=dt;b.pickupDelay=Math.max(0,b.pickupDelay-dt);
      const ox=b.x,oy=b.y;b.vy+=GRAVITY*dt;b.x+=b.vx*dt;b.y+=b.vy*dt;
      if(b.shot) {
        b.trail.push({x:b.x,y:b.y});if(b.trail.length>16)b.trail.shift();
        const target=HOOPS[b.shooter===0?1:0];
        if(!b.special) for(const p of this.players) {
          if(p.side===b.shooter || p.block<=0 || (this.mode==='practice'&&p.side===1))continue;
          const reach=p.star.id==='wemby'?48:31;
          const hx=p.x+p.facing*21,hy=p.y-p.star.height-6;
          if(Math.hypot(b.x-hx,b.y-hy)<reach+12) {
            b.vx=p.facing*(230+this.random()*120);b.vy=-210;b.shot=false;b.special=false;b.trail=[];b.pickupDelay=.3;
            p.stats.blocks++;this.heat(p,23);this.setNotice('BLOCK',.85);this.emit('block',{side:p.side});break;
          }
        }
        if(b.shot && b.vy>0 && oy<=target.y && b.y>=target.y) {
          const crossX=ox+(b.x-ox)*(target.y-oy)/(b.y-oy);
          if(Math.abs(crossX-target.x)<17) {b.x=target.x;this.score(b.shooter,b.value);return;}
        }
      }
      for(const hoop of HOOPS) {
        const bx=hoop.x+(hoop.x>W/2?48:-48);
        if(b.y>hoop.y-100 && b.y<hoop.y+12 && ((ox-bx)*(b.x-bx)<0)) {b.x=ox;b.vx*=-.63;b.rebound=true;this.emit('rim');}
        if(!b.scored) for(const rx of [hoop.x-28,hoop.x+28]) {
          const dx=b.x-rx,dy=b.y-hoop.y,d=Math.hypot(dx,dy);
          if(d<15&&d>0) {const nx=dx/d,ny=dy/d;b.x=rx+nx*15;b.y=hoop.y+ny*15;const dot=b.vx*nx+b.vy*ny;if(dot<0){b.vx-=1.6*dot*nx;b.vy-=1.6*dot*ny;b.rebound=true;this.emit('rim');}}
        }
      }
      if(b.x<55||b.x>W-55) {b.x=clamp(b.x,55,W-55);b.vx*=-.65;}
      if(b.y>FLOOR-11) {b.y=FLOOR-11;b.vy=-Math.abs(b.vy)*.60;b.vx*=.78;if(b.shot) {this.heat(this.players[b.shooter],8);this.emit('miss',{side:b.shooter});b.shot=false;b.special=false;b.trail=[];}if(Math.abs(b.vy)<60)b.vy=0;}
      if(b.pickupDelay<=0&&!b.scored) for(const p of this.players) {
        if(this.mode==='practice'&&p.side===1)continue;
        if(b.shot&&p.side===b.shooter&&!b.rebound)continue;
        if(p.stun<=0 && Math.abs(p.x-b.x)<49 && b.y>p.y-p.star.height-10 && b.y<p.y+7) {this.takeBall(p);this.emit('catch');break;}
      }
      if(this.mode==='practice'&&b.owner===null&&!b.shot&&b.age>3.6)this.takeBall(this.players[0]);
    }
    bot(dt) {
      const p=this.players[1],opp=this.players[0],b=this.ball;
      const difficulty=this.options.difficulty, scale=difficulty==='easy'?.65:difficulty==='hard'?1.2:1;
      const input={};let tx=p.x;
      if(b.owner===1) {
        const target=this.target(p);const dist=Math.abs(p.x-target.x);
        if(p.charge!==null) {
          if(p.charge>=p.aiTarget)input.release=true;
          if(Math.abs(opp.x-p.x)<70&&opp.block>0&&p.fake<=0&&this.random()<.003*scale){input.defend=true;p.aiWait=.5;}
        } else if(p.aiWait<=0) {
          if(p.heat>=100&&this.random()<(difficulty==='easy'?.32:.75))input.super=true;
          else if(dist<340 || (dist<595 && Math.abs(opp.x-p.x)>135 && this.random()<.005*scale)) {
            input.action=true;
            const variance=difficulty==='easy'?.23:difficulty==='hard'?.025:.10;
            p.aiTarget=.73+(this.random()-.5)*variance*2;p.aiWait=.55/scale;
          } else {tx=target.x+175;if(Math.abs(opp.x-p.x)<115&&p.dashCD<=0&&this.random()<.008*scale)input.dash=true;}
        }
      } else if(b.owner===0) {
        tx=clamp(opp.x+(opp.x<1055?62:-62),180,1070);
        if(Math.abs(p.x-opp.x)<95) {
          if(opp.charge!==null && opp.charge>.20/scale && p.y>=FLOOR-1)input.defend=true;
          else if(opp.charge===null&&p.stealCD<=0&&this.random()<.023*scale)input.action=true;
        }
      } else {
        if(b.shot) {
          tx=b.x+b.vx*.2;
          if(Math.abs(p.x-b.x)<125 && b.y>p.y-220 && b.y<p.y-70 && b.vy>0&&p.y>=FLOOR-1)input.defend=true;
        } else tx=b.x+b.vx*.13;
        if(b.y<p.y-75 && b.y>p.y-200 && Math.abs(p.x-b.x)<65&&p.y>=FLOOR-1)input.jump=true;
      }
      input.move=Math.abs(tx-p.x)>18?(tx>p.x?1:-1):0;return input;
    }
    pause() {if(this.state==='paused'){this.state=this.previousState;this.emit('resume');}else if(!['ended','idle'].includes(this.state)){this.previousState=this.state;this.state='paused';this.emit('pause');}}
    snapshot() {return {state:this.state,mode:this.mode,remaining:this.remaining,shotClock:this.shotClock,overtime:this.overtime,ball:{...this.ball,trail:undefined},players:this.players.map(p=>({name:p.star.name,x:p.x,y:p.y,score:p.score,heat:p.heat,charge:p.charge,stats:{...p.stats}}))};}
  }
  const api={Game,STARS,HOOPS,W,H,FLOOR,GRAVITY,clamp,rng};
  root.Court26=api;if(typeof module!=='undefined'&&module.exports)module.exports=api;
})(typeof globalThis!=='undefined'?globalThis:window);
