proctype f(chan in_f; ) {
    int a[5];
    int n;
    n = 5;
    int i;
    i = 0;
do
    :: (i < n) ->
    int j;
    j = 0;
do
    :: (j < ((n - i) - 1)) ->
if
    :: (a[j] > a[j + 1]) ->
    swap(a[j], a[j + 1]);
fi;
    j = j + 1;
    :: else -> break;
od;
    i = i + 1;
    :: else -> break;
od;
end :
printf("End of f\n");
}

