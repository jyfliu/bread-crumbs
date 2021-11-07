const { mat3 } = glMatrix;

// TODO: load from file
// chrome does not support loading from a local file for security reasons
// so will need to host a http server on the remote and fetch the file over http
const vertexShaderText = [
  'precision mediump float;',
  'attribute vec2 pos;',
  'attribute vec2 uv;',
  'uniform mat3 uMVP;',
  'varying highp vec2 vTextureCoord;',
  'void main() {',
  '  gl_Position = vec4((uMVP * vec3(pos, 1.0)).xy, 0.0, 1.0);',
  '  vTextureCoord = uv;',
  '}',
].join('\n');

const fragmentShaderText = [
  'precision mediump float;',
  'varying highp vec2 vTextureCoord;',
  'uniform sampler2D uSampler;',
  'void main() {',
  '  gl_FragColor = texture2D(uSampler, vTextureCoord);',
  '}',
].join('\n');

// Load textures
const isPowerOf2 = (val) => { return value & (value - 1) === 0; };
const loadTexture = (gl, url) => {
  const texture = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, texture);

  // temporary texture while loading
  gl.texImage2D(
    gl.TEXTURE_2D,
    0, // level
    gl.RGBA, // internal format
    2, 2, // width, height
    0, // border (?)
    gl.RGBA, // source format
    gl.UNSIGNED_BYTE, // source
    new Uint8Array([ // pixels
      255, 0, 255, 255,
      0, 0, 0, 255,
      255, 0, 255, 255,
      0, 0, 0, 255,
    ]),
  );

  const image = new Image();
  image.onload = () => {
    gl.bindTexture(gl.TEXTURE_2D, texture);
    gl.texImage2D(gl.TEXTURE_2D, level, internalFormat,
                  srcFormat, srcType, image);

    // WebGL1 has different requirements for power of 2 images
    // vs non power of 2 images so check if the image is a
    // power of 2 in both dimensions.
    if (isPowerOf2(image.width) && isPowerOf2(image.height)) {
       // Yes, it's a power of 2. Generate mips.
       gl.generateMipmap(gl.TEXTURE_2D);
    } else {
       // No, it's not a power of 2. Turn off mips and set
       // wrapping to clamp to edge
       gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
       gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
       gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    }
  };
  image.src = url;

  return texture;
};
const loadColourTexture = (gl, r, g, b) => {
  // colour is given as an rgba array like [0xff, 0xff, 0xff, 0xff]
  const texture = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, texture);

  gl.texImage2D(
    gl.TEXTURE_2D,
    0, // level
    gl.RGBA, // internal format
    1, 1, // width, height
    0, // border (?)
    gl.RGBA, // source format
    gl.UNSIGNED_BYTE, // source
    new Uint8Array([r, g, b, 255]), // pixel
  );

  return texture;
};

const keys = {};
let keysChanged = false;
let world = [[]];
let entities = [];
let healths = [];
let sprites = [ // TODO improve sprite loading system
  0xff0000,
  0x00cc00,
  0x0000e6,
  0x629537,
  0x253529,
  0x1e2a21,
  0x0d0d0d,
  0xffff00,
  0xff00ff,
  0x00ffff,
];

const colours = {
  red:   0xff0000,
  green: 0x00ff00,
  blue:  0x0000ff,
  black: 0x000000,
  white: 0xffffff,
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
    mat3.scale(M, M, [1./halfCamW, 1./halfCamH, 1.0]); // project to screen position
    mat3.translate(M, M, [-camX, -camY]); // translate model to camera position
    mat3.translate(M, M, [this.x, this.y]); // translate model to world position
    mat3.scale(M, M, [this.w, this.h, 1.0]); // scale model to correct size
    return M
  }
};

