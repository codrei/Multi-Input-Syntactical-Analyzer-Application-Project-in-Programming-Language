#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define MAX_ITEMS 10
#define SQUARE(x) ((x) * (x))
#define LOG(msg) \
    printf("%s\n", msg)
#pragma once

#ifdef DEBUG
#define TRACE 1
#else
#define TRACE 0
#endif

typedef struct {
    int x;
    int y;
} Point;

struct Node {
    int value;
    struct Node *next;
};

typedef unsigned long ulong;

enum Color { RED, GREEN, BLUE };

static const int LIMIT = 100;

int add(int, int);
int counter(void);
int sum(const int *values, size_t count);
void log_all(const char *fmt, ...);

int add(int a, int b) {
    return a + b;
}

int counter(void) {
    static int calls = 0;
    calls++;
    return calls;
}

int sum(const int *values, size_t count) {
    int total = 0;
    for (size_t i = 0; i < count; i++) {
        total += values[i];
    }
    return total;
}

void log_all(const char *fmt, ...) {
    (void)fmt;
}

int main(int argc, char **argv) {
    int numbers[MAX_ITEMS] = {1, 2, 3};
    Point p = {1, 2};
    struct Node *head = NULL;
    enum Color color = GREEN;
    char *name = malloc(16);
    unsigned int flags = 0;

    (void)argc;
    (void)argv;
    LOG("start");
    counter();
    printf("%d\n", add(p.x, p.y));
    printf("%d\n", SQUARE(4));

    switch (color) {
        case RED:
            puts("red");
            break;
        default:
            puts("other");
            break;
    }

    while (flags < 3) {
        flags++;
    }

    if (head == NULL && name != NULL) {
        strcpy(name, "ok");
    } else {
        puts("no");
    }

    free(name);
    return sum(numbers, MAX_ITEMS) > 0 ? 0 : 1;
}
