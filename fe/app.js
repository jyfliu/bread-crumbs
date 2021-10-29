const { mat3 } = glMatrix;

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
let entities = [];
let healths = [];
let colours = [
  new Float32Array([1., 0., 0.]),
  new Float32Array([0., 0.6, 0.]),
  new Float32Array([0., 0., 0.9]),
];

class Entity {
  constructor(x, y, w, h, spriteID) {
    this.x = x;
    this.y = y;
    this.w = w;
    this.h = h;
    this.spriteID = spriteID;
  }
  MVP() {
    let M = mat3.create()
    // note function application order is backwards
    // TODO move magic numbers. The meanings are
    // 600/800 is the aspect ratio
    // 20 is half of the number of units we want to display on our screen
    // (so our current view is from cam.x-20 to cam.x+20 units)
    mat3.scale(M, M, [600./800/10, 1./10, 1.0]); // project to screen position
    // mat3.translate(M, M, [-cam.x, -cam.y]); // translate model to camera position
    mat3.translate(M, M, [this.x, this.y]); // translate model to world position
    mat3.scale(M, M, [this.w, this.h, 1.0]); // scale model to correct size
    return M
  }
  render() {
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
  });
  window.addEventListener('keyup', event => {
    const key = event.key.toLowerCase();
    keys[key] = false;
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

  const render = () => {
    sock.emit('key_pressed', keys);

    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    gl.useProgram(program);

    entities.forEach(entity => {
      gl.uniformMatrix3fv(uMVP, gl.False, entity.MVP());
      gl.uniform3fv(uColour, colours[entity.spriteID]);
      gl.drawArrays(gl.TRIANGLES, 0, 6);
    })
  };

  let running = true;
  let start;
  const loop = (time) => {
    if (start === undefined) {
      start = time;
    }
    const delta = time - start;
    start = time;
    render();
    if (running) {
      requestAnimationFrame(loop);
    }
  };

  // connect to server
  let ip = prompt('Type IP here')
  if (!ip) ip = 'localhost';
  var sock = io.connect('http://' + ip + ':6942');

  sock.on("connect", () => requestAnimationFrame(loop));
  sock.on("update", elist => {
    entities = elist.map(tup => new Entity(...tup));
  });
  sock.on("health", elist => {
    healths = elist.map(tup => tup[4]);
    document.getElementById("tmphealthbar").innerHTML = "HP: " + healths.join(', ') + ". ";
  });
};

