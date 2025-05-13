void example(){
    unsigned char x = 0;

    while (1){
        if (x < 5){
            if (x % 2 == 0){
                printf("Even: %d\n", x);
            }
            else{
                printf("Odd: %d\n", x);
            }
            x++;
        }
        else{
            break;
        }
    }
}

int main(){
    example();
    return 0;
}