const main = () => {

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

  // init colours
  Object.keys(colours).map(name => {
    console.log(name, (colours[name] & 0xff0000) >> 16, // r
      (colours[name] & 0x00ff00) >>  8, // g
      (colours[name] & 0x0000ff) >>  0, // b
    )
    colours[name] = loadColourTexture( gl,
      (colours[name] & 0xff0000) >> 16, // r
      (colours[name] & 0x00ff00) >>  8, // g
      (colours[name] & 0x0000ff) >>  0, // b
    );
  });
  // temporary sprite loading system (until we actually have sprites)
  sprites = sprites.map(colour => {
    return loadColourTexture( gl,
      (colour & 0xff0000) >> 16, // r
      (colour & 0x00ff00) >>  8, // g
      (colour & 0x0000ff) >>  0, // b
    );
  });

  // init buffers
  const drawBuffer = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, drawBuffer);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([
     1,  1,
     1, -1,
    -1, -1,
     1,  1,
    -1,  1,
    -1, -1,
  ]), gl.STATIC_DRAW);

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

  const texCoordBuffer = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, texCoordBuffer);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([
    1, 1,
    1, 0,
    0, 0,
    1, 1,
    0, 1,
    0, 0,
  ]), gl.STATIC_DRAW);

  const uvAttr = gl.getAttribLocation(program, 'uv');
  gl.vertexAttribPointer(
    uvAttr,
    2,
    gl.FLOAT,
    gl.FALSE,
    0,
    0,
  );
  gl.enableVertexAttribArray(uvAttr);

  const uMVP = gl.getUniformLocation(program, 'uMVP');
  const uSampler = gl.getUniformLocation(program, 'uSampler');

  const drawSquare = (MVP, texture) => {
    gl.uniformMatrix3fv(uMVP, gl.False, MVP);
    // texture
    gl.bindBuffer(gl.ARRAY_BUFFER, texCoordBuffer);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, texture);
    gl.uniform1i(uSampler, 0);
    // draw square
    gl.bindBuffer(gl.ARRAY_BUFFER, drawBuffer);
    gl.drawArrays(gl.TRIANGLES, 0, 6);
  };

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
    // update view and projection matrices
    let VP = mat3.create();
    mat3.scale(VP, VP, [1./halfCamW, 1./halfCamH, 1.0]); // project to screen position
    mat3.translate(VP, VP, [-camX, -camY]); // translate model to camera position
    let M = mat3.create();

    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    gl.useProgram(program);

    // render world
    let worldStartX = Math.max(0, Math.floor(camX - halfCamW - 1));
    let worldStartY = Math.max(0, Math.floor(camY - halfCamH - 1));
    let worldEndX = Math.min(world.length - 1, Math.floor(camX + halfCamW + 1));
    let worldEndY = Math.min(world[0].length - 1, Math.floor(camY + halfCamH + 1));
    for (let i = worldStartX; i <= worldEndX; ++i) {
      for (let j = worldStartY; j <= worldEndY; ++j) {
        mat3.translate(M, VP, [i+0.5, j+0.5]); // translate model to world position
        //mat3.scale(M, M, [1., 1., 1.]); // scale model to correct size
        drawSquare(M, sprites[world[i][j]]);
      }
    }
    // render entities
    entities.forEach(entity => {
      gl.uniformMatrix3fv(uMVP, gl.False, entity.MVP());
      drawSquare(entity.MVP(), sprites[entity.spriteID]);
    });

    healths.forEach(health => {
        let [x, y, w, h, hp, maxHp] = health;

        let M0 = mat3.create();
        mat3.translate(M0, VP, [x, y+0.5*w+0.5]); // translate model to world position
        // black rectangle
        mat3.scale(M, M0, [1., 0.15, 1.]);
        drawSquare(M, colours.black);

        // red
        mat3.scale(M, M0, [0.97, 0.12, 1.]);
        drawSquare(M, colours.red);

        // green
        let ratio = hp / maxHp;
        if (ratio < 0) ratio = 0.;
        if (ratio > 1) ratio = 1.;
        mat3.translate(M, M0, [0.97 * (ratio - 1), 0.]);
        mat3.scale(M, M, [0.97 * ratio, 0.12, 1.]);
        drawSquare(M, colours.green);
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

