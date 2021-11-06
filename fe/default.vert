precision mediump float;
attribute vec2 pos;
uniform mat3 uMVP;
void main() {
  gl_Position = vec4((uMVP * vec3(pos, 1.0)).xy, 0.0, 1.0);
}
