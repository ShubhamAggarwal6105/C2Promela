#include <stdbool.h>

void proc1(){
    printf("Process 1 running \n");
}

void proc2(){
    printf("Process 2 running \n");
}

int main(){
    proc1();
    proc2();
    return 0;
}