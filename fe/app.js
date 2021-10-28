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
  'void main() {',
  '  gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0);',
  '}',
].join('\n');

const keys = {};
let entities = [];

class Entity {
  constructor(x, y) {
    this.x = x;
    this.y = y;
    this.scale = 0.5 // TODO: delete all mentions of scale once sprites are introduced
  }
  MVP() {
    let M = mat3.create()
    mat3.translate(M, M, [this.x, this.y]);
    mat3.scale(M, M, [600./800, 1.0, 1.0]);
    mat3.scale(M, M, [this.scale, this.scale, 1.0]);
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

  // init Player
  const updateEntities = (e) => {
    entities = e.map(tup => new Entity(...tup));
    entities[0].scale = 1.0;
  };

  const bufferObject = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, bufferObject);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([
     0.1,  0.1,
     0.1, -0.1,
    -0.1, -0.1,
     0.1,  0.1,
    -0.1,  0.1,
    -0.1, -0.1,
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

  const render = () => {
    sock.emit('key_pressed', keys);

    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    gl.useProgram(program);

    entities.forEach(entity => {
      gl.uniformMatrix3fv(uMVP, gl.False, entity.MVP());
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
  var sock = io.connect('http://localhost:6942');

  sock.on("connect", () => requestAnimationFrame(loop));
  sock.on("update", updateEntities);
};

