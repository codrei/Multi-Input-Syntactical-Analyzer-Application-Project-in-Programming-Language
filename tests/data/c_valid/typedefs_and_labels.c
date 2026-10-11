#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX(a, b) ((a) > (b) ? (a) : (b))

typedef struct Node {
    int value;
    struct Node *next;
} Node;

struct Point {
    int x, y;
} origin = {0, 0}, *current = NULL;

union Number {
    int i;
    float f;
};

enum Level { LOW, MEDIUM = 5, HIGH };

typedef enum {
    RED,
    GREEN
} Color;

static int add(int a, int b);
int apply(int (*fn)(int, int), int a, int b);
void print_all(const char *label,
               const int *values,
               size_t count);

static int add(int a, int b)
{
    return a + b;
}

int apply(int (*fn)(int, int), int a, int b)
{
    return fn(a, b);
}

void print_all(const char *label,
               const int *values,
               size_t count)
{
    printf("%s:", label);
    for (size_t i = 0; i < count; i++)
        printf(" %d", values[i]);
    printf("\n");
}

static Node *push(Node *head, int value)
{
    Node *node = malloc(sizeof *node);
    if (!node)
        return head;
    node->value = value;
    node->next = head;
    return node;
}

struct Point *make_point(int x, int y)
{
    struct Point *p = malloc(sizeof(struct Point));
    p->x = x;
    p->y = y;
    return p;
}

int main(void)
{
    int values[] = {3, 1, 2};
    int total = 0;
    unsigned long big = 10UL;
    Node *list = NULL;
    struct Point *p = make_point(1, 2);
    struct Point q = { .x = 1, .y = 2 };
    union Number n;
    enum Level level = HIGH;
    Color color = GREEN;
    char name[16];

    n.i = 4;
    strcpy(name, "abc");
    list = push(list, 1);
    list = push(list, 2);
    total = apply(add, values[0], values[1]);
    total += MAX(total, 7);
    ++total;
    --total;
    print_all("values", values, 3);

    switch (level) {
    case LOW:
        total = 0;
        break;
    case HIGH:
        total++;
        /* fall through */
    default:
        break;
    }

    for (int i = 0; i < 3; i++) {
        if (values[i] == 2)
            continue;
        if (values[i] > 2)
            goto done;
    }
done:
    do {
        total--;
    } while (total > 100);

    while (list) {
        Node *next = list->next;
        free(list);
        list = next;
    }
    printf("%d %lu %d %d %s %d %d\n", total, big, q.x, color, name, n.i,
           p->x);
    free(p);
    return 0;
}
