program AnaliseNumero;

procedure AnalisarNumero(n: integer);
begin
  if (n mod 2) = 0 then
    writeln('O número é par.')
  else
    writeln('O número é ímpar.');

  if n > 0 then
    writeln('O número é positivo.')
  else if n < 0 then
    writeln('O número é negativo.')
  else
    writeln('O número é zero.');

  if (n >= 1) and (n <= 100) then
    writeln('O número está entre 1 e 100.')
  else
    writeln('O número está fora do intervalo 1..100.');
end;

var valor: integer;
begin
  writeln('Introduza um número inteiro:');
  readln(valor);
  AnalisarNumero(valor);
end.
