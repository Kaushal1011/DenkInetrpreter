program Main;
    var x, y : integer;
    var t1 : boolean;
    var f1 : boolean;
    var t2 : boolean;
    var f2 : boolean;
    var t3 : boolean;
    var f3 : boolean;
    var t4 : boolean;
    var f4 : boolean;
    var t5 : boolean;
    var f5 : boolean;
    var t6 : boolean;
    var f6 : boolean;
    var t7 : boolean;
    var f7 : boolean;
begin { Main }
    x := 1;
    y := 0;
    t1 := true;
    f1 := not true;
    t2 := not f1;
    f2 := t1 and false;
    t3 := t2 or f2;
    f3 := (t1 or f1) and f2;
    t4 := t1 or f1 and t2 or f2;
    f4 := not (t1 or (f1 and t2)) or f2;
    t5 := 1 = 1;
    f5 := x <> 1;
    t6 := (1 + 2 <= 3) or t5;
    f6 := (1 + 2 <= 3 * 1) and f5;
    t7 := not(1 + 2 < 3) and (1 < 2) or (3 * 2 > 4);
    f7 := not(1 + 2 < 3) or -1 * 2 + 3 > 4 * 5 - 2 * 3;
    writeln(x,y,t1,f1,t2,f2,t3,f3,f4,t4,t5,f5,t6,f6,t7,f7)
end.  { Main }
