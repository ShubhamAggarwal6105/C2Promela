struct node{
    struct node *next;
    int value;
};

void test(){
    struct node *new = malloc(sizeof(struct node));
    free(new);
}