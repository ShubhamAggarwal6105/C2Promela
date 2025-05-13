void continue_example() {
 for (int i = 0; i < 10; i++) {
 if (i == 2) {
    printf("Skip i = 2");
    continue;
 }
printf("i");
 }
}
int main() {
 continue_example();
 return 0;
}
