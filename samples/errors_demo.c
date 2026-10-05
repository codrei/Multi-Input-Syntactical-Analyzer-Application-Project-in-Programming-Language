// C demo: common mistakes that SyntaxLens finds.
#include <stdio.h>

int main(void) {
    int count = 10
    double price = 5 + * 2;
    char *name = "Ada;
    char grade = 'AB';
    int 2nd = 3;
    if (count > 5 {
        printf("big\n");
    }
    for (int i = 0, i < 3, i++) {
        printf("%d\n", i);
    }
    if count > 0 {
        count--;
    }
    int octal = 09;
    while (count > 0);
    break;
}