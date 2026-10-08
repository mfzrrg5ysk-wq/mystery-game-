(function(root){
  'use strict';
  const {W,H,FLOOR,HOOPS,clamp}=root.Court26;
  const rounded=(c,x,y,w,h,r)=>{c.beginPath();c.roundRect(x,y,w,h,r);};
  const text=(c,s,x,y,size,color='#fff',align='center',weight=800)=>{c.font=`${weight} ${size}px Arial, sans-serif`;c.fillStyle=color;c.textAlign=align;c.textBaseline='middle';c.fillText(s,x,y);};
  function ball(c,x,y,r=12,spin=0,fire=false){
    c.save();c.translate(x,y);c.rotate(spin);if(fire){c.shadowColor='#ffac42';c.shadowBlur=30;}
    const g=c.createRadialGradient(-r*.3,-r*.4,1,0,0,r);g.addColorStop(0,'#ffc566');g.addColorStop(.55,'#ec852e');g.addColorStop(1,'#c15d23');
    c.fillStyle=g;c.beginPath();c.arc(0,0,r,0,Math.PI*2);c.fill();c.shadowBlur=0;c.strokeStyle='#492417';c.lineWidth=1.7;c.stroke();
    c.beginPath();c.moveTo(-r,0);c.lineTo(r,0);c.moveTo(0,-r);c.lineTo(0,r);c.stroke();
    c.beginPath();c.ellipse(-r*.7,0,r*.75,r,0,-Math.PI/2,Math.PI/2);c.ellipse(r*.7,0,r*.75,r,0,Math.PI/2,Math.PI*1.5);c.stroke();c.restore();
  }
  function person(c,p,t,opts={}){
    const s=p.star,face=p.facing||1,grounded=p.y>=FLOOR-1;
    const run=Math.sin(t*16)*Math.min(Math.abs(p.vx||0)/260,1),height=s.height;
    c.save();c.translate(p.x,p.y);if(opts.scale)c.scale(opts.scale,opts.scale);
    if(!opts.portrait){c.fillStyle='rgba(2,7,14,.28)';c.beginPath();c.ellipse(0,FLOOR-p.y+6,29+Math.min((FLOOR-p.y)*.09,16),7,0,0,Math.PI*2);c.fill();}
    const jump=!grounded&&!opts.portrait;
    c.lineCap='round';c.lineJoin='round';
    // Legs and shoes. The limbs are jointed around the actual player frame.
    c.strokeStyle=s.skin;c.lineWidth=13;
    for(const side of [-1,1]){
      const stride=run*side*13,knee=jump?side*19:side*11+stride;
      c.beginPath();c.moveTo(side*10,-35);c.lineTo(knee,-21);c.lineTo(side*14-stride,jump?-10:0);c.stroke();
      c.strokeStyle=side===-1?'#e7eaf1':'#a8b5cc';c.lineWidth=10;c.beginPath();c.moveTo(side*14-stride-5,jump?-7:0);c.lineTo(side*14-stride+12,jump?-7:0);c.stroke();c.strokeStyle=s.skin;c.lineWidth=13;
    }
    c.fillStyle=s.color;rounded(c,-22,-42,44,19,5);c.fill();c.fillStyle=s.accent;c.fillRect(-22,-43,44,4);
    c.fillStyle=s.color;rounded(c,-23,-84,46,48,[12,12,6,6]);c.fill();
    c.strokeStyle=s.accent;c.lineWidth=3;c.beginPath();c.moveTo(-20,-80);c.lineTo(-15,-50);c.moveTo(20,-80);c.lineTo(15,-50);c.stroke();
    c.fillStyle=s.skin;c.beginPath();c.ellipse(0,-83,9,5,0,0,Math.PI);c.fill();
    text(c,String(s.num),0,-61,23,'#fff', 'center',900);
    // Reaching arms are also the visual cue for the collision-based block.
    const shooting=p.charge!==null&&p.charge!==undefined,blocking=(p.block||0)>0,swipe=(p.fake||0)>0;
    c.strokeStyle=s.skin;c.lineWidth=12;
    for(const side of [-1,1]){
      let hx=side*29,hy=-54+run*side*4;
      if(shooting){hx=face*18+side*9;hy=-(height-30);}
      else if(blocking){hx=side*20;hy=-height-6;}
      else if(swipe&&side===face){hx=side*55;hy=-65;}
      c.beginPath();c.moveTo(side*23,-74);c.lineTo(side*32,shooting||blocking?-92:-65);c.lineTo(hx,hy);c.stroke();
      c.fillStyle=s.skin;c.beginPath();c.arc(hx,hy,7,0,Math.PI*2);c.fill();
    }
    const headY=-height+22,headR=30;
    c.fillStyle='#162030';c.beginPath();c.arc(0,headY,headR+2,0,Math.PI*2);c.fill();
    c.fillStyle=s.skin;c.beginPath();c.ellipse(0,headY,headR,32,0,0,Math.PI*2);c.fill();
    c.fillStyle=s.skin;c.beginPath();c.ellipse(-29,headY+1,5,8,0,0,Math.PI*2);c.ellipse(29,headY+1,5,8,0,0,Math.PI*2);c.fill();
    // Stylized original portraits; no extracted game artwork or team logos.
    c.fillStyle=s.hair;c.beginPath();c.arc(0,headY-3,30,Math.PI,Math.PI*2);c.lineTo(28,headY-9);c.quadraticCurveTo(5,headY-24,-28,headY-8);c.closePath();c.fill();
    if(s.style==='curl')for(let n=0;n<9;n++){c.beginPath();c.arc(-25+n*6.1,headY-25-Math.sin(n)*4,7,0,Math.PI*2);c.fill();}
    if(s.style==='sweep'){c.beginPath();c.moveTo(-27,headY-22);c.quadraticCurveTo(10,headY-47,31,headY-21);c.lineTo(18,headY-18);c.closePath();c.fill();}
    if(s.style==='braids'){c.strokeStyle=s.hair;c.lineWidth=5;for(let n=0;n<5;n++){c.beginPath();c.moveTo(-22+n*10,headY-29);c.quadraticCurveTo(-18+n*10,headY-37,-15+n*10,headY-31);c.stroke();}c.beginPath();c.moveTo(-face*25,headY-19);c.lineTo(-face*34,headY+21);c.stroke();}
    if(s.beard){c.fillStyle=s.hair;c.beginPath();c.moveTo(-25,headY+10);c.quadraticCurveTo(0,headY+46,25,headY+10);c.lineTo(22,headY+23);c.quadraticCurveTo(0,headY+44,-22,headY+23);c.closePath();c.fill();}
    const look=face*3;c.fillStyle='#fff';for(const side of [-1,1]){c.beginPath();c.ellipse(side*11+look,headY-1,6,4,0,0,Math.PI*2);c.fill();}
    c.fillStyle='#172335';for(const side of [-1,1]){c.beginPath();c.arc(side*11+look+face*2,headY,2.5,0,Math.PI*2);c.fill();}
    c.strokeStyle=s.hair;c.lineWidth=2.5;for(const side of [-1,1]){c.beginPath();c.moveTo(side*11+look-5,headY-9);c.lineTo(side*11+look+5,headY-8);c.stroke();}
    c.strokeStyle='#754b39';c.lineWidth=2;c.beginPath();c.moveTo(look+3,headY+3);c.lineTo(look+5,headY+11);c.lineTo(look,headY+12);c.stroke();
    c.strokeStyle=s.beard?'#d1a284':'#7e4d3b';c.beginPath();c.moveTo(-7+look,headY+21);c.quadraticCurveTo(look,headY+24,7+look,headY+21);c.stroke();
    c.restore();
  }
  class Renderer {
    constructor(canvas){this.canvas=canvas;this.c=canvas.getContext('2d');this.effects=[];this.shake=0;this.cached=null;this.court='arena';this.resize();}
    resize(){const dpr=Math.min(root.devicePixelRatio||1,2);this.canvas.width=W*dpr;this.canvas.height=H*dpr;this.dpr=dpr;this.cached=null;}
    onEvent(e,g){
      if(['score','block','steal','super','dunk'].includes(e.type)){
        const x=e.side===undefined?g.ball.x:g.players[e.side].x,y=e.type==='score'?266:g.ball.y;
        const color=e.type==='block'?'#8fe9fd':e.type==='super'?'#ffa342':e.type==='steal'?'#5cecbe': '#efbb64';
        for(let i=0;i<25;i++)this.effects.push({x,y,vx:(Math.random()-.5)*410,vy:-Math.random()*330,life:.8+Math.random()*.4,color});
        if(e.type==='dunk'||e.type==='super')this.shake=.23;
      }
    }
    background(c,court){
      const street=court==='street',g=c.createLinearGradient(0,0,0,H);g.addColorStop(0,street?'#183249':'#0c1829');g.addColorStop(.55,street?'#34445d':'#13273d');g.addColorStop(1,'#18384c');c.fillStyle=g;c.fillRect(0,0,W,H);
      if(street){
        for(let i=0;i<16;i++){const hh=45+((i*31)%110);c.fillStyle=i%2?'#1b2d42':'#21354a';c.fillRect(i*83-12,210-hh,71,hh+68);c.fillStyle='#e7b883';for(let j=0;j<4;j++)for(let k=0;k<3;k++)if((i+j+k)%3)c.fillRect(i*83+6+j*14,220-hh+k*22,5,9);}
        c.strokeStyle='#455d70';c.lineWidth=1;for(let i=0;i<60;i++){c.beginPath();c.moveTo(i*26-100,250);c.lineTo(i*26+90,80);c.stroke();c.beginPath();c.moveTo(i*26-100,80);c.lineTo(i*26+90,250);c.stroke();}
      }else{
        for(let row=0;row<5;row++){
          c.fillStyle=row%2?'#192d43':'#15253a';c.fillRect(0,76+row*25,W,25);
          for(let i=0;i<66;i++){const n=(i*17+row*31)%12;const x=i*19+row%2*9;c.fillStyle=['#6988a0','#345773','#ad7954','#536780','#a3abb1','#4b7995'][n%6];c.beginPath();c.arc(x,87+row*25,3.6,0,Math.PI*2);c.fill();c.fillStyle=n%3===0?'#af672f':n%3===1?'#284c72':'#38546c';rounded(c,x-4,90+row*25,8,10,2);c.fill();}
        }
        const light=c.createLinearGradient(0,0,0,150);light.addColorStop(0,'rgba(123,210,255,.09)');light.addColorStop(1,'rgba(123,210,255,0)');c.fillStyle=light;c.beginPath();c.moveTo(180,0);c.lineTo(445,270);c.lineTo(60,270);c.closePath();c.fill();c.beginPath();c.moveTo(1010,0);c.lineTo(1170,270);c.lineTo(790,270);c.closePath();c.fill();
        c.fillStyle='#a9c9d8';for(const x of [180,1010]){rounded(c,x-34,28,68,5,2);c.fill();}
      }
      c.fillStyle='#07131f';c.fillRect(0,211,W,55);c.fillStyle='#19354e';c.fillRect(0,212,W,3);
      text(c,"COURT KINGS  //  2026",600,239,20,'#7696ab','center',800);text(c,'PLAY YOUR GAME',264,239,12,'#3d647f');text(c,'ONE COURT. TWO STARS.',942,239,12,'#3d647f');
      c.fillStyle=street?'#516a7b':'#b08350';c.fillRect(0,285,W,H-285);
      if(!street){for(let j=0;j<15;j++){c.fillStyle=j%2?'rgba(236,188,127,.13)':'rgba(70,40,18,.08)';c.fillRect(0,285+j*26,W,25);c.strokeStyle='rgba(61,41,21,.11)';c.lineWidth=1;for(let i=0;i<10;i++){c.beginPath();c.moveTo(i*153+(j%3)*52,285+j*26);c.lineTo(i*153+(j%3)*52,311+j*26);c.stroke();}}}
      const fg=c.createLinearGradient(0,285,0,H);fg.addColorStop(0,'rgba(28,34,40,.08)');fg.addColorStop(1,'rgba(10,22,34,.32)');c.fillStyle=fg;c.fillRect(0,285,W,H-285);
      c.fillStyle=street?'#204b5b':'#1b4254';c.beginPath();c.moveTo(72,318);c.lineTo(305,318);c.lineTo(272,597);c.lineTo(47,597);c.closePath();c.fill();c.beginPath();c.moveTo(1128,318);c.lineTo(895,318);c.lineTo(928,597);c.lineTo(1153,597);c.closePath();c.fill();
      c.strokeStyle='rgba(255,239,212,.64)';c.lineWidth=3;
      c.beginPath();c.moveTo(71,315);c.lineTo(1129,315);c.lineTo(1172,601);c.lineTo(28,601);c.closePath();c.stroke();
      c.beginPath();c.moveTo(600,315);c.lineTo(600,601);c.stroke();c.beginPath();c.ellipse(600,453,90,66,0,0,Math.PI*2);c.stroke();
      for(const side of [-1,1]){const x=side===-1?77:1123;c.beginPath();c.ellipse(x,454,370,137,0,side===-1?-Math.PI/2:Math.PI/2,side===-1?Math.PI/2:Math.PI*1.5);c.stroke();const xx=side===-1?292:908;c.beginPath();c.ellipse(xx,455,47,84,0,side===-1?-Math.PI/2:Math.PI/2,side===-1?Math.PI/2:Math.PI*1.5);c.stroke();c.beginPath();c.moveTo(side===-1?70:1130,320);c.lineTo(xx,320);c.lineTo(xx,594);c.lineTo(side===-1?40:1160,594);c.stroke();}
      c.save();c.translate(600,451);c.scale(1,.70);text(c,'K',0,0,118,'rgba(28,47,53,.44)','center',900);c.restore();
      text(c,'26',600,579,18,'rgba(246,220,176,.5)');
      c.strokeStyle='rgba(12,29,40,.20)';c.lineWidth=2;c.beginPath();c.moveTo(0,FLOOR+6);c.lineTo(W,FLOOR+6);c.stroke();
      for(const hoop of HOOPS){
        const right=hoop.x>600,x=hoop.x+(right?48:-48);
        c.strokeStyle='#263d51';c.lineWidth=14;c.beginPath();c.moveTo(x+(right?26:-26),505);c.lineTo(x+(right?26:-26),210);c.lineTo(x,210);c.stroke();
        c.fillStyle='rgba(204,233,246,.20)';c.strokeStyle='#a9bcc8';c.lineWidth=5;rounded(c,x-4,hoop.y-97,8,111,3);c.fill();c.stroke();
        c.strokeStyle='rgba(232,241,245,.78)';c.lineWidth=2;for(let n=0;n<7;n++){const xx=hoop.x-27+n*9;c.beginPath();c.moveTo(xx,hoop.y+3);c.lineTo(hoop.x+(xx-hoop.x)*.48,hoop.y+43);c.stroke();}for(let n=1;n<4;n++){c.beginPath();c.moveTo(hoop.x-27+n*4,hoop.y+n*10);c.lineTo(hoop.x+27-n*4,hoop.y+n*10);c.stroke();}
        c.strokeStyle='#f09a45';c.lineWidth=5;c.beginPath();c.moveTo(hoop.x-28,hoop.y);c.lineTo(hoop.x+28,hoop.y);c.stroke();
      }
    }
    draw(game,dt=1/60){
      const c=this.c;c.setTransform(this.dpr,0,0,this.dpr,0,0);
      const court=game.options.court||'arena';
      if(!this.cached||court!==this.court){this.cached=document.createElement('canvas');this.cached.width=W;this.cached.height=H;this.background(this.cached.getContext('2d'),court);this.court=court;}
      c.clearRect(0,0,W,H);c.save();if(this.shake>0){this.shake-=dt;c.translate(Math.sin(game.time*120)*3,Math.cos(game.time*130)*2);}
      c.drawImage(this.cached,0,0);
      for(const p of game.players){
        if(game.mode==='practice'&&p.side===1)continue;
        if(p.dash>0){c.globalAlpha=.18;for(let n=3;n>0;n--)person(c,{...p,x:p.x-p.facing*n*17},game.time);c.globalAlpha=1;}
        person(c,p,game.time);
        if(game.state!=='idle'){
          const yy=p.y+27,active=game.ball.owner===p.side;
          if(active){c.fillStyle=p.side===0?'#8ebcff':'#f59489';c.beginPath();c.moveTo(p.x-7,yy+3);c.lineTo(p.x+7,yy+3);c.lineTo(p.x,yy-4);c.closePath();c.fill();}
          text(c,p.star.short,p.x,yy+22,12,p.side===0?'#d4e5ff':'#ffe0db');
          if(p.charge!==null){const width=82,x=p.x-width/2,y=p.y-p.star.height-50; c.fillStyle='#071222';rounded(c,x-3,y-3,width+6,16,7);c.fill();c.fillStyle='#2b3a4d';rounded(c,x,y,width,10,4);c.fill();const gw=game.greenWindow(p);c.fillStyle='#76e4ad';c.fillRect(x+(.73-gw)*width,y,gw*2*width,10);c.fillStyle=p.charge>.73+gw?'#ef7a5d':'#ebbe67';rounded(c,x,y,clamp(p.charge,0,1)*width,10,4);c.fill();c.fillStyle='#fff';c.fillRect(x+clamp(p.charge,0,1)*width-2,y-3,3,16);}
        }
      }
      const b=game.ball;
      if(b.trail.length){for(let i=0;i<b.trail.length;i++){c.globalAlpha=(i/b.trail.length)*.24;c.fillStyle=b.special?'#ffa65c':'#ffddae';c.beginPath();c.arc(b.trail[i].x,b.trail[i].y,(i/b.trail.length)*11+1,0,Math.PI*2);c.fill();}c.globalAlpha=1;}
      if(b.y<H+15)ball(c,b.x,b.y,12,game.time*5,b.special);
      for(const e of this.effects){e.life-=dt;e.x+=e.vx*dt;e.y+=e.vy*dt;e.vy+=700*dt;c.globalAlpha=clamp(e.life*2,0,1);c.fillStyle=e.color;c.fillRect(e.x,e.y,4,4);}this.effects=this.effects.filter(e=>e.life>0);c.globalAlpha=1;
      if(game.noticeTimer>0 && game.notice){c.fillStyle='rgba(6,19,33,.9)';const ww=Math.max(190,game.notice.length*13);rounded(c,600-ww/2,40,ww,39,8);c.fill();text(c,game.notice,600,60,18,game.notice.includes('GREEN')?'#8cf0b2':'#f2c281');}
      if(game.state==='countdown'){const n=Math.ceil(game.stateTimer);c.fillStyle='rgba(5,14,25,.36)';c.fillRect(0,0,W,H);text(c,n>0?String(n):'GO',600,320,128,'#fff');text(c,'GET READY',600,405,18,'#d2e1ec');}
      c.restore();
    }
  }
  root.CourtRender={Renderer,person,ball,text};
})(globalThis);
