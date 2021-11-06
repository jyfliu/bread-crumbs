const { mat3 } = glMatrix;

// TODO: load from file
// chrome does not support loading from a local file for security reasons
// so will need to host a http server on the remote and fetch the file over http
const vertexShaderText = [
  'precision mediump float;',
  'attribute vec2 pos;',
  'uniform mat3 uMVP;',
  'void main() {',
  '  gl_Position = vec4((uMVP * vec3(pos, 1.0)).xy, 0.0, 1.0);',
  '}',
].join('\n');

const fragmentShaderText = [
  'precision mediump float;',
  'uniform vec3 uColour;',
  'void main() {',
  '  gl_FragColor = vec4(uColour, 1.0);',
  '}',
].join('\n');

const keys = {};
let keysChanged = false;
let world = [[]];
let entities = [];
let healths = [];
let sprites = [ // TODO change to actual sprites
  new Float32Array([1., 0., 0.]),
  new Float32Array([0., 0.8, 0.]),
  new Float32Array([0., 0., 0.9]),
  new Float32Array([0.3843, 0.5843, 0.2157]),
  new Float32Array([0.1451, 0.2078, 0.1608]),
  new Float32Array([0.1176, 0.1646, 0.1294]),
  new Float32Array([0.05, 0.05, 0.05]),
  new Float32Array([1., 1., 0.]),
  new Float32Array([1., 0., 1.]),
  new Float32Array([0., 1., 1.]),
];

const colours = {
  red: new Float32Array([1., 0., 0.]),
  green: new Float32Array([0., 1., 0.]),
  blue: new Float32Array([0., 0., 1.]),
  black: new Float32Array([0., 0., 0.]),
  white: new Float32Array([1., 1., 1.]),
};

// position
let camX = 0.;
let camY = 0.;
// velocity
let camVX = 0.;
let camVY = 0.;
let playerX = 0.;
let playerY = 0.;
const aspectRatio = 800./600; // TODO query this from the page
const camSize = 10;
const halfCamW = camSize * aspectRatio;
const halfCamH = camSize;

// different camera smoothing techniques helpers
// linear interp
const lerp = (start, end, amount) => {
  return (1 - amount) * start + amount * end;
};

const cameraLerp = (dt) => {
  camVX = lerp(camVX, playerX - camX, 0.12);
  camVY = lerp(camVY, playerY - camY, 0.12);

  camX = lerp(camX, camX + camVX, 0.12);
  camY = lerp(camY, camY + camVY, 0.12);
};

// smooth critical damping
const cd_smoothTime = 500;
const cd_omega = 2. / cd_smoothTime;

const cd_maxSmoothSpeed = 1000.; // no max

const cameraSmoothCD = (dt) => {
  const x = cd_omega * dt;
  const exp = 1./ (1. + x + 0.48 * x * x + 0.235 * x * x * x);
  let changeX = Math.min(cd_maxSmoothSpeed, Math.max(-cd_maxSmoothSpeed, camX - playerX));
  let tempX = (camVX + cd_omega * changeX) * dt;
  camVX = (camVX - cd_omega * tempX) * exp;
  camX = playerX + (changeX + tempX) * exp;

  let changeY = Math.min(cd_maxSmoothSpeed, Math.max(-cd_maxSmoothSpeed, camY - playerY));
  let tempY = (camVY + cd_omega * changeY) * dt;
  camVY = (camVY - cd_omega * tempY) * exp;
  camY = playerY + (changeY + tempY) * exp;
};


class Entity {
  constructor(x, y, w, h, spriteID, isPlayer) {
    this.x = x;
    this.y = y;
    this.w = w;
    this.h = h;
    this.spriteID = spriteID;
    if (isPlayer) {
      playerX = x;
      playerY = y;
    }
  }
  MVP() {
    let M = mat3.create()
    // note function application order is backwards
    // TODO move magic numbers. The meanings are
    // 600/800 is the aspect ratio
    // 20 is half of the number of units we want to display on our screen
    // (so our current view is from cam.x-20 to cam.x+20 units)
    mat3.scale(M, M, [1./halfCamW, 1./halfCamH, 1.0]); // project to screen position
    mat3.translate(M, M, [-camX, -camY]); // translate model to camera position
    mat3.translate(M, M, [this.x, this.y]); // translate model to world position
    mat3.scale(M, M, [this.w, this.h, 1.0]); // scale model to correct size
    return M
  }
};

