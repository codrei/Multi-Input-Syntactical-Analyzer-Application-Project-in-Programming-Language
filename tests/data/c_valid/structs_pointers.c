/* Structs, pointers, arrays and dynamic memory in C. */
#include <stdio.h>
#include <stdlib.h>

typedef struct {
    int x;
    int y;
} Point;

struct Node {
    int value;
    struct Node *next;
};

enum Color { RED, GREEN, BLUE };

static void swap(int *a, int *b)
{
    int temp = *a;
    *a = *b;
    *b = temp;
}

static struct Node *push(struct Node *head, int value)
{
    struct Node *node = (struct Node *) malloc(sizeof(struct Node));
    if (node == NULL) {
        exit(1);
    }
    node->value = value;
    node->next = head;
    return node;
}

int main(int argc, char *argv[])
{
    Point p = {1, 2};
    Point *pp = &p;
    pp->x = pp->y * 2;

    int a = 5, b = 7;
    swap(&a, &b);

    struct Node *list = NULL;
    for (int i = 0; i < 3; i++) {
        list = push(list, i * 10);
    }
    for (struct Node *it = list; it != NULL; it = it->next) {
        printf("%d\n", it->value);
    }
    while (list != NULL) {
        struct Node *next = list->next;
        free(list);
        list = next;
    }

    int matrix[2][3] = {{1, 2, 3}, {4, 5, 6}};
    int *first = &matrix[0][0];
    enum Color color = GREEN;
    char letter = 'z' - 1;
    printf("%d %d %d %d %d %c %d\n", p.x, a, b, *first, (int) color, letter, argc);
    return argv[0] != NULL ? 0 : 1;
}
