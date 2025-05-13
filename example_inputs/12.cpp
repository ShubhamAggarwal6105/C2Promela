struct node{
    struct node *next;
    int value;
};
struct node *tail;

void test(struct node *tmp){
    tail->next = tmp;
    tail = tmp;
}