const init = () => {

  const canvas = document.getElementById('game-canvas');
  const gl = canvas.getContext('webgl');

  if (!gl) {
    // some browsers like older edge don't support webgl
    console.log('WebGL not supported, falling back to experimental-webgl');
    gl = canvas.getContext('experimental-webgl');
  }

  if (!gl) {
    alert('Your browser does not support WebGL');
  }

  gl.clearColor(0.75, 0.85, 0.8, 1.0);

  // init shaders
  const vertexShader = gl.createShader(gl.VERTEX_SHADER);
  const fragmentShader = gl.createShader(gl.FRAGMENT_SHADER);

  gl.shaderSource(vertexShader, vertexShaderText);
  gl.shaderSource(fragmentShader, fragmentShaderText);

  gl.compileShader(vertexShader);
  if (!gl.getShaderParameter(vertexShader, gl.COMPILE_STATUS)) {
    console.error('ERROR compiling vertex shader!', gl.getShaderInfoLog(vertexShader));
    return;
  }
  gl.compileShader(fragmentShader);
  if (!gl.getShaderParameter(fragmentShader, gl.COMPILE_STATUS)) {
    console.error('ERROR compiling fragment shader!', gl.getShaderInfoLog(fragmentShader));
    return;
  }

  const program = gl.createProgram();
  gl.attachShader(program, vertexShader);
  gl.attachShader(program, fragmentShader);

  gl.linkProgram(program);
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    console.error('ERROR linking program!', gl.getProgramInfoLog(program));
    return;
  }

  // if debugging
  gl.validateProgram(program);
  if (!gl.getProgramParameter(program, gl.VALIDATE_STATUS)) {
    console.error('ERROR validating program!', gl.getProgramInfoLog(program));
    return;
  }

  // init key events
  window.addEventListener('keydown', event => {
    const key = event.key.toLowerCase();
    console.log(key)
    keys[key] = true;
    keysChanged = true;
  });
  window.addEventListener('keyup', event => {
    const key = event.key.toLowerCase();
    keys[key] = false;
    keysChanged = true;
  });

  const bufferObject = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, bufferObject);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([
     1,  1,
     1, -1,
    -1, -1,
     1,  1,
    -1,  1,
    -1, -1,
  ]) , gl.STATIC_DRAW);

  const posAttr = gl.getAttribLocation(program, 'pos');
  gl.vertexAttribPointer(
    posAttr,
    2,
    gl.FLOAT,
    gl.FALSE,
    2 * Float32Array.BYTES_PER_ELEMENT,
    0,
  );
  gl.enableVertexAttribArray(posAttr);

  const uMVP = gl.getUniformLocation(program, 'uMVP');
  const uColour = gl.getUniformLocation(program, 'uColour');

  const render = (dt) => {
    if (keysChanged) {
      sock.emit('update_keys', keys);
      keysChanged = false;
    }
    if (Math.abs(playerX - camX) > halfCamW * 1.2 || Math.abs(playerY - camY) > halfCamH * 1.2) {
      // if camera gets too far then teleport it to player
      console.log('reset camera');
      camX = playerX;
      camY = playerY;
      camAX = camAY = camVX = camVY = 0;
    }

    cameraSmoothCD(dt);

    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    gl.useProgram(program);

    // render world
    let worldStartX = Math.max(0, Math.floor(camX - halfCamW - 1));
    let worldStartY = Math.max(0, Math.floor(camY - halfCamH - 1));
    let worldEndX = Math.min(world.length - 1, Math.floor(camX + halfCamW + 1));
    let worldEndY = Math.min(world[0].length - 1, Math.floor(camY + halfCamH + 1));
    for (let i = worldStartX; i <= worldEndX; ++i) {
      for (let j = worldStartY; j <= worldEndY; ++j) {
        // TODO move this and optimize
        let M = mat3.create();
        mat3.scale(M, M, [1./halfCamW, 1./halfCamH, 1.0]); // project to screen position
        mat3.translate(M, M, [-camX, -camY]); // translate model to camera position
        mat3.translate(M, M, [i+0.5, j+0.5]); // translate model to world position
        mat3.scale(M, M, [1., 1., 1.0]); // scale model to correct size
        gl.uniformMatrix3fv(uMVP, gl.False, M);
        gl.uniform3fv(uColour, sprites[world[i][j]]);
        gl.drawArrays(gl.TRIANGLES, 0, 6);
      }
    }
    // render entities
    entities.forEach(entity => {
      gl.uniformMatrix3fv(uMVP, gl.False, entity.MVP());
      gl.uniform3fv(uColour, sprites[entity.spriteID]);
      gl.drawArrays(gl.TRIANGLES, 0, 6);
    });

    healths.forEach(health => {
        let [x, y, w, h, hp, maxHp] = health;

        // TODO refactor
        let VP = mat3.create();
        mat3.scale(VP, VP, [1./halfCamW, 1./halfCamH, 1.0]); // project to screen position
        mat3.translate(VP, VP, [-camX, -camY]); // translate model to camera position
        mat3.translate(VP, VP, [x, y+0.5*w+0.5]); // translate model to world position
        let M = mat3.create();
        // black rectangle
        mat3.scale(M, VP, [1., 0.15, 1.]);
        gl.uniformMatrix3fv(uMVP, gl.False, M);
        gl.uniform3fv(uColour, colours.black);
        gl.drawArrays(gl.TRIANGLES, 0, 6);

        // red
        mat3.scale(M, VP, [0.97, 0.12, 1.]);
        gl.uniformMatrix3fv(uMVP, gl.False, M);
        gl.uniform3fv(uColour, colours.red);
        gl.drawArrays(gl.TRIANGLES, 0, 6);

        // green
        let ratio = hp / maxHp;
        if (ratio < 0) ratio = 0.;
        if (ratio > 1) ratio = 1.;
        mat3.translate(M, VP, [0.97 * (ratio - 1), 0.]);
        mat3.scale(M, M, [0.97 * ratio, 0.12, 1.]);
        gl.uniformMatrix3fv(uMVP, gl.False, M);
        gl.uniform3fv(uColour, colours.green);
        gl.drawArrays(gl.TRIANGLES, 0, 6);
    });
  };

  let running = true;
  let start;
  const loop = (time) => {
    if (start === undefined) {
      start = time;
    }
    const delta = time - start;
    start = time;
    render(delta);
    if (running) {
      requestAnimationFrame(loop);
    }
  };

  // connect to server
  let ip = prompt('Type IP here')
  if (!ip) ip = 'localhost';
  var sock = io.connect('http://' + ip + ':6942');

  sock.on("connect", () => requestAnimationFrame(loop));
  sock.on("entities", elist => {
    entities = elist.map(tup => new Entity(...tup));
  });
  sock.on("health", hlist => {
    healths = hlist;
  });
  sock.on("world", world_data => {
    world = world_data;
  });
};

