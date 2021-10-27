const vertexShaderText = [
  'precision mediump float;',
  'attribute vec2 vertPosition;',
  'void main() {',
  '  gl_Position = vec4(vertPosition, 0.0, 1.0);',
  '}',
].join('\n');

const fragmentShaderText = [
  'precision mediump float;',
  'void main() {',
  '  gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0);',
  '}',
].join('\n');

const keys = {};

class Player {
  constructor() {
    this.x = 0;
    this.y = 0;
    this.vertices = new Float32Array([
      this.x, this.y + 0.1,
      this.x - 0.1, this.y - 0.1,
      this.x + 0.1, this.y - 0.1,
    ]);
  }
  render() {
    this.vertices[0] = this.x;
    this.vertices[1] = this.y + 0.1;
    this.vertices[2] = this.x - 0.1;
    this.vertices[3] = this.y - 0.1;
    this.vertices[4] = this.x + 0.1;
    this.vertices[5] = this.y - 0.1;
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
    keys[key] = true;
  });
  window.addEventListener('keyup', event => {
    const key = event.key.toLowerCase();
    keys[key] = false;
  });

  // init Player
  const player = new Player();

  const updatePlayer = (x, y) => {
    player.x = x;
    player.y = y;
    console.log(x, y);
  };

  const bufferObject = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, bufferObject);
  gl.bufferData(gl.ARRAY_BUFFER, player.vertices, gl.STATIC_DRAW);

  const positionAttrLocation = gl.getAttribLocation(program, 'vertPosition');
  gl.vertexAttribPointer(
    positionAttrLocation,
    2,
    gl.FLOAT,
    gl.FALSE,
    2 * Float32Array.BYTES_PER_ELEMENT,
    0,
  );
  gl.enableVertexAttribArray(positionAttrLocation);

  const render = () => {
    sock.emit('key_pressed', keys);

    player.render();
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    gl.useProgram(program);

    gl.bindBuffer(gl.ARRAY_BUFFER, bufferObject);
    gl.bufferData(gl.ARRAY_BUFFER, player.vertices, gl.STATIC_DRAW);

    gl.drawArrays(gl.TRIANGLES, 0, 3);
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
  sock.on("update", updatePlayer);
};

