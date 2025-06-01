program ConstExampleInput;
const
  PI = 3.14;
var
  r: real;
begin
  writeln('Cálculo da área de um círculo. Introduz o raio:');
  readln(r);
  writeln('Área: ', PI * r * r);
end.
